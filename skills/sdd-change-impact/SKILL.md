---
name: sdd-change-impact
description: Classify a proposed change, bug, review finding, or implementation discovery by its earliest owning SDD stage; trace affected contracts and evidence; and produce a bounded update sequence. Use before revising requirements, design, tasks, code, tests, or finish artifacts when change propagation or contract drift matters. Do not use to implement the change, approve scope, or perform final convergence review.
---

# SDD Change Impact

Determine what a change actually changes before editing artifacts. Route it to the earliest owning layer, trace its downstream consequences, and make stale contracts and evidence visible.

This is an analysis workflow. It does not approve the change and does not modify Agent instructions, requirements, plans, tasks, code, tests, release metadata, or external systems unless the user separately authorizes those actions after the impact analysis.

Read [references/impact-model.md](references/impact-model.md) before assigning an owning layer, propagation model, impact status, or final outcome. Use [references/artifact-template.md](references/artifact-template.md) for a durable impact report.

## Boundaries

- Locate and obey `AGENTS.md`, `Agent.md`, and scoped repository rules before analyzing the change.
- Treat the current approved artifacts as the baseline, not necessarily the latest edited files.
- Separate the observed problem, the requested outcome, and the proposed solution. They are not interchangeable.
- Current code behavior does not define product intent. A bug label does not prove what the intended behavior should be.
- Do not silently expand a local request into a project-wide cleanup or redesign.
- Do not mark a proposed scope or contract change approved. Approval belongs to the authorized human owner.
- Passing tests and prior convergence evidence apply to the old contract unless their continued validity is demonstrated.
- Prefer the earliest layer whose meaning must change; propagate forward from there. Do not churn unaffected upstream contracts.

## Inputs

Inspect the minimum relevant evidence:

1. change request, defect report, review finding, incident, dependency change, or implementation discovery;
2. applicable Agent instructions and project constraints;
3. approved requirements and acceptance scenarios;
4. approved Plan, ADRs, data/state/interface contracts, and behavior slices;
5. affected implementation, configuration, tests, evals, and documentation;
6. current convergence or release evidence;
7. authority, urgency, compatibility, rollout, and risk context supplied by the user.

Record exact artifact versions, hashes, dates, or approval markers when available. If the authoritative baseline cannot be established, return `INSUFFICIENT_BASELINE` rather than analyzing against whichever file is easiest to find.

## Workflow

### 1. Normalize the change statement

Write four distinct statements:

- **Trigger**: what was requested or observed;
- **Current approved behavior**: what the authoritative contracts currently require;
- **Observed current behavior**: what the implementation or environment actually does;
- **Proposed behavior or correction**: what would be true after the change.

Label each statement as `FACT`, `REQUEST`, `PROPOSAL`, `APPROVED_DECISION`, or `UNKNOWN`. Do not fill an unknown desired behavior from the implementation or from common practice.

### 2. Establish authority state

Classify the change as:

- `PROPOSED`: impact may be analyzed, but scope is not approved;
- `APPROVED_FOR_PROPAGATION`: an authorized human approved the exact behavioral or constraint delta;
- `REJECTED`: retain for traceability but do not propagate;
- `SUPERSEDED`: replaced by a later change decision.

The Agent may recognize an explicit approval stated by the user; it may not create one. Urgency, an existing patch, or a merged implementation does not constitute approval of changed intent.

### 3. Select the earliest owning layer

Use exactly one primary route:

- `AGENT_RULES`: durable development constraints, safety rules, required workflow, coding standards, or repository-wide operating policy changed;
- `SPEC`: user-visible behavior, scope, terminology, data meaning, authorization, security/privacy obligation, compatibility promise, recovery semantics, or success criteria changed or are missing;
- `PLAN`: product intent remains stable, but architecture, state/data/interface design, migration, rollback, observability, test strategy, or another cross-cutting technical contract must change;
- `IMPLEMENT`: approved Spec and Plan remain adequate, but code, configuration, tests, or local documentation do not conform;
- `FINISH`: implementation is converged and only packaging, versioning, changelog, release evidence, deployment preparation, or authorization remains;
- `NO_CONTRACT_CHANGE`: editorial correction, evidence refresh, or mechanical/internal change that does not alter an approved contract.

If the route depends on an unresolved product or authority decision, use outcome `HUMAN_DECISION_REQUIRED` and identify the candidate routes instead of guessing.

Security, performance, and bugs are not routes by themselves. Route according to what must change: an existing implementation defect goes to `IMPLEMENT`; a missing product obligation goes to `SPEC`; a deficient technical control design goes to `PLAN`; a durable Agent safety rule goes to `AGENT_RULES`.

### 4. Select the propagation model

Choose one:

- `FLOW_FORWARD`: add a separate feature/change contract when the capability has an independent lifecycle, large scope, or audit value; retain the old feature record.
- `LIVING`: revise the active requirements contract when product intent changes within the same feature.
- `FLOW_BACK`: a lower-stage discovery exposes an upstream defect; return to the owning layer, repair the contract, then propagate forward.
- `LOCAL_CORRECTION`: approved upstream contracts remain valid; update only implementation or finish artifacts and reverify affected evidence.
- `NO_PROPAGATION`: rejected, superseded, or non-material informational change.

Record why this model preserves history and minimizes unnecessary churn.

### 5. Trace backward and forward

Trace backward to find the source contract that authorizes the current behavior. Trace forward using stable links where available:

```text
Agent rule
  -> Requirement FR / Acceptance AC
  -> Plan decision / invariant / external contract
  -> Behavior slice / execution card
  -> Code / configuration / migration
  -> Tests / system scenarios / semantic eval
  -> Convergence evidence
  -> Finish / release artifacts
```

Search by identifiers, interface/state names, data fields, user-visible terms, commands, and repository areas. Do not rely only on filenames or explicit links; record inferred links as `ASSESSMENT` with evidence.

Trace shared dependencies in both directions. A change to a common state transition, schema, output contract, or platform boundary may affect multiple slices or products even when the request names one feature.

### 6. Build the impact matrix

For every relevant artifact or evidence item, assign one status from the impact model:

- `INVALIDATED`
- `REVERIFY`
- `REVIEW_REQUIRED`
- `UNCHANGED`
- `UNKNOWN`

Record:

- exact item and version;
- trace link to the changed item;
- why it is affected or unaffected;
- required action;
- owner and approval gate;
- dependencies and sequencing.

Cover, as applicable:

- Agent instructions;
- requirements, acceptance scenarios, non-goals, and terminology;
- architecture, state/data/interface contracts, migration and rollback;
- behavior slices and current execution cards;
- implementation and configuration;
- unit, contract, integration, system, UI, performance, and semantic eval evidence;
- operational documentation, diagnostics, security and privacy review;
- version, changelog, compatibility notes, deployment and release evidence.

Do not mark an item `UNCHANGED` merely because its file was not edited. Explain why its semantics and evidence remain valid.

### 7. Produce the smallest safe update sequence

Start at the primary route and proceed forward:

1. obtain any required change or risk decision;
2. update and approve the owning contract;
3. revise only affected downstream contracts and slices;
4. implement with the required verification;
5. regenerate invalidated evidence and run convergence review;
6. refresh finish artifacts only after convergence.

For this Skill suite, typical handoffs are:

- `SPEC` -> `sdd-requirements-contract` in `REVISION` or new-contract mode;
- `PLAN` -> `sdd-plan-slices` to revise the design contract and affected slices;
- `IMPLEMENT` -> the approved implementation workflow for the affected slice;
- any completed change -> `sdd-converge-review` before Finish.

The handoff describes the next authorized analysis or work. It does not invoke another Skill automatically or imply permission to edit.

### 8. Check closure conditions

Define closure before work starts:

- approved contract version or explicit confirmation that no contract changes;
- affected slices and code complete;
- invalidated tests/evals rerun under the new baseline;
- cross-artifact consistency restored;
- required migration, compatibility, rollback, and operational evidence present;
- convergence decision renewed;
- finish artifacts refreshed where applicable.

Do not close the change because the patch exists, the local test passes, or the original ticket is marked done.

## Outcomes

Return exactly one:

- `IMPACT_READY`: baseline is usable, primary route and impact set are evidence-backed, and the next gate is known;
- `HUMAN_DECISION_REQUIRED`: intended behavior, approval, compatibility, risk, or scope must be decided before propagation;
- `INSUFFICIENT_BASELINE`: authoritative contracts or versions are missing or contradictory;
- `NO_MATERIAL_IMPACT`: the change is demonstrably non-semantic and requires no contract propagation beyond stated evidence refresh;
- `REJECTED_OR_SUPERSEDED`: no propagation should occur under the current decision record.

`IMPACT_READY` means the analysis is ready, not that the change is approved or implemented.

## Output contract

Return or create:

1. a change record with trigger, authority state, before/after behavior, and evidence;
2. primary route and propagation model;
3. backward/forward trace map;
4. impact matrix and evidence-invalidation ledger;
5. smallest safe update sequence with human gates;
6. closure criteria and concise handoff summary.

Preserve the current approved baseline. A proposed change report must not overwrite the artifacts it analyzes.

## References

- Classification, propagation, impact, and evidence rules: [references/impact-model.md](references/impact-model.md)
- Durable change-impact report template: [references/artifact-template.md](references/artifact-template.md)
- Behavioral evaluation cases: [evals/cases.md](evals/cases.md)
