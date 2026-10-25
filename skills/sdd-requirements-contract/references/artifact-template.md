# Requirements Contract Templates

Use the repository's established format when it preserves the same semantics. Remove irrelevant optional sections rather than filling them with boilerplate.

## Requirements contract

```markdown
# <Feature or Change> Requirements Contract

Status: NEEDS_INPUT | READY_FOR_APPROVAL | APPROVED | SUPERSEDED
Version: <stable version or content hash>
Operating route: SYNTHESIZE | TARGETED_CLARIFY | DISCOVERY | REVISION
Owner / approver: <human role or name if known>
Sources: <request, issue, approved prior spec, repository evidence>
Applicable Agent instructions: <AGENTS.md, Agent.md, or equivalent>

## Problem and desired outcome

- Problem: ...
- Affected actors: ...
- Desired outcome: ...
- Why now / source evidence: ...

## Scope

### In scope

- ...

### Non-goals

- ...

### Deferred

| Item | Rationale | Owner / revisit condition |
|---|---|---|

## Domain and current-state facts

### Glossary

| Term | Contract meaning |
|---|---|

### Relevant facts

| ID | Fact | Evidence source | Last verified |
|---|---|---|---|

## User journeys

### US-01 — <observable user outcome> (Priority: P1)

- Actor and goal: ...
- Value: ...
- Independent evidence: ...
- Requirement links: FR-001, FR-002

## Functional requirements

### FR-001 — <one binding obligation>

The system must ...

- Rationale / source: ...
- Acceptance links: AC-001.1, AC-001.2
- Related constraints: C-001

## Acceptance scenarios

### AC-001.1 — <scenario name>

- Given: ...
- When: ...
- Then: ...
- And / must not: ...
- Evidence type: automated scenario | state table | sample evaluation |
  manual observation | metric | other

## Rules, boundaries, and state semantics

Use a decision table, state table, examples, or concise rules where clearer
than repeated prose.

| Condition / state | Action / event | Required outcome | Prohibited outcome |
|---|---|---|---|

## External data and interface semantics

Only externally depended-on meanings and compatibility promises, not internal
implementation design.

## Non-functional and quality requirements

| ID | Requirement | Workload/environment | Measure and threshold | Evidence |
|---|---|---|---|---|

For model-generated output, include structural constraints, semantic rubric,
representative sample strategy, and passing rule where applicable.

## Constraints and dependencies

| ID | Constraint / dependency | Source | Contract impact |
|---|---|---|---|

## Decisions, assumptions, and open questions

### User decisions

| ID | Decision | Alternatives considered | Rationale | Owner/date |
|---|---|---|---|---|

### Assumptions

| ID | Assumption | Owner | Impact if false | Validate before |
|---|---|---|---|---|

### Open questions

| ID | Question | Why it matters | Blocking? | Owner / next action |
|---|---|---|---|---|

## Coverage and quality gate

| Requirement | Acceptance evidence | Normal | Failure/boundary | Status |
|---|---|---|---|---|

- [ ] Terms and data/state meanings are consistent
- [ ] No blocking product decision remains
- [ ] No invented metric or hidden business assumption remains
- [ ] Scope, non-goals, and deferrals are explicit
- [ ] Internal design has not leaked into the product contract
- [ ] Applicable Agent constraints are referenced without conflict

## Approval record

- Exact version/hash: ...
- Reviewer: ...
- Decision: pending | approved | changes requested
- Date: ...
- Approved assumptions/exceptions: ...

## Revision history

| Version | Status | Summary | Approved by/date | Supersedes |
|---|---|---|---|---|
```

## Decision-frontier question

```markdown
### Q<n> — <decision>

Why this changes the contract: ...
Evidence already established: ...

| Option | User-visible / operational implication |
|---|---|
| A — ... | ... |
| B — ... | ... |

Recommendation: <option and evidence-based reason, or no recommendation>
Affected items: <FR/AC IDs when revising>
```

Ask only questions whose prerequisites are already resolved. Wait for the current frontier before asking dependent questions.

## Revision delta

```markdown
# Requirements Contract Delta — <old version> to <proposed version>

Proposed status: READY_FOR_APPROVAL
Reason and source: ...

## Changes

| Type | Requirement / section | Before | Proposed | Rationale |
|---|---|---|---|---|
| Added | ... | — | ... | ... |
| Modified | ... | ... | ... | ... |
| Removed | ... | ... | — | ... |

## Downstream impact

| Artifact / evidence | Affected links | Required action | Current validity |
|---|---|---|---|

## Approval

- Reviewer: ...
- Decision: pending | approved | rejected
- Effective version/date: ...
```

## Handoff summary

```markdown
Status: NEEDS_INPUT | READY_FOR_APPROVAL | APPROVED | SUPERSEDED
Route: <route and rationale>
Contract version: ...
Authoritative sources: ...
Resolved decisions: ...
Blocking questions: ...
Visible assumptions: ...
Quality gate: pass | fail, with failed items
Downstream invalidation for revisions: ...
Recommended next action: ...
```
