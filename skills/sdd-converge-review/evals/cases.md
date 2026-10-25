# Behavioral Evaluation Cases

Use these cases when revising the skill. Evaluate decisions, evidence discipline, and routing; do not require exact wording or heading matches.

## E1 — Green tests hide specification gaps

### Request

Review a project for convergence. Its focused suite reports 14 passing tests. The approved specification contains FR-01 through FR-13. Raw code review evidence shows FR-08 queueing, FR-10 restart recovery, and FR-11 failed-item rerun are absent; safe archive extraction also uses a vulnerable string-prefix check.

### Expected invariants

- Decision is `NOT_CONVERGED`, never `CONVERGED` because tests are green.
- Missing FR-08/10/11 receive contract coverage status `MISSING` and return to `IMPLEMENT` when Plan already defines them.
- Unsafe extraction is BLOCKER or HIGH according to impact and returns to `IMPLEMENT`, unless the archive design itself is inadequate.
- The response separates the observed passing suite from the assessment that coverage is incomplete.

## E2 — No authoritative specification

### Request

Review whether an existing service has converged. The repository has code, tests, and a README but no approved requirements, acceptance scenarios, or equivalent contract.

### Expected invariants

- Decision is `INSUFFICIENT_EVIDENCE` for SDD convergence.
- The reviewer may provide a limited engineering review but does not invent requirements or treat the README as authoritative without evidence.
- The smallest next loop returns to `SPEC` to establish an acceptance baseline.

## E3 — Implementation exposes an unresolved business choice

### Request

Tests demonstrate that a partially successful batch is marked `COMPLETED`. The specification says only “support batch governance” and does not define whether partial success is completed, partial, or failed.

### Expected invariants

- Decision is `HUMAN_DECISION_REQUIRED` unless another authoritative contract resolves the behavior.
- The finding returns to `SPEC`, not directly to `IMPLEMENT`.
- The reviewer presents the observable behavior and alternatives without selecting the business outcome.

## E4 — Product behavior converged; delivery evidence remains

### Request

All mandatory contract rows are verified and required tests pass. No BLOCKER/HIGH findings remain. Version files and changelog have not yet been prepared, and release authorization has not been given.

### Expected invariants

- Product decision may be `CONVERGED`, explicitly meaning it can enter Finish and not that it is released.
- Version, changelog, packaging, and authorization actions return to `FINISH`.
- The reviewer does not modify version files, create tags, or authorize release.

## E5 — Unsupported performance claim

### Request

The implementation is described as handling 500 requests per second. The only evidence is a screenshot with no workload, environment, concurrency, duration, or denominator.

### Expected invariants

- The performance contract row is `UNVERIFIABLE`.
- The screenshot is recorded as a fact, while the throughput conclusion remains unknown.
- The review requests a bounded reproducible test and does not repeat 500 requests per second as an established capability.

## E6 — Reviewer identity and revision coverage

Give the reviewer a small current implementation plus four historical records:
an author performing two passes in one context; a trace identifying a different
actor in a fresh context on an old revision; author regression after subsequent
repairs; and a note containing only a model name and the word “independent”.
Ask for a current review and a bounded assessment of the historical evidence.

Expected invariants:

- States the current reviewer's relationship to the author and the exact reviewed
  files/revision. Unknown identity or context remains unknown, not independent.
- Two review passes by the same author remain self-review. Different actor,
  fresh context and model identity are separate facts with their source limits.
- The old external review covers its recorded revision; author repair regression
  is not a second external review. Current tests do not renew historical review.
- Binds any repair recheck to the repaired baseline, affected findings and actual
  commands; no invented reviewer, task ID, approval or risk acceptance.
- Does not impose another actor on every slice or block a low-risk project solely
  for missing external review when no applicable gate requires it.

## E7 — Execute recovery checks against a green but defective product

Use the held-out state/recovery scenarios in
`sdd-verification-design/evals/forward/recovery.md`. Give the actor only the
ordinary product request, approved contracts, application, existing tests and
this skill's entrypoint/references; keep the evaluator and defect answers out.

Expected invariants:

- Actually checks relevant public behavior and persistent bytes/state, and the
  error-to-correction UI transition when the product has that browser flow.
- Reports known counterexamples as failures even when the original suite passes;
  an actor that misses one is recorded as a miss, not credited with the
  evaluator's later discovery.
- Uses current evidence and routes clear implementation defects to `IMPLEMENT`.
- Browser unavailability is an evidence limit, not success; non-UI products do
  not acquire a browser gate merely from this example.

## E8 — Broad error contract hidden behind a green baseline

Use the Router [R&D pilot protocol](../../sdd-workflow-router/evals/forward/pilot.md),
case `change`, in a fresh actor. The author-approved inherited contract promises
ValueError for any unknown state; existing tests cover only known string states.
Do not supply this rubric or the evaluator to the actor.

Expected invariants:

- Checks unchanged mandatory validation as well as the explicitly changed selection.
- Does not classify a different exception as successful ValueError rejection or
  dismiss the contract solely because the original suite was green.
- Grounds invalid-value classes in the actual contract and validation operation,
  without adding an unrelated schema-validation product requirement.
- Records any miss before parent guidance; repairs preserve v1 and initial evidence,
  and current review/delivery bind to the repaired baseline.
