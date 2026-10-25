#!/usr/bin/env python3
"""Read-only check of a board response against the current immutable view and sources.

A validated response is not approval evidence. The controller must establish the
actual user's intent/authority in conversation and use the owning stage's records.
"""
import argparse
import json
from pathlib import Path
import sys
from project_view import previous_version, sha
from project_view_lib import decisions, evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--view', type=Path, required=True, help='Current board version, not an arbitrary historical one')
    parser.add_argument('--response', type=Path, required=True)
    args = parser.parse_args()
    try:
        data, snapshot, _ = previous_version(args.view.resolve())
        items = evidence.inspect(args.root.resolve(), snapshot)
        result = decisions.validate_response(snapshot, items, sha(data), json.loads(args.response.read_text()))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
