---
name: sdd-implement-slice
description: Implement exactly one approved SDD behavior slice from its current execution card, using a verified workspace, an appropriate RED/GREEN or characterization loop, required regression evidence, and explicit upstream routing when contracts fail. Use after Plan approval when one bounded slice is authorized for code and test changes. Do not use to create the Plan, execute an entire backlog, approve contract changes, or decide whole-feature convergence.
---

# SDD Implement Slice

Complete one approved vertical behavior slice and close it with reproducible evidence. Preserve the Spec and Plan as contracts, keep the change surface bounded, protect existing workspace changes, and stop at the slice boundary.

Read [references/execution-model.md](references/execution-model.md) before selecting an execution mode, classifying a blocker, or declaring the slice complete. Use [references/execution-report-template.md](references/execution-report-template.md) for a durable evidence receipt.

## Execution context

An authorized Router RUN may call this Skill repeatedly, once per current card. Mission authorization covering those slices satisfies implementation authority; it need not be requested per card. RUN may supply a Spec marked `AUTHORIZED_DERIVATION` and a Plan marked `DELEGATED_TECHNICAL` under their respective gates; keep these distinct from human approval. This worker still completes only one slice per invocation and returns to the controller.

## Boundaries

- Locate and obey applicable `AGENTS.md`, `Agent.md`, and scoped repository rules before changing files.
- Require an approved Spec and Plan, a ready slice with satisfied dependencies, a current execution card, and explicit implementation authorization. A planning-only card does not authorize code changes.
- Implement one slice only. Do not start the next ready slice, absorb an adjacent feature, or perform a broad cleanup because it is nearby.
- Treat the Spec as product authority and the Plan as technical authority. The execution card narrows current work; it cannot override either.
- Do not invent missing behavior, change an interface or state contract silently, weaken a valid test, or turn current code into the desired contract.
- Do not overwrite, reset, discard, commit, merge, push, publish, deploy, or clean up unrelated work without the required authorization.
- A completed slice is not a completed feature, a convergence decision, or release readiness.

## Required inputs

Load the current card's requirements, acceptance conditions and relevant Plan
invariants, including shared constraints that affect this slice. Reuse applicable
content still visible from the same verified baseline; do not reload all completed
slices or historical reports. Expand to the primary contract when scope or meaning
is uncertain. After context loss, read the current load-bearing clauses again;
a matching hash or prior summary does not restore their meaning or authorization.

Inspect and identify exact versions of:

1. applicable Agent instructions;
2. approved Spec and acceptance scenarios linked by the slice;
3. approved Plan, ADRs, interfaces, state/data invariants, and verification strategy;
4. `tasks.md` slice definition and dependency status;
5. current execution card with authorization, objective, stop condition, change surface, RED/GREEN evidence, and regression commands;
6. current repository/worktree/branch/head, dirty state, and relevant progress ledger or handoff;
7. current tests, fixtures, implementation seams, and commands named by the card.

Do not trust paths, symbols, commands, completion claims, or line numbers merely because the card lists them. Verify short-lived execution detail against the current repository.

## Workflow

### 1. Establish slice identity and authority

Record:

- slice ID and one observable outcome;
- linked requirements, acceptance scenarios, Plan decisions, and proof obligations;
- implementation authorization and actions still requiring approval;
- prerequisite slices and evidence that they are complete;
- exact stop condition for this slice;
- excluded adjacent behaviors and later slices.

If product behavior is missing or contradictory, return `NEEDS_SPEC`. If technical state, interface, migration, verification, or rollback design is inadequate, return `NEEDS_PLAN`. Do not patch around an upstream gap.

### 2. Protect and baseline the workspace

Before editing:

- resolve repository and worktree identity;
- inspect branch/head and modified, staged, and untracked files;
- identify which existing changes belong to the user, this slice, another slice, or are unknown;
- compare any handoff/ledger with the current Plan and repository state;
- preserve unrelated work and establish the slice's starting diff or evidence anchor;
- run the smallest useful baseline check when it distinguishes a new regression from a pre-existing failure.

If relevant existing changes have unknown ownership or overlap the intended edit surface, return `WORKSPACE_RECONCILIATION_REQUIRED`. Do not create a “clean” baseline by hiding or destroying changes.

A progress ledger is evidence only when it names the current Plan or slice and its cited commits/artifacts exist. A foreign or stale ledger cannot authorize skipping work.

### 3. Validate the execution card against reality

Confirm that the card has no unresolved placeholders and that:

- the objective still fits one focused execution context;
- paths, symbols, commands, interfaces, and fixtures exist or have a clearly authorized creation point;
- the proposed seam can observe the contract rather than only a mock or private implementation detail;
- the required evidence is sufficient for the risk and agrees with `sdd-verification-design` when one exists;
- the implementation constraints do not contradict current code architecture or approved Plan decisions;
- the stop condition is achievable without implementing a later slice.

Correct stale mechanical detail such as moved paths when the intended responsibility and contract are unchanged, and record the deviation. Route behavior, design, risk, or scope changes upstream instead of “fixing” the card locally.

### 4. Select the execution evidence mode

Choose one:

- `RED_GREEN`: new behavior or bug correction; establish a focused failing test or observation before production implementation.
- `CHARACTERIZE_PRESERVE`: behavior-preserving refactor; first establish green characterization, contract, golden, or differential evidence for the approved current behavior.
- `BEFORE_AFTER`: mechanical, generated, configuration, documentation, packaging, or migration work whose approved card defines another observable before/after check and explains why ordinary RED/GREEN is not the faithful mode.

Repository rules may be stricter. If they require TDD for the work, use `RED_GREEN`. An exception must come from the user or applicable project policy, not the implementing Agent.

### 5. Establish trustworthy pre-change evidence

For `RED_GREEN`:

1. add or select the smallest test that expresses the slice behavior;
2. name the production change that would make it pass;
3. run the exact focused command;
4. confirm it fails rather than errors;
5. confirm the failure is caused by the missing or defective behavior.

If it passes immediately, determine whether the behavior already exists, the test is weak, or the slice baseline is stale. If it fails for setup, syntax, fixture, environment, or unrelated reasons, fix the test harness until the intended RED is visible before changing production behavior.

For `CHARACTERIZE_PRESERVE`, confirm current behavior and safety-net evidence are green before structural changes. Label known tolerated defects rather than silently blessing them as desired behavior.

For `BEFORE_AFTER`, capture the approved baseline and expected delta in a reproducible form. Do not use visual inspection alone when a deterministic check is available.

### 6. Implement the smallest complete slice behavior

- Change only the production, test, fixture, configuration, migration, or documentation surface necessary for the slice.
- Keep stable interfaces, data meanings, state transitions, compatibility promises, and error semantics unchanged unless the approved contract explicitly changes them.
- Reuse established repository patterns where they satisfy the Plan; do not introduce speculative abstraction or future-slice infrastructure.
- Keep external, model, network, credentialed, destructive, and irreversible actions behind their existing authorization gates.
- Preserve diagnostics, observability, security, recovery, and rollback obligations named by the card.

One slice may need several small RED/GREEN cycles. Each cycle must remain inside the slice outcome. Do not bundle the whole slice into one opaque test merely to claim TDD.

### 7. Verify GREEN and refactor safely

After each behavior increment:

- run the focused command and confirm the intended evidence passes;
- inspect warnings, skips, hangs, unexpected output, generated state, and side effects rather than reading only the exit code;
- fix production behavior when a valid contract test fails; do not weaken the test to match the implementation;
- refactor only while the focused evidence remains green;
- avoid broad formatting, renaming, dependency upgrades, or cleanup unrelated to the slice.

For a refactor slice, use differential, golden, contract, or system evidence to show behavioral equivalence at the protected boundaries. Aggregate line coverage alone is not equivalence proof.

### 8. Run the required regression portfolio

Run the commands required by the execution card and repository policy, normally progressing from narrow to broad:

1. focused DT/component evidence;
2. affected contract tests;
3. affected integration/system/UI/eval evidence;
4. cross-platform, migration, security, performance, or real-dependency checks when authorized and required for this slice;
5. full offline regression when the card, risk, or repository gate requires it.

Do not call a subset “full”. Record checks not run and why. Historical results remain historical.

When a check fails, classify it before acting:

- `SLICE_REGRESSION`: caused by this implementation; repair inside the slice.
- `PREEXISTING_FAILURE`: present at the verified baseline; preserve evidence and assess whether it blocks the slice gate.
- `TEST_OR_FIXTURE_DEFECT`: the oracle or data is wrong relative to the approved contract; correct it without weakening coverage.
- `ENVIRONMENT_FAILURE`: dependency, OS, credentials, service, resource, or tooling prevents valid evidence.
- `CONTRACT_DISCOVERY`: failure exposes missing or wrong Spec/Plan meaning; stop and route upstream.
- `OUT_OF_SCOPE_FINDING`: real issue outside this slice; record it without silently fixing or discarding it.

Do not rerun until green without explaining an intermittent result. Do not hide failures through skips, broader mocks, relaxed assertions, or excluded files.

### 9. Review the slice from the contract outward

Before closure, compare the actual diff and evidence with the card:

- every linked obligation is implemented and evidenced;
- no unrequested behavior or later-slice work was added;
- changed paths are understood and unrelated user changes remain intact;
- interfaces, persisted state, files, events, UI, and diagnostics agree where the contract requires consistency;
- negative, recovery, isolation, and compatibility paths required by the slice are present;
- no new secret, local path, generated task data, debug artifact, or uncontrolled dependency entered the change;
- any deviation from the card is mechanical and documented, or has approved upstream authority;
- remaining findings are classified and do not contradict slice completion.

Use an independent slice review when project policy or risk requires it. The implementer's self-review is useful but not independent convergence evidence.

### 10. Close exactly this slice

`SLICE_COMPLETE` requires:

- the observable outcome and stop condition are satisfied;
- required RED/GREEN, characterization, or before/after evidence is recorded;
- every mandatory focused and regression gate passed on the current slice baseline;
- no unresolved contract discovery or workspace conflict remains;
- actual changes stay within the approved slice or have explicit recorded authorization;
- completion evidence identifies commands, results, environment limits, changed files, and remaining non-blocking risks.

Update the established task status or plan-scoped ledger only if the repository workflow authorizes it. Record completion against the current Plan/slice identity and source range. Do not rewrite Plan meaning, approve new decisions, require a commit, or create one unless separately authorized.

Return after reporting this slice. For a direct invocation, recommend the next action without starting it. In authorized RUN, return the receipt to the controller, which rechecks state and starts the next appropriate invocation; do not end the overall mission merely because this slice is complete.

## Outcomes

Return exactly one:

- `SLICE_COMPLETE`: this slice, and only this slice, meets its contract and evidence gates;
- `NEEDS_SPEC`: observable behavior, scope, acceptance, compatibility, recovery, or another product decision is missing or contradictory;
- `NEEDS_PLAN`: architecture, state/data/interface design, migration, rollback, verification strategy, or technical ownership is inadequate;
- `HUMAN_DECISION_REQUIRED`: implementation authority, irreversible action, security-sensitive choice, external side effect, risk acceptance, or another owner decision blocks progress;
- `WORKSPACE_RECONCILIATION_REQUIRED`: overlapping or unowned existing changes prevent safe execution or closure;
- `ENVIRONMENT_BLOCKED`: required evidence cannot be obtained because the named environment or dependency is unavailable;
- `SLICE_INCOMPLETE`: the authorized slice was attempted but its implementation or mandatory evidence remains failing or unfinished without an upstream contract decision.

## Output contract

Return or create one slice execution receipt containing:

1. outcome, slice ID, objective, execution mode, and authorization boundary;
2. Spec/Plan/card versions and starting workspace identity;
3. actual change surface and deviations from the card;
4. RED or pre-change evidence;
5. GREEN, refactor, focused, and regression evidence with exact commands and results;
6. failure classifications, discoveries, and upstream routing;
7. changed files, generated state, unrun checks, and remaining risks;
8. exact slice stop condition result and recommended next action.

Do not present code volume, commit count, test count, or one passing command as the completion claim. Lead with the observable slice outcome and evidence boundary.

## References

- Execution modes, scope, blocker routing, test truth, and completion rules: [references/execution-model.md](references/execution-model.md)
- Durable slice execution receipt: [references/execution-report-template.md](references/execution-report-template.md)
- Behavioral evaluation cases: [evals/cases.md](evals/cases.md)
