# Change Impact Model


## Contents

- [1. Separate five things](#1-separate-five-things)
- [2. Primary route decision table](#2-primary-route-decision-table)
- [3. Common traps](#3-common-traps)
- [4. Propagation models](#4-propagation-models)
- [5. Impact statuses](#5-impact-statuses)
- [6. Invalidation rules by owning layer](#6-invalidation-rules-by-owning-layer)
- [7. Impact dimensions](#7-impact-dimensions)
- [8. Minimal propagation principle](#8-minimal-propagation-principle)
- [9. Facts and assessments](#9-facts-and-assessments)


## 1. Separate five things

| Item | Question |
|---|---|
| Trigger | What request, observation, incident, dependency, or review finding started the analysis? |
| Approved baseline | What exact behavior and design are currently authorized? |
| Observed state | What does the current implementation or environment actually do? |
| Proposed delta | What outcome or constraint would change? |
| Proposed mechanism | How someone currently suggests implementing the delta? |

A proposed mechanism must not decide the route. “Add a database table” may implement a new product history requirement (`SPEC`), repair a missing persistence design (`PLAN`), or be an unnecessary solution to an implementation defect (`IMPLEMENT`).

## 2. Primary route decision table

Choose the earliest layer whose authoritative meaning must change.

| Diagnostic question | Route |
|---|---|
| Does a durable Agent working constraint or repository-wide engineering rule change? | `AGENT_RULES` |
| Does externally observable behavior, scope, data meaning, authorization, recovery, compatibility, or success evidence change or remain undefined? | `SPEC` |
| Is product intent stable but a technical invariant, architecture, state/data/interface contract, migration, rollback, observability, or verification design inadequate? | `PLAN` |
| Are Spec and Plan adequate, while code/config/tests/local docs violate them? | `IMPLEMENT` |
| Is implementation converged and only packaging, version, changelog, deployment evidence, or release authorization affected? | `FINISH` |
| Is meaning unchanged and only wording, evidence timestamp, verified rename, or mechanical representation changes? | `NO_CONTRACT_CHANGE` |

If two routes appear necessary, choose the earliest as primary and list later routes as propagation steps. Do not report “Spec + Plan + Implement” as three equal roots.

## 3. Common traps

### “It is a bug, so route to Implement”

First compare observed behavior with approved behavior. If the contract clearly defines the desired outcome, route to `IMPLEMENT`. If the contract is silent or contradictory, route to `SPEC` or `HUMAN_DECISION_REQUIRED`.

### “It is security, so route to Spec”

An existing rule to treat archives as untrusted plus a path-traversal defect is `IMPLEMENT`. A missing user-visible rejection/audit obligation may be `SPEC`. A deficient sandbox or trust-boundary design may be `PLAN`. A new repository-wide mandatory safety workflow may be `AGENT_RULES`.

### “Only an internal format changed”

If external consumers, persisted historical data, operators, migrations, or compatibility promises depend on the format, it is not purely internal. Route to `SPEC` for the external promise and `PLAN` for realization.

### “Tests still pass”

Old tests may encode the old contract. A passing result stays historical evidence until checked against the new requirement, design, data, and environment.

### “The patch is already merged”

Implementation existence does not approve changed product intent. Use `FLOW_BACK` to repair the owning contract and reassess the implementation.

### “Urgent hotfix”

Urgency may change sequencing and approval policy, not truth. Record the emergency authority and temporary deviation, then restore contract alignment and evidence. Do not rewrite history to make the bypass disappear.

## 4. Propagation models

### `FLOW_FORWARD`

Use for a distinct capability or substantial follow-up with its own approval and lifecycle. Create a new contract and retain the old feature history. Link dependencies explicitly.

### `LIVING`

Use for a changed decision within the same active feature. Revise the requirements contract, approve the exact version, then re-plan, re-slice, re-implement, and re-converge only the affected scope.

### `FLOW_BACK`

Use when implementation, testing, operations, or review exposes a missing or wrong upstream contract. Stop local patching at the discovery point, repair the earliest owner, then flow forward.

### `LOCAL_CORRECTION`

Use when approved upstream meaning is adequate. Patch the implementation or finish artifact, regenerate relevant evidence, and reconverge affected scope.

### `NO_PROPAGATION`

Use for rejected, superseded, duplicate, or genuinely informational records.

## 5. Impact statuses

| Status | Meaning |
|---|---|
| `INVALIDATED` | The artifact or evidence asserts old meaning and cannot support the changed baseline |
| `REVERIFY` | It may remain correct, but shared behavior, environment, or dependency changed and evidence must be rerun |
| `REVIEW_REQUIRED` | The analysis cannot establish validity without an owner or domain review |
| `UNCHANGED` | Evidence shows its meaning and validity are outside the changed dependency path |
| `UNKNOWN` | Missing links, versions, or evidence prevent classification |

`UNCHANGED` is an evidence-backed conclusion, not the default. Use `UNKNOWN` when tracing is incomplete.

## 6. Invalidation rules by owning layer

### Agent rules change

Review all in-scope active contracts, implementation work, tests, and review evidence that depended on the old rule. Do not assume every repository artifact is affected; use rule scope.

### Spec change

Invalidate affected Plan responsibilities, slices, expected tests/evals, implementation-conformance claims, convergence rows, and finish claims. Unaffected requirements can remain valid when shared dependencies were checked.

### Plan change

Keep approved product intent unless the design discovery exposed a product ambiguity. Invalidate affected slices, execution cards, implementation assumptions, technical tests, migration/rollback evidence, and convergence rows.

### Implementation correction

Contracts normally remain unchanged. Reverify focused behavior, shared regressions, and affected convergence evidence. A regression test becomes new evidence; it is not automatically a new requirement.

### Finish change

Normally keep earlier contracts and implementation evidence. Reverify packaging or release-specific evidence and confirm no built artifact differs from the converged source.

## 7. Impact dimensions

Inspect only dimensions relevant to the changed dependency path:

- user-visible workflow and permissions;
- scope, terminology, and non-goals;
- data meaning, retention, authority, persistence, and migration;
- state transitions, ordering, concurrency, retry, recovery, cancellation, and idempotence;
- external interface and compatibility;
- security, privacy, secrets, audit, and untrusted input;
- model/code responsibility and generated-output contract;
- performance, capacity, timeout, and reliability;
- platform and cross-product shared components;
- unit, contract, integration, system, UI, performance, and semantic evaluation;
- operational diagnostics, observability, support documentation, and rollback;
- versioning, changelog, packaging, deployment, and release authorization.

Do not populate every dimension with boilerplate. State why omitted dimensions are not on the dependency path when the risk warrants it.

## 8. Minimal propagation principle

Rebuild from the earliest changed contract, but only across affected trace links:

```text
earliest owner
  -> approve exact delta
  -> revise affected downstream contracts
  -> replace invalid slices/cards
  -> implement
  -> regenerate invalidated evidence
  -> reconverge
  -> refresh finish artifacts
```

This is neither “edit everything” nor “patch only the code”. The goal is the smallest set that restores an internally consistent, evidence-backed chain.

## 9. Facts and assessments

Use:

- `FACT` for direct artifact, code, command, or runtime evidence;
- `ASSESSMENT` for inferred dependency, blast radius, risk, or likely owner;
- `DECISION` only for an explicit human choice;
- `UNKNOWN` when evidence is absent.

Every material assessment should cite the facts that support it. Never describe risk acceptance, scope approval, or release authorization as an assessment the Agent can make.
