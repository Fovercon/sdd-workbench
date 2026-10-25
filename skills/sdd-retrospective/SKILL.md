---
name: sdd-retrospective
description: Turn completed or paused SDD work, incidents, repeated rework, or method experiments into an evidence-backed learning package and bounded proposals for project rules, contracts, Skills, templates, tests, and eval cases. Use when the goal is to improve how future work is performed. Do not use for delivery status, convergence review, blame analysis, or automatic mutation of the assets being reviewed.
---

# SDD Retrospective

Convert project experience into scoped, testable learning. Reconstruct what happened from evidence, compare expected and actual workflow, explain material deviations without inventing causality, and route each lesson to the smallest durable asset that can prevent recurrence or preserve a successful practice.

A retrospective supplies the learning package for the method-learning loop. Adoption and regression close that loop. It does not reopen delivery work automatically, rewrite history, or promote every observation into a universal rule.

Read [references/learning-model.md](references/learning-model.md) before assigning evidence strength, causes, recurrence, promotion level, or asset destination. Use [references/retrospective-template.md](references/retrospective-template.md) for a durable learning package.

## Execution context

This Skill produces the learning package; that alone does not close adoption and validation. In Router RUN, return the package to the controller. When current or prior mission authorization includes method maintenance, the controller may apply a bounded candidate, run before/after regression, adjudicate and retain or revert it without asking for the same permission again. Product-only authorization permits recording proposals, not editing global method assets. Historical authorship is optional provenance, never a prerequisite for this engineering loop.

## Boundaries

- Locate and obey applicable `AGENTS.md`, `Agent.md`, repository rules, and data-handling constraints.
- Treat approved contracts, repository history, code, tests, command outputs, review findings, issue records, and measured results as distinct evidence sources.
- Separate `FACT`, `REPORTED`, `ASSESSMENT`, `HYPOTHESIS`, and `UNKNOWN`. Do not present a reconstructed story as direct observation.
- Do not infer causality from sequence alone. Record contributing conditions and competing explanations when the evidence cannot isolate a root cause.
- Do not claim speed, quality, coverage, cost, or productivity improvements without a defined denominator and comparable baseline.
- Do not use the retrospective to approve product behavior, accept delivery risk, declare convergence, or certify Finish readiness.
- Do not edit `AGENTS.md`, Spec, Plan, Skills, templates, tests, evals, issue trackers, or external systems unless current or prior user authorization covers those follow-up changes.
- Do not assign personal blame. Analyze decisions, information, workflow, controls, interfaces, tools, and system conditions.
- Preserve unresolved work and negative evidence. A polished narrative must not erase failures, deferred items, or contradictory results.

## Select a mode

Choose one primary mode and state why:

- `MILESTONE`: learn from a completed feature, iteration, prototype, release, or declared stage boundary.
- `INCIDENT`: analyze a defect, failed gate, unsafe action, repeated debugging episode, or costly rework.
- `METHOD_EXPERIMENT`: assess an explicit comparison of prompts, Skills, frameworks, workflows, or review methods.
- `PERIODIC`: aggregate several deliveries or incidents to decide whether a pattern is recurring and promotable.

Use `MILESTONE` only when there is enough execution evidence to compare intent and result. A stage transition alone does not require a retrospective. Use a normal status report when the user only asks what is complete or blocked.

## Workflow

### 1. Define the learning question and boundary

Record:

- subject, repository, time or baseline range, and included scope;
- why the retrospective is being performed now;
- decisions it may inform;
- excluded topics and unavailable evidence;
- whether the work is complete, paused, failed, superseded, or still evolving.

Phrase the learning question so evidence can answer it. Prefer “Why did the queue bypass survive existing tests?” over “What went wrong?”. Do not let a broad request such as “summarize lessons” silently become a claim about the entire project.

### 2. Freeze the evidence baseline

Identify the exact versions or ranges of relevant:

- Agent instructions and engineering rules;
- Spec, Plan, Tasks, verification design, and approved changes;
- execution cards, receipts, ledgers, commits, diffs, and working state;
- test, system, semantic, performance, security, and cross-platform evidence;
- convergence and Finish reports;
- review findings, issue/debug records, decisions, and prior retrospectives;
- comparison protocol, inputs, model/tool versions, repetitions, and judge data for method experiments.

Use only evidence necessary for the learning question. If a source was reconstructed later, label its provenance and corroborate load-bearing claims against primary artifacts where possible.

Return `INSUFFICIENT_EVIDENCE` when missing identity, baselines, or outcome evidence would make the central conclusion speculative. Return `RECONCILIATION_REQUIRED` when authoritative records conflict and the conflict cannot be bounded.

### 3. Reconstruct the decision and event chain

Build a concise sequence of material events:

```text
expectation or decision
  -> action taken
  -> observable result
  -> detection mechanism
  -> response or correction
  -> current state
```

For every event, cite the source and distinguish event time from the time it was documented. Include positive controls and uneventful gates only when they help explain why a practice worked. Do not copy the entire Git log or conversation.

### 4. Compare intended and actual workflow

Assess the dimensions relevant to this case:

- product outcome and acceptance coverage;
- Spec, Plan, Tasks, and implementation fidelity;
- Slice sizing, ordering, and interruption/rework;
- TDD or characterization discipline and test sensitivity;
- convergence, independent review, and risk decisions;
- Finish identity, operability, and handoff quality;
- Agent context, instructions, permissions, and human gates;
- environment, tools, dependencies, and process fit;
- measured time, cost, quality, or throughput only when comparable.

Classify each deviation as `BENEFICIAL`, `NEUTRAL`, `COSTLY`, `RISKY`, or `UNKNOWN`. A deviation from the planned process is not automatically a failure; judge its effect and evidence.

### 5. Analyze material findings

For each finding, separate:

1. observed outcome or symptom;
2. expected control or behavior;
3. detection point and why it was or was not detected earlier;
4. immediate mechanism;
5. contributing conditions;
6. earliest owning layer;
7. evidence strength and competing explanations;
8. consequence, recurrence likelihood, and reversibility.

Use the cause taxonomy in the learning model. Stop causal depth when the proposed explanation no longer changes a future control. Avoid “AI made a mistake” as a root cause; identify the missing contract, weak oracle, absent gate, context loss, execution deviation, tool limitation, or local defect that made the outcome possible.

### 6. Extract successes and failures symmetrically

For a failure, ask what control should prevent, expose, contain, or recover from it. For a success, ask what evidence shows the practice contributed and whether removing it would plausibly weaken the result.

Do not promote a practice because it sounds reasonable. Distinguish:

- a confirmed existing control that worked;
- a new candidate control;
- a one-off workaround;
- a hypothesis needing another run;
- a practice that added ceremony without observable value.

When an existing rule or Skill already covers the lesson, prefer strengthening its example, evaluation case, trigger, or enforcement evidence over duplicating the rule elsewhere.

### 7. Route each learning item to the smallest durable asset

Choose one primary destination:

- `AGENT_RULE`: stable repository-wide Agent behavior, safety boundary, coding principle, or mandatory workflow constraint;
- `SPEC`: project/product behavior, scope, acceptance, terminology, or business policy;
- `PLAN`: architecture, interface, state, data ownership, recovery, migration, or verification design;
- `SKILL`: repeatable judgment-heavy procedure useful across multiple qualifying tasks;
- `TEMPLATE`: stable output structure or checklist whose value does not depend on substantial judgment;
- `TEST_OR_EVAL`: concrete failure, boundary, counterexample, or behavior that should detect regression;
- `BUSINESS_PROFILE`: domain-specific rubric, dataset, oracle, or evaluation rule;
- `PROJECT_BACKLOG`: valid improvement or debt that remains local to this project;
- `KNOWLEDGE_NOTE`: explanatory context worth retaining but not enforcing;
- `NO_PROMOTION`: unsupported, obsolete, redundant, or harmful candidate.

Apply the promotion criteria in the learning model. One occurrence normally produces a candidate, not a universal rule. A single high-consequence safety failure may justify immediate project protection when the rule is clear, low-cost, and testable; record that exception explicitly.

Do not confuse destinations: product semantics do not belong in `AGENTS.md`; a fixed document skeleton does not need a Skill; a concrete bug should usually become a test before it becomes a generic instruction.

### 8. Define bounded follow-up proposals

For every promoted or retained item, specify:

- proposed destination and exact scope;
- minimal change, not full rewritten content unless requested;
- evidence supporting the proposal;
- owner or required human gate;
- validation method and rollback/removal condition;
- dependencies and conflicts with existing assets;
- whether delivery contracts or evidence would be invalidated.

If a learning item changes approved product or technical contracts, route its project impact through `sdd-change-impact` before edits. If it proposes a new or changed Skill, preserve it as a Skill change proposal until a Skill-authoring workflow is authorized; existing mission maintenance authorization can satisfy this gate. Do not bundle unrelated proposals into one large process rewrite.

### 9. Close the learning loop

Prioritize actions by consequence, recurrence, evidence strength, prevention value, cost, and maintenance burden. Separate:

- immediate containment or unfinished delivery work;
- next-iteration project improvements;
- method-asset proposals;
- experiments needed to validate hypotheses;
- observations intentionally retained without action.

Define how the next qualifying project will tell whether each adopted change helped. A retrospective action without a future observation or evaluation point is not closed-loop learning.

## Outcomes

Return exactly one:

- `LEARNING_PACKAGE_READY`: findings, evidence limits, asset routes, and bounded follow-ups are complete enough for review and prioritization;
- `HUMAN_DECISION_REQUIRED`: desired method, promotion scope, ownership, risk, or conflicting priorities require an authorized decision;
- `RECONCILIATION_REQUIRED`: contradictory histories, baselines, or outcome records must be reconciled before credible learning can be extracted;
- `INSUFFICIENT_EVIDENCE`: the central learning question cannot be answered reliably from available evidence;
- `NO_RETROSPECTIVE_NEEDED`: the request is a status/review task, the activity is too trivial, or no meaningful learning boundary exists.

`LEARNING_PACKAGE_READY` does not approve or apply any proposed asset change, and it does not imply the underlying delivery is complete.

Use `LEARNING_PACKAGE_READY` when the evidence supports bounded proposals even though their adoption still awaits normal approval. Use `HUMAN_DECISION_REQUIRED` when an unresolved method, scope, ownership, or risk choice prevents the retrospective from selecting a credible promotion route.

## Output contract

Return or create one learning package containing:

1. outcome, mode, learning question, scope, and evidence baseline;
2. outcome snapshot and evidence limitations;
3. material event/decision timeline;
4. intended-versus-actual workflow comparison;
5. evidence-backed findings with cause, consequence, and confidence;
6. successful practices, failed controls, and unresolved hypotheses;
7. learning-item register with destination and promotion state;
8. prioritized follow-up proposals with owners, gates, validation, and rollback;
9. future observation plan and explicitly unclaimed conclusions.

Use the repository's established retrospective location when one exists. Otherwise return the package in the response or use a user-specified path. Do not invent a permanent directory or overwrite prior retrospectives without authorization.

## References

- Evidence, causal analysis, promotion, asset routing, and closure rules: [references/learning-model.md](references/learning-model.md)
- Durable retrospective learning package: [references/retrospective-template.md](references/retrospective-template.md)
- Behavioral evaluation cases: [evals/cases.md](evals/cases.md)
