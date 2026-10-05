"""Exercise checkout and link behavior without touching the user's Git or home."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
ORIGIN = "https://github.com/Olbbemi/Flax.git"


class SharedTodoTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.home = self.base / "home"
        self.home.mkdir()
        self.destination = self.home / ".local/share/flax"
        self.env = {
            key: value for key, value in os.environ.items()
            if not key.startswith("GIT_")
        }
        self.env.update(
            HOME=str(self.home), XDG_CONFIG_HOME=str(self.home / ".config"),
            GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
            GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1",
        )
        self.repo = self.base / "source"
        self.run_command("git", "init", "--template=", str(self.repo))
        for name in ("scripts/link_shared_todo.py", "tools/scripts/git/post-checkout"):
            target = self.repo / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        self.git("config", "user.name", "Hook Test")
        self.git("config", "user.email", "hook-test@example.invalid")
        self.git("remote", "add", "origin", ORIGIN)
        self.git("add", ".")
        self.git("commit", "-m", "Test fixture")

    def run_command(self, *args, cwd=None, success=True):
        result = subprocess.run(
            args, cwd=cwd, env=self.env, capture_output=True, text=True,
            stdin=subprocess.DEVNULL,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def git(self, *args, **kwargs):
        return self.run_command("git", *args, cwd=self.repo, **kwargs)

    def link(self, *args, success=True, repo=None):
        return self.run_command(
            sys.executable, "-B", str(ROOT / "scripts/link_shared_todo.py"),
            str(repo or self.repo), *args, success=success,
        )

    def hook(self, old="0" * 40, branch="1", success=True):
        return self.run_command(
            str(self.repo / "tools/scripts/git/post-checkout"), old, "1" * len(old),
            branch, cwd=self.repo, success=success,
        )

    def test_manual_link_and_repeat_preserve_records(self):
        self.link()
        self.assertEqual(self.destination.resolve(), self.repo / "data")
        record = self.destination / "todo/existing.md"
        record.write_text("keep this record\n")
        self.link()
        self.assertEqual(record.read_text(), "keep this record\n")

    def test_dry_run_does_not_write(self):
        self.link("--dry-run")
        self.assertFalse((self.repo / "data").exists())
        self.assertFalse(self.destination.parent.exists())

    def test_destination_conflicts_preserved_before_creating_data(self):
        self.destination.parent.mkdir(parents=True)
        for kind in ("file", "directory", "other_link", "broken_link"):
            with self.subTest(kind=kind):
                if kind == "file":
                    self.destination.write_text("keep")
                elif kind == "directory":
                    self.destination.mkdir()
                else:
                    target = self.home if kind == "other_link" else self.base / "missing"
                    self.destination.symlink_to(target)
                self.link(success=False)
                self.assertTrue(os.path.lexists(self.destination))
                self.assertFalse((self.repo / "data").exists())
                if self.destination.is_symlink():
                    self.assertEqual(self.destination.readlink(), target)
                    self.destination.unlink()
                elif self.destination.is_dir():
                    self.destination.rmdir()
                else:
                    self.assertEqual(self.destination.read_text(), "keep")
                    self.destination.unlink()

    def test_broken_link_to_expected_data_is_preserved(self):
        self.destination.parent.mkdir(parents=True)
        self.destination.symlink_to(self.repo / "data")
        self.link(success=False)
        self.assertFalse((self.repo / "data").exists())
        self.assertEqual(self.destination.readlink(), self.repo / "data")

    def test_invalid_storage_is_preserved(self):
        data = self.repo / "data"
        data.write_text("keep")
        self.link(success=False)
        self.assertEqual(data.read_text(), "keep")
        data.unlink()
        data.mkdir()
        (data / "todo").symlink_to(self.home)
        self.link(success=False)
        self.assertEqual((data / "todo").readlink(), self.home)
        self.assertFalse(os.path.lexists(self.destination))

    def test_wrong_or_missing_origin_is_skipped_by_hook(self):
        self.git("remote", "set-url", "origin", "https://github.com/Someone/Flax.git")
        self.hook()
        self.link(success=False)
        self.git("remote", "remove", "origin")
        self.hook()
        self.assertFalse((self.repo / "data").exists())

    def test_normal_checkout_and_file_checkout_do_not_prepare_paths(self):
        self.hook(old="a" * 40)
        self.hook(branch="0")
        self.assertFalse((self.repo / "data").exists())
        self.assertFalse(os.path.lexists(self.destination))

    def test_initial_checkout_supports_ssh_and_sha256(self):
        self.git("remote", "set-url", "origin", "ssh://git@github.com/Olbbemi/Flax")
        self.hook(old="0" * 64)
        self.assertTrue((self.destination / "todo").is_dir())

    def test_real_clone_and_worktree_checkout(self):
        clone = self.base / "clone with spaces"
        # Transport rewriting keeps the canonical origin while cloning locally.
        self.run_command(
            "git", "-c", f"url.{self.repo.as_uri()}.insteadOf={ORIGIN}",
            "clone", "--template=", "-c", "core.hooksPath=tools/scripts/git",
            ORIGIN, str(clone),
        )
        self.assertEqual(self.destination.resolve(), clone / "data")
        self.assertTrue((self.destination / "todo").is_dir())
        worktree = self.base / "extra worktree"
        self.run_command("git", "worktree", "add", "--detach", str(worktree), cwd=clone)
        self.assertEqual(self.destination.resolve(), clone / "data")
        self.assertFalse((worktree / "data").exists())
        self.link(repo=worktree, success=False)
        # Even without a link, a subsequent checkout must not initialize it again.
        self.destination.unlink()
        self.run_command("git", "checkout", "--detach", "HEAD", cwd=clone)
        self.assertFalse(os.path.lexists(self.destination))

    def test_hook_reports_conflicts(self):
        self.destination.parent.mkdir(parents=True)
        self.destination.write_text("keep")
        self.hook(success=False)
        self.assertEqual(self.destination.read_text(), "keep")
        self.assertFalse((self.repo / "data").exists())


if __name__ == "__main__":
    unittest.main()
