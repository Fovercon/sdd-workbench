# SDD Workflow Routing Model


## Contents

- [1. The router's position](#1-the-routers-position)
- [2. Evidence and authority order](#2-evidence-and-authority-order)
- [3. Trigger classification](#3-trigger-classification)
- [4. Gate states](#4-gate-states)
- [5. Lifecycle gate matrix](#5-lifecycle-gate-matrix)
- [6. Normal route selection](#6-normal-route-selection)
- [7. Exception precedence](#7-exception-precedence)
- [8. Stage-outcome translation](#8-stage-outcome-translation)
- [9. Route quality checks](#9-route-quality-checks)
- [10. Diagnostic procedure and result meanings](#10-diagnostic-procedure-and-result-meanings)
- [11. Detailed diagnostic record](#11-detailed-diagnostic-record)


Use this model to select a next workflow from evidence rather than from filenames, optimism, or the apparent age of a project.

For `RUN`, apply [closed-loop-model.md](closed-loop-model.md) to authority, continuous invocation and completion. The diagnostic model below selects one route; its no-execution restrictions do not terminate an authorized RUN mission.

## 1. The router's position

```text
                         context boundary
                                |
                         context-handoff
                                |
project bootstrap -> requirements -> plan -> implement -> converge -> finish
                         ^           |          ^          |
new/changed intent ------+           +-> verification -----+
                                                ^
change/discovery/drift -> change-impact

governance Skill quality -> available governance-skill-eval, else bounded evaluation preparation
                            (separate evaluation line)
```

The router observes and recommends. Each routed workflow retains its own gates, outcomes, mutation boundaries, and authorization requirements.

## 2. Evidence and authority order

Use the narrowest applicable sources. When sources disagree, do not resolve authority by modification time alone.

1. system, user, and applicable repository Agent instructions;
2. explicit human approvals and decisions for an identifiable artifact version;
3. approved Spec, Plan, ADRs, Tasks, and verification contracts;
4. current source, tests, configuration, generated artifacts, and repository state;
5. reproducible command or runtime evidence tied to a baseline;
6. convergence, Finish, impact, and handoff records tied to their cited sources;
7. unverified summaries, conversation memory, filenames, and inferred intent.

Lower-ranked sources can reveal drift or defects but cannot silently redefine a higher-ranked contract. Repository instructions determine the actual authority order when they specify one.

## 3. Trigger classification

Classify the routing subject before selecting a stage.

| Trigger | Meaning | Typical first consideration |
|---|---|---|
| `PROJECT_BASELINE` | Repository onboarding or durable Agent rules are missing, stale, or conflicted | project Bootstrap |
| `NEW_INTENT` | New behavior or outcome without an approved contract | requirements contract |
| `CONTINUE` | Existing approved work should advance | earliest unsatisfied lifecycle gate |
| `CHANGE` | Someone proposes changing approved behavior, design, or delivery scope | change impact |
| `DISCOVERY` | Implementation/review reveals a missing or false assumption | change impact or earliest owner |
| `REVIEW` | User asks whether implementation matches contracts | convergence review |
| `FINISH_TARGET` | User names PR, merge, release, deploy, handoff, archive, or cleanup | convergence identity, then Finish readiness |
| `CONTEXT_BOUNDARY` | Work must resume or move across a context boundary | context handoff |
| `SKILL_EVALUATION` | A governance Skill's output quality is being measured | available domain eval Skill, otherwise bounded project action |
| `DIRECT_TASK` | Requested action is already bounded and prerequisites are clear | no routing needed |

Feature size is not a trigger. A one-line request may need Spec work; a large mechanical update may not.

## 4. Gate states

| State | Meaning | Routing consequence |
|---|---|---|
| `SATISFIED` | Current authoritative evidence meets the gate | continue forward |
| `PENDING_HUMAN` | Artifact is ready, but approval/decision/action is outstanding | stop at human gate |
| `GAP` | Required artifact, content, or evidence is absent | route to owning workflow |
| `STALE` | Evidence refers to an older baseline | refresh from earliest invalidated owner |
| `CONFLICT` | Authorities disagree | reconcile; do not guess |
| `BLOCKED_EXTERNAL` | Required external capability is unavailable | expose blocker and owner |
| `NOT_APPLICABLE` | Gate is irrelevant for this scope, with evidence | skip it |
| `UNKNOWN` | State cannot be established | obtain evidence or return insufficient context |

Never use a downstream `SATISFIED` state to infer an upstream one.

## 5. Lifecycle gate matrix

| Gate | Satisfied when | Owner when unsatisfied | Important non-equivalence |
|---|---|---|---|
| Agent rules | Applicable rules are located, current, approved where required, and conflicts are understood | `sdd-project-bootstrap` | no `AGENTS.md` does not grant unrestricted behavior |
| Requirements | Exact Spec is testable and human-approved, or AUTHORIZED_DERIVATION under RUN conditions | `sdd-requirements-contract` | document exists != approved |
| Design | Technical contract is reviewed/approved as required and matches Spec | `sdd-plan-slices` | architecture diagram != design contract |
| Tasks | Dependency-aware slices exist; current ready Slice has a complete card | `sdd-plan-slices` | checklist != executable Slice plan |
| Verification design | Applicable proof obligations, layers, oracles, data, environments, and gates are defined | `sdd-verification-design` | test count/coverage != evidence strategy |
| Slice implementation | One Slice meets its stop condition and current evidence gates | `sdd-implement-slice` | code/commit/one pass != Slice complete |
| Scope implementation | All in-scope Slices or declared review milestone are closed | next Slice or Plan reconciliation | one Slice complete != feature complete |
| Convergence | Current exact baseline has a `CONVERGED` decision under applicable gates | `sdd-converge-review` | all tests pass != converged |
| Finish readiness | Named target is assessed against exact converged source/artifact identity | `sdd-finish-readiness` | converged != ready for target |
| External action | Required authorization exists for exact action, target, destination, and baseline | human/project delivery workflow | ready != executed or authorized |

Agent-rule absence is not automatically a hard stop when higher-level instructions and repository conventions are sufficient for a small task. Route to `sdd-project-bootstrap` when onboarding a repository, establishing a reusable SDD baseline, or repairing stale/conflicting project rules. Do not impose Bootstrap on an ordinary bounded task that can safely follow current higher-level instructions.

## 6. Normal route selection

For a concrete diff, commit range, PR or code-area engineering review, use
`sdd-code-review` when no approved specification governs that subject. When a
Spec/convergence baseline does govern it, use `sdd-converge-review`. Choosing the
route is diagnostic, not execution of either review. A directly selected applicable
stage needs no routing interposition.

Walk from the earliest relevant gate:

1. A durable project baseline is required and Agent rules are missing/stale/conflicted -> `sdd-project-bootstrap`.
2. Product behavior or acceptance is unknown/unapproved -> `sdd-requirements-contract`.
3. Spec is approved; design or Slices are missing/unapproved -> `sdd-plan-slices`.
4. Spec and design are sufficient; a material verification portfolio is required but absent -> `sdd-verification-design`.
5. A current Slice card is ready and implementation is authorized -> `sdd-implement-slice`.
6. A Slice closed but more in-scope Slices remain -> the next ready Slice, normally through `sdd-implement-slice`; if none is ready, return to Plan or the named blocker.
7. Scope or review milestone is implemented -> `sdd-converge-review`.
8. Exact baseline converged and a target is named -> `sdd-finish-readiness`.
9. Finish is ready -> explicit human/project action under its own authorization, followed by target-specific verification.

Do not require verification-design as a document ceremony for every edit. Apply it when any of these are material:

- multiple test layers or system boundaries;
- persistence, concurrency, recovery, migration, security, or compatibility;
- performance, reliability, or another quality attribute;
- model or heuristic output requiring semantic evaluation;
- real versus simulated dependencies or multiple environments;
- refactoring whose behavior must be characterized;
- repository policy or the Plan explicitly requires it.

## 7. Exception precedence

### 7.1 Context and identity

Use `sdd-context-handoff` when continuation depends on transported or reconstructed transient state. A normal new request with self-contained primary artifacts does not need a handoff.

If a supplied handoff conflicts with the repository, reconcile the mismatch before choosing a development stage. A valid `RESUME_READY` outcome restores the point of continuation but not implementation authority.

### 7.2 Change and contract drift

Use `sdd-change-impact` before edits when a proposed change, discovery, or review finding may invalidate approved contracts, downstream slices, tests, convergence, or Finish evidence.

Skip a separate impact analysis only when the existing owning workflow has already bounded the impact adequately or the change is demonstrably local and non-semantic. A current impact report should be consumed, not duplicated.

### 7.3 Human gates

Stop at a human gate when the next fact depends on product intent, design approval, risk acceptance, target choice, external action, or explicit authority. Do not route to a Skill merely to produce more prose around an undecided question.

When the exact artifact, owner, and approval action are known, the router can return `NEXT_STEP_READY` with a `HUMAN_GATE` route. Return `HUMAN_DECISION_REQUIRED` when the choice itself is still too undefined to select one downstream route.

### 7.4 Unavailable domain evaluation extension

Check the available Skill inventory before routing a `SKILL_EVALUATION` request
to a domain extension. If `governance-skill-eval` is absent, use `PROJECT_ACTION`
for a bounded evaluation-preparation step: identify the supplied domain sources,
case set, rubric/oracles, comparison baseline, execution permissions and missing
evidence. Give one concrete objective and stop condition; do not fabricate a
Skill invocation, install an extension or claim quality results. A missing
business decision takes the earlier human-input route. This fallback does not
turn semantic Skill evaluation into product verification or authorize model calls.

### 7.5 Workspace state

Dirty state becomes `RECONCILIATION_REQUIRED` when it:

- overlaps the routed scope with unknown ownership;
- makes source identity or cited evidence ambiguous;
- conflicts with an execution card, handoff, or convergence baseline;
- risks overwriting, discarding, or falsely attributing user work.

Unrelated, attributable changes should be preserved and noted without blocking an otherwise sound route.

## 8. Stage-outcome translation

### Project Bootstrap

| Outcome | Next route |
|---|---|
| `DISCOVERY_COMPLETE` | review unknowns and authorize `CREATE`, `AUDIT`, or `REFRESH` as needed |
| `BASELINE_READY_FOR_APPROVAL` | owner approval of the exact Agent-rule baseline |
| `BASELINE_APPROVED` / `BASELINE_CURRENT` | requirements or the already identified bounded task |
| `HUMAN_DECISION_REQUIRED` | named project-rule, source-of-truth, safety, or convention decision |
| `RECONCILIATION_REQUIRED` | reconcile instruction/repository/workspace conflict |
| `INSUFFICIENT_EVIDENCE` | obtain the smallest missing repository evidence |

### Requirements contract

| Outcome | Next route |
|---|---|
| `NEEDS_INPUT` | human input/decision, then requirements contract |
| `READY_FOR_APPROVAL` | human approval of exact version |
| `APPROVED` | Plan, unless a current approved Plan already covers it |
| `AUTHORIZED_DERIVATION` | In authorized RUN only, Plan using the recorded intent mapping and exact baseline |
| `SUPERSEDED` | locate the current approved version before routing |

### Plan and Slices

| Outcome | Next route |
|---|---|
| `NEEDS_SPEC` | requirements contract; use impact first if approved downstream baselines exist |
| `NEEDS_DECISION` | human design decision |
| `READY_FOR_DESIGN_REVIEW` | human design review |
| `READY_FOR_IMPLEMENTATION` | verification design if applicable and missing; otherwise one ready Slice |

### Verification design

| Outcome | Next route |
|---|---|
| `VERIFICATION_DESIGN_READY` | integrate into current Plan/card, then implement one Slice |
| `NEEDS_SPEC` | requirements contract, with impact handling when needed |
| `NEEDS_PLAN` | Plan revision, with impact handling when needed |
| `HUMAN_DECISION_REQUIRED` | named owner decision |
| `INSUFFICIENT_BASELINE` | restore contract identity before continuing |

### Slice implementation

| Outcome | Next route |
|---|---|
| `SLICE_COMPLETE` | next ready Slice, or convergence when declared scope is complete |
| `NEEDS_SPEC` / `NEEDS_PLAN` | impact analysis when approved downstream work is affected, then owning stage |
| `HUMAN_DECISION_REQUIRED` | named human gate |
| `WORKSPACE_RECONCILIATION_REQUIRED` | reconcile workspace ownership/state |
| `ENVIRONMENT_BLOCKED` | restore or obtain required environment/evidence |
| `SLICE_INCOMPLETE` | continue the same Slice if contract and authority remain valid; otherwise reroute by finding |

### Convergence review

| Outcome | Next route |
|---|---|
| `CONVERGED` | Finish readiness for a named target, or stop if no Finish target exists |
| `NOT_CONVERGED` | follow each finding's earliest return stage; impact analysis before contract propagation when needed |
| `INSUFFICIENT_EVIDENCE` | obtain or design the missing evidence; do not route to Finish |
| `HUMAN_DECISION_REQUIRED` | named risk/product decision |

### Finish readiness

| Outcome | Next route |
|---|---|
| `READY_FOR_HUMAN_ACTION` | explicitly authorized target action; do not auto-execute |
| `NOT_READY` | bounded preparation of Finish-owned gaps, then reassess |
| `NEEDS_CONVERGENCE` | convergence review or its reported earlier owner |
| `HUMAN_DECISION_REQUIRED` | target/version/risk/rollback decision |
| `INSUFFICIENT_EVIDENCE` | restore source, artifact, environment, or policy evidence |

### Change impact and context handoff

| Outcome | Next route |
|---|---|
| `IMPACT_READY` | follow the reported earliest update step after required approval |
| `NO_MATERIAL_IMPACT` | refresh only named evidence or continue prior stage |
| `REJECTED_OR_SUPERSEDED` | stop this change path |
| `HANDOFF_READY` | transfer package; underlying work state is unchanged |
| `RESUME_READY` | resume at verified continuation action within existing authority |
| `RECONCILIATION_REQUIRED` | reconcile identity/state before stage routing |
| `NO_HANDOFF_NEEDED` | continue the already identified workflow |

## 9. Route quality checks

A good route record can answer:

- What exact work is being routed?
- Which current evidence establishes each satisfied prerequisite?
- What is the earliest unresolved gate?
- Why does the selected workflow own that gate?
- What may the next workflow do, and what remains unauthorized?
- What observable result ends the next step?
- What single later route follows if that result succeeds?

The route is weak if it recommends several Skills in parallel without dependency reasoning, reports the whole project as a single stage despite mixed scopes, or uses an artifact inventory as proof of readiness.

## 10. Diagnostic procedure and result meanings

This procedure applies to ENTRY, STATUS, AFTER_OUTCOME and REROUTE, not a visibly
applicable direct task or an explicitly requested VIEW. Inspect relevant instructions,
user decisions, contracts, workspace and evidence. Identify a bounded subject; if
multiple efforts cannot be distinguished, request the smallest identifying fact.

Build only the applicable state map: Agent rules, requirements, design, current
slice/tasks, verification, implementation, convergence, Finish, context freshness
and change propagation. Use §4 states; missing facts stay UNKNOWN. Do not search
for every possible artifact or infer earlier approval from later files.

Apply §7 exception precedence before §6's earliest unsatisfied relevant gate:
identity/context; affected approved baselines; a real human gate; unavailable domain
evaluation; then lifecycle selection. Diagnose one owner/objective/stop condition,
with at most one later route when it follows deterministically. When two routes
remain plausible, identify which missing contract fact would decide between them.
Do not provide a menu just to avoid a decision.

In AFTER_OUTCOME, verify the named result and cited baseline before using §8.
Spec AUTHORIZED_DERIVATION and delegated Plan bases retain their exact meanings
and are valid only under RUN's authority conditions. A finished slice closes only
that slice. CONVERGED permits Finish assessment, not delivery. REVIEW_COMPLETE
provides findings, not repair authority: a separate explicit repair request may
already supply that authority and should be consumed after leaving read-only review,
without asking for it again. IMPACT_READY does not authorize contract mutation;
RESUME_READY restores context, not action permission.

| Diagnostic outcome | Meaning |
|---|---|
| `NEXT_STEP_READY` | One primary skill, HUMAN_GATE or bounded PROJECT_ACTION is supported; a recommendation, not execution approval. Use HUMAN_GATE when exact subject/version, owner and requested approval are known. |
| `HUMAN_DECISION_REQUIRED` | An unresolved intent, authority, risk or target choice prevents selecting one truthful next route. |
| `RECONCILIATION_REQUIRED` | Observable baseline, ownership or source conflict must be reconciled first. |
| `INSUFFICIENT_CONTEXT` | Work identity or material evidence cannot be established. |
| `NO_ROUTING_NEEDED` | A clear applicable workflow/direct task already owns the request, or SDD routing is unnecessary. This creates no new authority. |

Validate the route against current primary evidence, the owner's trigger and
prerequisites, existing authority, the exact unresolved question and an observable
end to the next step. In RUN the controller uses the same evidence selection, then
continues authorized work under closed-loop-model; diagnostic stopping restrictions
do not terminate the mission.

## 11. Detailed diagnostic record

Keep these facts in context or an existing project record, using the template only
when useful. A normal reply explains user-visible results, actual verification,
artifact paths/approval bases, unfinished work and next action; it need not dump
this inventory. An explicitly requested audit receives the full record.

1. outcome, operation, bounded subject and evidence timestamp;
2. existing authorization and applicable instructions;
3. authoritative baseline and relevant gate states;
4. trigger classification and precedence reason;
5. one primary route, owner, required inputs, objective and stop condition;
6. blockers, real human questions, stale evidence or conflicts;
7. one later route only if it follows deterministically.

Use established record locations; do not invent a permanent workflow-state directory.
No presentation shortcut removes a gate, actual question, evidence or authority check.
