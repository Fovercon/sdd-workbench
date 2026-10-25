---
name: sdd-plan-slices
description: Turn an approved SDD specification into a reviewable design contract and dependency-aware vertical behavior slices before implementation. Use after requirements are stable and before coding, especially for multi-module or long-running work that needs traceability from Spec to tests. Do not use to discover requirements, transfer transient context, review completed implementation, or replace repository Agent instructions.
---

# SDD Plan Slices

Convert an authorized, stable Spec into two durable artifacts:

- `plan.md`: the stable technical design contract.
- `tasks.md`: dependency-aware vertical behavior slices that implement the contract.

Create a detailed execution card only for the slice currently being implemented. Keep speculative implementation code out of the durable Plan.

## Execution context

In authorized Router RUN, `AUTHORIZED_DERIVATION` is valid Spec input under its contract-model conditions. Routine design choices within explicit technical delegation may pass the design gate as `DELEGATED_TECHNICAL` after the consistency review; record the exact Plan hash, delegation source and choice rationale. Explicit delegation means the user stated the delegated class of choices (for example, "the technical design is yours to decide"); a technology-stack constraint bounds the design, it does not delegate it. Whether a domain semantic — a format, rule, or terminology the product must honor — is implemented correctly is consequential by default: it decides whether the core output is correct, and engine-level replaceability does not demote it. This is not human approval. Consequential choices, required project approvals, and approval gates the user explicitly reserved still return `NEEDS_DECISION`. If a Spec's core-domain semantics rest on assumptions, return `NEEDS_SPEC` instead of planning around them. Elsewhere, use the explicit approval route. References to approved contracts below include these distinctly recorded executable baselines only in RUN.

## Boundaries

- Locate and obey the repository's `AGENTS.md`, `Agent.md`, or documented equivalent before planning. Treat these Agent instructions as the highest development constraints within their scope.
- Treat the approved Spec as the source of product intent. Do not silently resolve missing or conflicting requirements in the Plan.
- Treat the Plan as a technical contract, not a second requirements document and not a task checklist.
- Treat Tasks as observable behavior increments, not layers such as “finish backend”, “write frontend”, and “add tests”.
- Planning does not authorize implementation, commits, migrations, deployments, or destructive actions.
- Do not claim a design is approved merely because the AI generated it.

Return `NEEDS_SPEC` when acceptance behavior is absent or materially ambiguous. Return `NEEDS_DECISION` when a consequential technical choice requires human approval. Otherwise progress through `READY_FOR_DESIGN_REVIEW` and, after the design gate is passed, `READY_FOR_IMPLEMENTATION`.

## Inputs

Inspect only what is needed to establish the current contract:

1. `AGENTS.md`, `Agent.md`, or the repository's equivalent Agent instructions, plus scoped engineering rules. A methodology “constitution” may supplement these rules but must not replace or override them.
2. The approved Spec, acceptance scenarios, and explicit exclusions.
3. Current architecture, interfaces, data models, tests, and nearby implementation patterns.
4. Relevant ADRs, operational constraints, compatibility promises, and migration limits.
5. Existing Plan or Tasks when revising rather than creating them.

Label statements as one of:

- **Fact**: verified in a source artifact or repository.
- **Decision**: selected design choice with rationale and owner.
- **Assumption**: temporary premise that must be validated before its dependent slice starts.
- **Open question**: unresolved item that blocks Spec, design approval, or execution.

Never invent file paths, interfaces, or repository conventions. Inspect them or describe the intended responsibility without claiming an exact location.

## Workflow

### 1. Check Spec readiness

Confirm that the Spec states the actors or callers, observable behavior, key inputs and outputs, failure behavior, and acceptance evidence. Map every mandatory requirement to a stable identifier.

If a missing answer would change user-visible behavior, data semantics, security, recovery, or compatibility, stop with `NEEDS_SPEC`. If the behavior is stable but the implementation choice is consequential, record alternatives and stop at the design gate with `NEEDS_DECISION`.

### 2. Select planning depth

Choose `LIGHT`, `STANDARD`, or `DETAILED` using [references/granularity-model.md](references/granularity-model.md). Base the choice on risk, uncertainty, dependency shape, reversibility, and handoff needs—not line count or an arbitrary duration target.

Record the selected mode and one-sentence rationale in the Plan. Increase detail only where risk or ambiguity demands it.

### 3. Write the design contract

Use [references/artifact-templates.md](references/artifact-templates.md) and define:

- scope and mapping to Spec requirements;
- affected system boundaries and responsibilities;
- data, state, interface, and invariants;
- failure, retry, recovery, security, and compatibility behavior;
- migration or rollout strategy where existing data or consumers are affected;
- verification strategy derived from Spec acceptance scenarios;
- material decisions, alternatives, assumptions, and open questions.

Describe interfaces precisely enough to review compatibility. Cover the design as views, not prose alone; express them as Mermaid diagrams inside the Plan unless the repository establishes another durable format. At `STANDARD` depth the design contract includes:

- a system context view: the system boundary, external actors, services, and data stores, and their interactions;
- an end-to-end business flow view: how each primary user journey travels through the system, including the principal failure and retry paths;
- a structure view: modules or components with responsibilities and dependency direction;
- a data/state view: persistent entities, key state machines, and ownership.

At `DETAILED` depth, add for each module whose internal logic is non-trivial an interface-level module design: responsibilities, public interfaces, and key collaborations as class or sequence views. `LIGHT` may collapse views into short prose. A directory-and-file listing is a layout, not a design, at any depth.

For `STANDARD` or `DETAILED`, read [references/design-views.md](references/design-views.md) to select views and check their semantic depth. A diagram's existence does not satisfy a design obligation: critical interactions need call/return and failure semantics; state transitions need triggers and guards; persistent data needs identity and ownership. Add deployment, trust-boundary or other views when the actual risks demand them, rather than treating the four overview views as a ceiling. Record coverage and justified omissions in the Plan; no fixed diagram count is a quality target.

When the project maintains a board (Router `VIEW`), surface each selected view as a cited `design` item carrying this exact Mermaid source, a question it answers, and its approval state. Flowchart, sequence, state, class and ER views render graphically offline; see the router's project-view reference. Improve incomplete design in the Plan before regenerating the board; the board must not invent missing design.

Do not paste full prospective implementations into the Plan.

### 4. Pass the design gate

Present material decisions and unresolved risks for human review before declaring the work executable. A reviewer must be able to answer:

- Does this design implement the Spec without adding hidden product behavior?
- Are ownership, interfaces, state transitions, and failure behavior explicit?
- Are migration, rollback, observability, and test boundaries adequate for the risk?
- Can later implementation choices change without invalidating the contract?
- Can a reviewer trace each consequential design decision through the relevant overview, interaction/interface, data/state and failure details to Spec acceptance? Are diagram names, signatures and state transitions consistent with the prose?

Use `READY_FOR_DESIGN_REVIEW` until the gate is passed by required human approval or a checked `DELEGATED_TECHNICAL` baseline in authorized RUN, covering only explicitly delegated choice classes. Record the authority basis and proceed to slicing. Do not stop solely to reapprove routine choices already delegated. Do not pass a design gate the user explicitly reserved. When the mission did not delegate the design, present the Plan to the user — path, key decisions, the required design views (context, business flow, structure, data/state, and module designs at the chosen depth), and how each core-domain semantic is grounded — and wait for approval before implementation begins.

Make that gate answerable: ask the concrete review question with the exact version,
scope and real choices (accept, request changes, defer where applicable) in the
available question UI or conversation. A status label alone is insufficient.
Consume a clear scoped reply without redundant reapproval, check source freshness,
and record it in the design review record. A requested board uses the same decision
ID and question; see the suite's [human decision interaction](../sdd-workflow-router/references/human-decisions.md)
for draft handoff and version checks. Do not equate approval of diagram styling
with approval of the underlying Plan.

### 5. Slice vertically by behavior

Create slices that each deliver one independently observable or verifiable behavior. A slice should cross the necessary layers instead of completing one technical layer for all features.

For every slice, record:

- slice ID, title, and linked Spec requirements;
- behavior and completion evidence;
- prerequisites and blocking edges;
- inputs, outputs, interface contracts, and invariants touched;
- expected repository areas, using exact paths only when verified;
- the failing test or other RED evidence to establish first;
- the smallest implementation outcome that makes it GREEN;
- refactoring and regression checks;
- risks, rollback notes, and assumptions relevant to this slice.

Keep test work inside its behavior slice. Do not defer all tests to a final testing phase. Permit foundational tasks only when they unblock the first behavior slice and produce a reviewable contract or executable capability.

Order slices as a directed acyclic graph. Prefer an early tracer slice that crosses the real boundaries and exposes integration risk. Do not force every slice into a fixed number of minutes; require instead that it fits one focused execution context, has a clear stopping point, and can be verified without relying on vague future work.

### 6. Prepare the current execution card

Before implementing a slice, expand only that slice into a short-lived execution card. Include verified files and symbols, preconditions, the exact RED command, implementation constraints, focused and regression verification, and the evidence to report.

Executable cards must not contain placeholders such as “handle errors”, “update related code”, or unresolved `TBD`s. Route unresolved product behavior back to the Spec and consequential design choices back to the Plan.

Do not require a commit unless the user or repository workflow authorizes it.

### 7. Run the consistency review

Before returning `READY_FOR_IMPLEMENTATION`, verify:

- every mandatory Spec requirement is covered, explicitly deferred with approval, or marked not applicable with rationale;
- no slice introduces behavior absent from the Spec;
- the Plan and Tasks agree on names, states, interfaces, and failure semantics;
- the dependency graph has no cycles or orphan slices;
- tests and evidence derive from acceptance scenarios;
- high-risk behavior has explicit failure, recovery, and rollback treatment;
- exact paths and commands were verified rather than guessed;
- the first ready slice has a complete execution card with no placeholders.

Report uncovered requirements and contradictions instead of hiding them through optimistic wording.

## Output contract

Return or update:

1. `plan.md`, using the durable design-contract template.
2. `tasks.md`, using the vertical-slice template.
3. One current execution card when implementation is the next authorized action.
4. A concise planning summary containing:
   - status;
   - selected planning mode and rationale;
   - ready and blocked slices;
   - decisions requiring approval;
   - Spec coverage gaps;
   - recommended next action.

Preserve existing approved decisions when revising artifacts. Make changes as explicit deltas and explain why the contract changed.

## References

- Planning depth and slice-quality rules: [references/granularity-model.md](references/granularity-model.md)
- Reusable artifact templates: [references/artifact-templates.md](references/artifact-templates.md)
- Behavioral evaluation cases: [evals/cases.md](evals/cases.md)
