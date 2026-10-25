# Verification Design Model


## Contents

- [1. Verification owns proof, not intent](#1-verification-owns-proof-not-intent)
- [2. Proof-obligation record](#2-proof-obligation-record)
- [3. Evidence lines](#3-evidence-lines)
- [4. Verification layers](#4-verification-layers)
- [5. Risk-guided portfolio](#5-risk-guided-portfolio)
- [6. Oracle selection](#6-oracle-selection)
- [7. Test-double rule](#7-test-double-rule)
- [8. Stateful system rule](#8-stateful-system-rule)
- [9. Refactoring safety net](#9-refactoring-safety-net)
- [10. Bug regression rule](#10-bug-regression-rule)
- [11. Test data classes](#11-test-data-classes)
- [12. Evidence strength and currency](#12-evidence-strength-and-currency)
- [13. Coverage model](#13-coverage-model)
- [14. Failure triage](#14-failure-triage)


Use this model to build evidence around risk and contracts instead of accumulating tests without a proof strategy.

## 1. Verification owns proof, not intent

```text
Spec: what observable behavior and quality must hold
Plan: what technical invariants and boundaries must hold
Verification design: how sufficient evidence will be produced
Implementation: code and test the approved slices
Convergence review: judge the actual evidence and remaining gaps
```

If the verification design needs to decide what success means, it has found a Spec gap. If it needs to invent state or interface semantics, it has found a Plan gap.

## 2. Proof-obligation record

Each obligation should contain:

| Field | Meaning |
|---|---|
| ID | Stable identifier such as `VO-001` |
| Source | Agent rule, FR, AC, NFR, Plan invariant, defect, or risk |
| Proposition | Observable statement that evidence must establish |
| Risk | Consequence and relevant uncertainty |
| Scope | Actors, state, data, environment, and exclusions |
| Oracle | How pass/fail or quality is decided |
| Evidence line | Deterministic, real-integration, DFX, or semantic-quality |
| Gate | Where evidence is required |

One obligation may need multiple cases. One case may prove multiple obligations only when the trace remains diagnostically clear.

## 3. Evidence lines

Keep evidence with different failure ownership separate.

### Deterministic product line

Proves platform-owned behavior: validation, state transitions, scheduling, files, APIs, UI wiring, retry policy, diagnostics, and deterministic transformation structure. Suitable for repeatable gates.

### Real-integration line

Proves that actual runtimes, operating systems, services, credentials, adapters, or models can be reached and honor the assumed protocol. It does not by itself prove full product behavior or content quality.

### DFX line

Measures performance, capacity, reliability, resource behavior, recovery time, security, compatibility, or long-running stability under frozen conditions. Results have a bounded scope; they are not universal properties of the product.

### Semantic-quality line

Evaluates generated or heuristic content against a representative data set and explicit rubric. It may use deterministic structural checks plus calibrated human or independent model judgment. Report distributions, uncertainty, sample identity, and disagreement; do not hide variability behind a single green test.

Release may require evidence from several lines, but their cases, data, cadence, and reports should remain distinguishable.

## 4. Verification layers

| Layer | Best for | Typical failure if misused |
|---|---|---|
| Static/architecture tripwire | Dependency direction, forbidden imports, schema/static policies | Encodes taste or current file layout as architecture |
| DT unit | Pure rules, parsing, calculations, state transition functions | Mirrors implementation and misses wiring |
| DT component | Collaboration within one owned module boundary | Excessive mocking makes it a unit test in disguise |
| Contract | API, event, command, persisted format, adapter and output schema | Verifies shape but not the complete workflow |
| Backend system/integration | Public API through real owned modules, persistence, queue, subprocess | Too slow or broad for every edge condition |
| Browser/UI functional | User actions, navigation, button capability, rendered state, download | Brittle DOM/text checks instead of behavior |
| Real dependency smoke | Runtime/profile/provider connectivity and minimum protocol | Mistaken for correctness or semantic-quality proof |
| DFX/specialized | Load, soak, recovery, security, compatibility, cross-platform | Unfrozen environment produces unactionable numbers |
| Semantic eval | Meaning and usefulness of non-deterministic output | Exact golden text or self-judging model produces false certainty |

Select the lowest faithful layer. “Lowest” does not mean private-function testing; it means the narrowest boundary that still observes the contract.

## 5. Risk-guided portfolio

Consider:

- user, data, security, operational, compatibility, and cost consequence;
- likelihood and change frequency;
- ease of observing failure before release;
- reversibility and recovery cost;
- concurrency, ordering, persistence, and time sensitivity;
- external/model variability;
- number of dependent features and consumers.

High-risk stateful behavior normally needs a fast local guardrail plus a wider persistence/recovery case. Low-risk pure logic may need only a focused DT. Avoid mandatory layer quotas.

## 6. Oracle selection

### Exact and state-transition oracle

Use for deterministic values, status, counts, transitions, ordering, and error codes.

### Cross-representation invariant

Use when API, persisted metadata, progress records, files, events, or UI are projections of the same truth. Assert agreement, not just individual existence.

### Contract/schema oracle

Use for stable external shapes, allowed fields, compatibility, command-line invocation, event protocol, or persisted data. Avoid overspecifying incidental serialization details.

### Structural golden oracle

Use for stable, order-sensitive deterministic output where a field-by-field assertion would obscure the contract. Keep samples small and representative; also parse or validate structure. Review golden updates as contract changes, not routine regeneration.

### Property/metamorphic oracle

Use when many inputs share an invariant: round trips, idempotency, monotonic progress, stable identity, no duplicate records, or transformations that should preserve selected properties.

### Differential oracle

Use during migration/refactoring when old and new paths should be equivalent. Document tolerated divergences explicitly rather than normalizing them away.

### Performance/statistical oracle

Use a defined workload, repetitions, denominator, percentile, error budget, resource boundary, and comparison policy. Separate regression threshold from aspirational target.

### Semantic rubric

Use binary or small explicit criteria tied to business meaning, representative positive/negative samples, independent judging, calibration examples, and a disagreement path. Deterministic schema and safety checks should remain separate hard gates.

## 7. Test-double rule

Use this boundary test:

```text
owned deterministic product path -> real
external/costly/non-deterministic dependency -> substitute
substitute/adapter protocol -> contract tested
real environment -> small separate smoke
semantic quality -> separate eval data and rubric
```

A substitute should make failures controllable, not make the system pass. Include explicit scenarios for transient, blocking, malformed, missing, partial, and hanging behavior when those branches exist.

## 8. Stateful system rule

For workflows involving persistence, queues, processes, progress, retries, or recovery, consider assertions across:

- public response or user-visible state;
- canonical persisted state;
- derived projections and counts;
- emitted files/events/logs;
- child-process/resource lifecycle;
- behavior after restart or retry;
- isolation from unrelated tasks and prior successes.

A green UI with wrong durable state, or correct files with a wrong task state, is a failure when the contract requires consistency.

## 9. Refactoring safety net

Before behavior-preserving structural work:

1. identify approved external behavior and known tolerated defects;
2. add Characterization Tests at high-risk seams;
3. freeze public API, persisted format, event, and output contracts;
4. add representative golden paths for complex deterministic transformation;
5. add directional architecture tripwires for the agreed target structure;
6. establish branch-aware coverage and hotspot gaps;
7. change one boundary at a time, running affected DT, contracts, system cases, and full regression;
8. keep semantic fixes and refactoring in separate change records.

Coverage percentage is a map, not permission to refactor. High aggregate coverage can coexist with an unprotected critical boundary.

## 10. Bug regression rule

- Reproduce the failure before fixing it when feasible.
- Put the precise regression at the lowest faithful layer.
- Add a system case when the failure was user-visible because of cross-stage wiring, persistence, process, or state inconsistency.
- Preserve the negative condition that distinguishes the bug from the happy path.
- Do not weaken or rewrite a stable contract test merely because the current implementation cannot satisfy it.

## 11. Test data classes

| Class | Purpose | Default cadence |
|---|---|---|
| Minimal positive | Fast main path and basic contract | Local/PR |
| Targeted negative | Rejection, failure classification, cleanup, isolation | Local/PR |
| Boundary/adversarial | Limits, unsafe input, path/permission/data exposure | PR/scheduled |
| Representative golden | Complex deterministic transformations and regressions | PR |
| Real integration sample | Connectivity and protocol | Environment/release |
| Semantic eval set | Meaning and quality distribution | Scheduled/release |
| Scale/soak data | Throughput, resource, long-running stability | Scheduled/release |

Do not reuse a large historical task as the default fixture merely because it already exists. Keep execution output in isolated temporary roots.

## 12. Evidence strength and currency

Record both type and currency:

| Type | Meaning |
|---|---|
| `DESIGNED` | Case and oracle exist only in the plan |
| `IMPLEMENTED_NOT_RUN` | Test exists but current execution evidence is absent |
| `CURRENT_RUN` | Reproduced on the stated baseline and environment |
| `HISTORICAL` | Report exists for another time or baseline |
| `BLOCKED` | Required evidence could not be obtained |
| `NOT_APPLICABLE` | Explicitly outside scope with rationale |

Historical evidence may establish a comparison point but cannot silently prove the current version. Missing measurements remain missing; do not estimate them into a pass.

## 13. Coverage model

Report several forms separately:

- contract coverage: mandatory requirements with an evidence route;
- risk coverage: high-consequence failures with negative/recovery cases;
- boundary coverage: interfaces, persistence, processes, environments, and dependencies exercised;
- code line/branch coverage: implementation areas executed;
- data coverage: representative categories, edge cases, and scale;
- environment coverage: supported combinations actually exercised;
- semantic coverage: rubric dimensions and sample strata.

No single percentage combines these honestly. Test count measures inventory, not strength.

## 14. Failure triage

Keep failure ownership visible:

- product regression;
- contract/specification mismatch;
- test implementation defect;
- fixture/data defect;
- environment or external dependency failure;
- semantic-quality failure;
- performance/capacity regression;
- evidence unavailable.

Do not rerun until green without recording flaky or environmental failure. Do not report a subset as “all tests passed.”
