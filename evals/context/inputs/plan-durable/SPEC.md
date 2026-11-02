# Durable job admission v1
Status: APPROVED (synthetic fixture state only, not Plan approval).

FR-01: Two independent processes may call enqueue(path, job_id, payload).
IDs and payloads are strings; identity is exact. Successful calls return the stored
{'id': job_id, 'payload': payload}. Repeating the same ID and payload, including
concurrently, returns that one record without duplicates. Same ID/different payload
raises ValueError without changing its stored record. Other input types excluded.
FR-02: list_jobs(path) returns those records in persisted admission order. Concurrent
overlapping calls may be ordered either way; a completed call precedes a later call.
No records may be lost by competing admissions; partial/corrupt records never appear.
FR-03: An enqueue success is acknowledged only after durable commit. After process
termination (including SIGKILL) and reopen, every acknowledged record remains. For
a call killed before acknowledgment, either committed or absent is allowed; retry
is safe under FR-01. Power loss/hardware failure, remote filesystems and job
execution/scheduling are excluded. Do not add an execution queue service.
FR-04: Explicit import_legacy(source, target) reads the old JSON list into a separate
new target. Preserve IDs, payloads, order and source bytes. An exact rerun must not
duplicate records or drop newer admissions. Invalid JSON or conflicting IDs abort
without partial import. A fresh import needs an empty target; rerun of a completed
same-source import is allowed. Preserve a rollback route to the untouched old file;
switch consumers only after verification with writers stopped. Technical format
and locking design are open choices; new target path is supplied explicitly.
FR-05: Existing enqueue/list_jobs public names and record shapes remain compatible;
path now names the explicit new target. No consumer reads private storage bytes.
AC-01: Competing processes with distinct/same IDs preserve FR-01/02 on reopen.
AC-02: Kill before/after commit acknowledgment and retry satisfies FR-01/03.
AC-03: Valid legacy import/rerun, malformed input and conflicting IDs satisfy FR-04.

Design approval remains pending; the current request authorizes planning only.
