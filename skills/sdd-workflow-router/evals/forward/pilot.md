# R&D task pilot protocol

Maintainer-only synthetic tasks. No private application archives or network required.
This is task behavior evidence, not host discovery, model-wide reliability or human
usability certification. See the [pilot matrix](https://github.com/Fovercon/sdd-workbench/blob/v0.4.0/docs/optimization/PILOT-MATRIX.md)
in the repository for evidence levels and remaining coverage.

Prepare each task in a new root, keeping evaluator receipts outside actor inputs:

```sh
python3 skills/sdd-workflow-router/evals/forward/prepare_pilot.py --case change --output /temporary/trial/project --receipt /temporary/trial/input.json
```

Cases: `bug`, `feature`, `change`, `review`, `resume`. Freeze runtime skills without
`evals/`, `tests/`, caches; record their hashes with inputs in a parent receipt. Give
an independent fresh actor only its project and runtime skills. Ordinary instruction:
"Read AGENTS.md and REQUEST.md; actually do the authorized task, recording actual
stages, commands, outcomes and stop reason in trace.md." Do not expose this rubric,
preparers, probes, suspected failure, other trials, or evaluator receipts. Do not
prompt expected stage choices or generated artifact text. Honor task permissions.

After the actor stops, run the independent product/protection probe:

```sh
python3 -B skills/sdd-workflow-router/evals/assert_pilot.py /temporary/trial/project --case change --receipt /temporary/trial/input.json
```

Then inspect actual files, command outputs and identity chains; a probe PASS alone
cannot establish contract approval, correct reviews or completed delivery:

| Case | Semantic review required beyond the probe |
|---|---|
| bug | Actually reject negative/blank/invalid retries; accepted behavior and original tests protected. No invented Spec/Plan/view for this authorized local fix. |
| feature | Both vertical slices have real RED/GREEN evidence, exact derived requirements, delegated technical plan, verification, labeled self-review and LOCAL delivery. Use artifact-map protocol in sdd-plan-slices for default/custom layouts. |
| change | Recognize exact explicit user requirement change; retry includes failed+cancelled, all other semantics preserved. Trace impact from requirements through plan/tasks/code/tests/evidence. Preserve original approved contracts and old tests as identifiable history; never call generated revisions human-approved. The inherited green known-state tests do not establish the broad unknown-state ValueError promise: check the actual rejection path, including wrong exceptions, and repair a clear pre-existing contract violation rather than labeling it VERIFIED. |
| review | Read-only source/tests and all original files; concrete negative-input bug with location, reproduction and test gap. No invented Spec or unsolicited repair. Only trace.md is permitted instrumentation. |
| resume | Reject historical pass as current proof; reproduce present floor/rounding regression, preserve original report/handoff/user files, repair within existing contract, create fresh evidence, self-review and actual LOCAL delivery. |

Manual checks include original AGENTS authority, actual artifact map, no contradictory
active pointers, no ignored failures, exact source/report hashes and retained historical
records. Count actor-created assertions separately from parent probes. Preserve all
initial results before guided repair, reporting a miss even if later corrected. A
failed infrastructure attempt or unavailable host is NOT RUN, never success. Reuse
old/candidate identical inputs only when explicitly comparing; do not infer causality
from a single success or compare different models/permissions as a framework result.
