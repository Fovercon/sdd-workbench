# SDD Context Handoff

## Header

```yaml
outcome: HANDOFF_READY | RESUME_READY | RECONCILIATION_REQUIRED | INSUFFICIENT_CONTEXT | NO_HANDOFF_NEEDED
mode: PREPARE | RECEIVE | RECOVER | REFRESH
created_at: <timestamp and timezone>
prepared_by: <session/agent/person if known>
intended_receiver: <session/agent/person/tool>
purpose: <bounded continuation objective>
reason_for_boundary: <why context must move or be reconstructed>
freshness: <evidence anchors and time>
```

## 1. Authorization boundary

- Authorized objective: ...
- Allowed actions already granted: ...
- Actions requiring new approval: ...
- Explicit non-goals: ...

Do not infer authorization from this package. Copy only authority actually supplied by the user or repository workflow.

## 2. Work identity

| Field | Value | Evidence |
|---|---|---|
| Repository/root | ... | resolved path |
| Worktree/workspace | ... | command or environment |
| Branch | ... | command |
| Base/head | ... | revision IDs or `UNKNOWN` |
| Change/plan | ... | artifact path and version |
| Current slice/task | ... | stable ID |
| Contract baseline | ... | status/version/hash |
| Agent instructions | ... | applicable paths |

## 3. Read in this order

| Order | Source | Authority/type | Why needed | Relevant scope/version |
|---|---|---|---|---|
| 1 | `AGENTS.md` | PRIMARY | Highest development constraints | ... |
| 2 | `spec.md` | PRIMARY | Product baseline | APPROVED v... |
| 3 | `plan.md` | PRIMARY | Design baseline | ... |
| 4 | `tasks.md` / execution card | PRIMARY | Current slice | ... |
| 5 | diff/test/report | PRIMARY | Current state/evidence | ... |

## 4. Current contract state

### Effective decisions

| Decision | Owner layer | Authority state | Source | Affected scope |
|---|---|---|---|---|
| ... | SPEC / PLAN / ... | APPROVED / ... | ... | ... |

### Pending proposals and assumptions

| Item | Type | Owner | Blocking effect | Validation/decision point |
|---|---|---|---|---|
| ... | PROPOSAL / ASSUMPTION | ... | ... | ... |

### Open questions

| Question | Owning layer | Why it matters | Stop condition |
|---|---|---|---|
| ... | ... | ... | ... |

### Rejected or superseded paths

Include only costly, plausible repeats.

| Path | Status | Reason/evidence | Reconsider only if |
|---|---|---|---|
| ... | REJECTED / SUPERSEDED / FAILED_EXPERIMENT | ... | ... |

## 5. Verified working state

| Slice/item | State | Evidence | Last verification | Notes |
|---|---|---|---|---|
| ... | COMPLETE / IN_PROGRESS / BLOCKED / UNTOUCHED | path, commit, command | timestamp/environment | ... |

### Relevant workspace changes

- Modified: ...
- Untracked: ...
- Generated/temporary: ...
- Active external/process state: ...
- Files that must not be overwritten: ...

### Verification evidence

| Command/check | Result | Baseline covered | Time/environment | Limitation |
|---|---|---|---|---|
| ... | PASS / FAIL / BLOCKED / NOT_RUN | FR/AC/slice/... | ... | ... |

## 6. Risks and drift watchpoints

- Safety or irreversible-action gate: ...
- Contract drift risk: ...
- Shared dependency/parallel work: ...
- Stale evidence risk: ...
- Sensitive information redacted: yes/no; what the receiver must obtain separately: ...

## 7. Continuation capsule

### Startup verification

1. Confirm ...
2. Read ...
3. Compare ...

### One next action

`<specific bounded action>`

Expected evidence of completion: ...

### Stop and escalate if

- ...

### Suggested routing

- Skill/workflow: ...
- Trigger condition: ...
- This suggestion does not authorize: ...

## 8. Receipt verification

Complete this section in `RECEIVE` or `RECOVER` mode.

| Check | Result | Evidence/difference |
|---|---|---|
| Identity tuple matches | PASS / FAIL / UNKNOWN | ... |
| Agent instructions re-read | PASS / FAIL | ... |
| Contract baseline matches | PASS / FAIL / DRIFT | ... |
| Workspace state understood | PASS / FAIL / DRIFT | ... |
| Completion claims verified | PASS / FAIL / PARTIAL | ... |
| Open gates preserved | PASS / FAIL | ... |
| Next action remains valid | PASS / FAIL | ... |

Drift classification: `NONE | EXPECTED | MATERIAL | UNKNOWN`

Resume outcome: `RESUME_READY | RECONCILIATION_REQUIRED | INSUFFICIENT_CONTEXT`

First safe action after receipt: ...
