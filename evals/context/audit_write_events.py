#!/usr/bin/env python3
"""Replay a closeout trial's filesystem notifications against exact authorized files."""
import argparse
import hashlib
import json
from pathlib import Path

if __package__:
    from .check_delivery_manifest import relative_name
else:
    from check_delivery_manifest import relative_name


WRITES = {"ATTRIB", "CLOSE_WRITE", "CREATE", "DELETE", "DELETE_SELF", "MODIFY",
          "MOVED_FROM", "MOVED_TO", "MOVE_SELF"}
WATCHED_ROOTS = {"project", "runtime", "sandbox-tmp"}


def watched_path(value):
    if not isinstance(value, str):
        raise ValueError("missing event path")
    path = relative_name(value)
    if path.split("/", 1)[0] not in WATCHED_ROOTS:
        raise ValueError(f"path outside the recorded roots: {value!r}")
    return path


def inspect(log_path, allowed_files):
    findings, issues = [], []
    digest = None
    allowed = set()
    record_count = None
    try:
        allowed = {watched_path(path) for path in allowed_files}
        if allowed & WATCHED_ROOTS:
            raise ValueError("--allow-file requires a file below a recorded root")
        raw = log_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        rows = json.loads(raw)
        if not isinstance(rows, list):
            raise ValueError("expected a JSON array of filesystem notifications")
        record_count = len(rows)
        for number, row in enumerate(rows, 1):
            if not isinstance(row, dict):
                issues.append(f"row {number}: invalid event record")
                continue
            events = row.get("events")
            if not isinstance(events, list) or not events or not all(isinstance(x, str) for x in events):
                issues.append(f"row {number}: missing or invalid event names")
                continue
            unknown = set(events) - WRITES
            if unknown:
                issues.append(f"row {number}: lost watch, overflow or unsupported events {sorted(unknown)}")
            writes = [name for name in events if name in WRITES]
            if not writes:
                continue
            try:
                path = watched_path(row.get("path"))
                if type(row.get("directory")) is not bool:
                    raise ValueError("missing or invalid directory flag")
            except ValueError as exc:
                issues.append(f"row {number}: {exc}")
                continue
            if path not in allowed or row["directory"]:
                findings.append({"row": number, "path": path, "events": writes})
    except (OSError, ValueError) as exc:
        issues.append(str(exc))
    status = "NO_OUT_OF_SCOPE_EVENTS_RECORDED"
    if issues:
        status = "INCOMPLETE"
    elif findings:
        status = "OUT_OF_SCOPE_EVENTS"
    return {"status": status, "log_sha256": digest, "record_count": record_count,
            "allowed_files": sorted(allowed), "findings": findings, "issues": issues}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="controller's watch.json")
    parser.add_argument("--allow-file", action="append", default=[], help="one permitted trial-relative file")
    args = parser.parse_args()
    result = inspect(args.log, args.allow_file)
    print(json.dumps(result, indent=2))
    raise SystemExit({"NO_OUT_OF_SCOPE_EVENTS_RECORDED": 0, "OUT_OF_SCOPE_EVENTS": 1, "INCOMPLETE": 2}[result["status"]])
