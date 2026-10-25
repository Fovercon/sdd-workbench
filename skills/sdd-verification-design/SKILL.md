---
name: sdd-verification-design
description: Design a risk-based, traceable verification safety net from an approved Spec and technical Plan, covering deterministic tests, system flows, quality attributes, and semantic or model-output evaluation. Use before implementation, refactoring, or a material change when the project needs evidence beyond local unit tests. Do not use to implement tests, execute a suite, or decide final convergence.
---

# SDD Verification Design

Turn requirements, design invariants, and failure risks into a layered evidence plan. The result should explain what must be proved, at which boundary, with which oracle and data, in which environment, and at which delivery gate.

This Skill designs the safety net. It does not implement test code, run the suite, repair failures, approve a technical Plan, or judge completed implementation.

Read [references/verification-model.md](references/verification-model.md) before assigning layers, oracles, evidence strength, or readiness. Use [references/artifact-template.md](references/artifact-template.md) for a durable verification design.

## Boundaries

- Locate and obey applicable `AGENTS.md`, `Agent.md`, and scoped repository rules.
- Treat the approved Spec as the source of observable product obligations and the Plan as the source of technical invariants and boundaries. Tests derived only from current code can mirror the implementation and miss the contract.
- Do not invent acceptance semantics, quality thresholds, supported environments, risk tolerance, or release gates.
- Do not equate test count, line coverage, generated files, or a green exit code with sufficient verification.
- Do not use an LLM judge as the sole oracle for deterministic behavior. Do not use exact-text assertions as the default oracle for variable semantic output.
- Keep platform behavior verification and generated-content or model-quality evaluation as separate evidence lines when their determinism, data, cost, and failure ownership differ.
- Verification design does not authorize network calls, real model use, production data access, performance load, environment mutation, commits, or test implementation.

## Inputs

Inspect the minimum relevant sources:

1. applicable Agent instructions;
2. approved requirements, acceptance scenarios, non-goals, NFRs, and success measures;
3. approved or review-ready Plan, ADRs, state/data/interface contracts, and behavior slices;
4. current architecture, test layout, fixtures, test commands, CI gates, reports, known defects, and coverage data;
5. external dependency contracts and supported environment matrix;
6. change-impact report when revising an existing safety net;
7. governance, compliance, cost, data sensitivity, and release constraints supplied by authorized owners.

Record artifact versions and evidence dates. Existing tests and reports are evidence about the current safety net, not proof that the proposed contract is covered.

## Select a primary mode

Choose one primary mode; add secondary concerns when needed:

- `FEATURE`: design verification for new or changed observable behavior.
- `BUG_REGRESSION`: reproduce a defect at the lowest faithful layer and protect any affected user flow.
- `REFACTOR_SAFETY_NET`: characterize current approved behavior and freeze stable boundaries before structural change.
- `QUALITY_ATTRIBUTE`: verify performance, reliability, recovery, security, compatibility, observability, or another NFR.
- `SEMANTIC_EVAL`: evaluate model-generated, heuristic, or otherwise non-deterministic output against a data set and rubric.

Mode affects the evidence portfolio; it does not change product intent. If the desired behavior is unresolved, return to Spec instead of encoding a guess in a test.

## Workflow

### 1. Establish the verification baseline

Identify:

- exact Spec and Plan baselines and their approval state;
- feature, change, slice, or refactoring scope;
- stable external contracts and internal design invariants;
- existing verification assets and current gaps;
- environments and dependencies that differ between offline development and release validation.

Return `INSUFFICIENT_BASELINE` if no authoritative behavior or technical baseline can be established. Return `NEEDS_SPEC` when success, failure, recovery, or quality meaning is materially ambiguous. Return `NEEDS_PLAN` when product intent is clear but state, interface, data ownership, migration, or observability design is too incomplete to test coherently.

### 2. Derive proof obligations

Start from each applicable requirement, acceptance scenario, NFR, Plan invariant, and high-consequence failure. Express each proof obligation as an observable proposition, for example:

```text
When a selected failed item is rerun, successful and unselected items remain unchanged,
the original record is replaced rather than duplicated, and persisted state agrees with the API.
```

Cover, where material:

- main success path;
- invalid and adversarial input;
- boundary and empty cases;
- partial success and failure isolation;
- retry, timeout, cancellation, pause, resume, restart, and recovery;
- ordering, concurrency, idempotency, and duplicate prevention;
- persisted state, derived projections, files, events, and user-visible consistency;
- authorization, data exposure, diagnostics, redaction, and auditability;
- migration, compatibility, rollback, and cross-platform behavior;
- performance, resource, capacity, cost, and long-running stability;
- semantic quality and model variability.

Do not create one test per sentence mechanically. Combine obligations only when one scenario proves them through the same setup and oracle without obscuring failure diagnosis.

### 3. Prioritize by risk

Assess consequence, likelihood, detectability, reversibility, state/ordering sensitivity, dependency variability, and change blast radius. Use the repository's risk scale when available; otherwise label relative priority and explain it without inventing numerical scores.

For every high-risk obligation, identify:

- the cheapest fast guardrail;
- the boundary-level proof needed to catch integration drift;
- the environment-specific or human gate that automation cannot replace;
- the consequence if evidence is absent.

Spend verification effort on high-risk branches and boundaries before raising aggregate coverage through low-value paths.

### 4. Select the smallest sufficient layer portfolio

Choose from the model rather than requiring every layer:

- static or architecture tripwire;
- DT unit test;
- DT component test;
- contract test;
- integration or backend system test;
- browser/UI functional test;
- real dependency or model smoke test;
- performance, stability, security, recovery, compatibility, or cross-platform test;
- semantic quality evaluation.

Place each assertion at the lowest layer that can faithfully observe the obligation. Add a wider system or UI case when correctness depends on wiring, persistence, processes, state transitions, user actions, or multiple stages.

For a user-visible defect, plan a minimal reproducing regression and, when the defect crosses stages or boundaries, a system-flow regression. For a behavior-preserving refactor, freeze public contracts and representative current behavior before changing structure; add architecture tripwires only for explicit design direction, not personal taste.

### 5. Choose an oracle that can fail for the right reason

Select one or more:

- exact value or state transition;
- invariant across multiple representations;
- schema or interface contract;
- deterministic structural golden sample;
- property, metamorphic relation, or differential comparison;
- observable UI behavior;
- performance/statistical threshold under frozen conditions;
- semantic rubric with representative samples and independent review.

For persisted workflows, verify at least the relevant public response and durable state or output. Status-only or file-exists-only checks are insufficient when the contract requires both to agree.

For complex deterministic transformations, use a small representative golden path and separately validate parseability, schema, or invariants so an opaque snapshot is not the only signal. For legacy characterization, label whether the baseline is approved behavior, a tolerated defect, or unknown behavior; do not silently convert a defect into a permanent contract.

For high-risk generated tests or tripwires, design a sensitivity check: a controlled mutation, deliberately broken fixture, or known counterexample should cause the intended test to fail. Do not mutate a live workspace destructively merely to demonstrate this.

### 6. Design test doubles at the unstable boundary

Keep as much of the owned product path real as is practical. Replace only external, costly, slow, non-deterministic, or unavailable dependencies.

A deterministic substitute must:

- implement the real invocation, event, file, state, and error contract needed by the product;
- expose scenarios explicitly through configuration or fixture input, never by inspecting a test name;
- reproduce success, transient failure, blocking failure, malformed/missing output, timeout/hang, and partial completion when relevant;
- be checked by contract tests so it cannot drift unnoticed from the real adapter;
- avoid claiming semantic quality or real-environment compatibility.

Use a small real-dependency smoke line to cover wiring and environment assumptions that the substitute cannot prove. Keep it out of the default offline gate when it needs credentials, network, cost, or unstable service capacity.

### 7. Design data and environment matrices

Use minimal deterministic data for fast gates, representative golden data for complex behavior, adversarial data for safety boundaries, and scale data for performance. Keep these purposes separate.

- Build fixtures deterministically when practical.
- Use an isolated temporary workspace; do not read or modify historical user task directories by default.
- Record data identity and hash when results will be compared over time.
- Keep production or sensitive data out unless explicitly authorized and governed.
- Cover only supported environment combinations, but make untested combinations visible.

For performance and reliability claims, freeze workload, denominator, version, commit/dirty state, dependency/model identity, concurrency, timeout/retry policy, host/resources, network path, time window, and repetitions. Report skipped, failed, retried, and missing measurements separately. A configurable maximum is not a verified capacity.

### 8. Build traceability and gates

Create a matrix linking:

```text
Agent rule / FR / AC / NFR / Plan invariant
  -> risk and proof obligation
  -> case and verification layer
  -> oracle and test data
  -> environment and command
  -> delivery gate and expected evidence
```

Use differentiated gates:

- local change: affected DT and contracts;
- pre-commit or PR: stable offline suite plus affected system cases;
- main or scheduled: broader system/UI, stability, and supported environment checks;
- release: real dependency smoke, performance/DFX, semantic quality, migration, or manual acceptance as applicable.

Gate deterministic, reproducible obligations. Measure and trend variable quality where a binary threshold is not approved. Do not put paid, networked, long-running, or credentialed tests into the default gate without an explicit operational decision.

### 9. Review the design

Confirm:

- every mandatory contract item has an evidence route or an explicitly approved deferral;
- high-risk failures have negative and recovery evidence, not only happy paths;
- no test derives desired behavior solely from current code;
- the layer is faithful and not wider or more brittle than necessary;
- substitutes stop at the correct boundary and have contract protection;
- test data is isolated, purpose-specific, and reproducible;
- semantic quality is not confused with platform function;
- coverage and test count are used as diagnostics, not completion claims;
- commands, markers, environments, owners, costs, and evidence retention are explicit;
- tests invalidated by a changed contract are identified for revision rather than weakened to stay green.

Route material contract drift through `sdd-change-impact`. Feed an approved design into the relevant Plan and slices. After implementation and execution, use `sdd-converge-review` to judge actual evidence against the contract.

## Outcomes

Return exactly one:

- `VERIFICATION_DESIGN_READY`: obligations, risks, layers, oracles, data, environments, gaps, and gates are complete enough for review or Plan integration;
- `NEEDS_SPEC`: observable intent or acceptance meaning is missing or contradictory;
- `NEEDS_PLAN`: the technical boundary or invariant needed for a coherent test strategy is unresolved;
- `HUMAN_DECISION_REQUIRED`: threshold, supported environment, cost, risk acceptance, deferral, or gate policy needs an authorized decision;
- `INSUFFICIENT_BASELINE`: authoritative artifacts or current verification assets cannot be identified sufficiently.

`VERIFICATION_DESIGN_READY` is not human approval and does not authorize implementation or execution.

## Output contract

Return or create:

1. baseline, scope, primary mode, outcome, and evidence limits;
2. risk and proof-obligation register;
3. contract-to-evidence trace matrix;
4. layered case portfolio with oracle, data, doubles, environment, and frequency;
5. deterministic platform, real-integration, semantic-quality, and DFX lines where applicable;
6. fixture and environment matrix;
7. delivery gates, evidence retention, and failure triage rules;
8. gaps, human decisions, and the smallest next action.

Follow an established repository format and location. Otherwise return the design in the response or use a user-specified path; do not invent a new permanent project directory.

## References

- Layers, proof obligations, oracles, doubles, evidence, and coverage rules: [references/verification-model.md](references/verification-model.md)
- Verification design and matrix template: [references/artifact-template.md](references/artifact-template.md)
- Behavioral evaluation cases: [evals/cases.md](evals/cases.md)
