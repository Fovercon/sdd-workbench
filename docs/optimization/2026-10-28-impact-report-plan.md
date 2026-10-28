# Impact report precision implementation plan

> Execute inline with `executing-plans`; one fresh review at the end.

Goal: make existing Change Impact reports distinguish authority/time, original
contract owner versus the next unsynchronized stage, and evidence scope.

Spec: [the optimization plan](POST-0.5.0-PLAN.md), fourth-batch findings and next
batch input. The user authorized continued incremental optimization. This is a
bounded maintenance choice within that plan, not a new product decision.

## Constraints and design

- Work on `codex/skills-optimization` in the existing isolated worktree.
- Reuse the existing report/template and outcome/status vocabularies. No new
  skill, schema, approval, database, UI, business implementation or live install.
- Current validity is evaluated against the effective approved baseline. A
  proposed delta has conditional downstream effects. Historical PASS stays a
  historical fact and does not prove conformity to changed meaning.
- Keep the earliest owning route even if its exact delta is already approved;
  the next action starts at the first remaining unsynchronized stage.
- Each material evidence claim names what the source/assertion actually covers.
- Freeze inputs and runtime; keep negative trials and raw scores. No `--accept`,
  release, merge, or automatic push of this new batch.

## Task 5: one bounded report change

Interfaces: consumes the existing Change Impact workflow, model and template;
produces the same analysis outputs with explicit baseline and scope qualifiers.

- [x] RED: run five fresh controls per authority state using commit `28a1d3e`
  and unchanged impact fixtures/prompts. Read calls, final replies and reports;
  record actual defects before editing skill instructions. If controls show no
  relevant defect, retain current instructions instead.
- [x] GREEN (candidate attempted, then withdrawn): minimally adjust existing fields and reference guidance for the
  observed omissions; add forward cases that check semantics, not exact wording.
- [x] Verify five candidate runs per state against identical project/prompt
  bytes. Read every call/final claim and report; mechanical guards are separate.
- [x] Run root, router and context suites, package and documentation checks.
  A retained method change also runs the frozen standard profile against its
  exact runtime, without accepting a baseline or editing L2/L3/oracles.
- [x] One independent whole-branch review; Important/Critical findings get one
  RED/GREEN fix pass. Record limitations and deferred findings in the ledger.
- [x] Commit the verified bounded change locally; preserve experiment artifacts
  outside the package/repository. Do not publish.

## Review focus

1. PROPOSED with valid v1 convergence must not become currently invalid solely
   because a v2 proposal exists.
2. APPROVED v2 with an exact approved delta must not demand the same approval
   again; incomplete Plan/code/evidence remains visible.
3. A count output outside a shared masking dependency needs its own evidence;
   unchanged source bytes alone do not prove semantic independence.
4. Output assertions, static call-graph inspection and historical receipts prove
   different claims; no passing assertion is invented.
5. Compact replies and existing project formats retain the same distinctions
   without mandatory new ceremonies or a large duplicated report.

Pre-flight: one task; model semantics feed template fields and workflow handoff.
No shared implementation interface or migration is introduced.

## Execution ruling: candidate withdrawal and bounded guard repair

The first candidate improves current/conditional matrix columns but two fresh
proposal reports contradict the exact output delta. Withdraw its three runtime
instruction files and finish all frozen trials without repair. This does not
establish that the candidate caused those errors. Retain counterexamples and
semantic evaluation guidance; no method change means no new standard run.

### Task 6: propagate guard failure to shell callers

Scope: close the prior 4B deferred Minor in `evals/context/evaluate_workflow.py`.
Consume the existing `evaluate(case, run)` result without changing its checks or
JSON fields. Return exit 0 for PASS and 1 for FAIL, including identity rejection;
Python callers still receive a dictionary. This is evaluation maintenance.

- [x] RED: public CLI tests for a missing report, protected Spec modification and
  wrong-case dispatch each observe FAIL JSON but exit 0 (three failures).
- [x] GREEN: print the same result and map non-PASS to nonzero. The missing-report
  test also verifies a requested output yields PASS/0. Check stdout equals the
  saved report and wrong identity never executes project code.
- [x] Run context, root, router, package/docs and diff checks. Review the whole
  branch once and commit the retained change locally.

Pre-flight: Task 6 changes CLI status only; native trial Python callers consume
JSON dictionaries. Trials already use a frozen evaluator and retain its identity.
All installed skill runtime bytes must match `28a1d3e` after withdrawal.

Completion: the runtime candidate was rejected, not GREEN/accepted. The retained
CLI fix has RED/GREEN plus root105/router171/context37, package/docs and independent
review (no new findings). Local commit identity is recorded in Git and external
provenance; no push or release.
