# SDD Workflow Route Record

## 1. Routing header

- Outcome:
- Operation: `ENTRY | STATUS | AFTER_OUTCOME | REROUTE`
- Repository/worktree:
- Routing subject:
- Scope identifier:
- Evidence inspected at:
- Prepared by:

## 2. Authorization boundary

- User-authorized activity:
- Read-only diagnosis authorized:
- Mutations authorized by this routing step: none
- Actions requiring separate approval:
- Applicable Agent instructions:

## 3. Trigger

- Classification:
- Trigger evidence:
- Current requested outcome:
- Why SDD routing is or is not needed:

## 4. Authoritative baseline

| Artifact/evidence | Identity/version | Authority state | Freshness | Notes |
|---|---|---|---|---|
| Agent instructions |  |  |  |  |
| Requirements |  |  |  |  |
| Plan/ADR |  |  |  |  |
| Tasks/current Slice |  |  |  |  |
| Verification design |  |  |  |  |
| Source/worktree |  |  |  |  |
| Execution evidence |  |  |  |  |
| Convergence |  |  |  |  |
| Finish target/evidence |  |  |  |  |
| Impact/handoff |  |  |  |  |

Use `UNKNOWN` rather than guessing. Omit rows that are clearly not applicable.

## 5. Workflow state map

| Gate | State | Evidence | Consequence |
|---|---|---|---|
| Agent rules |  |  |  |
| Requirements |  |  |  |
| Design |  |  |  |
| Tasks/current Slice |  |  |  |
| Verification design |  |  |  |
| Slice implementation |  |  |  |
| Scope implementation |  |  |  |
| Convergence |  |  |  |
| Finish readiness |  |  |  |
| Context/change propagation |  |  |  |

Allowed states: `SATISFIED`, `PENDING_HUMAN`, `GAP`, `STALE`, `CONFLICT`, `BLOCKED_EXTERNAL`, `NOT_APPLICABLE`, `UNKNOWN`.

## 6. Precedence decision

- Exception checked:
- Result:
- Earliest unsatisfied gate:
- Why later-stage evidence cannot bypass it:

## 7. Primary next route

- Route type: `SKILL | HUMAN_GATE | PROJECT_ACTION | NONE`
- Recommended Skill/action:
- Reason:
- Required inputs:
- Objective:
- Expected outcome:
- Stop condition:
- Explicitly not authorized:

## 8. Blockers and reconciliation

| ID | Type | Evidence | Owner | Required resolution |
|---|---|---|---|---|
|  |  |  |  |  |

## 9. Deterministic later route

Include only when it follows directly after the primary gate succeeds.

- If primary outcome is:
- Then consider:
- Condition that must be rechecked:

## 10. Routing summary

- Current stage/state:
- One next step:
- Why this step is first:
- Human decision needed now:
- Evidence that must be refreshed afterward:
