#!/usr/bin/env python3
"""Verify a declared SHA256SUMS file against an independent list of deliverables."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import sys


def relative_name(name):
    name = name.removeprefix("./")
    if (not name.isprintable() or "\\" in name
            or any(part in ("", ".", "..") for part in name.split("/"))):
        raise ValueError(f"unsupported relative path: {name!r}")
    return name


def regular_file(root, name):
    path = root
    for part in name.split("/"):
        path = path / part
        if path.is_symlink():
            raise ValueError(f"symlink in path: {name!r}")
    if not path.is_file():
        raise ValueError(f"missing or non-regular file: {name!r}")
    return path


def check(root, manifest, expected):
    if os.name != "posix":
        raise ValueError("requires a POSIX project snapshot")
    wanted = {relative_name(name) for name in expected}
    receipt = regular_file(root, relative_name(manifest))
    listed = {}
    with receipt.open(encoding="utf-8", newline="\n") as lines:
        for number, row in enumerate(lines, 1):
            match = re.fullmatch(r"([0-9a-fA-F]{64}) [ *](.+)", row.removesuffix("\n"))
            if not match:
                raise ValueError(f"invalid SHA256SUMS row at line {number}")
            name = relative_name(match[2])
            if name in listed:
                raise ValueError(f"duplicate path at line {number}: {name!r}")
            listed[name] = match[1].lower()

    if wanted != listed.keys():
        raise ValueError(f"missing: {sorted(wanted - listed.keys())!r}; "
                         f"unexpected: {sorted(listed.keys() - wanted)!r}")
    for name, recorded in listed.items():
        path = regular_file(root, name)
        if path.samefile(receipt):
            raise ValueError(f"manifest lists itself: {name!r}")
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest() != recorded:
            raise ValueError(f"digest mismatch: {name!r}")
    return len(listed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="root of a stable project snapshot")
    parser.add_argument("manifest", help="project-relative path to the separate SHA256SUMS file")
    parser.add_argument("expected", nargs="+", help="project-relative paths from the delivery agreement")
    args = parser.parse_args()
    try:
        count = check(args.project, args.manifest, args.expected)
    except (OSError, ValueError) as error:
        sys.exit(f"FAIL: {error}")
    print(f"PASS: {count} files")
