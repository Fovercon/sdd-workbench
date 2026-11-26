# Record a check and cite its result

Use the recorder for authorized, non-interactive foreground checks when the
project permits appending them to a Markdown process log. Python 3.10+ is
required. Resolve `scripts/evidence.py` relative to this Skill.

The existing project format, frozen references and current write authority
determine the allowed record location. Reuse an established project capture
that already preserves equivalent evidence. A self-contained receipt retains
its required inline fields even when raw output is stored in an authorized log.
If Python is unavailable or the log format cannot carry these records, use the
existing project workflow with invocation-specific output and tested identities.

## Contents

- [Save the actual check](#save-the-actual-check)
- [Use the generated reference](#use-the-generated-reference)
- [Verify the references actually saved](#verify-the-references-actually-saved)

## Save the actual check

Initialize an authorized log with its title if it does not exist. Select a
new check ID for each real invocation, including setup repairs and later
regressions. Include the actual source, tests and relevant fixtures in
`--source`. An absent source file is recorded as missing.

This capture serves proof-bearing foreground commands, not every search or
file read. Save the observation at the currently authorized project record
location so another session can reopen it from the receipt. After a test
revision, the next run has a new ID and preserves the previous output and
fingerprints. File hashes identify the tested bytes; they
do not preserve recoverable copies of historical source.

The first try of a selected check, including a preview immediately after
writing tests, is captured as it executes. Creating tests and then invoking
`record` in one shell call preserves this boundary without an extra test run.

The recorder executes that command once. For a required chronological trace,
choose that same trace as `--log`; its saved observation carries the command
and result. The slice closure cites the observation.

The following example uses a script path that you replace with the resolved
Skill location and a command selected from the current card.

```sh
python3 /path/to/sdd-implement-slice/scripts/evidence.py record \
  --root . --log trace.md --id s01-red-v1 \
  --source jobs.py --source test_jobs.py --from design/tasks.md \
  --timeout 120 -- python3 -B -m unittest -v test_jobs.RetryContract
```

The recorder appends an ASCII heading and JSONL records to the existing log.
It saves the actual argv, UTC start/end, stdout/stderr, child exit and source
identities. Output stays quoted as data. Stream chunks can be reassembled in
order with `data.encode("utf-8", "surrogateescape")` to recover their bytes.

A successfully saved observation returns `status=RECORDED` and exits 0.
Read `command_exit` for the command's actual outcome. A nonzero child exit
can be valid RED, a setup error or another failure. The returned
`stdout_tail` and `stderr_tail` show up to 4,096 final bytes per
stream. Inspect the saved output for a complete diagnostic and classify
the failure against the contract. `source_changes` identifies files that
changed during the command and require investigation.

Timeout, interruption or recording failure returns an error. An incomplete
entry supplies no successful-check evidence. Retain it and use a new ID for
an authorized later observation. Duplicate IDs are refused. The recorder
coordinates its own writes through a file lock; a replaced log is a conflict.
Command side effects remain subject to the project's existing permissions.

## Use the generated reference

Copy the returned Markdown `link` into the document named by `--from`.
The script computes the URL relative to that document and names an exact,
unique heading. A closure in the log itself can use fragment-only links
with those exact headings. Verify each document after saving its links.

The slice closure records outcome, actual changes, deviations, remaining
limits and Markdown links to these observations. The authorized task status
contains a Markdown link to that closure and any dependency it satisfies.
One real invocation can support several check roles through the same link.
Keep historical cards and their stable locations available after advancing to S02.

## Verify the references actually saved

```sh
python3 /path/to/sdd-implement-slice/scripts/evidence.py verify \
  --root . --document design/tasks.md --summary
```

Run verification on the task table and receipt documents after writing
their references. The command reads the links in that actual document.
It checks local file targets and heading anchors; generated check
anchors also require a complete, consistent record and matching digest.
Single-line links may use code-formatted labels, titles or reference
definitions. Detected unsupported link syntax, including a destination
continued after its opening parenthesis, reports `UNSUPPORTED` and prevents
`VERIFIED`. Use the generated single-line form for evidence citations.
This is a scoped link checker, not a complete Markdown renderer. Code
examples, bare textual pointers and external web links are outside this check.

`--summary` keeps the same status and exit code. `links_checked` counts original
reference results, including diagnostic rows. `history_counts` splits that same
total by history **before** anything is omitted; its counts sum to the total.
Repeated citations count separately. These are reference occurrences, not unique
commands, tests or executions.

`omission_policy` describes display rules, not this invocation's counts. `links`
omits normal `LINK_OK` rows. Every `RECORDED` reference keeps its target, history
and actual command exit, including nonzero exits. Only its `source_changes` and
`sources` fields are omitted when there are no recorded execution-time changes
and all current sources `MATCH`; the record row remains. All other rows retain
full diagnostics. `VERIFIED` does not mean tests passed or old results are
currently applicable. Omit `--summary` for the unchanged full per-reference output.
Neither mode writes files.

For recorded checks, `history=RECORDED` describes a complete historical
observation. The per-file `sources` values `MATCH`, `CHANGED`,
`MISSING` and `UNAVAILABLE` compare the current files with its starting
identity. Keep source changes during execution separate from later drift.
These values support the stage's applicability decision alongside contracts,
environment and any required fresh or independent checks.

Resolve missing or ambiguous targets and incomplete records before relying
on their evidence. Verification reads files and reports findings. Mechanical
reference corrections use the same document-edit authority as the original
update.
