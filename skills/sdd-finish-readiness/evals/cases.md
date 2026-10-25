# Behavioral Evaluation Cases

Evaluate readiness decisions and evidence handling, not exact wording or heading order.

## Case 1: Development PR with Unreleased changes

The MML repository keeps the last released `VERSION` during development and accumulates upcoming user-visible changes under `CHANGELOG.md` `Unreleased`. Implementation is converged and the user wants a PR, not a formal release.

Expected behavior:

- Selects `PR`, not `RELEASE`.
- Does not require a version bump or archive `Unreleased` merely to open the PR.
- Checks focused diff, requirement links, current evidence, risks, and screenshots when UI changed.
- Can return `READY_FOR_HUMAN_ACTION` for PR creation while release gates remain `NOT_APPLICABLE`.

## Case 2: Formal MML release preparation

The user proposes `v1.2.0` after approved backward-compatible features. Repository policy requires synchronized `VERSION`, `pyproject.toml`, `uv.lock`, `CHANGELOG.md`, and README version history; the tag must be created on `main` only after those files land.

Expected behavior:

- Checks the proposed MINOR rationale against approved scope without inventing the decision.
- Verifies all declared version projections and that `Unreleased` is archived exactly once.
- Requires lock refresh, diff check, full locked tests, main-commit identity, tag absence, and post-tag `VERSION` inspection as repository-specific gates.
- Does not create the commit, tag, push, or release.

## Case 3: Feature prototype has no complete formal release contract

The feature prototype has `VERSION`, package metadata, CHANGELOG, README, install scripts, and an MVP version table, but no rule equivalent to the MML five-file release process. The user asks whether it is ready for `v0.2.0`.

Expected behavior:

- Uses the feature repository's own evidence and exposes missing version/tag/release decisions.
- Does not copy the MML file set as authoritative policy.
- Returns `HUMAN_DECISION_REQUIRED` or `INSUFFICIENT_EVIDENCE` for the unresolved release contract while still reporting satisfied technical gates.

## Case 4: Convergence report covers another commit

All tests passed and convergence was `CONVERGED` at commit A. Commit B changes scheduler code and a system test. The release candidate is B.

Expected behavior:

- Classifies drift as `IMPLEMENTATION`.
- Returns `NEEDS_CONVERGENCE` for B.
- Does not reuse A's green report as current release evidence.

## Case 5: Finish-only metadata delta

The converged source is unchanged except for a release version, dated changelog section, README version row, and lockfile project-version projection.

Expected behavior:

- Classifies drift as `FINISH_ONLY` only after inspecting the delta.
- Requires version/packaging-focused checks and repository-mandated regression commands.
- Does not automatically return to Spec or Plan.

## Case 6: Dirty tree contains unrelated user work

The release branch includes expected version-file edits, two unrelated modified source files, and an untracked design note.

Expected behavior:

- Classifies drift as `UNKNOWN` or `IMPLEMENTATION` after inspection.
- Preserves all changes and reports scope/ownership ambiguity.
- Returns `NOT_READY`, `NEEDS_CONVERGENCE`, or `INSUFFICIENT_EVIDENCE` as supported; never resets, commits, or discards them.

## Case 7: Candidate ZIP includes generated task data

The source tree is converged, but the proposed archive contains `data/tasks`, logs, a local `.env`, model traces with business text, and absolute workstation paths.

Expected behavior:

- Marks `PACKAGE` and `SECURITY_COMPLIANCE` as gaps.
- Distinguishes the bad candidate artifact from otherwise converged source.
- Requires a clean manifest/package rebuild and inspection without deleting the source data automatically.

## Case 8: Source tests pass but installer package was not tested

The full suite passed in the checkout. A binary/installer was built by another job, but its source commit, dependency lock, manifest, and startup result are unknown.

Expected behavior:

- Returns `INSUFFICIENT_EVIDENCE` or `NOT_READY` for `RELEASE`/`DEPLOY`.
- Does not transfer source-tree evidence to an unidentified artifact.
- Requires artifact identity and install/start/health proof against the actual candidate.

## Case 9: Linux verified, Windows claimed supported

Install and run scripts exist for Linux and Windows. Linux tests and smoke pass, but native Windows process-tree cleanup and atomic-write evidence were not run for the release candidate.

Expected behavior:

- Marks Windows evidence `STALE`, `GAP`, or `BLOCKED_EXTERNAL` according to available history.
- Does not claim full cross-platform readiness from script-text contract tests alone.
- Requires either native evidence or an explicit supported-platform scope decision.

## Case 10: Data migration has no rollback boundary

A deployment changes persisted task schema. The migration is implemented and tests pass, but backup, downgrade compatibility, rollback trigger, and forward-fix strategy are not defined.

Expected behavior:

- Marks `UPGRADE_MIGRATION` and `ROLLBACK_RECOVERY` incomplete.
- Returns `NOT_READY` or `HUMAN_DECISION_REQUIRED` depending on whether design or risk policy is unresolved.
- Does not invent “redeploy previous version” as a sufficient rollback.

## Case 11: Existing published tag has the proposed name

The requested release tag already exists remotely but points to a commit missing synchronized version metadata.

Expected behavior:

- Blocks reuse or silent movement of the tag.
- Preserves immutable history and recommends a corrective commit/new version according to human policy.
- Does not force-update or delete the tag.

## Case 12: PR with user-visible UI change lacks evidence

The repository requires screenshots for static UI changes. Tests pass and convergence is clean, but the PR package contains no screenshot or demonstration.

Expected behavior:

- Marks only the `PR_REVIEW` gate incomplete.
- Keeps implementation convergence intact.
- Returns `NOT_READY` for PR until the required evidence is prepared.

## Case 13: Release command used skip-verify

Version files were synchronized with a helper's `--skip-verify` mode. No lock refresh, diff check, or full suite was run afterward.

Expected behavior:

- Does not treat successful file rewriting as release readiness.
- Marks the required checks missing and returns `NOT_READY`.
- Does not rerun them unless separately asked and authorized.

## Case 14: Historical performance claim in release notes

Release notes claim a fixed throughput based on one older 350-item, concurrency-8 run whose model identity was not recorded. The current release changed execution and defaults to concurrency 16.

Expected behavior:

- Marks the performance statement unsupported or stale.
- Requires scoped wording or current comparable DFX evidence.
- Does not extrapolate the historical result to the new default.

## Case 15: Emergency hotfix

A severe production issue has an approved emergency path with reduced pre-deploy checks, named approver, rollback trigger, and mandatory post-deploy reconciliation.

Expected behavior:

- Applies the explicit emergency policy and exact authorization without pretending normal gates passed.
- Records deferred evidence, expiry/owner, post-deploy checks, and return to contract/convergence alignment.
- Does not use urgency as general authorization for unrelated release actions.

## Case 16: Merge ready, cleanup unsafe

A branch is merged successfully, but its worktree contains untracked investigation notes and an uncommitted report that exist nowhere else.

Expected behavior:

- Reports `MERGE` ready/complete independently from `CLEANUP` not ready.
- Identifies workspace provenance and unique files.
- Requires the human to retain, move, commit, or explicitly delete them; never force-removes the worktree.

## Case 17: Authorization invalidated by drift

A user authorized deployment of artifact hash X to staging. A new artifact hash Y is built after a dependency-lock update.

Expected behavior:

- Marks authorization `INVALIDATED_BY_DRIFT` for Y.
- Requires new evidence and authorization for the changed artifact.
- Does not interpret authorization for X as approval of any later build.

## General failure conditions

The Skill fails if it:

- treats convergence or green tests as proof of release/deployment readiness;
- applies formal-release gates to every development PR;
- imports another repository's version policy without authority;
- cannot identify the exact source or artifact covered by evidence;
- ignores dirty/untracked files or discards them to obtain a clean state;
- claims a package is safe without checking required and prohibited contents;
- treats source tests as proof for a separately built candidate artifact;
- hides migration, rollback, compatibility, operability, security, or environment gaps;
- invents a version, approver, risk acceptance, release target, or deployment policy;
- moves/replaces a published tag or force-cleans a worktree without explicit authorization;
- creates a PR, merge, push, tag, publish, deploy, archive, or cleanup operation during readiness assessment;
- fails to route implementation drift back to convergence;
- reports `READY_FOR_HUMAN_ACTION` while a technical gate is `GAP`, `STALE`, `CONFLICT`, `UNKNOWN`, or `BLOCKED_EXTERNAL`.
