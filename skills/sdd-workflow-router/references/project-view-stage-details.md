# Readable rules, clarification, execution and delivery views

Use this additive observation extension when the board needs these four stages.
Keep the normal source-bound item and lifecycle fields in project-view.md. The
board is a derived snapshot, not a rule author, test runner or delivery approver.

Add `stage_detail` to a `progress` or `capability` item with nonempty `note` and
actual `sources`. Keep it separate from `work`: a behavior slice and a test run
are different subjects. Existing plain records remain readable as stage evidence.
Do not create records merely to fill a section; missing input has an explicit
empty state. Unknown commands, ownership, delivery facts and approvals stay unknown.

| Item stage | `stage_detail.type` | Content |
|---|---|---|
| Constitution | `constraint` | Label states the rule; note explains its actual scope/limit, citing project rules |
| Constitution | `command` | Exact `command`; optional root-relative `cwd`; optional recorded `result` |
| Align | `context` | Actual users, problem and current difficulty, from intent sources |
| Align | `assumption` | Assumption and what remains unverified; do not turn source existence into confirmation |
| Implement | `implementation` | What actually exists and what is incomplete; link actual tasks/files |
| Implement | `test_run` | Required `result`; optional exact `command` and `cwd`; note states run scope and limitations |
| Finish | `deliverable` | Required `delivery_status`; optional `path`, with stricter rules below |
| Finish | `usage` | Conditions, steps and expected result; optional `steps`, `command`, `cwd` |
| Finish | `limitation` | Actual remaining issues, unsupported scope and known limits; no automatic risk acceptance |
| Finish | `handoff` | Actual next work; optional known `owner` and `steps`; do not invent a responsible person |
| Finish | `recovery` | Source-documented recovery/rollback steps, optional command/cwd; state unverified boundaries |

All types may carry `record_ids`, a list of source-dependent observation IDs.
They must exist; self-links/cycles are rejected. Citing a linked file/record only
as a label is insufficient: read and include all load-bearing sources for claims.
Source changes propagate along these references and withdraw current support.
Returned upstream stages also require review of downstream records. Stable links
navigate to the original record/evidence; they do not approve it.

`result`: PASS / FAIL / NOT_RUN / UNKNOWN. PASS and FAIL require
`kind: runtime_evidence` with the actual report, scope, command when known, and
relevant code/contract inputs. A documented command without a result is explicitly
unexecuted/unknown; the renderer never runs it. Preserve original command bytes.
Do not substitute a green acceptance record for an unexecuted implementation test.
Separate the source's recorded outcome from whether you reran it: preserve a
previous report's PASS/FAIL in `result`, label its historical scope in `note`, and
state explicitly that this board generation did not rerun it. Use UNKNOWN only
when the recorded outcome itself is unknown. For an explicitly synthetic fixture,
the record can represent the fixture's reported run with `kind: runtime_evidence`
only when visibly labeled synthetic; it is never evidence of a real project run.
Do not turn a source-reported FAIL into UNKNOWN merely because you did not rerun it.
The Implement view also lists existing work slices and actual implementation_ids;
acceptance records stay labeled as such, rather than being counted as local tests.

`delivery_status`: PLANNED / PREPARED / DELIVERED. PLANNED may name a future
root-relative path, clearly shown as planned. PREPARED requires an actual `path`
also cited in sources; it is not delivered. DELIVERED additionally requires
`kind: runtime_evidence`, a distinct `delivery_receipt` path, and sources citing
both output and actual delivery receipt. Never infer delivered from file existence,
passing tests, a README or a prepared release. Show source/receipt drift separately
from the historical recorded delivery. Neither status authorizes publication.
`cwd`, `path`, `delivery_receipt` must stay within the declared project root;
prepared/delivered paths identify files, not directories.
The delivery_receipt field belongs only to DELIVERED records; preparation plans
must not present a draft receipt as an actual delivery receipt.

Example fragments; add normal item fields, own stage, note, and sources actually read:

```json
{"type":"command","command":"python3 -m unittest discover -s tests","cwd":".","result":"NOT_RUN"}
{"type":"test_run","result":"FAIL","record_ids":["implementation-file"]}
{"type":"deliverable","path":"README.md","delivery_status":"PREPARED"}
{"type":"handoff","owner":"the actual recorded owner","steps":["Complete the source-documented next action."]}
```

Align reuses a source-bound `work.type: brief` for goal/scope and the existing
`decision` records for actual unresolved human questions. Preserve their exact
subject, source, owner and reply route; only a real owner response can resolve them.
Do not create a simulated question, fabricate approval, or require a new decision
when the existing session already authorized the work.
When goal and boundaries are available, create that brief with structured
`in_scope` and `out_of_scope` lists. A plain record named “goal and scope” leaves
the dedicated section empty. For example, add this `work` object to its own
source-bound progress item (separate from `stage_detail`):

```json
{"type":"brief","in_scope":["Continue unfinished work after a pause."],"out_of_scope":["Production deployment."]}
```

Use plain language: rules, problem, task, test result, delivery file, usage steps,
remaining issue. State expected behavior and material limits directly. Keep the
neutral typography and top stage navigation. Avoid jargon invented for the board,
decorative colors, or turning every explanatory statement into a gate.

Keep completed bundles immutable when correcting observations. Write a new input
file if useful, then use `update --previous <old-view> --input <corrected-input>
--output <new-sibling-view>` with the root and other required CLI arguments. Never
delete an old bundle to reuse its directory, edit its generated HTML, or rewrite
its receipt. Keep both versions and their predecessor link for review.

Verify real browser navigation across all four stages, source links, command/source
text, pending questions, prepared-versus-delivered distinction, failed/unexecuted
runs, missing records, changed references, keyboard/deep links, narrow-screen inner
scrolling and no-JS reading. Preserve actual screenshots and immutable predecessors.
