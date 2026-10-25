# Convergence Review Model

Use this model to keep reviews consistent across projects. Project-specific severity or release policies take precedence when they are stricter.

## 1. Evidence Types

Label important statements so observation and interpretation do not blur together.

| Type | Meaning | Example |
|---|---|---|
| `FACT` | Directly observed in a contract, file, diff, command output, report, or runtime behavior | `pytest tests/test_queue.py -q` passed 8 tests |
| `ASSESSMENT` | Reviewer interpretation derived from one or more facts | Queue recovery is covered for process restart but not host reboot |
| `UNKNOWN` | Evidence is absent, stale, contradictory, or could not be reproduced | The performance report does not record the model version |

An assessment must cite its supporting facts. An unknown must remain unknown until new evidence is obtained.

## 2. Contract Coverage Status

Use one status for every mandatory contract item.

| Status | Definition |
|---|---|
| `VERIFIED` | Implementation evidence exists and appropriate verification passed |
| `PARTIAL` | Some required behavior exists or is tested, but a stated path, boundary, or condition is missing |
| `MISSING` | No implementation evidence for an agreed requirement |
| `CONTRADICTED` | Implementation behavior conflicts with the agreed contract |
| `UNREQUESTED` | Material behavior was added without a contract basis and changes risk or scope |
| `UNVERIFIABLE` | Implementation may exist, but available evidence cannot establish compliance |
| `NOT_APPLICABLE` | The item is explicitly outside the reviewed scope; include the scope evidence |

Do not use `VERIFIED` merely because code exists, a test has a similar name, or an AI summary says it is complete.

## 3. Finding Severity

| Severity | Use when |
|---|---|
| `BLOCKER` | Data loss, serious security exposure, contract-breaking corruption, unauthorized release action, or a mandatory workflow cannot complete |
| `HIGH` | A mandatory requirement is missing/contradicted, a critical recovery or safety path is unverified, or the evidence gate is materially unreliable |
| `MEDIUM` | The main workflow can complete but a bounded correctness, compatibility, observability, or maintainability risk remains |
| `LOW` | Minor risk, clarity issue, or local improvement with no immediate delivery impact |

Severity expresses consequence, not implementation effort. A one-line defect can be BLOCKER; a large refactor can be LOW priority.

## 4. Finding Record

Each material finding should contain:

| Field | Required content |
|---|---|
| ID | Stable identifier such as `CVG-001` |
| Severity | BLOCKER / HIGH / MEDIUM / LOW |
| Contract | Requirement, acceptance scenario, AGENTS rule, plan invariant, or quality gate |
| FACT | Exact file/line, command result, report section, or observed behavior |
| ASSESSMENT | What does not converge and why |
| Consequence | Concrete user, data, security, operation, or maintenance impact |
| Return stage | SPEC / PLAN / IMPLEMENT / FINISH |
| Closure evidence | Observable evidence that would close the finding |

Avoid combining unrelated problems into one finding. Combine repeated instances only when they share the same cause, consequence, and return stage.

## 5. Return-Stage Routing

### Return to SPEC

Use when the team must decide what the system should do:

- missing acceptance behavior or priority;
- ambiguous success/failure definition;
- new business rule or scope change discovered during implementation;
- conflicting authorities or terminology;
- residual risk requiring product acceptance.

Expected closure: updated and approved specification, followed by impact updates to Plan and Tasks.

### Return to PLAN

Use when intent is clear but the solution contract is inadequate:

- state model cannot represent required behavior;
- data ownership or model/program responsibility is wrong;
- cross-cutting security, persistence, compatibility, or observability design is missing;
- local patches would create or deepen architectural debt;
- verification strategy cannot demonstrate a quality requirement.

Expected closure: updated design/ADR/contracts, impact analysis, and revised tasks.

### Return to IMPLEMENT

Use when Spec and Plan are sufficient:

- code or configuration defect;
- missing test for an agreed behavior;
- incomplete error/recovery path;
- implementation diverges from an interface or state contract;
- documentation needed to operate the implemented behavior.

Expected closure: focused change, regression evidence, and an updated coverage row.

### Return to FINISH

Use when product behavior is converged but delivery evidence is incomplete:

- version or changelog mismatch;
- missing deployment or rollback instructions;
- missing known-issue disclosure;
- package contents differ from the reviewed baseline;
- human release authorization has not been recorded.

Expected closure: complete release evidence without changing agreed product behavior.

## 6. Final Decisions

### `CONVERGED`

All mandatory contract items are `VERIFIED` or explicitly `NOT_APPLICABLE`; required deterministic gates pass; semantic/eval evidence meets the agreed rubric; no unresolved BLOCKER/HIGH finding exists; any residual risk has explicit human acceptance.

This decision means the reviewed baseline may proceed to Finish. It is not release authorization.

### `NOT_CONVERGED`

At least one mandatory item is `MISSING`, `PARTIAL`, or `CONTRADICTED`, or an unresolved BLOCKER/HIGH finding exists. State the smallest return loop.

### `INSUFFICIENT_EVIDENCE`

The review lacks an authoritative specification, cannot inspect the relevant implementation, or cannot obtain required verification evidence. List exactly what is absent or blocked. Do not downgrade missing evidence to a lower-severity pass.

### `HUMAN_DECISION_REQUIRED`

Implementation facts are sufficiently established, but convergence depends on a business choice, scope decision, exception, or residual-risk acceptance that the reviewer cannot make. State the decision owner and alternatives without choosing for them.

## 7. Gate Rules

- A passing unit suite cannot override a missing acceptance scenario.
- A code review cannot replace executable evidence for deterministic behavior.
- An LLM judge cannot be the sole gate for deterministic invariants.
- A generated artifact existing on disk does not prove its structure or semantics are valid.
- Historical results must include their date and baseline; otherwise mark their currency `UNKNOWN`.
- Performance and quality numbers require a denominator and test boundary.
- Known failing or hanging tests remain part of the decision even when a passing subset is reported.
