---
name: sdd-converge-review
description: Review whether an implementation has converged with its AGENTS.md, specification, design, tasks, and verification evidence. Use for pre-delivery convergence checks, specification-compliance reviews, implementation-fidelity audits, or deciding whether findings must return to Spec, Plan, or Implement. Do not use to compare SDD frameworks or for an ordinary code review that has no specification baseline.
---

# SDD Converge Review

Determine whether the current implementation is supported by enough evidence to enter Finish. Review independently against the project's persistent contracts; do not treat passing tests or the implementer's summary as sufficient proof.

## Execution context

In authorized Router RUN, the Spec/Plan may be distinctly marked `AUTHORIZED_DERIVATION` / `DELEGATED_TECHNICAL` after their owning gates. Review their source mappings and delegated choices as well as exact hashes; do not claim human approval. Return findings to the controller. Existing mission authorization to implement and repair allows a subsequent repair invocation; this review remains read-only and must be refreshed after changes.

## Boundaries

- This is a review workflow. Do not modify code, specifications, tests, release metadata, or external systems unless the user separately asks for fixes.
- Do not compare frameworks or skills. Review one implementation against its own agreed contracts.
- Do not invent missing requirements, acceptance criteria, test results, or risk acceptance.
- A human owns scope decisions, requirement approval, residual-risk acceptance, and final release authorization.
- Follow every applicable `AGENTS.md` before applying this skill. Repository rules outrank this workflow.

## Required Review Model

Read [references/review-model.md](references/review-model.md) before classifying coverage, findings, return stages, or the final decision.

Read [references/report-template.md](references/report-template.md) when producing a durable convergence report or when the repository has no established review format.

## Workflow

### 1. Establish the review baseline

Discover, in this order:

1. applicable `AGENTS.md` files and repository instructions;
2. signed or current specification and acceptance scenarios;
3. plan, ADRs, interfaces, data/state contracts, and tasks;
4. requested change scope, current diff, and relevant implementation;
5. existing test commands, test reports, E2E evidence, evals, and known issues.

State which artifacts are authoritative and which are missing, stale, ambiguous, or only advisory. When several documents conflict, do not silently choose one: record the conflict and route it to the owning stage.

If no usable specification or acceptance baseline exists, perform only a limited engineering review and return `INSUFFICIENT_EVIDENCE`; do not claim SDD convergence.

### 2. Build the contract coverage matrix

Start from the specification, not from the code or existing tests. Enumerate each mandatory user story, functional requirement, success criterion, acceptance scenario, boundary, and relevant non-functional requirement.

For every contract item, record:

- requirement identifier or a stable local label;
- implementation evidence with file and line when available;
- verification evidence with exact command, report, or reproducible observation;
- coverage status from the review model;
- remaining gap and return stage.

Existing tests count as evidence only for the behavior they actually assert. Test names, test counts, generated files, process exit code, and UI visibility do not by themselves prove business success.

### 3. Verify the evidence

Prefer current, reproducible evidence. Run safe, relevant checks when the user's request and repository rules permit them. Record the exact command and result; distinguish a fresh run from a historical report.

Select verification in proportion to risk:

- deterministic logic: focused unit and component tests;
- state, persistence, queue, recovery, and process boundaries: integration or restart scenarios;
- user-visible workflows: API or browser E2E evidence;
- model-generated or semantic output: schema checks plus golden samples, representative sampling, or an explicit eval rubric;
- security and untrusted input: negative and adversarial cases;
- performance claims: workload, environment, concurrency, timeout, retry, model, and denominator must accompany the number.

If a check cannot complete, preserve the failure or blockage as evidence. Never convert “not run”, “hung”, “environment unavailable”, or “unknown” into pass.

### 4. Perform two independent review passes

Keep the passes separate to reduce anchoring.

**Contract-fidelity pass**

- missing, partial, contradictory, or unrequested behavior;
- acceptance, error, recovery, compatibility, and scope boundaries;
- divergence among Spec, Plan, Tasks, tests, and implementation;
- model/program responsibility and data-authority violations.

**Engineering-quality pass**

- correctness, security, unsafe input handling, state consistency, and resource lifecycle;
- maintainability problems that create concrete change risk;
- tests that mirror the implementation, omit critical paths, or weaken the contract;
- hidden environment assumptions, generated-state pollution, release or observability gaps.

Report only evidence-backed findings. Separate `FACT` from `ASSESSMENT`; attach a concrete consequence to every finding. Avoid generic style advice and speculative redesign.

### 5. Route every material finding

Assign one primary return stage:

- `SPEC`: intent, scope, acceptance, terminology, or business decision is missing or changed;
- `PLAN`: architecture, state/data/interface contract, quality strategy, or cross-cutting design is inadequate;
- `IMPLEMENT`: agreed design is clear but code, tests, configuration, or documentation does not satisfy it;
- `FINISH`: implementation is converged but packaging, versioning, deployment evidence, known issues, or release authorization is incomplete.

Do not route a structural design problem to Implement merely because code can be patched locally. Do not route a clear implementation defect back to Spec.

### 6. Decide convergence

Use exactly one decision from the review model:

- `CONVERGED`
- `NOT_CONVERGED`
- `INSUFFICIENT_EVIDENCE`
- `HUMAN_DECISION_REQUIRED`

`CONVERGED` requires all mandatory contract items to be verified, required gates to pass, no unresolved BLOCKER or HIGH finding, and no unapproved residual risk. The model may recommend convergence but may not accept risk or authorize release for the user.

## Output

Lead with the decision and the most important reason. Then provide:

1. review baseline and evidence limits;
2. BLOCKER/HIGH findings first, each with evidence, consequence, and return stage;
3. contract coverage summary and matrix;
4. verification results, including failures and checks not run;
5. residual risks and decisions requiring a human;
6. smallest next loop: return to Spec, Plan, Implement, or proceed to Finish.

When the user requests a durable artifact, follow the repository's established location and use the report template. Otherwise return the review in the response without inventing a new project directory.

## Completion Check

Before finishing, confirm that:

- every conclusion traces to a contract or observable fact;
- facts and assessments are visibly separated;
- every mandatory requirement has a coverage status;
- every material finding has one return stage;
- blocked or absent evidence is not reported as passing;
- the decision follows the defined gate and does not imply release authorization.
