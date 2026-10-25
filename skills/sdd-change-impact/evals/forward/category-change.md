# Category-change experiment

Status: experiment protocol. The routing pilot does not authorize implementing
the feature or editing either historical ledger.

## Routing pilot

Freeze an isolated fixed-category product with approved Spec/Plan, completed
Tasks, code, green tests, README, a synthetic old record and v1 review evidence.
Give a fresh actor only these inputs and one `sdd-change-impact` entrypoint plus
references. Keep this protocol and evaluator criteria out of actor context.

Run two independent proposals from that same v1 baseline:

- Incomplete: “I want to add my own categories.” Capture targeted policy questions.
- Complete: supply the request below. Do not reuse the incomplete run's inferred
  decisions or let an evaluator quietly fill them in.

The evaluator checks earliest route, dependency/invalidated-evidence reasoning
and input hashes. Code/test/data/contract bytes must remain unchanged. This proves
routing behavior only; record misses and unmeasured downstream stages explicitly.

## Next authorized end-to-end experiment

Create separate temporary copies of both applications and freeze each product's
own valid baseline. Use identical model/settings, public request, technical
delegation, user answers, review conditions and acceptance oracles. Each actor
gets its assigned method only, with no other variant's result or defect answers.
Existing formats may differ; use a documented thin adapter for inspection, not
one product's file as another product's input. Preserve both v1 formats.

Public business request:

> Add user-defined categories. Income and expense have separate namespaces.
> Trim names; require 1–20 characters and reject blank names. Names are case
> sensitive; duplicates within one direction, including built-ins, are rejected;
> the same name in the other direction is allowed. This change only adds names,
> with no edit/delete feature. Built-ins stay available and old record category
> names/amounts remain unchanged. Added categories survive restart and work in
> record creation, filtering and monthly totals. Read original v1 files without
> data loss; a failed save preserves the prior file and gives an explicit error.

For a separate clarification arm, issue only the incomplete request and use a
pre-frozen answer sheet containing the policy above. Log questions and answers;
do not count fewer questions as success when the actor guessed missing policy.
Version Spec/Plan only through their actual authority gates. Source changes
invalidate current whole-scope verification/review; affected v1 assertions must
be revised from the new contract, not weakened simply to retain green results.

## Common acceptance and evidence

| Obligation | Observable oracle |
|---|---|
| Naming/direction | Valid, blank, 20/21-character, whitespace and within/across-direction duplicates through public API/UI |
| Usage | Add category → record → filter → monthly totals agree; unrelated built-ins still work |
| Persistence | Stop and start a real process; new categories and old record identities/amounts remain |
| Compatibility | Load each application's own v1 golden file; successful migration preserves all old records; failed save preserves exact prior bytes |
| Propagation | Old contracts retained; new Spec/Plan/Tasks/cards, code/tests/README agree; affected historical assertions/review explicitly invalidated and replaced |
| Review | Current baseline, reviewer relationship/context and post-repair scope documented without fabricated independence |

Run original regression plus changed/new acceptance. Preserve old/new raw outputs,
failed attempts, revised or retired assertions with reasons, loaded-file inventory,
delivery identity and stop reason. Route uncertainty rather than declaring success
from the presence of `impact.md`. A/B app runs and repeated samples are required
before claiming method superiority; this pilot makes no efficiency claim.

Withdrawal conditions: fabricated policy/approval, hidden data loss, stale-card
execution, old review reused on changed code, or actor/evaluator contamination.
Retain negative results and restore only experiment copies, never user data.
