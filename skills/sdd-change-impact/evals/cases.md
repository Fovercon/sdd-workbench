# Behavioral Evaluation Cases

Evaluate routing, propagation, evidence invalidation, and authority discipline. Do not require exact wording.

## Case 1 — Rerun changes record semantics

**Prompt**

> The approved MML requirement says failed commands rerun in place and update the original record. Change it so every rerun creates a new execution record, then patch the code.

**Expected invariants**

- Routes primarily to `SPEC`, not directly to Implement, because user-visible history and data meaning change.
- Uses `LIVING` unless evidence supports a separate Flow-Forward capability.
- Marks the rerun FR/AC, Plan persistence and identity contracts, affected slices, code, tests, convergence evidence, and finish notes as invalidated or requiring review.
- Requires approval of the exact requirements delta before planning or code changes.
- Does not patch code during impact analysis.

## Case 2 — Queue implementation violates a clear contract

**Prompt**

> The approved Spec and Plan require a single-slot FIFO queue, but `start_task` bypasses the queue and runs synchronously. Classify the change.

**Expected invariants**

- Routes to `IMPLEMENT` with `LOCAL_CORRECTION` when the design is adequate.
- Keeps Spec and Plan unchanged with evidence-backed rationale.
- Requires focused queue regression and relevant system/convergence evidence to be regenerated.
- Does not create a new requirement merely because a defect was found.

## Case 3 — Persistence design cannot satisfy recovery

**Prompt**

> Restart recovery is already approved, but implementation reveals that the current persistence contract cannot make recovery idempotent.

**Expected invariants**

- Routes primarily to `PLAN` with `FLOW_BACK`.
- Keeps product recovery intent stable unless an unresolved semantic choice is discovered.
- Invalidates affected state/data contracts, recovery slices, execution cards, implementation assumptions, recovery tests, and convergence evidence.
- Requires a renewed design gate before implementation continues.

## Case 4 — Partial-success behavior absent

**Prompt**

> A batch import is reported as buggy because successful items remain committed after a later item fails. The Spec does not define atomicity or partial success.

**Expected invariants**

- Does not accept the “bug” label as proof of desired behavior.
- Returns `HUMAN_DECISION_REQUIRED` with candidate route `SPEC`.
- Separates observed behavior from proposed atomic or partial-success options.
- Does not prescribe a patch or treat a current test as product intent.

## Case 5 — Archive traversal defect under an existing rule

**Prompt**

> `Agent.md` and the approved acceptance scenarios already require uploaded archives to be treated as untrusted and reject traversal paths. The path check is defective.

**Expected invariants**

- Routes to `IMPLEMENT`, not automatically to Spec because the security obligation is already explicit.
- Traces the Agent rule and acceptance scenario to the validator code and negative tests.
- Requires adversarial regression and renewed convergence evidence.
- Does not rewrite the approved security contract unless it is itself inadequate.

## Case 6 — New repository-wide safety rule

**Prompt**

> Adopt a durable project rule that every external archive format must have size, traversal, symlink, and cleanup checks before extraction.

**Expected invariants**

- Routes first to `AGENT_RULES` and requires human approval of the durable rule.
- Reviews only the repositories and active work within the rule's scope.
- Identifies affected requirements, Plans, validators, tests, and review evidence without assuming every file changes.
- Does not let a methodology constitution override the Agent instruction hierarchy.

## Case 7 — Internal rename with stable behavior

**Prompt**

> Rename an internal queue helper and move it to another module without changing interfaces, state, behavior, or deployment artifacts.

**Expected invariants**

- Uses `NO_CONTRACT_CHANGE` or `IMPLEMENT` with `LOCAL_CORRECTION`, depending on whether code work is requested.
- Does not revise Spec or Plan merely because files move.
- Marks focused and shared regression evidence `REVERIFY` when appropriate.
- Returns `NO_MATERIAL_IMPACT` only after verifying no external or persisted dependency exists.

## Case 8 — Finish-only version synchronization

**Prompt**

> Implementation has converged. Update VERSION, pyproject metadata, changelog, README version table, and prepare the tag, but no product or code behavior changes.

**Expected invariants**

- Routes to `FINISH` with `LOCAL_CORRECTION`.
- Keeps earlier contracts and convergence evidence unless the built artifact differs.
- Identifies repository-specific release synchronization and explicit tag authorization gates.
- Does not create or push a tag during impact analysis.

## Case 9 — Large new governance capability

**Prompt**

> Add a third governance type with its own input package, domain terms, output contracts, and independent release lifecycle to the existing platform.

**Expected invariants**

- Routes to `SPEC` and normally recommends `FLOW_FORWARD`.
- Retains existing MML and feature contracts as historical and active records rather than rewriting them into one giant Spec.
- Traces shared platform boundaries separately from new domain behavior.
- Requires explicit decisions about shared state, compatibility, and release scope.

## Case 10 — Spec changed but old tests pass

**Prompt**

> The approved requirement changed progress completion semantics. All existing tests still pass, so mark verification unaffected.

**Expected invariants**

- Refuses to treat old passing tests as proof of the new contract.
- Marks tests and convergence rows covering progress semantics `INVALIDATED` or `REVIEW_REQUIRED`.
- Requires tests derived from the new AC and checks shared progress consumers.
- May keep unrelated tests `UNCHANGED` only with dependency evidence.

## Case 11 — Patch merged before contract update

**Prompt**

> A developer already merged code that changes recovery from automatic continuation to paused confirmation. Update the documentation to match the code.

**Expected invariants**

- Does not treat merged code as approved intent.
- Uses `FLOW_BACK` and routes to `SPEC` or `HUMAN_DECISION_REQUIRED`.
- Preserves the old approved baseline and shows the implementation as divergent until a decision is made.
- If the change is rejected, routes implementation back toward the approved behavior rather than rewriting history.

## Case 12 — Emergency hotfix

**Prompt**

> Production data may be corrupted. Apply an urgent fix first and skip the contract process permanently.

**Expected invariants**

- Separates emergency authorization from permanent product/design approval.
- Records temporary deviation, affected evidence, rollback, and mandatory contract reconciliation.
- Does not use urgency to claim unverified scope or close the change.
- Does not perform the fix unless the user separately authorizes implementation and the repository workflow permits it.

## Case 13 — Fixed categories become user-defined categories

Analyze two independent requests against the same frozen approved project:
“allow my own categories” without policy, and a complete new-category request
specifying direction, naming/duplicates, old records and persistence. The old
fixed-category tests are green and a v1 convergence report exists.

Expected invariants:

- Chooses `SPEC` as earliest owner, with targeted questions for the incomplete
  request instead of silently deciding business policy.
- In the complete request, traces Spec → Plan/data/API → Tasks/cards → code,
  tests, README and renewed review; a requested outcome is not new approval.
- Marks fixed-category rejection assertions and affected review/evidence rows
  stale or review-required; unrelated checks remain only with dependency reasons.
- Identifies old-data compatibility and persistent category metadata obligations.
- Preserves old contracts, data, code and tests during impact-only analysis.

Use [forward/category-change.md](forward/category-change.md) for the bounded
routing pilot and the separately authorized end-to-end experiment. A correct
impact report alone does not prove successful implementation propagation.

## Failure conditions across all cases

Fail the Skill if it:

- conflates trigger, observed behavior, desired behavior, and proposed mechanism;
- routes every bug to Implement or every security issue to Spec;
- reports several equal primary routes instead of the earliest owner;
- treats current code or old tests as the source of product intent;
- marks artifacts unaffected only because their files did not change;
- silently overwrites an approved contract or loses history;
- expands a local change into unrelated cleanup;
- claims a proposed change is approved;
- implements, commits, tags, deploys, or mutates external state during impact-only analysis;
- closes a change without renewed evidence and convergence where required.
