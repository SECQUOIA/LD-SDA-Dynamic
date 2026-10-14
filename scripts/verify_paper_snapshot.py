"""Verify the recorded paper artifacts without regenerating published outputs."""

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def verify(root=ROOT):
    manifest = json.loads((root / 'paper' / 'manifest.json').read_text())
    problems = []
    actual = {
        str(path.relative_to(root))
        for directory in manifest['frozen_roots']
        for path in (root / directory).rglob('*')
        if path.is_file() and '__pycache__' not in path.parts
    }
    for name in sorted(actual - manifest['files'].keys()):
        problems.append(f'unrecorded: {name}')
    for name, expected in manifest['files'].items():
        path = root / name
        if not path.is_file():
            problems.append(f'missing: {name}')
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            problems.append(f'changed: {name}')
    return problems


def main():
    problems = verify()
    if problems:
        print('\n'.join(problems), file=sys.stderr)
        return 1
    count = len(json.loads((ROOT / 'paper' / 'manifest.json').read_text())['files'])
    print(f'Verified all {count} frozen paper artifact files.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
