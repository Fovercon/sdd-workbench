---
name: sdd-context-handoff
description: Prepare or receive a verifiable context package for continuing SDD work across sessions, agents, tools, repositories, or interrupted runs. Use when active work and its reasoning must travel without treating a lossy summary as authority. Do not use as a substitute for Spec, Plan, progress tracking, or final review.
---

# SDD Context Handoff

Transfer the minimum context needed to continue correctly. Preserve contract identity, verified state, decisions, unfinished work, and the next safe action without copying the whole conversation.

A handoff is a navigation and recovery artifact. It points to primary sources and records transient state; it does not become a new requirements, design, approval, or completion authority.

Read [references/context-model.md](references/context-model.md) before selecting a handoff mode, assigning trust, or accepting a received package. Use [references/handoff-template.md](references/handoff-template.md) when producing a durable package.

## Boundaries

- Locate and obey applicable `AGENTS.md`, `Agent.md`, and repository instructions. They remain the highest development constraints within their scope.
- Treat approved Spec, Plan, ADRs, Tasks, code, tests, and repository state as primary evidence. A handoff summarizes and links them; it does not replace them.
- Do not turn an assumption, recommendation, implementation choice, or conversation summary into an approved decision.
- Do not claim that work, tests, review, or approval occurred without reproducible evidence.
- Do not include secrets, credentials, private personal data, full environment dumps, or irrelevant conversation history. Redact sensitive values while preserving what the receiver needs to know.
- Preparing or receiving a handoff does not authorize implementation, commits, branch changes, external writes, deployments, or destructive actions.
- Do not silently adopt a handoff belonging to another repository, worktree, plan, slice, or contract version.

## Select a mode

Choose one mode and state why:

- `PREPARE`: package active work for a new session, Agent, tool, colleague, directory, or repository.
- `RECEIVE`: validate a supplied package against its cited sources before continuing.
- `RECOVER`: reconstruct working state after compaction, interruption, crash, or loss of conversational memory using repository evidence and any available ledger or handoff.
- `REFRESH`: update an existing package because authoritative artifacts or working state changed; preserve the prior package when audit history matters.

Do not create a handoff merely because a phase ended. Continue in the current session when primary reasoning is still needed and context remains usable. Use a normal task brief when only one already-self-contained slice is being delegated. Use a progress ledger for frequent execution checkpoints; use this Skill when context must travel or be reconstructed.

## Workflow

### 1. Define the continuation target

Record:

- who or what will receive the context;
- the next phase or bounded objective;
- why a context boundary is necessary;
- expected repository, worktree, branch, plan, slice, and contract baseline;
- what the receiver is and is not authorized to do.

If the intended next action is not known, the handoff may preserve state but must not pretend to be execution-ready.

### 2. Establish identity before content

Capture enough identity to prevent cross-task contamination:

- repository name and resolved root;
- worktree or workspace identity;
- branch and base/head commit when Git is used;
- task, change, plan, and current slice identifiers;
- authoritative Agent instructions and contract paths with versions, hashes, approval markers, or dates when available;
- handoff creation time and authoring context.

Use `UNKNOWN` for unavailable identity fields. Never fabricate a commit, approval, version, command result, or file path. If identity is insufficient to distinguish this work from another active effort, return `INSUFFICIENT_CONTEXT`.

### 3. Build a source map

Classify every load-bearing item:

- `PRIMARY`: authoritative instruction, approved contract, repository state, code, test output, or external decision record;
- `VERIFIED_CLAIM`: concise statement checked against a named primary source during this handoff;
- `REPORTED_CLAIM`: statement from the prior Agent or conversation that has not been independently checked;
- `ASSESSMENT`: interpretation or recommendation, with rationale;
- `UNKNOWN`: unresolved or unavailable information.

Reference primary sources by precise path, URL, identifier, version, and relevant section. Do not paste whole Specs, Plans, diffs, logs, or conversations into the handoff. Include a short excerpt only when the exact wording is needed to prevent ambiguity.

### 4. Record contract and decision state

Summarize only decisions that affect continuation. For each one, record:

- decision and owning layer: `AGENT_RULES`, `SPEC`, `PLAN`, `IMPLEMENT`, or `FINISH`;
- authority state and decision owner;
- source and exact baseline version;
- rationale that would be costly to rediscover;
- affected requirements, slices, interfaces, tests, or risks.

Separate these lists:

- approved and still effective decisions;
- proposals awaiting approval;
- assumptions awaiting validation;
- rejected or superseded options;
- open questions and their blocking effect.

Rejected approaches belong in the package only when retrying them is a realistic failure mode. State the evidence or constraint that ruled them out.

### 5. Record observable working state

Describe the current state as evidence, not recollection:

- completed, in-progress, blocked, and untouched slices;
- changed and untracked files relevant to scope;
- commits or patches that contain completed work;
- exact verification commands and results, including time and environment limits;
- active processes, generated data, migrations, fixtures, or temporary dependencies needed for continuation;
- known findings, deferred observations, and scope boundaries.

Do not use “done” alone. Link completion to a contract item and evidence. A passing command under an old Spec or Plan baseline is stale evidence until its applicability is re-established.

For long-running implementation, point to the plan-scoped progress ledger instead of duplicating every event. Verify that the ledger identifies this plan and that cited commits or artifacts exist.

### 6. Define the continuation capsule

Give the receiver a bounded startup sequence:

1. verify workspace and task identity;
2. read the listed Agent instructions and authoritative contracts in priority order;
3. inspect the relevant diff, code, and evidence anchors;
4. reconcile any drift detected since package creation;
5. perform one specific next action;
6. stop or escalate at stated decision, safety, scope, or evidence gates.

Name suggested Skills only when their trigger conditions are met. A suggestion is routing information, not permission to invoke a mutating workflow.

Keep the capsule small enough that the receiver can load all required material without rediscovering the project. Prefer exact pointers and retrieval order over broad directory lists.

### 7. Validate on receipt or recovery

In `RECEIVE` and `RECOVER`, do not continue from the package immediately. Run the resume gate:

1. re-read applicable Agent instructions;
2. verify repository root, worktree, branch, head, task, plan, and contract identity;
3. open the cited primary contracts and confirm status/version;
4. inspect current diff/status and compare it with the package;
5. verify claimed completed work through cited commits, files, or current tests in proportion to risk;
6. detect newer decisions, artifact edits, or external changes;
7. reclassify unverified package statements as claims rather than facts.

When state drift changes product intent or contract coverage, route through `sdd-change-impact`. When only implementation has advanced consistently, refresh the working-state section and proceed from the first unfinished slice.

Never rerun, overwrite, discard, or commit existing work merely because the package and repository disagree. Preserve the conflict and request reconciliation.

### 8. Decide readiness

Return exactly one outcome:

- `HANDOFF_READY`: a `PREPARE` or `REFRESH` package has adequate identity, sources, state, boundaries, and a next action;
- `RESUME_READY`: a received or recovered package matches current authoritative state closely enough to continue at the stated point;
- `RECONCILIATION_REQUIRED`: material drift, conflicting claims, dirty-state ambiguity, or changed contracts must be resolved first;
- `INSUFFICIENT_CONTEXT`: the task, baseline, authority, or evidence cannot be identified safely;
- `NO_HANDOFF_NEEDED`: no meaningful context boundary exists or the next unit is already self-contained.

`HANDOFF_READY` does not mean the underlying work is approved or complete. `RESUME_READY` authorizes no action beyond the authority already granted by the user and repository workflow.

## Output contract

Return or create one context package containing:

1. outcome, mode, purpose, receiver, and authorization boundary;
2. identity block and freshness marker;
3. ordered source map and authoritative contract baseline;
4. decisions, proposals, assumptions, rejected paths, and open questions;
5. verified working state and evidence ledger;
6. scope boundaries, hazards, and drift watchpoints;
7. continuation capsule with one next action and stop conditions;
8. receipt verification section for the next Agent to complete.

Use the repository's established handoff location when one exists. Otherwise return the package in the response, or use a user-specified path. Do not invent a permanent project directory or overwrite a prior package without authorization.

## References

- Trust levels, handoff boundaries, freshness, and resume rules: [references/context-model.md](references/context-model.md)
- Durable prepare/receive template: [references/handoff-template.md](references/handoff-template.md)
- Behavioral evaluation cases: [evals/cases.md](evals/cases.md)
