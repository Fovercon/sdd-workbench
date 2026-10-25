# SDD Finish Readiness Report

## Header

```yaml
outcome: READY_FOR_HUMAN_ACTION | NOT_READY | NEEDS_CONVERGENCE |
  HUMAN_DECISION_REQUIRED | INSUFFICIENT_EVIDENCE
targets: [LOCAL, PR, MERGE, RELEASE, DEPLOY, HANDOFF, ARCHIVE, CLEANUP]
destination: <local workspace, base branch, registry, release channel, environment, or owner>
reviewed_at: <timestamp and timezone>
authorization: NOT_REQUIRED | PENDING | GRANTED_FOR_BASELINE |
  INVALIDATED_BY_DRIFT
```

## 1. Exact baseline

| Item | Identity/status | Evidence |
|---|---|---|
| Repository/worktree | ... | ... |
| Branch/base | ... | ... |
| Source head/tree/diff | ... | ... |
| Dirty/untracked state | ... | ... |
| Agent instructions | ... | ... |
| Spec/Plan | ... | approved versions |
| Convergence decision | ... | report, command evidence, date |
| Candidate artifact | ... | hash/manifest or not yet built |

Drift: `NONE | FINISH_ONLY | IMPLEMENTATION | UNKNOWN`

Evidence limitations: ...

## 2. Target readiness summary

| Target | State | Blocking gates | Human action |
|---|---|---|---|
| LOCAL | READY / NOT_READY / N/A | ... | verify actual local deliverables and usage evidence |
| PR | READY / NOT_READY / N/A | ... | choose/create PR |
| RELEASE | READY / NOT_READY / N/A | ... | authorize version/tag/publish |

## 3. Gate matrix

| Gate | Applies to | State | Fact/evidence | Gap or risk | Owner | Closure evidence |
|---|---|---|---|---|---|---|
| SOURCE_IDENTITY | all | SATISFIED | ... | ... | ... | ... |
| CHANGE_SCOPE | PR/MERGE | ... | ... | ... | ... | ... |
| VERSION | RELEASE | ... | ... | ... | ... | ... |
| CHANGELOG_NOTES | PR/RELEASE/HANDOFF | ... | ... | ... | ... | ... |
| DEPENDENCY_LOCK | RELEASE/DEPLOY | ... | ... | ... | ... | ... |
| PACKAGE | RELEASE/DEPLOY/HANDOFF | ... | ... | ... | ... | ... |
| INSTALL_START_HEALTH | RELEASE/DEPLOY | ... | ... | ... | ... | ... |
| UPGRADE_MIGRATION | RELEASE/DEPLOY | ... | ... | ... | ... | ... |
| ROLLBACK_RECOVERY | DEPLOY | ... | ... | ... | ... | ... |
| OPERABILITY | DEPLOY/HANDOFF | ... | ... | ... | ... | ... |
| SECURITY_COMPLIANCE | target policy | ... | ... | ... | ... | ... |
| PR_REVIEW | PR | ... | ... | ... | ... | ... |
| MERGE | MERGE | ... | ... | ... | ... | ... |
| TAG_RELEASE | RELEASE | ... | ... | ... | ... | ... |
| DEPLOYMENT | DEPLOY | ... | ... | ... | ... | ... |
| HANDOFF_ARCHIVE | HANDOFF/ARCHIVE | ... | ... | ... | ... | ... |
| CLEANUP | CLEANUP | ... | ... | ... | ... | ... |

Allowed gate state: `SATISFIED | GAP | STALE | CONFLICT | HUMAN_GATE | BLOCKED_EXTERNAL | NOT_APPLICABLE | UNKNOWN`.

## 4. Version and history integrity

- Release type and rationale: ...
- Authoritative version source: ...
- Declared synchronized projections: ...
- Unreleased/release-note status: ...
- Compatibility and migration disclosure: ...
- Tag name and expected source commit: ...
- Existing tag/release collision check: ...
- Post-publish version check: ...

## 5. Candidate artifact

```yaml
artifact_id: ...
source_commit_or_tree: ...
build_command_and_environment: ...
dependency_lock: ...
manifest_or_hash: ...
tested_artifact_same_as_candidate: true | false | unknown
```

Required contents: ...

Prohibited contents checked: secrets, local configuration, uploads, logs, generated user state, debug traces, absolute local paths, unrelated components, ...

Install/start/health evidence: ...

## 6. Deployment and recovery

- Environment/configuration prerequisites: ...
- Migration/upgrade order: ...
- Backup/recovery point: ...
- Rollout and observation window: ...
- Health and success signals: ...
- Rollback trigger and owner: ...
- Data consequences/forward-fix boundary: ...
- Diagnostics, alerts, support, and escalation: ...

## 7. PR or handoff package

- Motivation and user/operator impact: ...
- Scope/non-goals: ...
- Requirement/change links: ...
- Verification and convergence evidence: ...
- Risks, known issues, compatibility, and manual steps: ...
- Required screenshots/demonstration: ...
- Reviewers/owners: ...

## 8. Blockers and decisions

| Item | Type | Consequence | Owner | Required action |
|---|---|---|---|---|
| ... | FINISH_GAP / CONVERGENCE / HUMAN_DECISION / EXTERNAL_BLOCKER | ... | ... | ... |

## 9. Guarded action sequence

1. Recheck exact source/artifact identity.
2. ...
3. Perform the authorized local delivery or target action.
4. Verify resulting local files/usage, PR/merge/tag/artifact/environment.
5. Preserve or clean up only according to provenance and retained data.

Stop if: ...

Recovery path: ...

Fresh authorization required for: ...
