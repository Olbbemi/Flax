#!/usr/bin/env python3
"""Prepare Flax's data/todo directory and shared data link."""

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys


FLAX_URL = re.compile(
    r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)"
    r"Olbbemi/Flax(?:\.git)?/?", re.IGNORECASE
)


class LinkError(Exception):
    pass


def git(*args, cwd):
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True,
        stdin=subprocess.DEVNULL,
    )
    if result.returncode:
        raise LinkError(result.stderr.strip() or "Git command failed.")
    return result.stdout.rstrip("\n")


def repository_root(directory):
    return Path(git("rev-parse", "--show-toplevel", cwd=directory)).resolve()


def is_main_worktree(root):
    git_dir = Path(git("rev-parse", "--absolute-git-dir", cwd=root)).resolve()
    common_dir = Path(git("rev-parse", "--git-common-dir", cwd=root))
    if not common_dir.is_absolute():
        common_dir = root / common_dir
    return git_dir == common_dir.resolve()


def is_flax(root):
    result = subprocess.run(
        ["git", "config", "--local", "--get", "remote.origin.url"],
        cwd=root, capture_output=True, text=True, stdin=subprocess.DEVNULL,
    )
    if result.returncode == 1:
        return False
    if result.returncode:
        raise LinkError(result.stderr.strip() or "Cannot read origin URL.")
    return FLAX_URL.fullmatch(result.stdout.rstrip("\n")) is not None


def shared_todo_paths(root):
    source = root / "data"
    for directory, boundary in ((source, root), (source / "todo", source.resolve())):
        if os.path.lexists(directory) and (
            not directory.is_dir() or not directory.resolve().is_relative_to(boundary)
        ):
            raise LinkError(f"Data path is not a directory inside its storage: {directory}")
    destination = Path.home() / ".local/share/flax"
    if (
        destination.is_symlink() and destination.is_dir()
        and destination.resolve() == source.resolve()
    ):
        return source, destination
    if os.path.lexists(destination):
        raise LinkError(f"Destination already exists; left unchanged: {destination}")
    for parent in destination.parents:
        if os.path.lexists(parent) and not parent.is_dir():
            raise LinkError(f"Parent is not a directory; left unchanged: {parent}")
    return source, destination


def link_shared_todo(root, dry_run=False):
    source, destination = shared_todo_paths(root)
    if dry_run:
        for directory in (source, source / "todo"):
            if not directory.exists():
                print(f"Would create directory: {directory}")
    else:
        (source / "todo").mkdir(parents=True, exist_ok=True)
    if destination.is_symlink():
        print(f"OK: Link already points to {source}")
    elif dry_run:
        print(f"Would link: {destination} -> {source}")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(source, target_is_directory=True)
        print(f"OK: {destination} -> {source}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        root = repository_root(args.repository)
        if not is_main_worktree(root):
            raise LinkError("Run the linker from the main worktree.")
        if not is_flax(root):
            raise LinkError("The repository's origin is not Olbbemi/Flax on GitHub.")
        link_shared_todo(root, dry_run=args.dry_run)
    except (LinkError, OSError, RuntimeError) as error:
        print(f"Flax todo link: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
