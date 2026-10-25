# Slice Execution Model


## Contents

- [1. Authority chain](#1-authority-chain)
- [2. What makes a slice executable](#2-what-makes-a-slice-executable)
- [3. Execution modes](#3-execution-modes)
- [4. Slice scope model](#4-slice-scope-model)
- [5. Upstream routing](#5-upstream-routing)
- [6. RED truth table](#6-red-truth-table)
- [7. GREEN and regression truth](#7-green-and-regression-truth)
- [8. Workspace safety](#8-workspace-safety)
- [9. Failure classification](#9-failure-classification)
- [10. Completion evidence receipt](#10-completion-evidence-receipt)
- [11. Progress and context loss](#11-progress-and-context-loss)
- [12. Closure rule](#12-closure-rule)


Use this model to keep implementation bounded, evidence-backed, and correctly routed.

## 1. Authority chain

```text
Agent instructions
  -> approved Spec and acceptance scenarios
  -> approved Plan and verification design
  -> tasks dependency map
  -> current execution card
  -> current repository evidence
```

Later items add execution detail but cannot change earlier meaning. Current code is evidence about implementation, not product authority.

## 2. What makes a slice executable

All should be true:

- one observable outcome and explicit stop condition;
- linked approved requirement and Plan decisions;
- dependencies complete or available through verified interfaces;
- no unresolved product or consequential technical decision;
- verified repository surface and commands;
- an evidence mode and sufficient proof obligations;
- bounded risk, rollback, and authorization conditions;
- implementation authorization for the exact slice.

If the card says “handle errors”, “update related code”, “add tests”, or another unbounded placeholder, it is not executable.

## 3. Execution modes

### `RED_GREEN`

Use for new behavior and bug correction. The RED must fail for the contract reason before production behavior changes. GREEN is the smallest complete behavior, not the smallest line count.

### `CHARACTERIZE_PRESERVE`

Use for behavior-preserving refactoring. Establish approved current behavior, stable external contracts, known tolerated defects, and representative equivalence evidence before structural edits. The safety net starts green; structural changes must keep it green.

### `BEFORE_AFTER`

Use when the deliverable is mechanical or another approved oracle is more faithful than RED/GREEN, such as deterministic generated metadata, a packaging manifest, documentation link integrity, or a migration rehearsal. The card must name the before state, exact expected delta, validation, and rollback boundary.

Do not choose a mode merely because it is easier. Repository rules can require a stricter mode.

## 4. Slice scope model

Classify changed work:

| Class | Treatment |
|---|---|
| `REQUIRED` | Directly implements or verifies the slice outcome |
| `SUPPORTING` | Small necessary adaptation at a touched boundary; record why |
| `MECHANICAL_DEVIATION` | Card detail moved/renamed but contract unchanged; record actual path |
| `LATER_SLICE` | Do not implement now |
| `UNRELATED` | Preserve and exclude |
| `CONTRACT_CHANGE` | Stop and route upstream |

Do not broaden `SUPPORTING` into opportunistic cleanup. A repeated nearby smell is not automatically part of the slice.

## 5. Upstream routing

| Discovery | Route/outcome |
|---|---|
| User-visible success/failure, scope, permission, compatibility, recovery, or data meaning unclear | `NEEDS_SPEC` |
| Architecture, ownership, state model, interface, migration, rollback, observability, or verification design insufficient | `NEEDS_PLAN` |
| Desired change approved but impact across existing contracts unknown | `sdd-change-impact`, then revise affected owners |
| Authorization, destructive/irreversible action, sensitive decision, external mutation, or accepted risk needed | `HUMAN_DECISION_REQUIRED` |
| Existing changes overlap or ownership is unknown | `WORKSPACE_RECONCILIATION_REQUIRED` |
| Required service/tool/OS/credential/resource prevents evidence | `ENVIRONMENT_BLOCKED` |
| Implementation/evidence simply not complete under an adequate contract | `SLICE_INCOMPLETE` |

Do not use `ENVIRONMENT_BLOCKED` for an implementation failure. Do not use `SLICE_INCOMPLETE` to hide a Spec or Plan defect.

## 6. RED truth table

| Observation | Meaning/action |
|---|---|
| Fails with expected assertion because behavior is absent/wrong | Valid RED; implement |
| Passes immediately | Behavior may exist, test may be weak, or baseline/card may be stale; investigate |
| Errors before exercising behavior | Harness/setup defect; repair RED first |
| Fails on an unrelated assertion | Narrow or correct the test; no production change yet |
| Requires a broad mock that bypasses owned behavior | Wrong seam; select a faithful boundary |
| Reproduces only after changing production code | Not demonstrated RED; restore or reconstruct evidence without destroying user work |

Watching a command fail is not enough. The failure must establish sensitivity to the intended behavior.

A test runner may label a missing executable, wrong command, unstarted service
or failed import as an assertion failure. Inspect the underlying stdout/stderr
and the exercised boundary; the runner's `FAIL` label does not make it a behavior
RED. For a new entrypoint, establish a runnable seam that accepts the intended
invocation, record this as setup, then observe the missing behavior before
implementing it. If that distinction cannot be demonstrated, retain the failure
as setup evidence and disclose that behavioral RED was not established.

## 7. GREEN and regression truth

- Focused GREEN proves only the focused obligation.
- Contract tests prove stable boundary shape/semantics, not the entire flow.
- System tests prove collaboration for the scenarios they assert, not semantic quality by existence.
- Full-suite green does not prove untested acceptance behavior.
- Historical results do not prove the current diff.
- A rerun that passes after an unexplained failure is evidence of instability, not clean proof.
- Skips, xfails, warnings, partial collections, timeouts, and generated-state pollution must remain visible.

Record command, result, baseline, and relevant environment. Preserve stdout excerpts only when needed; do not paste huge logs into the receipt.

## 8. Workspace safety

Before implementation, create a mental or recorded ownership map:

```text
existing user changes
+ prior slice changes
+ current slice starting point
+ current slice new delta
```

Use diff/status/history to separate them. Do not assume all dirty files are yours. If safe separation is impossible, reconcile before editing.

Do not require a new worktree universally. Use the repository/environment's established isolation strategy. Never create or remove a worktree, branch, or stash merely because this model mentions isolation.

## 9. Failure classification

### `SLICE_REGRESSION`

The current delta breaks an approved obligation. Repair it before closure.

### `PREEXISTING_FAILURE`

Reproduce on the starting baseline when safe and practical. It may still block closure if the required gate demands green; report rather than silently excluding it.

### `TEST_OR_FIXTURE_DEFECT`

The test contradicts the approved contract or cannot exercise its claimed boundary. Correct the test with evidence. Do not call a valid failing test defective because implementation is inconvenient.

### `ENVIRONMENT_FAILURE`

The evidence cannot run because a named external condition is unavailable or invalid. Preserve command and error; do not report pass.

### `CONTRACT_DISCOVERY`

Execution reveals missing or wrong upstream meaning. Stop behavior implementation and route it.

### `OUT_OF_SCOPE_FINDING`

Record evidence, consequence, and likely owning stage. Do not fix it silently or discard it. If it is load-bearing for this slice, it is no longer safely out of scope and must block/route.

## 10. Completion evidence receipt

For every required check record:

- purpose and linked obligation;
- exact command or reproducible observation;
- RED/GREEN/baseline/regression role;
- result and meaningful count/exit status;
- source/diff identity;
- environment and substitute/real dependency boundary;
- limitations, skips, or checks not run.

Facts and assessments remain separate. “The code is clean” is an assessment; changed paths and command results are facts.

## 11. Progress and context loss

For long or interrupted slices, use a plan/slice-scoped ledger or `sdd-context-handoff`. Record only stable recovery facts:

- Plan and slice identity;
- starting and current source anchors;
- completed cycles and evidence;
- open failure classifications;
- decisions/routings and next safe action.

Verify the ledger against repository evidence after compaction or transfer. Conversation memory does not override the ledger, and the ledger does not override contracts or current repository facts.

## 12. Closure rule

`SLICE_COMPLETE` means:

```text
approved one-slice outcome
+ current faithful implementation
+ required current evidence
+ bounded actual diff
+ no unresolved load-bearing finding
+ reproducible receipt
```

It does not mean:

- all slices complete;
- feature accepted;
- final review passed;
- branch should be merged;
- release is authorized.

After closure, return from this worker invocation. In authorized Router RUN, the controller continues the mission; direct slice execution ends here. The Plan/controller chooses the next slice; `sdd-converge-review` judges whole-scope convergence at the appropriate boundary.
