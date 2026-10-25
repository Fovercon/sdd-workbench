---
name: sdd-workflow-router
description: Route unclear SDD work, run an authorized multi-stage engineering mission, or generate/update a requested project view showing progress, module relationships, next actions and source evidence. Use for complete-and-deliver requests, recovery, unclear next gates, or project visualization. Diagnostics stay read-only; VIEW writes derived snapshots and requested local feedback records; RUN never invents business decisions or external authority.
---

# SDD Workflow Router

Choose the smallest applicable way to handle the user's actual goal. Route uncertain
SDD work from evidence, coordinate an authorized multi-stage mission, or create a
requested project view. Do not make users learn stage names before they can work.
Load one owning stage at a time; routing grants no authority of its own.

## First choose the kind of work

Read applicable repository rules and the request. Establish the bounded subject,
current workspace and existing authorization before selecting a path. Inspect only
the relevant files; a branch name, chat summary or latest timestamp is not authority.

| Observed request and evidence | Handling |
|---|---|
| A clear stage-specific request whose prerequisites are already satisfied | `NO_ROUTING_NEEDED`; let that stage own the work without an extra routing ceremony. |
| A known local correction with clear intended behavior, limited/reversible scope and a faithful focused check; no affected approved contract, required project gate, consequential uncertainty or ownership conflict | `NO_ROUTING_NEEDED`; use the ordinary authorized project workflow. Do not manufacture Spec/Plan/cards, a RUN checkpoint, handoff, view or Finish review. |
| A status, next-step or routing question | Diagnose read-only using the routing model below. Do not treat the question as implementation or view authorization. |
| An explicitly requested project visualization | `VIEW`; use its reference, not the full diagnostic/mission procedure. |
| An authorized multi-stage complete-and-deliver mission | `RUN`; use the closed-loop controller and current stage gates below. |
| Missing business meaning, consequential design/risk, contract drift, reserved approval or uncertain workspace identity | Resolve the earliest real gate using the routing model; a small diff is not permission to bypass it. |

A direct task is a scope/authority decision, not a shortcut into `sdd-implement-slice`
without that skill's contracts/card. Do not classify payments, migrations, security,
persistence or other consequential changes as local merely because they are short.
Preserve explicit requests for planning/review and all user-reserved approval gates.

For an already-authorized direct repair, conclude routing and return control to the
ordinary implementation workflow so the repair actually proceeds. Do not stop with
only an offer or ask for the same permission again. If only diagnosis was requested,
report the route and stop without edits. Missing material meaning still needs a
concrete input question; do not invent it to make the direct path available.

## Load only the selected operation's detail

Reuse instructions and contract clauses already visible in the current context
while their identity and applicability remain current; do not reread them merely
because another slice starts. Retrieve the current card's obligations and relevant
cross-cutting constraints, expanding scope when dependencies or uncertainty require
it. Keep large results in files and retrieve bounded fields. After compaction or a
real handoff, re-establish authority and meaning from primary sources: hashes alone
cannot restore forgotten content. Changing the active Skill does not unload prior
messages, reset a host context window or establish lower total token use.

- **Diagnostics — `ENTRY`, `STATUS`, `AFTER_OUTCOME`, `REROUTE`:** read
  [references/routing-model.md](references/routing-model.md) before assigning stages,
  applying exception precedence, interpreting outcomes or creating a state map.
  It owns the gate vocabulary, route/outcome tables and diagnostic procedure.
  A visibly applicable direct task above needs no lifecycle inventory.
- **`RUN`:** read [references/closed-loop-model.md](references/closed-loop-model.md)
  for mission authority, continuous stage invocation, evidence, recovery and actual
  completion, and the routing model when choosing stages. Never infer Spec derivation
  or technical delegation from delivery phrasing. Establish them explicitly as that
  reference requires; preserve already-recorded authority and reserved human gates.
  A stage return hands control back to the controller, not automatically to the user.
- **`VIEW`:** read [references/project-view.md](references/project-view.md) and the
  relevant project sources. Use the public `describe` and `check --summary` commands before diagnosing internals.
  Produce a source-bound derived snapshot; a new lifecycle,
  approved Spec or Archify install is not a prerequisite. Keep business flows distinct
  from code/data structure. Explain a requested Archify option only when available.
- **A real human gate or explicitly requested in-board feedback:** read
  [references/human-decisions.md](references/human-decisions.md). Ask the concrete
  scoped question with exact subject/version and a usable reply path. For direct board
  submission, create an immutable view and start the bundled loopback service; static
  HTML alone cannot save feedback. Feedback receipts do not approve engineering gates
  or start an agent. Reuse existing decisions and authorization.
- Use [references/route-record-template.md](references/route-record-template.md)
  only when a durable detailed record is useful or requested. Reuse the project's
  established location. Do not create a new state directory for every request.

Do not preload all stage skills, references, templates or evals. Load an owning
stage only when it genuinely applies and the task authorizes execution.

## Hard boundaries

- Follow system/user authority and applicable repository instructions; this skill
  does not replace them. Preserve unrelated edits and reconcile overlapping unowned
  work before mutation. Dirty files alone are not a blocker.
- Keep user decisions, approved contracts, actual source/tests and observed evidence
  distinct. File existence is not approval; passing tests are not convergence;
  convergence is not readiness, authorization or verified delivery.
- Diagnose one primary next route. Diagnostics do not invoke downstream skills or
  change contracts, code, tests, reports, views, branches or external systems.
  `RUN` may execute stage-owned work only within the mission's existing authority.
- Do not invent domain semantics, source identities, artifact paths, outcomes, Skill
  availability, approvals, risk acceptance or command results. Missing required facts
  remain unknown; missing business decisions go to their real owner.
- Handle changed approved baselines through the earliest owning contract and impact
  rules. Recheck context/source drift before reusing a handoff, review or receipt.
- A missing domain evaluation extension becomes one bounded preparation action under
  routing-model §7.4, not an imagined invocation/install/model run or product test
  substituted for semantic evaluation.
- External actions, destructive cleanup and publication require their own covered
  authorization. A recommendation, `READY` or completed stage does not provide it.

## Results and user-facing replies

For diagnostics return one of `NEXT_STEP_READY`, `HUMAN_DECISION_REQUIRED`,
`RECONCILIATION_REQUIRED`, `INSUFFICIENT_CONTEXT`, `NO_ROUTING_NEEDED`; use their
meanings and record fields in routing-model §§10–11. Do not present a recommendation
as permission. `RUN` returns `MISSION_COMPLETE`, `MISSION_WAITING` or `MISSION_BLOCKED`
under the closed-loop contract. `VIEW` uses its own referenced output contract.

Explain the actual result in the user's language: behavior now available, contract
paths and approval bases when artifacts were produced, what was actually verified
and where, unfinished work, and the next necessary action/decision. Distinguish stage
completion, experiments and installed subsets from whole-mission verified delivery.
Explain internal state names only when they help the user decide. Keep the detailed
state map in context or an existing record; expose it when requested. A short reply
must not conceal an unmet obligation, invented approval or missing evidence.

## Maintenance references

- Diagnostic contracts and procedure: [references/routing-model.md](references/routing-model.md)
- RUN controller and optional checkpoint helper: [references/closed-loop-model.md](references/closed-loop-model.md)
- Behavior evaluation: [evals/cases.md](evals/cases.md); evals are maintainer-only.
