---
name: sdd-workflow-router
description: Route unclear SDD work, run an authorized multi-stage engineering mission, or generate/update a requested project view showing progress, module relationships, next actions and source evidence. Use for complete-and-deliver requests, recovery, unclear next gates, or project visualization. Diagnostics stay read-only; VIEW writes derived snapshots and requested local feedback records; RUN never invents business decisions or external authority.
---

# SDD Workflow Router

Turn an ambiguous repository state into one trustworthy next step. Inspect the goal, authority, contracts, working state, and evidence; identify the earliest unsatisfied gate; then recommend exactly one primary route.

Diagnostic operations recommend one route without executing it. `RUN` coordinates actual stage work under the user’s existing mission authorization. It does not replace stage gates or convert a recommendation into authority.

For a requested project view, use `VIEW` and read only
[references/project-view.md](references/project-view.md) plus the relevant project
sources. It generates or updates a derived offline snapshot with the bundled
renderer; it does not require a new lifecycle, approved Spec or Archify installation.
For an explanation of how the project works, show business flows separately from
code/data structure; the VIEW reference covers source-bound standalone diagrams,
including a user-requested Archify viewer when available.
Ordinary status questions remain diagnostic and do not create a view.

When the user asks to submit feedback inside the board, read the local-service
section in [references/human-decisions.md](references/human-decisions.md). Render
a new immutable view, start the bundled loopback feedback service and give its
working URL. A static HTML preview alone cannot save feedback. Explicit submission
persists scoped feedback and updates its receipt; it does not approve stage gates
or start an agent automatically.

When a real human decision is the next gate, read
[references/human-decisions.md](references/human-decisions.md). Present the concrete
question, scoped options or required input, exact subject/version and a usable
reply route in the conversation or requested board. A pending badge alone does
not fulfill this interaction. Reuse existing authorization and recorded answers.

**For RUN, read [references/closed-loop-model.md](references/closed-loop-model.md) and follow its controller loop.** Load only the currently owning stage Skill. The diagnostic workflow below remains applicable for selecting each route, but its no-invocation/no-mutation restrictions apply only to diagnostic operations.

Read [references/routing-model.md](references/routing-model.md) before assigning a stage, applying precedence, or interpreting another Skill's outcome. Use [references/route-record-template.md](references/route-record-template.md) when a durable route record is useful.

## Boundaries

- Locate and obey applicable `AGENTS.md`, `Agent.md`, and scoped repository instructions. They outrank this workflow.
- Treat approved requirements, Plan, Tasks, code, tests, reports, and repository state as evidence with different authority; do not collapse them into one summary.
- File existence is not readiness. A generated or edited artifact is not approved unless its approval state and exact baseline are established.
- Passing tests are not convergence. Convergence is not Finish readiness. Readiness is not authorization to merge, publish, deploy, or clean up.
- Recommend one primary route. Mention a secondary route only when it is genuinely supporting or follows after an explicit gate.
- In diagnostic operations, do not create or revise Spec, Plan, Tasks, tests, code, reports, releases, branches, commits, or external state while routing. In RUN, perform stage-owned work only within mission authorization.
- Diagnostic routes do not invoke another Skill. RUN may invoke the selected stage when its prerequisites and existing authority hold; the route itself grants no permission.
- Do not force a full SDD lifecycle onto a small, already-bounded request that does not need it.

## Select an operation

Choose one and state it:

- `RUN`: continuously complete an authorized engineering mission using the closed-loop reference. A request to complete and deliver multi-stage work can authorize this mode without requiring the word RUN; Spec derivation and technical delegation, however, must be established explicitly at mission start and are never inferred from delivery phrasing.

- `VIEW`: generate, recheck or update an explicitly requested project visualization. Write new snapshot versions and, when requested, separate local feedback records in the agreed output location; preserve sources, previous versions and unresolved decisions. The detailed VIEW contract replaces the diagnostic routing output below for this operation.

- `ENTRY`: determine how a new or newly presented request enters the SDD flow.
- `STATUS`: reconstruct the current stage and next gate from repository evidence.
- `AFTER_OUTCOME`: consume a named result from another Skill and select the next route.
- `REROUTE`: resolve a blocker, discovery, drift, failed gate, or contradictory route.

For diagnostic operations, if the user explicitly selected an applicable stage Skill and its prerequisites are visibly satisfied, return `NO_ROUTING_NEEDED` rather than interposing this Skill.

## Workflow

### 1. Establish the routing subject

Identify:

- repository and worktree;
- requested outcome and current bounded scope;
- whether this is new work, continued work, a proposed change, a review finding, Finish preparation, a context transfer, or a Skill evaluation;
- actions the user authorized and actions still requiring approval;
- relevant task, change, Spec, Plan, slice, convergence, Finish, or handoff identifiers.

Do not infer a feature identity from a branch name or nearby files alone. Return `INSUFFICIENT_CONTEXT` when the subject cannot be distinguished from other active work.

### 2. Load the minimum authoritative evidence

Inspect only what is necessary to establish the route, normally in this order:

1. applicable Agent instructions and repository workflow rules;
2. user request and explicit decisions;
3. approved requirements contract and acceptance baseline;
4. approved design, Tasks, dependency graph, and current execution card;
5. verification design when applicable;
6. current repository status, relevant diff, task ledger, and slice receipts;
7. convergence decision for the exact baseline;
8. Finish target, artifacts, and readiness evidence;
9. handoff or change-impact records when the request depends on them.

Use `UNKNOWN` for missing facts. Do not search broadly merely to make the route look complete. Do not treat a handoff, chat summary, filename, newest timestamp, or AI assertion as primary authority.

### 3. Build a compact workflow state map

For each applicable gate, record one state:

- `SATISFIED`: authoritative current evidence meets the gate;
- `PENDING_HUMAN`: technically prepared but exact approval or decision is outstanding;
- `GAP`: required content or evidence is absent;
- `STALE`: evidence applies to an older contract, source, slice, or environment;
- `CONFLICT`: authoritative sources disagree;
- `BLOCKED_EXTERNAL`: a required environment, dependency, reviewer, or service is unavailable;
- `NOT_APPLICABLE`: the gate does not apply, with rationale;
- `UNKNOWN`: available evidence cannot establish the state.

Assess at least the gates relevant to the requested outcome: Agent rules, requirements, design, Tasks/current slice, verification design, implementation, convergence, Finish, context freshness, and change propagation.

Do not infer earlier gates from later artifacts. Existing code does not prove an approved Spec; a release package does not prove convergence.

### 4. Apply routing precedence

Apply these rules before walking the linear lifecycle:

1. **Identity or context cannot be trusted**: use `sdd-context-handoff` in `RECEIVE` or `RECOVER` when a real context boundary exists; otherwise request the smallest missing identity evidence.
2. **Approved baselines may be invalidated by a proposed change, discovery, or drift**: use `sdd-change-impact` before revising downstream artifacts when propagation matters.
3. **A human decision or approval is the actual next gate**: route to that human gate; do not send the problem to a downstream Skill to invent the answer.
4. **The request is specifically to evaluate a governance-content Skill**: use `governance-skill-eval` only when it is available and applicable. If absent, recommend one bounded project action to prepare an evaluation protocol from the supplied domain decisions, representative samples, rubric/oracles and execution permissions. Missing business meaning goes to its concrete human-input gate. Do not invent the extension, install it, claim an evaluation ran, or substitute product verification for semantic Skill evaluation.
5. **No exception applies**: select the earliest unsatisfied lifecycle gate using the routing model.

Dirty or untracked files do not automatically change the SDD stage. Make them routing blockers only when ownership, identity, overlap, or evidence validity cannot be established safely.

### 5. Select the earliest owning route

Use these normal routes:

- missing, stale, conflicting, or unapproved repository Agent instructions when a durable project baseline is required -> `sdd-project-bootstrap`;
- unclear, unapproved, changed, or incomplete product intent -> `sdd-requirements-contract`;
- approved Spec with missing, unapproved, or inadequate technical design/slices -> `sdd-plan-slices`;
- approved Spec and sufficient Plan, but a risk-relevant evidence strategy is required and absent -> `sdd-verification-design`;
- one approved and ready execution card with implementation authority -> `sdd-implement-slice`;
- all in-scope slices or the declared review milestone are complete, but current convergence is absent -> `sdd-converge-review`;
- exact source baseline is converged and a Finish target is named -> `sdd-finish-readiness`;
- a concrete diff, commit range, PR, or code area needs engineering review and no approved specification baseline governs it -> `sdd-code-review`;
- active work must cross a session, Agent, tool, repository, or interruption boundary -> `sdd-context-handoff`;
- a change or finding must be classified and propagated across approved artifacts -> `sdd-change-impact`.

`sdd-verification-design` is conditional, not ceremonial. Require it when repository policy, Plan, risk, non-functional behavior, recovery, integration, model variability, or cross-environment evidence demands a designed portfolio beyond an obvious local check.

After one slice completes, route to the next ready slice when the Plan still contains in-scope work. Do not route to convergence merely because one slice passed. Route to Finish only from convergence evidence for the exact current baseline.

### 6. Consume stage outcomes without losing meaning

When operating in `AFTER_OUTCOME`, verify the cited outcome and baseline, then apply its defined meaning rather than translating all positive-sounding statuses into “done”. In particular:

- In diagnostic operations, `READY_FOR_APPROVAL`, `READY_FOR_DESIGN_REVIEW`, and `READY_FOR_HUMAN_ACTION` lead to their gates. In RUN, check whether a gate is already covered by explicit intent, delegated technical decisions or action authorization; otherwise ask. Do not forge exact-version human approval;
- `BASELINE_READY_FOR_APPROVAL` leads to owner review of the exact Agent-rule baseline; `BASELINE_APPROVED` permits entry to requirements work but authorizes no feature changes;
- `APPROVED` requirements may enter Plan, but only for that exact version;
- `READY_FOR_IMPLEMENTATION` may enter verification design or one Slice, depending on applicable evidence gates and authority;
- `SLICE_COMPLETE` closes only that Slice;
- `CONVERGED` permits Finish assessment, not delivery;
- `REVIEW_COMPLETE` delivers review findings only; fixes, merges, and product decisions remain separate authorizations;
- `IMPACT_READY` permits the reported update sequence, not contract mutation;
- `RESUME_READY` restores context, not action authority.

For `NEEDS_SPEC`, `NEEDS_PLAN`, or contract discoveries arising after approved downstream work exists, consider `sdd-change-impact` first so invalidated artifacts and evidence are not skipped. Follow an existing, current impact report instead of creating a second classification.

### 7. Validate the proposed route

Before returning, confirm:

- the route owns the earliest unresolved question;
- all prerequisites claimed as satisfied cite current evidence;
- no later-stage evidence is being used to conceal an earlier contract gap;
- the recommended Skill's trigger condition actually holds;
- human approval and execution authority remain explicit;
- the route has one bounded objective and a clear stop condition;
- alternatives are included only when a missing decision would materially select between them.

If two routes appear equally valid, look for the earliest contract whose answer could change downstream work. If that remains unknowable, return `HUMAN_DECISION_REQUIRED` or `INSUFFICIENT_CONTEXT`; do not list a menu merely to avoid deciding.

## RUN outcomes

- `MISSION_COMPLETE`: current acceptance, convergence, actual verified delivery and authorized method-maintenance obligations are all closed.
- `MISSION_WAITING`: a concrete human decision, authority or ownership conflict requires input; retain the checkpoint.
- `MISSION_BLOCKED`: mandatory external evidence or an exhausted progress/budget boundary prevents completion; provide evidence and a recovery condition.

A stage return never by itself ends a RUN mission. The optional [gate checker](scripts/sdd_loop.py) supports checkpoint consistency, not autonomous model execution or independent semantic judgment.

## Diagnostic outcomes

Return exactly one:

- `NEXT_STEP_READY`: one primary Skill, human gate, or bounded project action is supported by current evidence;
- `HUMAN_DECISION_REQUIRED`: intent, scope, approval, risk, target, or authority must be decided before a truthful route exists;
- `RECONCILIATION_REQUIRED`: conflicting baselines, overlapping work, or material drift must be reconciled before routing;
- `INSUFFICIENT_CONTEXT`: repository, task, contract, evidence, or identity is too incomplete to establish the next step;
- `NO_ROUTING_NEEDED`: the requested workflow is already explicit and applicable, or the work does not need SDD stage routing.

`NEXT_STEP_READY` is a recommendation, not execution approval. It does not mean the overall feature or delivery is ready.

Use `NEXT_STEP_READY` with route type `HUMAN_GATE` when the exact artifact, decision owner, and requested approval are already known. Use `HUMAN_DECISION_REQUIRED` when the unresolved human choice prevents selection of one truthful next route. Use `RECONCILIATION_REQUIRED` for observable conflicting state; use `INSUFFICIENT_CONTEXT` when the needed state cannot be identified at all.

## Output contract

For a normal user-facing status or delivery reply, explain in the user's language:
what behavior is now available or changed; which contract artifacts now exist, with
path and approval status (`APPROVED` / `AUTHORIZED_DERIVATION` / `DELEGATED_TECHNICAL`);
what was actually verified and where;
what remains unfinished; and the next necessary action or decision, if any.
State whole-mission completion separately from a finished stage or installed subset.
Distinguish implemented/delivered work from experiments, prototypes and pending human
validation. Explain internal state names in ordinary language when they matter.
A technical user asking for diagnostic detail may receive the full record below.

Maintain the routing facts below in working context or an existing project record.
The user-facing reply need not reproduce the state map, authorization table or gate
inventory. Link an existing record when useful; this presentation rule creates no
new file requirement and removes no gate, evidence or authorization checks.

The detailed route record contains:

1. outcome, operation, routing subject, and evidence timestamp;
2. authorization boundary and applicable Agent instructions;
3. authoritative baseline and compact workflow state map;
4. trigger classification and precedence rule used;
5. one primary next route with reason, required inputs, objective, and stop condition;
6. blockers, human gates, stale evidence, and contradictions;
7. one later route only when it follows deterministically from the primary gate.

When the user requests the detailed record, return it in the response. Use an established repository location or a user-specified path when persistence is requested; do not invent a permanent workflow-state directory.

## References

- Optional project-view generation, updates and provenance: [references/project-view.md](references/project-view.md)
- Authorized continuous execution and checkpoint rules: [references/closed-loop-model.md](references/closed-loop-model.md)
- Stage gates, precedence, outcome translation, and route selection: [references/routing-model.md](references/routing-model.md)
- Durable workflow route record: [references/route-record-template.md](references/route-record-template.md)
- Behavioral evaluation cases: [evals/cases.md](evals/cases.md)
