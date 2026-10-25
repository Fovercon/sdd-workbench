---
name: sdd-requirements-contract
description: Turn new product intent or an impact-routed requirements revision into an approved, traceable SDD requirements contract before technical planning. Use when intent must be discovered, normalized, quality-checked, versioned, or handed to Plan. For changes that may invalidate approved downstream artifacts, use change-impact first; do not use this Skill for architecture, task breakdown, implementation, or completed-code review.
---

# SDD Requirements Contract

Produce a durable statement of **what must be true and why**, with enough acceptance evidence for downstream planning and convergence review. Adapt the amount of questioning to the readiness of the input; do not conduct an interview merely because the workflow supports one.

The contract is not a legal document. It is the approved product-intent baseline shared by the user, developer, planning Agent, implementation Agent, and reviewer.

## Boundaries

- Locate and obey `AGENTS.md`, `Agent.md`, or the repository's documented equivalent. These are the highest development constraints within their scope. A methodology constitution may supplement but not override them.
- Requirements define observable behavior, scope, outcomes, constraints, and acceptance. Architecture, internal module design, file paths, function signatures, technology choice, and task sequencing belong in Plan.
- An external API, persisted format, compatibility promise, or user-visible workflow may be part of the requirements contract when stakeholders depend on its behavior. Its internal implementation still belongs in Plan.
- Repository behavior is evidence about the current state, not automatically the desired requirement.
- Do not invent business semantics, security/privacy choices, recovery behavior, compatibility guarantees, thresholds, or success metrics.
- Domain grounding is a hard precondition, not a judgment call: when a mandatory obligation's correctness depends on domain semantics carried by user-held artifacts — sample data, file formats, rule sets, domain terminology — those semantics must come from an explicit user decision, a user-provided artifact, or repository evidence. When the artifact is absent, request it and return `NEEDS_INPUT`; never fill the gap with a generic or invented semantic.
- An assumption may carry only peripheral, low-consequence premises. A premise that shapes whether the product's primary output is correct is a blocking question, regardless of how the implementation is layered. Replaceability ("the engine can be swapped later") is an architecture property; it never converts an invented domain semantic into a routine technical detail.
- Approval gates the user explicitly reserved in the mission or in repository policy are binding on every route; neither faithful derivation nor technical delegation satisfies them.
- Do not mark a contract `APPROVED`; only an explicit human decision can do that. A faithful derivation of already-explicit user intent in an authorized RUN mission may instead be `AUTHORIZED_DERIVATION`, subject to the contract-model conditions. Do not manufacture a new product choice.
- Requirements work does not authorize implementation, commits, issue publication, branch creation, migrations, or external changes.

Use the status and classification rules in [references/contract-model.md](references/contract-model.md).

## Select an operating route

Choose one route after inspecting the request and available evidence:

- **SYNTHESIZE**: product decisions are already resolved **and** every domain-defining input the obligations depend on is explicitly provided or verifiable in repository evidence. Normalize the material into the contract and run the quality gate without repeating an interview. Prompt completeness is not decision completeness: silence about a domain-defining semantic means it is unresolved, not decided.
- **TARGETED_CLARIFY**: most intent is stable, but a small number of material decisions block a testable contract. Ask only those decision-frontier questions.
- **DISCOVERY**: the request is an idea or contains several dependent product choices. Build and clear a decision tree in rounds before finalizing the contract.
- **REVISION**: an approved requirement changed or implementation exposed a requirements defect. Produce an explicit delta and downstream impact; do not silently overwrite the approved baseline.

Record the route and a short rationale. Route by uncertainty and consequence, not feature size or document length.

## Workflow

### 1. Establish authority and current state

Inspect only the relevant sources:

1. Agent instructions and scoped project rules;
2. the user's request and prior decisions;
3. the current approved Spec or product documentation, if any;
4. repository behavior, tests, terminology, external interfaces, and known limitations relevant to the change;
5. issue, incident, user research, or operational evidence supplied for the request.

Identify the authoritative product owner or reviewer when stated. Record source provenance for load-bearing facts and decisions. If sources conflict, expose the conflict rather than choosing the convenient one.

### 2. Separate facts from decisions

Classify each material statement:

- `FACT`: verified current-state or external evidence;
- `USER_DECISION`: product intent explicitly selected by an authorized human;
- `ASSUMPTION`: visible, provisional premise with an owner and validation point;
- `OPEN_QUESTION`: unresolved choice or missing information;
- `CONSTRAINT`: applicable limit from policy, compatibility, operations, or Agent instructions.

Investigate discoverable facts yourself. Ask the user for decisions, preferences, authority, or unavailable domain knowledge—not for repository facts the Agent can inspect.

Never convert an unanswered product decision into an assumption merely to make the contract look complete.

### 3. Clarify only the decision frontier

For `TARGETED_CLARIFY` or `DISCOVERY`, map dependent choices as a decision tree. Ask in each round only questions whose prerequisites are settled.

For every question provide:

- the decision and why it changes the contract;
- credible options and their user-visible or operational implications;
- a recommendation when evidence supports one;
- the affected requirements or scenarios, when revising an existing contract.

Group a coherent frontier into one round, then wait for the answers. Recompute the frontier after each round. Do not impose an arbitrary maximum number of important questions, and do not ask downstream technical questions before product behavior is settled.

When a compatible grilling Skill is available and the user asks to use it, its cleared decision record can be consumed as input. Do not require that dependency: apply the decision-frontier discipline directly when needed.

### 4. Write the contract

Follow the repository's established Spec location and format when it preserves the contract model. In a fresh repository with no established location, use the suite default `design/spec.md` unless the user names another destination, and record the choice in AGENTS.md so later runs stay consistent. Otherwise use [references/artifact-template.md](references/artifact-template.md).

The contract must make these explicit, as applicable:

- problem, actors, desired outcomes, scope, and non-goals;
- domain terms and current-state facts that affect interpretation;
- prioritized user journeys or externally observable capabilities;
- functional requirements with stable identifiers;
- acceptance scenarios linked to requirements;
- error, boundary, partial-success, retry, recovery, and cancellation behavior;
- data meaning, external interface semantics, compatibility, privacy, and security obligations;
- measurable non-functional requirements and success evidence;
- assumptions, dependencies, open questions, and deferred scope;
- source, version, status, approver, and revision history.

Use `Given / When / Then` where it clarifies observable scenarios, not as ceremony for simple invariants. For model-generated or semantic outputs, define structural validation and an explicit evaluation rubric or representative evidence; deterministic tests alone may not prove quality.

Do not fabricate numerical targets. If a threshold matters but has no agreed value, keep it as a blocking question or define a measurement activity without claiming the requirement is ready.

### 5. Run the requirements quality gate

Review from the contract outward, not from a proposed implementation. Confirm:

- every mandatory requirement expresses one testable obligation;
- each requirement has acceptance evidence or a justified verification method;
- happy path, material failure, boundary, recovery, and permission cases are covered where relevant;
- terms, actors, states, and data meanings are consistent;
- scope and non-goals prevent foreseeable scope creep;
- no requirement depends on an unresolved product decision;
- core-domain semantics — formats, rules, and terminology that determine whether the primary output is correct — trace to a user decision, a user-provided artifact, or verified repository evidence; an assumption is not a valid source for them;
- assumptions are explicit, owned, and do not hide business semantics;
- success measures are observable and not invented;
- internal design has not leaked into the product contract without a stakeholder reason;
- all mandatory Agent constraints that affect the feature are referenced and no conflict is hidden;
- downstream Plan and review can cite stable requirement and acceptance identifiers.

Run a separate ambiguity pass: look for words such as “appropriate”, “fast”, “normally”, “support”, “safe”, “user-friendly”, and “etc.” that lack an observable interpretation.

### 6. Establish the authority gate

Use exactly one outcome:

- `NEEDS_INPUT`: facts or product decisions still block a sound contract;
- `READY_FOR_APPROVAL`: the contract passes the quality gate but has not been approved;
- `APPROVED`: a human explicitly approved this exact version;
- `AUTHORIZED_DERIVATION`: RUN is authorized, all material semantics map to explicit user decisions, no new business choice or blocking assumption exists, no core-domain semantic rests on an assumption, no user-reserved approval gate covers this contract, the quality gate passes, and repository policy permits derived contracts;
- `SUPERSEDED`: a later approved contract replaced this version.

Present material assumptions, exclusions, and unresolved non-blocking risks before requesting approval. Approval applies to an exact version or content hash, not to an evolving filename.

Give the user a concrete question and reply route, not just `NEEDS_INPUT` or
`READY_FOR_APPROVAL`. State the exact subject/version and scope; ask for the
missing fact/artifact or offer real approval/change/deferral choices as appropriate.
Use an available question UI or concise conversation. Accept clear natural-language
answers, recheck the baseline and record the scoped decision; do not ask again for
an already explicit answer. If a board is maintained, share this question/decision
ID with its card using the suite's [human decision interaction](../sdd-workflow-router/references/human-decisions.md).
Browser drafts alone are not approval evidence and cannot resolve absent domain input.

An `APPROVED` contract is stable input to Plan. In authorized RUN, `AUTHORIZED_DERIVATION` is also executable input with its exact hash and obligation-to-source mapping. Preserve the distinction from human approval. Do not request duplicate approval merely for restating already-decided intent.

### 7. Handle revisions without losing history

When changing an approved contract:

1. preserve the approved baseline;
2. describe additions, modifications, removals, and rationale;
3. identify affected requirement and acceptance identifiers;
4. mark impacted Plan decisions, slices, tests, documentation, and prior convergence evidence as needing re-evaluation;
5. return the proposed revision to `READY_FOR_APPROVAL`, or `AUTHORIZED_DERIVATION` only when it faithfully records an already-explicit user change under the same authority conditions;
6. mark the prior version `SUPERSEDED` only after the new version is approved.

Keep identifiers stable when semantics are unchanged. Allocate new identifiers for new obligations; record removed requirements rather than silently reusing their IDs.

## Output contract

Return or update:

1. one durable requirements contract, normally `spec.md` or the repository's established equivalent;
2. a decision and provenance log when material decisions would otherwise be lost;
3. for revisions, a contract delta and downstream impact list;
4. a concise handoff summary containing:
   - status and operating route;
   - contract version and authoritative sources;
   - decisions resolved in this run;
   - remaining blockers or assumptions;
   - quality-gate result;
   - recommended next action.

Do not produce a technical Plan or implementation checklist as part of this output.

## References

- Contract states, classifications, and readiness rules: [references/contract-model.md](references/contract-model.md)
- Requirements contract and revision templates: [references/artifact-template.md](references/artifact-template.md)
- Behavioral evaluation cases: [evals/cases.md](evals/cases.md)
