#!/usr/bin/env python3
"""Verify upstream Git trees and Cargo package checksums without network access."""

import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def object_hash(kind, content):
    return hashlib.sha1(kind + b' ' + str(len(content)).encode() + b'\0' + content).digest()


def tree_hash(folder):
    entries = []
    count = 0
    for path in folder.iterdir():
        name = os.fsencode(path.name)
        if path.name == '.git':
            raise ValueError(f'Nested Git metadata: {path}')
        if path.is_symlink():
            mode = b'120000'
            digest = object_hash(b'blob', os.fsencode(os.readlink(path)))
            count += 1
        elif path.is_dir():
            mode = b'40000'
            digest, children = tree_hash(path)
            count += children
        else:
            mode = b'100755' if path.stat().st_mode & 0o111 else b'100644'
            digest = object_hash(b'blob', path.read_bytes())
            count += 1
        entries.append((name + (b'/' if mode == b'40000' else b''),
                        mode + b' ' + name + b'\0' + digest))
    return object_hash(b'tree', b''.join(entry for _, entry in sorted(entries))), count


def main():
    sources = json.loads((ROOT / 'third_party/sources.json').read_text())
    for item in sources['libraries']:
        if item['local_modifications']:
            raise ValueError(f'Review local modifications before verifying {item["name"]}')
        digest, count = tree_hash(ROOT / item['path'])
        if digest.hex() != item['tree'] or count != item['tracked_file_count']:
            raise ValueError(f'Upstream snapshot differs: {item["path"]}')
        print(f'OK {item["name"]}: {count} files, Git tree {digest.hex()}')

    registry = json.loads((ROOT / 'third_party/rust-registry.json').read_text())
    for item in registry['packages']:
        root = ROOT / item['path']
        checksums = json.loads((root / '.cargo-checksum.json').read_text())
        if checksums['package'] != item['package_sha256']:
            raise ValueError(f'Package checksum differs: {root}')
        actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
        expected = set(checksums['files']) | {'.cargo-checksum.json'}
        if actual != expected:
            raise ValueError(f'Package file list differs: {root}')
        for filename, digest in checksums['files'].items():
            if hashlib.sha256((root / filename).read_bytes()).hexdigest() != digest:
                raise ValueError(f'Package file differs: {root / filename}')
    print(f'OK {len(registry["packages"])} registry packages: file lists and SHA-256 checksums')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as error:
        sys.exit(str(error))
