---
name: sdd-finish-readiness
description: Assess whether a converged change is ready for a specific integration, release, deployment, handoff, archive, or cleanup action by checking source identity, release metadata, package contents, operational evidence, and human gates. Use after convergence and before PR, merge, tag, publish, deploy, or destructive cleanup. Do not execute those actions or substitute for convergence review.
---

# SDD Finish Readiness

Determine whether the exact converged baseline can safely proceed to a named Finish action. Make missing release mechanics, stale evidence, artifact drift, operational gaps, and human authorization visible before an irreversible or externally visible step.

This is a readiness review. It does not modify version files, build or publish packages, create PRs, merge, push, tag, deploy, archive, delete branches, or clean worktrees as part of this assessment. In authorized Router RUN, the controller may subsequently prepare and execute actions already covered by the mission; fresh permission is needed only for an uncovered action or decision.

Read [references/readiness-model.md](references/readiness-model.md) before assigning gate states, drift, target readiness, or the final outcome. Use [references/artifact-template.md](references/artifact-template.md) for a durable readiness report.

## Boundaries

- Locate and obey applicable `AGENTS.md`, `Agent.md`, release policy, branch protection, and scoped repository rules.
- Require a usable `sdd-converge-review` decision or equivalent evidence for the exact implementation baseline. Finish does not repair missing requirements, design, code, or verification.
- Do not equate a green test suite with release readiness. Version identity, packaging, compatibility, deployment, recovery, known issues, and authorization may still be incomplete.
- Do not invent a semantic-version bump, support matrix, changelog policy, release channel, deployment strategy, rollback promise, approver, or risk acceptance.
- Do not require a formal version bump for an ordinary development PR when the repository intentionally accumulates changes under `Unreleased`.
- Treat generated state, logs, uploads, credentials, local configuration, and user data as excluded from delivery unless an explicit artifact contract says otherwise.
- Human owners choose integration strategy, accept residual risk, authorize release/deployment, and approve destructive cleanup.

## Select the Finish target

Choose one or more targets and evaluate each separately:

- `PR`: submit a reviewable change without claiming it is merged or released.
- `MERGE`: integrate into the confirmed base branch or merge queue.
- `RELEASE`: create a versioned source/package release, tag, or release record.
- `DEPLOY`: move a reviewed artifact into a named environment.
- `HANDOFF`: transfer a finished deliverable and its evidence to an operator, customer, or owning team.
- `ARCHIVE`: close and retain the completed change/spec/evidence history.
- `CLEANUP`: remove a branch, worktree, temporary release state, or other finish workspace.

Do not collapse these into one “done” state. A change can be PR-ready but not release-ready, release-ready but not deployment-ready, or integrated while cleanup remains unsafe.

## Workflow

### 1. Define the target and authority boundary

Record:

- requested Finish target, destination, and release/deployment channel;
- exact action being assessed and actions explicitly out of scope;
- authorized human owner for integration, version, risk, release, deployment, and cleanup decisions when known;
- repository workflow, branch policy, and approval requirements;
- whether this is a development integration, formal release, hotfix, rollback, or handoff-only event.

If the target is vague, distinguish the candidate targets and return `HUMAN_DECISION_REQUIRED` rather than applying the strictest possible release checklist to every change.

### 2. Pin the converged source identity

Establish:

- repository and worktree root;
- branch or detached-head state;
- confirmed base branch or target ref;
- head commit and relevant diff/tree identity;
- dirty and untracked files;
- convergence report, reviewed contract versions, commands, evidence dates, and residual risks;
- current package/build source when an artifact already exists.

The readiness baseline must identify the same content that convergence reviewed. Classify drift:

- `NONE`: source and contracts match the converged baseline;
- `FINISH_ONLY`: only release metadata, packaging instructions, or other non-behavioral Finish artifacts changed and their effects are understood;
- `IMPLEMENTATION`: code, configuration, requirements, design, tests, runtime behavior, or evidence-bearing assets changed;
- `UNKNOWN`: identity or change meaning cannot be established.

`IMPLEMENTATION` drift returns to convergence. `FINISH_ONLY` drift requires focused review and release-specific verification. Do not reset, overwrite, commit, or discard a dirty tree to make the baseline look clean.

### 3. Confirm convergence entry conditions

Require:

- mandatory contract items verified or explicitly not applicable;
- no unresolved BLOCKER/HIGH implementation finding;
- required deterministic, system, semantic, DFX, security, compatibility, and environment evidence current for this target;
- residual risks visible with human acceptance where policy requires it;
- no known failure hidden by skips, subset-only runs, rerun-until-green, or stale reports.

Return `NEEDS_CONVERGENCE` when the gap belongs to Spec, Plan, implementation, tests, or convergence evidence rather than Finish.

### 4. Build the target gate matrix

Assess only applicable gates:

1. `SOURCE_IDENTITY`: exact source, base, branch, dirty state, and reviewed diff are known.
2. `CHANGE_SCOPE`: the diff contains the approved change and no unexplained unrelated work.
3. `VERSION`: version choice and all declared version sources are consistent.
4. `CHANGELOG_NOTES`: user-visible behavior, compatibility, known issues, and upgrade impact are described accurately.
5. `DEPENDENCY_LOCK`: dependency manifests and lock files are synchronized and reproducible as required.
6. `PACKAGE`: the deliverable contains required files, excludes prohibited state/secrets, and maps to the reviewed source.
7. `INSTALL_START_HEALTH`: supported install, startup, configuration, health, and minimum smoke paths are evidenced.
8. `UPGRADE_MIGRATION`: compatibility, data/schema migration, backup, and upgrade order are defined and verified where applicable.
9. `ROLLBACK_RECOVERY`: rollback or safe-disable behavior, recovery point, and data implications are known.
10. `OPERABILITY`: diagnostics, logs, metrics, resource/capacity limits, support ownership, and runbook are adequate for the target.
11. `SECURITY_COMPLIANCE`: secret scanning, untrusted input, dependency/license, privacy, signing, SBOM, or approval evidence required by policy is present.
12. `PR_REVIEW`: title/body, motivation, scope, requirement links, evidence, risk, screenshots, reviewers, and template fields are ready.
13. `MERGE`: base branch, required reviews/checks, merge queue or strategy, and post-merge verification policy are satisfied.
14. `TAG_RELEASE`: tag/version identity, tag absence, source branch/commit rule, release notes, artifact hashes/signatures, and post-publish verification are prepared.
15. `DEPLOYMENT`: artifact promotion, environment configuration, secrets, migration sequencing, rollout, health, observation window, and rollback trigger are prepared.
16. `HANDOFF_ARCHIVE`: ownership, retained contracts/evidence, known issues, support information, and recovery location are clear.
17. `CLEANUP`: integration/release result is confirmed, workspace provenance is known, and no unique uncommitted files will be destroyed.

Use gate definitions from the readiness model. Mark non-applicable gates explicitly; do not fill the report with generic boilerplate.

### 5. Verify version and history integrity

Follow the repository's own version contract. Check, as applicable:

- semantic or project-specific version policy and whether the proposed bump matches the approved release scope;
- one authoritative runtime version source and all declared projections;
- package metadata, lockfile, API/UI display, documentation, and release notes consistency;
- `Unreleased` contents are complete before archiving into a dated release section;
- previously released history is retained;
- the proposed tag is absent and will identify a commit that already contains synchronized metadata;
- published tags or immutable releases are not moved to repair a mistake;
- post-publish verification can read the version and artifact identity from the released object.

Version synchronization is project-specific. If no release contract exists, report the missing decision or policy; do not copy another repository's file list as authority.

### 6. Verify the deliverable, not just the source tree

When a package, archive, image, installer, binary, or generated bundle exists or is required:

- identify its source commit/tree and build conditions;
- inspect manifest or contents against the artifact contract;
- ensure excluded files, credentials, debug traces, local paths, generated user tasks, and unrelated products are absent;
- verify entrypoints, dependency resolution, configuration templates, version reporting, and minimal startup/health behavior;
- record checksum, signature, SBOM, provenance, or reproducibility evidence when policy requires it;
- confirm the artifact actually tested is the artifact proposed for promotion.

A source test run cannot prove that a differently built package is correct. A package that exists cannot prove it was built from the converged source.

### 7. Verify operational and recovery readiness

For `RELEASE`, `DEPLOY`, or operational `HANDOFF`, examine:

- supported platforms and environment prerequisites;
- installation, configuration, startup, shutdown, and health checks;
- migration/upgrade sequencing and historical-data compatibility;
- backup, rollback, safe-disable, and forward-fix boundaries;
- observability, failure diagnostics, alert ownership, and support path;
- capacity/performance evidence scoped to the actual workload and environment;
- canary, staged rollout, observation window, or maintenance window if required;
- known limitations and manual steps that an operator must not infer.

Do not invent a rollback procedure for an irreversible migration. Surface the decision and protection gap before deployment.

### 8. Separate technical readiness from human action

Record authorization separately for each external or destructive action:

- `NOT_REQUIRED`
- `PENDING`
- `GRANTED_FOR_BASELINE`
- `INVALIDATED_BY_DRIFT`

Approval applies to the exact target, version, destination, and source/artifact identity. A general “looks good” does not authorize a tag, push, deployment, or deletion unless the context makes that action explicit.

If all technical gates pass and the only remaining step is an ordinary explicit choice or authorization, return `READY_FOR_HUMAN_ACTION`. If the human must still decide version, release scope, compatibility, risk acceptance, integration strategy, or rollback policy, return `HUMAN_DECISION_REQUIRED`.

### 9. Define the guarded action sequence

Describe—but do not execute—the smallest safe sequence for the selected target. Include:

- pre-action identity recheck;
- exact gate/evidence refresh triggered by the action;
- ordered integration, build, tag, publish, deploy, archive, or cleanup steps at the level justified by project policy;
- verification of the resulting merged commit, tag, artifact, or environment;
- stop conditions and recovery path;
- which steps require fresh user authorization.

For merge, verify the merged result when policy requires it. For tags, verify the tag contains the expected version. For deployment, verify health and rollback triggers. For cleanup, preserve any branch/worktree that still contains unique or uncommitted data.

## Outcomes

Return exactly one:

- `READY_FOR_HUMAN_ACTION`: all applicable technical gates for the named target are satisfied; the next integration, release, deployment, handoff, archive, or cleanup action still follows its authorization policy;
- `NOT_READY`: one or more Finish-owned gaps, stale artifacts, or target-specific checks must be corrected;
- `NEEDS_CONVERGENCE`: implementation/contract drift or missing verification requires return to `sdd-converge-review` or an earlier SDD stage;
- `HUMAN_DECISION_REQUIRED`: target, version, release scope, integration choice, compatibility, residual risk, rollback, or another owner decision is unresolved;
- `INSUFFICIENT_EVIDENCE`: source, convergence, artifact, environment, or policy evidence cannot support a readiness conclusion.

No outcome means that a PR was created, code was merged, a release was published, an environment was changed, or cleanup occurred.

## Output contract

Return or create:

1. outcome, selected target, destination, and authorization state;
2. exact source, convergence, contract, and artifact baselines;
3. drift classification and evidence limits;
4. target gate matrix with owner and closure evidence;
5. version/history and package-integrity results where applicable;
6. deployment, rollback, operability, and known-issue readiness where applicable;
7. blockers, human decisions, and accepted residual risks;
8. guarded next action sequence with stop conditions.

Do not mutate Finish artifacts as part of the readiness report. If preparation or execution is covered by the current or prior user request, return the guarded sequence to the RUN controller for execution and result verification. Preserve the authorized baseline; do not require a new request solely because readiness assessment ended.

## References

- Gate states, target profiles, drift, artifact identity, and decision rules: [references/readiness-model.md](references/readiness-model.md)
- Durable Finish readiness report template: [references/artifact-template.md](references/artifact-template.md)
- Behavioral evaluation cases: [evals/cases.md](evals/cases.md)
