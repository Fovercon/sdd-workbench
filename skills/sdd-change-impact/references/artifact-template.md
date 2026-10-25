# Change Impact Artifact Template

Follow an established repository change-record format when it preserves the same semantics. Otherwise use this template and remove irrelevant optional rows.

```markdown
# Change Impact — CR-<stable-id>: <title>

Outcome: IMPACT_READY | HUMAN_DECISION_REQUIRED |
         INSUFFICIENT_BASELINE | NO_MATERIAL_IMPACT |
         REJECTED_OR_SUPERSEDED
Authority state: PROPOSED | APPROVED_FOR_PROPAGATION | REJECTED | SUPERSEDED
Primary route: AGENT_RULES | SPEC | PLAN | IMPLEMENT | FINISH |
               NO_CONTRACT_CHANGE | UNRESOLVED
Propagation model: FLOW_FORWARD | LIVING | FLOW_BACK |
                   LOCAL_CORRECTION | NO_PROPAGATION
Prepared against: <artifact versions / hashes / approval markers>

## 1. Change statement

- Trigger (`FACT` or `REQUEST`): ...
- Current approved behavior (`FACT`): ...
- Observed current behavior (`FACT` or `UNKNOWN`): ...
- Proposed behavior (`PROPOSAL` or `APPROVED_DECISION`): ...
- Proposed mechanism, if any (`PROPOSAL`): ...
- Reason / expected value: ...
- Urgency and authority evidence: ...

## 2. Baseline and evidence limits

| Artifact | Version / approval | Authority | Missing or conflicting evidence |
|---|---|---|---|

## 3. Classification

- Earliest owner and reason: ...
- Why earlier layers do not need to change: ...
- Why later layers are consequences rather than roots: ...
- Propagation model and history rationale: ...
- Human decisions still required: ...

## 4. Trace map

```text
<source rule / FR / AC>
  -> <Plan decision / invariant>
  -> <slice / execution card>
  -> <code / configuration>
  -> <test / eval / evidence>
  -> <convergence / finish artifact>
```

Mark inferred links as `ASSESSMENT`.

## 5. Impact matrix

| Layer | Artifact / item | Trace reason | Status | Required action | Owner / gate |
|---|---|---|---|---|---|
| Spec | FR-... / AC-... | ... | INVALIDATED | Revise and approve | Product owner |

Allowed status: INVALIDATED | REVERIFY | REVIEW_REQUIRED | UNCHANGED | UNKNOWN

## 6. Evidence invalidation ledger

| Evidence | Previously proved | Why validity changed | New evidence required |
|---|---|---|---|

Include historical tests that still pass but assert the old contract.

## 7. Risks and shared dependencies

| Risk / dependency | Fact or assessment | Affected scope | Mitigation / decision |
|---|---|---|---|

Cover compatibility, migration, rollback, security, recovery, and shared
platform boundaries only when they are on the dependency path.

## 8. Smallest safe update sequence

1. <human decision or approval>
2. <owning contract update>
3. <affected downstream contract/slice update>
4. <implementation and verification>
5. <renewed convergence and finish evidence>

For each step state its prerequisite and stopping gate.

## 9. Closure criteria

- [ ] Exact change decision approved or explicitly rejected
- [ ] Owning contract updated and approved, or no-contract-change justified
- [ ] Affected downstream artifacts synchronized
- [ ] Invalidated and reverify evidence regenerated
- [ ] Cross-artifact consistency restored
- [ ] Convergence decision renewed
- [ ] Finish artifacts refreshed if applicable

## 10. Handoff

- Next owning stage / Skill: ...
- Authorized next action: ...
- Actions not yet authorized: ...
- Remaining blockers: ...
```

## Compact response format

When no durable file is requested, return:

```markdown
Outcome: ...
Primary route: ...
Propagation model: ...
Why: ...
Invalidated: ...
Reverify: ...
Human decisions: ...
Smallest next loop: ...
Evidence limits: ...
```

The compact response must still distinguish the approved baseline, observed behavior, and proposed behavior.
