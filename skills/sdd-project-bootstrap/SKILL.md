---
name: sdd-project-bootstrap
description: Discover, create, audit, or refresh an AI-ready SDD project baseline grounded in the current repository, including scoped AGENTS.md instructions, sources of truth, verified development commands, artifact conventions, quality gates, and safety boundaries. Use at project onboarding or when repository-level Agent rules are missing or stale. Do not use to define feature requirements, invent architecture, install tooling, or approve the generated baseline on behalf of its owner.
---

# SDD Project Bootstrap

Establish Stage 0 from repository evidence. Give future Agents a concise, executable map of how to work in this project while keeping product intent in Spec, technical decisions in Plan, and task detail in execution artifacts.

The primary Constitution artifact is the repository's applicable `AGENTS.md`, `Agent.md`, or documented equivalent. The Bootstrap process discovers and proposes that contract; it does not become a second competing constitution.

Read [references/bootstrap-model.md](references/bootstrap-model.md) before classifying repository facts, choosing instruction scope, claiming command validity, or deciding readiness. Use [references/artifact-templates.md](references/artifact-templates.md) to draft Agent instructions and the supporting evidence record.

## Boundaries

- Obey all already-applicable Agent instructions and repository policies while bootstrapping. A new draft cannot override higher-level or externally supplied rules.
- Inspect the repository before writing rules. Do not invent commands, paths, architecture, coding standards, test layers, release procedures, or sources of truth.
- Keep feature behavior, domain semantics, API decisions, and current implementation tasks out of Agent instructions; point to their authoritative Spec or Plan instead.
- Do not install dependencies, initialize frameworks, run networked or credentialed commands, modify product code, migrate data, commit, tag, push, publish, deploy, or delete state merely to bootstrap the project.
- Preserve existing user changes. Do not replace an existing `AGENTS.md`, nested instruction file, CI workflow, manifest, or project document wholesale when a bounded update is possible.
- Never copy secrets, `.env` values, credentials, private data, full environment dumps, or machine-specific absolute paths into shared instructions.
- Distinguish a command declared by documentation from one statically verified in project configuration and one actually executed successfully.
- AI may prepare a baseline for review; only the authorized project owner can approve the exact rule version and consequential exceptions.

## Select a mode

Choose one and state it:

- `DISCOVER`: inspect the repository and return a baseline inventory without editing files.
- `CREATE`: create the first project Agent instructions and minimal SDD conventions when the user authorized repository changes.
- `AUDIT`: evaluate existing Agent instructions and project baseline for accuracy, scope, conflicts, staleness, and usability without editing them.
- `REFRESH`: make an authorized, bounded update because the repository, workflow, tooling, or approved method changed.

Default to `AUDIT` when instructions already exist and the user asks generally to “bootstrap” or “check” the project. Do not silently replace mature rules with this Skill's preferred layout.

## Workflow

### 1. Establish repository identity and authority

Identify:

- resolved repository/worktree root and version-control state when applicable;
- requested Bootstrap mode and authorized write scope;
- existing root and nested Agent instruction files and their scope;
- project owner or required approval gate;
- active work whose assumptions could be invalidated by changing repository rules.

Inspect the working tree before editing. If the target instruction file contains overlapping unowned changes or two applicable rule sources conflict without a precedence rule, return `RECONCILIATION_REQUIRED`. Do not reset, stash, overwrite, or select one arbitrarily.

### 2. Discover the repository from primary evidence

Inspect only relevant sources, normally:

- directory structure and module/package boundaries;
- manifests, lockfiles, task runners, scripts, containers, and workspace configuration;
- CI/CD workflows and required checks;
- test layout, configuration, fixtures, and representative existing commands;
- README/contributor documentation and actual entry points;
- requirements, design, ADR, issue/task, changelog, version, release, and deployment artifacts;
- ignore rules, generated/state directories, sample configuration, and data boundaries;
- external services, credentials, platforms, migrations, and destructive or irreversible operations.

Classify every load-bearing statement as:

- `VERIFIED_REPOSITORY_FACT`: directly observed in current repository artifacts;
- `DECLARED_NOT_EXECUTED`: documented or configured but not run in this Bootstrap;
- `EXECUTED_EVIDENCE`: command was run for this exact baseline, with result and environment;
- `PROPOSED_CONVENTION`: new rule or layout awaiting approval;
- `CONFLICT`: authoritative sources disagree;
- `UNKNOWN`: evidence is insufficient.

Do not treat a README, historical log, copied script, or stale Agent file as automatically current. Do not execute project code merely to turn every declaration into executed evidence.

### 3. Build the source-of-truth map

Identify which artifacts own:

- repository-level Agent behavior and safety;
- product requirements and acceptance;
- architecture, interfaces, data, and operational design;
- tasks, current Slice, and execution state;
- tests, evaluation, and convergence evidence;
- versions, packages, deployment, known issues, and release history.

Record precedence and conflict handling. If the repository has no SDD artifact convention, propose the smallest workable convention that fits its existing documentation layout; do not create a large directory hierarchy or duplicate current documents without approval.

Use stable pointers instead of copying mutable content into `AGENTS.md`. The instruction should tell an Agent where the truth lives and when to read it.

### 4. Establish a trustworthy command catalog

For each applicable activity, identify the exact repository-supported command or mark it unknown:

- dependency setup;
- focused test;
- full offline test suite;
- formatting, linting, type checking, build, or package validation;
- local start and minimal smoke check;
- generated-code refresh or schema validation;
- target-specific system, UI, semantic, performance, security, or cross-platform gates;
- version and release preparation.

Record command evidence as `DECLARED`, `STATICALLY_VERIFIED`, `EXECUTED_PASS`, `EXECUTED_FAIL`, `BLOCKED`, or `UNKNOWN` using the Bootstrap model. A command found in CI or a manifest may be statically verified without being safe or cheap to execute locally.

Run only safe, relevant checks within the user's authorization and repository policy. Do not run commands requiring network, credentials, paid models, long-lived services, external environments, destructive actions, or substantial cost without explicit authority. Report unrun gates honestly.

### 5. Select durable Agent instructions

Include only rules that are stable, actionable, scoped, and supported by repository evidence or an explicit owner decision. Prefer these categories when applicable:

- repository map and scoped ownership;
- authoritative contracts and required reading order;
- development workflow and contract-change discipline;
- verified build/test commands and evidence expectations;
- coding conventions that differ from language defaults or are enforced locally;
- generated files, external inputs, persistent state, and data isolation;
- version, review, release, and external-action boundaries;
- security, privacy, destructive-action, credential, and environment constraints;
- nested instruction scope and conflict precedence.

Write rules in executable form: trigger, required action, and observable check where useful. Replace “follow best practices” with the project-specific behavior an Agent can actually perform.

Keep volatile details out:

- current task lists and temporary workarounds;
- exact feature behavior or page details;
- speculative future architecture;
- user-machine paths and one-session state;
- copied manuals or generic language tutorials;
- commands not supported by repository evidence.

### 6. Decide root versus scoped instructions

Use one root instruction file when rules apply broadly. Add or retain nested instruction files only when a subtree has materially different commands, generated-file policy, language conventions, ownership, or safety boundaries.

For every nested file:

- state its scope through location and content;
- inherit rather than repeat root rules;
- document intentional overrides;
- ensure no contradiction with higher-level constraints;
- avoid fragmenting the repository into instructions that Agents cannot discover reliably.

Monorepo size alone does not require nested instructions.

### 7. Define the minimal SDD operating baseline

Make the project workflow explicit without fabricating feature artifacts:

```text
Agent rules
  -> approved requirements
  -> reviewed Plan and behavior Slices
  -> implementation and verification evidence
  -> convergence decision
  -> Finish readiness and authorized delivery action
```

Record:

- established or proposed artifact locations and naming;
- approval/version markers for Spec and Plan;
- how the current Slice and evidence are identified;
- required human gates;
- when changes return through impact analysis;
- where durable handoff and retrospective records belong, if the repository uses them.

Do not create empty Spec, Plan, Tasks, verification, handoff, or retrospective files as decoration. Create a structure only when current work needs it or the owner approves it as a repository convention.

### 8. Draft, audit, or refresh with minimal change

In `CREATE`, produce the smallest useful instruction baseline and supporting Bootstrap evidence. In `AUDIT`, classify findings by consequence and propose precise changes without applying them. In `REFRESH`, compare the approved baseline with current repository facts and change only stale, missing, conflicting, or newly approved rules.

For existing instructions:

- preserve accurate project-specific guidance and established tone;
- remove or revise stale absolute paths, unavailable tools, false commands, and superseded rules only with evidence and authorization;
- consolidate duplication only when scope and meaning remain intact;
- record material additions, removals, and rationale;
- identify active Specs, Plans, Slices, tests, or evidence affected by a rule change.

Use `sdd-change-impact` before applying an Agent-rule change when it can invalidate active approved work or evidence. Use an evidence-backed `sdd-retrospective` proposal as input, not as automatic approval.

### 9. Validate usability and conflicts

Before proposing approval, check:

- every path and command is verified or visibly marked with its evidence state;
- instruction scope and precedence are unambiguous;
- the file is concise enough to load routinely and points to deeper sources instead of duplicating them;
- business behavior remains in Spec and architecture remains in Plan;
- safety rules identify protected data, generated state, external inputs, credentials, and consequential actions;
- no instruction depends on a missing personal path, unavailable Skill, implicit secret, or undocumented environment;
- rules do not contradict manifests, CI, tests, documentation, or nested instructions;
- exceptions and human approvals are explicit;
- proposed SDD conventions reuse existing project structure where possible.

Do not claim the baseline is complete merely because the document is well formatted.

### 10. Pass the human gate

Present the exact draft or delta together with evidence gaps, unexecuted commands, conflicts, and consequential rules. Approval applies to an identifiable content version or hash.

After approval, future work may treat that exact instruction baseline as the repository's Stage 0 contract. Approval does not authorize commands, dependency installation, implementation, commits, releases, deployment, or destructive actions beyond their own policies.

## Outcomes

Return exactly one:

- `DISCOVERY_COMPLETE`: repository facts, unknowns, and proposed next Bootstrap action are recorded without file changes;
- `BASELINE_READY_FOR_APPROVAL`: a created or refreshed exact baseline is complete enough for owner review but is not yet approved;
- `BASELINE_APPROVED`: the authorized owner explicitly approved the exact baseline version;
- `BASELINE_CURRENT`: an audit found the existing approved baseline accurate and sufficient for the declared scope;
- `HUMAN_DECISION_REQUIRED`: rule scope, source-of-truth authority, project convention, safety policy, or consequential exception needs an owner decision;
- `RECONCILIATION_REQUIRED`: applicable instructions, repository facts, or overlapping work conflict and must be reconciled safely;
- `INSUFFICIENT_EVIDENCE`: the repository does not provide enough trustworthy evidence to establish the requested baseline.

`BASELINE_READY_FOR_APPROVAL` is not approval. `BASELINE_APPROVED` does not mean any feature Spec, implementation, or release is ready.

## Output contract

Return or create:

1. the root Agent instruction draft/audit and any justified scoped-instruction deltas;
2. a Bootstrap evidence record containing repository identity, mode, outcome, and authorization boundary;
3. source-of-truth and instruction-scope maps;
4. command catalog with evidence states and unrun conditions;
5. generated/state/data/security and external-action boundaries;
6. minimal SDD artifact and approval conventions;
7. conflicts, unknowns, affected active work, and human decisions;
8. exact proposed delta, validation result, approval state, and next step.

Use the repository's established instruction filename and documentation locations. Prefer `AGENTS.md` when creating a new Codex-compatible baseline and no convention exists. Keep the evidence record in the response unless the repository or user names a durable location; do not invent another project-management directory.

## References

- Discovery evidence, instruction layering, command states, durability, and approval rules: [references/bootstrap-model.md](references/bootstrap-model.md)
- Agent instruction and Bootstrap evidence templates: [references/artifact-templates.md](references/artifact-templates.md)
- Behavioral evaluation cases: [evals/cases.md](evals/cases.md)
