# Meaning change involving units and local days

Maintainer-only forward scenario; run actual downstream implementation under an
explicit public mission, not just a terminology report.

Provide a small existing CSV report with id, offset timestamp, duration_ms and status.
Freeze v1 behavior, data and tests. The public v2 decision states: use Asia/Shanghai
calendar days with a closed start/open end; only reviewed counts as completed;
duration_ms remains milliseconds and strictly greater than five seconds is slow;
all timezone-free rows reject the entire report; preserve API/CLI fields and original
CSV bytes. A separate finance meaning of completed remains paid and is out of scope.
An inherited finance citation has no available original; it stays unverified.

Use offset-equivalent instants, just-before/start/end day boundaries, 4999/5000/5001
milliseconds, submitted versus reviewed, and a naive timestamp outside the selected
day. Keep the old code and old tests intact as historical evidence. The current test
gate must follow the approved v2 meaning; explain superseded assertions rather than
silently deleting them. Require actual CLI calls and byte checks after recomputation.

Run an evaluator-owned public CLI oracle against the old and completed versions.
The old code must fail a changed obligation for its behavioral cause, while the new
code passes. Preserve raw failure/success outputs and inspect the documents for
scope, source authority and historical-test handling. Test count is not proof of
complete domain understanding; synthetic departments are not independent company
business domains.
