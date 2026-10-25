# Authorized closed-loop execution

Read this reference only for `RUN`. The diagnostic operations remain read-only. RUN is an Agent execution protocol, not a separate model service: the current Agent acts as controller and loads one stage Skill at a time. The optional Python helper checks checkpoint gates; it does not perform the engineering work.

## 1. Establish a mission

Recover the user's current and prior authorization, applicable repository rules, required acceptance IDs, excluded work, technical delegation, delivery target/destination, and any method-maintenance authorization. Do not ask for permission again when the task already covers an action. Do not infer deployment or method maintenance from authorization to implement a product.

Establish derivation and delegation explicitly. When the mission does not state whether Spec derivation (`AUTHORIZED_DERIVATION`) or technical delegation (`DELEGATED_TECHNICAL`) is granted, ask once at mission start rather than inferring either from delivery phrasing; record the answer and do not ask again for the same classes of choice. Approval gates the user explicitly reserved anywhere in the mission are recorded as pending decisions and are never satisfied by either derived status.

Accept explicit user intent as product authority. When all material semantics are already decided, synthesize a Spec with status `AUTHORIZED_DERIVATION`, exact hash, quality-gate result, and a source mapping for each obligation. This status means faithful derivation under the user's task authorization; it does not mean the human reviewed the generated file. A new business choice, hidden assumption, changed scope, a repository requirement for exact-version approval, a user-reserved approval gate, or any core-domain semantic grounded only in an assumption prevents this route. Prompt completeness is not decision completeness. Use `APPROVED` only for actual human approval.

Use `DELEGATED_TECHNICAL` for Plan choices within explicit delegation — delegation the user stated for a named class of choices, not a stack constraint — after the design consistency review. Otherwise obtain the required design decision. Whether the product's core output is semantically correct is consequential by default and never delegated implicitly. Neither status authorizes unrelated work, residual-risk acceptance, external actions, or destructive changes.

## 2. Controller loop

```text
while mission has unfinished obligations:
    inspect current authorization, contracts, workspace, evidence and budget
    if real context boundary: reconcile checkpoint with actual files first
    select earliest owning gate (apply impact analysis when meaning changed)
    if missing human decision / permission / ownership: checkpoint and ask
    else execute one bounded stage or authorized project action
    save actual result, commands, identity, findings and next gate
    invalidate affected downstream evidence after every material change
    if failed: classify and repair/reroute; never relabel failure as success
    if step finished: continue, including the next dependency-ready slice
    check delivery result and learning obligations before claiming completion
```

A stage worker's `stop` or report means return to the controller. Direct invocation still performs only that stage/slice. Stage boundaries prevent scope mixing; they do not require a new human prompt during an authorized multi-stage mission.

Surface every contract artifact when it is produced: tell the user the artifact path, its approval status (`APPROVED`, `AUTHORIZED_DERIVATION`, `DELEGATED_TECHNICAL`), which core-domain semantics remain assumption-grounded, and — for a Plan — its design views (system context, business flow, structure, data/state, and module designs at the chosen depth). A mission reply that leaves the user unaware a Spec or Plan exists, or unable to find it, is incomplete even when the work itself is correct.

When maintaining a project view is part of the user's mission, use the router's
`VIEW` reference after a meaningful source, decision or module change, or at the
requested handoff/delivery point. Recheck first; publish a new version with its
parent receipt and updated observations when warranted. A view links the actual
contracts and evidence; it is neither a new progress ledger nor a gate. Without
that requested deliverable, continue normally without generating view files.

| Gate/result | Controller action |
|---|---|
| No project rules | Inspect existing workflow; Bootstrap only if a durable baseline is part of the task. |
| Requirements/Plan gap | Use its owning Skill; preserve prior contracts and decisions. |
| Domain-defining input absent | Stop synthesis and request the artifact or decision from the user (`NEEDS_INPUT`); never substitute an invented, generic, or "reference" semantic for the missing input. |
| Ready card | Invoke implement-slice once; then reobserve and select the next card. |
| SLICE_INCOMPLETE / regression | Repair within the same authorized slice, then rerun evidence. |
| NEEDS_PLAN | Impact analysis if downstream contracts exist; repair delegated design, otherwise ask for the consequential decision. |
| NEEDS_SPEC | Investigate a discoverable fact; ask only for unresolved business meaning, never invent it. |
| All slices closed | Run required whole-scope verification, then converge-review from the contract outward. |
| Review findings | Report first, then invoke the appropriate repair stage under existing fix authorization; reverify and re-review the changed baseline. |
| CONVERGED | Finish-readiness for the actual target. |
| READY_FOR_HUMAN_ACTION | Check existing action authorization. If covered, execute guarded action and verify its result; otherwise ask after preparation. |
| Delivery complete | Register retrospective; apply and regress method changes only when authorized. |

Tests passing do not substitute for requirement coverage, semantic judgment, independent review where required, or actual delivery. An implementer's review must not be described as independent. Stage Skills remain responsible for their full gates; the helper checks only the summarized checkpoint.

## 3. Failure, progress, and recovery

Keep a bounded retry policy in the mission. Count no progress when repeating an action without new evidence, a changed hypothesis, or closing an obligation; command count alone is not progress. Three consecutive no-progress rounds is a reasonable initial local default, not a universal threshold. Keep the user informed during long runs. Budget exhaustion means `STOP_BUDGET`, not success.

Environment failures: attempt reasonable authorized repairs or alternate faithful evidence; do not replace required evidence with a weaker mock. Record the missing prerequisite if it remains unavailable. Workspace conflicts: preserve files and resolve attribution, never reset or stash merely to proceed.

At a real interruption, set `observed=false`. Recheck repository identity, relevant dirty files, authority, contracts, receipts and actual results. Then set `observed=true` with a recovery entry. A summary alone is not enough. Reconcile drift before reusing evidence.

## 4. Completion and method maintenance

Classify proof timing in Plan: engineering acceptance is verified before convergence; an acceptance item that depends on actual integration/deployment/handoff must be checked in the target’s post-action evidence. Never mark a delivery-dependent item passed before that action.

Completion requires every mandatory acceptance item, all declared slices, current verification, current converged review with every finding disposed, target readiness, verified delivery receipt, and a short learning record. A learning record may say no change is warranted.

When method maintenance is authorized: select one bounded candidate; freeze old/new Skill snapshots and scenarios; run structural validation, relevant deterministic checks and realistic forward behavior tests; adjudicate failures and regressions; retain, revise or revert the candidate. Record observations separately from hypotheses about benefit. Do not promote a universal rule from one successful fixture. Without maintenance authority, save the proposal and finish the product mission.

## 5. Optional checkpoint helper

Start from [loop-state.example.json](../evals/loop-state.example.json). Save a copy in the repository's established task/evidence location. All paths below are relative to `--root`. Use Python 3 standard library only.

```bash
python3 /path/to/sdd-workflow-router/scripts/sdd_loop.py identity loop.json --root /path/to/project
python3 /path/to/sdd-workflow-router/scripts/sdd_loop.py status loop.json --root /path/to/project
```

`identity` computes hashes from actual files. After executing and assessing work, the Agent records these identities in receipts. Never update a receipt's baseline without rerunning the relevant work. `status` returns exactly one route or stop; the Agent executes, updates the checkpoint with truthful evidence, then calls it again. `COMPLETE` is a checkpoint consistency result, not independent verification that the descriptions, authorization or semantic claims are true.

Required checkpoint fields:

| Field | Content |
|---|---|
| `schema` | `1` |
| `mission` | Intent; authorization source; `continuous`; `technical_delegation`; `delivery` target/destination/authorized; `maintain_method`. |
| `mandatory` | Nonempty unique engineering acceptance IDs required for convergence. Keep delivery-dependent acceptance in the named Finish target and verify it in the actual delivery receipt; never drop an obligation to pass a gate. The Spec retains the complete chain. |
| `observed`, `conflicts`, `pending_decisions`, `change_pending` | Actual recovery/ownership/decision/impact state. |
| `budget` | `steps`, `max_steps`, `no_progress`, `max_no_progress`; integers, positive limits. |
| `contracts` | `spec` and `plan`, null until created. Each has `path`, `sha256`, `basis`, `sources`, `quality_passed`. Spec basis is `USER_APPROVED` or `AUTHORIZED_DERIVATION`; Plan basis is `USER_APPROVED` or `DELEGATED_TECHNICAL`. |
| `slices` | ID, dependency IDs, linked `acceptance`, `done`, and receipt after closure. Receipt has contract identity and hashed report. |
| `source_files` | Nonempty exact relevant source/configuration/test/dependency/asset manifest before verification. Include generated deliverables when their content matters. Review the manifest against actual diff and project policy. |
| `verification` | Null or baseline, command(s), integer `exit_code`, covered acceptance IDs and hashed report. This aggregates all required checks, not merely a selected passing subset. |
| `review` | Null or baseline, `outcome`, covered IDs, findings and hashed report. Findings have `id`, `severity`, `status`, `route`; unresolved ones route to `IMPLEMENT`, `PLAN` or `REQUIREMENTS`. Use `CLOSED`, or `ACCEPTED`/`DEFERRED` with a current decision receipt: baseline, hashed report, actual `authority_source`, and `policy_allows=true`. Without that evidence the helper stops for a decision. The controller must verify the source and policy, not invent risk acceptance. |
| `finish` | Null or delivery identity, `ready`, hashed report and optional receipt. Receipt has delivery identity, `verified` and hashed result report. LOCAL still needs an actual deliverable receipt. |
| `learning` | Hashed short `record`, `changed_assets` list and regression if assets changed. Regression has method identity, `passed` and hashed report; include old/new results and behavior evaluation limits. |

An artifact reference is `{"path":"evidence/report.md","sha256":"actual sha256"}`. Source identity includes current Spec/Plan hashes and every source-file path/hash. Delivery identity additionally includes the target and destination. Method identity includes all changed method assets. Missing/changed report files invalidate that gate. Historical slice reports remain valid process records as source evolves, but their contract identity must still match; final whole-scope checks are current.

The helper deliberately fails closed on malformed checkpoints, cycles, unknown dependencies and unsafe paths. It cannot discover an omitted file, omitted requirement, fabricated report, secretly weakened test or false authorization. The controller and reviewer must audit those claims. Do not add a mandatory JSON ledger to a trivial task when an existing task record suffices; apply the same invariants directly.
