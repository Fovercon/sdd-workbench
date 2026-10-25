# Finish Readiness Model

Use this model to distinguish converged implementation from a deliverable that is ready for a particular Finish action.

## 1. Finish position in SDD

```text
approved contracts
  -> implementation and verification
  -> convergence decision for exact baseline
  -> Finish readiness for named target
  -> explicit human/external action
  -> post-action verification
  -> archive and safe cleanup
```

Finish readiness consumes convergence evidence. It does not recreate or weaken it.

## 2. Target profiles

| Target | Minimum focus | Common conditional gates |
|---|---|---|
| `PR` | source identity, scope, evidence summary, template, reviewability | screenshots, migration notes, security reviewers |
| `MERGE` | PR gates, confirmed base, reviews/checks, integration strategy | merge queue, merged-result verification |
| `RELEASE` | version/history, package identity, release notes, tag plan | signatures, SBOM, multi-platform packages |
| `DEPLOY` | promoted artifact, environment/config, migration, health, rollback | canary, maintenance window, approval board |
| `HANDOFF` | deliverable identity, instructions, evidence, ownership, limitations | customer acceptance, support SLA |
| `ARCHIVE` | final decision/evidence, supersession links, recovery location | spec archive tooling, retention policy |
| `CLEANUP` | outcome confirmed, provenance, no unique files, recovery status | worktree/branch deletion, temporary artifact removal |

Select only gates whose absence could make the named action unsafe, misleading, unreproducible, or unauditable.

## 3. Gate states

| State | Meaning |
|---|---|
| `SATISFIED` | Current evidence meets the applicable policy for the exact baseline and target |
| `GAP` | Required Finish artifact, procedure, or evidence is missing |
| `STALE` | Evidence exists but covers another source, artifact, environment, or time |
| `CONFLICT` | Two authoritative Finish artifacts disagree |
| `HUMAN_GATE` | Technical preparation is adequate but explicit approval/action remains |
| `BLOCKED_EXTERNAL` | Required external system, environment, reviewer, or service is unavailable |
| `NOT_APPLICABLE` | Gate is outside the selected target with rationale |
| `UNKNOWN` | Available evidence cannot establish a state |

`HUMAN_GATE` is not a technical failure. `UNKNOWN` is not a pass.

## 4. Readiness versus authorization

Readiness asks whether the action is prepared. Authorization asks whether the owner permits it now.

| Technical state | Decision state | Outcome |
|---|---|---|
| All applicable gates satisfied | Ordinary explicit action pending | `READY_FOR_HUMAN_ACTION` |
| Finish-owned gap/stale/conflict | Any | `NOT_READY` |
| Product/implementation evidence invalid | Any | `NEEDS_CONVERGENCE` |
| Technical evidence adequate but consequential policy choice unresolved | Pending decision | `HUMAN_DECISION_REQUIRED` |
| Baseline/policy/artifact cannot be identified | Unknown | `INSUFFICIENT_EVIDENCE` |

An explicit release authorization can be recognized, but drift invalidates it for a changed baseline.

## 5. Drift model

### `NONE`

Source, contracts, evidence, and artifact identity match convergence.

### `FINISH_ONLY`

Only version metadata, changelog, packaging manifests, deployment notes, or other non-behavioral Finish files changed. Review the delta and rerun affected packaging/version checks. A Finish-only label must be evidence-backed; configuration can alter behavior.

### `IMPLEMENTATION`

Code, runtime configuration, tests, requirements, design, externally observable assets, migrations, or behavior-bearing generated files changed. Return to convergence for the affected scope.

### `UNKNOWN`

Dirty state, untracked files, missing commit/tree identity, or ambiguous generated artifacts prevent classification. Preserve the workspace and investigate.

## 6. Source and artifact identity

A delivery claim should be traceable across:

```text
approved contract versions
+ convergence report/evidence
+ source commit/tree/diff
+ build inputs and dependency lock
+ artifact identifier/hash
+ release tag or deployment revision
+ destination/environment
```

Not every project publishes a binary artifact, signature, or SBOM. Require only what its contract, risk, or policy needs. Always prevent an unidentifiable artifact from inheriting evidence from a different source tree.

## 7. Version and changelog rules

- Use the repository's declared version authority and synchronization set.
- Development work may accumulate under `Unreleased`; a formal bump happens at the release boundary when policy says so.
- Select version magnitude from approved compatibility impact, not commit count or Agent preference.
- Preserve historical release sections and avoid duplicate or decreasing versions.
- Release notes describe user/operator impact, not merely file changes.
- Breaking changes, migrations, deprecated behavior, known limitations, and required actions must not be hidden under a generic “Changed”.
- A tag should point to content already carrying that version. Post-publish verification should inspect the tag/artifact, not only the working tree.
- Treat a published tag or release as immutable unless repository policy explicitly defines another recovery procedure.

## 8. Package integrity

Check the package against a positive and negative manifest:

- required executable/library/assets/config templates/docs/licenses;
- correct version and entrypoints;
- locked or declared dependencies;
- required Skills/prompts/models or other runtime assets when they are part of the product;
- absence of credentials, `.env`, local caches, logs, uploads, user tasks, test secrets, debug traces, absolute local paths, and unrelated products;
- deterministic or explainable generated contents;
- checksum/signature/provenance when required.

Run the smallest installation/startup/smoke proof against the actual candidate artifact, not a neighboring source checkout.

## 9. Deployment and rollback

For environment-changing targets, make these explicit:

- artifact promotion source and destination;
- environment-specific configuration and secret ownership;
- compatibility with currently stored data and running versions;
- schema/data migration order and idempotency;
- backup/recovery point and restoration verification;
- rollout method, observation period, and success signals;
- rollback trigger, commands/procedure owner, and data consequences;
- forward-fix plan when rollback is impossible;
- support, alerts, diagnostics, and escalation path.

“Redeploy the previous version” is not a rollback plan when data or external contracts have changed.

## 10. PR and merge readiness

A review-ready change normally includes:

- confirmed target/base branch;
- focused, explainable diff and understood dirty state;
- motivation, user/operator impact, scope, and non-goals;
- links to requirements/issues and convergence evidence;
- exact current test/eval commands and results;
- risks, compatibility, migration, rollback, and known gaps as applicable;
- screenshots or demonstrations required for user-visible changes;
- required reviewers/checks and repository template fields.

The integration choice belongs to the human owner. A PR can remain open with its workspace intact for feedback.

## 11. Cleanup safety

Cleanup is a separate destructive target. Require:

- the intended integration/release/deployment result is confirmed;
- the exact branch/worktree/temp artifacts are identified;
- workspace ownership/provenance is known;
- no modified or untracked file exists only in the cleanup target;
- recovery references exist where required;
- remote/local branch and worktree policies permit removal.

Do not force-remove a refused worktree or force-delete a branch merely to complete the checklist. Ask the owner to commit, move, retain, or explicitly delete unique files.

## 12. Post-action verification

Readiness is incomplete without defining how the result will be checked:

- PR URL and base/head identities;
- merged commit and required tests/checks;
- tag content/version and immutability;
- published artifact checksum/version/install smoke;
- deployed revision, health, key workflow, telemetry, and rollback window;
- archive location and supersession links;
- cleanup confirmation and retained recovery path.

The readiness Skill plans these checks; the action workflow records their actual results.

## 13. Common category errors

| Claim | Correction |
|---|---|
| “Converged means released” | Converged means implementation may enter Finish |
| “Tests passed, so version files are fine” | Version and package integrity are separate gates |
| “Source is green, so the ZIP/image is green” | Test the candidate artifact identity |
| “It is only configuration” | Runtime configuration may be implementation drift |
| “The branch is merged, so cleanup is automatic” | Unique files and workspace provenance still matter |
| “Tag can be fixed later” | Publish only after metadata is in the tagged commit; correct forward |
| “Rollback is previous binary” | Account for migrations, data, config, and external contracts |
| “Every PR needs a version bump” | Follow the repository's release-boundary policy |
