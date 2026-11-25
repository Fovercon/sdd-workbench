# Record a check and cite its result

Use the recorder for authorized, non-interactive foreground checks when the
project permits appending them to a Markdown process log. Python 3.10+ is
required. Resolve `scripts/evidence.py` relative to this Skill.

The existing project format, frozen whole-file references and write authority
determine the allowed record location. For an explicit self-contained format,
use its established evidence workflow. If Python is unavailable, follow the
existing manual receipt workflow.

## Save the actual check

Initialize an authorized log with its title if it does not exist. Select a
new check ID for each real invocation, including setup repairs and later
regressions. Include the actual source, tests and relevant fixtures in
`--source`. An absent source file is recorded as missing.

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
Keep historical cards and
their stable locations available after advancing to S02.

## Verify the references actually saved

```sh
python3 /path/to/sdd-implement-slice/scripts/evidence.py verify \
  --root . --document design/tasks.md
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
