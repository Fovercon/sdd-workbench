# Project overview → requirements → slices → verification

Use this optional extension when the requested board must explain what is being
built, how work is split, what is blocked and how requirements are verified.
Read the existing sources first. This is a derived view, not a replacement Spec,
Tasks file, approval record or test runner. Ordinary status questions stay read-only.

## Author individual source-bound records

Keep the existing item fields, source hashes and lifecycle bindings from
[project-view.md](project-view.md). Add `work` only when the relevant facts can be
read from actual sources. Never extract DONE or PASS by guessing from prose,
file existence, stage location, test counts or a previous green board.

| `work.type` | Required fields inside `work` | Owning item |
|---|---|---|
| `brief` | `in_scope`, `out_of_scope`: lists of concrete boundaries; empty means unrecorded | One optional stage-bound `progress` item; label is the goal, note explains the problem/context |
| `requirement` | `acceptance`: nonempty list of observable acceptance conditions/examples | `capability`, `stage: Spec`; label describes user behavior, note explains its purpose |
| `slice` | `requirement_ids`: nonempty list; `status`: `TODO`, `DOING`, `BLOCKED`, `DONE` | `capability`, `stage: Tasks`; note explains the slice's delivered behavior |
| `check` | `requirement_ids`, `slice_ids`: nonempty lists; `result`: `PASS`, `FAIL`, `NOT_RUN`, `UNKNOWN`; `acceptance_refs` maps requirement IDs to exercised acceptance indexes | `capability`, `stage: Converge`; note names the actual run/scope/limit; PASS requires `kind: runtime_evidence` |

A slice may include `depends_on` (other slice IDs) and `blocker` (concrete reason).
BLOCKED requires a blocker. DONE is an explicit execution fact from the Tasks or
execution record, separate from the item's evidence `state`. Link current actual
files with the existing item-level `implementation_ids`; each file must have a
`structure` item with `file`, and the slice must cite those files in its sources.
Do not invent planned files as current implementation. Shared files remain one node.

Every ID reference must identify an existing record of the correct type. Dependencies
must be acyclic. A check's requirement and slice links must describe the same scope.
A check for two slices must actually have exercised both; several checks may cover
one slice. Keep requirements/checks granular enough to expose missing acceptance
coverage. Citing the same broad report for many rows does not prove those behaviors:
use exact lines/sections and state each run's bounded scope. An unexecuted test may
be listed as NOT_RUN with its actual plan source; it cannot claim runtime PASS.

List distinct observable acceptance conditions separately. In a check, use
`acceptance_refs: {"R1": [1, 2]}` only if its cited run actually verified both
conditions. Indexes are 1-based positions in that exact requirement snapshot;
reordering or changing conditions requires re-reading and updating the sources and
mapping. A missing mapping stays a visible gap. Never map an untested condition to
a PASS to obtain green coverage. A known acceptance gap belongs on its requirement
row; do not bury it in an unrelated impact note while leaving the row green.

Example extension shapes (fragments only; replace IDs and add the standard item
fields and sources actually read before rendering):

```json
{"type":"requirement","acceptance":["找不到指定编号时提示未命中，不回退为标题匹配。"]}
{"type":"slice","requirement_ids":["R1"],"status":"DOING","depends_on":["S0"]}
{"type":"check","requirement_ids":["R1"],"slice_ids":["S1"],"result":"NOT_RUN","acceptance_refs":{"R1":[1]}}
```

## Read the resulting board

The enriched board opens at **项目总览**, with goal, in/out scope, bounded requirement,
slice and verification counts, a reading path, and actionable gaps. The existing
next-action card still uses `next_id`; source identity failures take priority.
Select **需求规格** to read acceptance conditions and related slices/checks;
**任务拆分** to see execution columns with explicit dependency links and blockers;
**对照验收** to follow each requirement through slices, implementation files and runs.
Click a name for evidence and related records. Browser back/deep links and no-JS
reading retain all observations. Legacy boards remain valid; missing structured
subjects are shown as missing rather than inferred from notes.

“所列验项通过” requires current usable requirement evidence, DONE slices, current
linked implementation files and applicable PASS records for **every** declared
slice and **every** listed acceptance condition. Any declared failed/unexecuted/unknown check prevents that row being green.
The calculation is conservative navigation over declared observations; it does not
run tests or prove that the author listed every requirement/acceptance condition.
A fresh source fingerprint does not establish human approval or semantic correctness.
The view never declares business acceptance, overall convergence or release readiness.

Changed/missing requirement, slice, implementation or check sources invalidate
linked downstream coverage on recheck/update. A return to an earlier stage also
withdraws downstream coverage. Historical recorded PASS/DONE remains visible beside
the warning, rather than being silently rewritten. The page is an offline snapshot:
source edits require a check/new version, not a browser refresh of an old snapshot.

## Verify the mainline

For the actual project, compare every row with its cited source. Follow requirement
→ slice → code → check and back. Confirm the scope, blockers, next action and
missing verification are understandable without opening full documents. Check
keyboard navigation, browser back/reload, original source links and narrow-screen
reading/inner table scrolling. Inspect actual screenshots. Use synthetic data only
when explicitly labeled; never substitute it for project verification or approval.
