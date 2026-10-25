# Artifact Templates

Adapt section depth to `LIGHT`, `STANDARD`, or `DETAILED`. Do not retain empty headings that add no review value.

## Record placement

Default locations in a fresh repository are `design/plan.md` and `design/tasks.md` (alongside the suite Spec default); follow an established repository convention or explicit user destination when one exists, and keep the choice consistent with the AGENTS.md source-of-truth map.

Planning verifies the map against what was actually written, not a forecast made
during requirements. A concise map distinguishes the stable Plan from Tasks and the
current card. Edit/consolidate an incorrect agent-added location statement within
existing authority; do not leave competing instructions as append-only history.
Superseded execution evidence stays historical, but conflicting current rules are
not an archive. This adds no mandatory document or universal filename convention.

For a small change, keep the current execution card under its slice in `tasks.md`
and the planning/execution receipts in an existing process log. A card or receipt
is a record, not necessarily a separate file. Give each record a stable ID and
revision, for example `tasks.md#card-s02-v2`; mark the current card explicitly and
retain superseded cards and failed attempts as history.

Record each fact once and reference its exact record ID elsewhere. The current
card still needs the contract versions/hashes, authority source and exclusions,
objective, preconditions, verified surface, RED/GREEN and regression commands,
risks and stop condition below. Keep changing progress out of frozen Spec/Plan.
On resume or contract drift, verify the referenced record against current files
and authority before using it; a historical card is not current authorization.

For checkpoints that hash whole report files, keep a referenced receipt file
frozen. Appending another receipt to that file invalidates its previous hash;
use separate frozen receipts in that case. Section IDs aid navigation and do
not replace file hashes or authorize refreshing stale evidence.

## `plan.md`

```markdown
# <Change> Technical Plan

Status: READY_FOR_DESIGN_REVIEW | NEEDS_DECISION | APPROVED | DELEGATED_TECHNICAL
Planning mode: LIGHT | STANDARD | DETAILED
Mode rationale: <risk/uncertainty/dependency/handoff reason>
Spec source: <artifact, version, APPROVED or valid RUN AUTHORIZED_DERIVATION basis>
Project constraints: <relevant AGENTS.md, Agent.md, or equivalent rules>

## Scope and Spec mapping

| Requirement | Planned responsibility | Evidence | Notes |
|---|---|---|---|
| FR-01 | ... | ... | ... |

Explicitly excluded: ...

## Current context

- Facts: ...
- Constraints: ...
- Existing patterns reused: ...

## Proposed design

### Design views (mode-scaled, Mermaid unless the repository establishes another format)

- System context (`flowchart`): <system boundary, actors, external services/stores, interactions>
- Business flow (`flowchart` / `sequenceDiagram`): <primary journeys end to end — success and principal failure/retry paths>
- Structure/modules (`flowchart` or C4-style blocks): <module responsibilities and dependency direction>
- Data/state (`stateDiagram-v2` / `erDiagram`): <persistent entities, key state machines, ownership>
- Module designs (`DETAILED` only; `classDiagram` / `sequenceDiagram`): <per non-trivial module — responsibilities, public interfaces, key collaborations>

Apply the skill's design-view selection and depth checks. Add
deployment/trust-boundary/recovery views only when relevant. Separate data structure
and lifecycle state when both carry obligations; one does not stand in for the other.

| Design concern / Spec link | View and question answered | Interface / invariant / failure detail | Deliberate omission and rationale |
|---|---|---|---|
| <actual concern> | <section anchor; diagram type> | <contract section, not a vague promise> | <only when relevant> |

Each diagram has a short reading note: scope and level, what its arrows mean,
the contract decision it explains, and any deferred or unresolved detail. Critical
interactions include return/error outcomes, state diagrams include guards, and
interface tables name input/output types and errors. A board uses these same
sources and notes; visual styling never changes the design or approval state.

### Boundaries and responsibilities
...

### Data, state, and invariants
...

### Interfaces
...

### Failure, recovery, and security
...

### Compatibility, migration, and rollback
...

## Verification strategy

Map acceptance scenarios to unit, contract, integration, UI, performance,
or operational evidence as appropriate.

## Decisions and alternatives

| ID | Decision | Alternatives | Rationale | Owner/status |
|---|---|---|---|---|

## Assumptions and open questions

| ID | Item | Impact if false | Must resolve before |
|---|---|---|---|

## Design review record

- Authority basis: PENDING | USER_APPROVED | DELEGATED_TECHNICAL
- Exact Plan version/hash receipt: ...
- Authority source/date: <actual approval or explicit delegation of named choice classes>
- Delegated scope and choice rationale: <choices covered; consequential or reserved choices remain pending>
- Consistency review result: pass | fail, with evidence
- Human reviewer/result: <actual approval/changes requested, or not human-approved>
- Design views reviewed: <which of context / business flow / structure / data-state / module designs, and at what depth>
- Approved exceptions: ...
```

`DELEGATED_TECHNICAL` is executable only in authorized RUN after the design
consistency review and only for explicitly delegated choice classes. It does
not satisfy reserved human gates. Keep a final whole-file hash in a separate
frozen receipt; do not embed a self-invalidating hash in the Plan.

## `tasks.md`

```markdown
# <Change> Behavior Slices

Plan source: <artifact, exact version/hash, APPROVED or valid RUN DELEGATED_TECHNICAL basis>
Status: DRAFT | READY_FOR_IMPLEMENTATION

## Dependency overview

<small DAG, Mermaid diagram, or edge list>

## Slice S01 — <observable behavior>

- Spec links: FR-01, AC-02
- Outcome: <observable result>
- Preconditions: <approved contract and preceding slices>
- Depends on: none | Sxx
- Consumes / produces: <interfaces, data, states>
- Repository scope: <verified paths or named responsibilities>
- RED evidence: <test/observation that fails before implementation>
- GREEN outcome: <smallest complete behavior>
- Refactor/regression checks: <what must remain true>
- Acceptance evidence: <command, scenario, screenshot, metric, or artifact>
- Risk/rollback: <when relevant>
- Assumptions: <none or IDs from Plan>

## Coverage matrix

| Spec requirement | Slice(s) | Evidence | Coverage status |
|---|---|---|---|

## Deferred work

Only approved deferrals, each with owner and rationale.
```

## Current slice execution card

```markdown
# Execution Card — <slice ID and title>

Contract sources: <exact Spec/Plan versions/hashes, authority bases and source records>
Authorization: planning only | implementation authorized

## Objective and stop condition

<one behavior and exact completion evidence>

## Preconditions

- ...

## Verified change surface

| Path / symbol | Current responsibility | Intended change |
|---|---|---|

## RED

- Test or observation to add/run: ...
- Command: ...
- Expected failing evidence: ...

## GREEN

- Implementation constraints: ...
- Required interface/state behavior: ...
- Focused verification command: ...

## Refactor and regression

- Cleanup allowed without changing behavior: ...
- Regression command(s): ...
- Manual/operational evidence: ...

## Report back

- Changed files and contract impact
- RED and GREEN evidence
- Deviations or new decisions
- Remaining risks
```

## Planning summary

```markdown
Status: READY_FOR_DESIGN_REVIEW | READY_FOR_IMPLEMENTATION |
        NEEDS_SPEC | NEEDS_DECISION
Mode: <mode and rationale>
Contract authority: <Spec/Plan basis, scope and exact hash receipts; distinguish from human approval>
Ready slices: ...
Blocked slices: <slice -> blocker>
Decisions awaiting approval: ...
Spec coverage gaps: ...
Recommended next action: ...
```

The summary reports state; it does not replace the durable artifacts.
