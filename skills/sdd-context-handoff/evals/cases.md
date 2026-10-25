# Behavioral Evaluation Cases

Evaluate decisions and resulting artifacts, not exact wording or heading order.

## Case 1: MML rerun slice moves to a fresh session

The approved Spec defines rerun as updating the original governance record. The implementation session completed persistence changes, has an uncommitted API test, and has not started the UI slice. The user asks for a handoff to continue tomorrow.

Expected behavior:

- Uses `PREPARE` and identifies repository, branch/worktree, Spec/Plan versions, rerun slice, head, and dirty files.
- Points to the rerun requirements and relevant system-test evidence rather than copying them.
- Separates completed persistence work from the uncommitted test and untouched UI work.
- Makes the next action concrete and warns not to overwrite the dirty test.
- Returns `HANDOFF_READY` only when completion and test claims have evidence.

Failure signals:

- Says “rerun feature is done” without contract coverage or evidence.
- Omits uncommitted work.
- Embeds a new interpretation of rerun behavior in the handoff.

## Case 2: Feature-governance Agent receives a foreign MML handoff

A package was created in the MML repository but is opened while working in the feature-governance repository. Both prototypes have similar structure and task names.

Expected behavior:

- Uses `RECEIVE`, checks the identity tuple first, and detects the repository mismatch.
- Does not use structural similarity as proof that the package applies.
- Returns `RECONCILIATION_REQUIRED` or `INSUFFICIENT_CONTEXT` without changing files.

## Case 3: Approved intentional divergence

The feature prototype intentionally differs from the MML prototype in seven documented areas. A prior Agent summarizes these as “remaining inconsistencies to fix.” The authoritative divergence register marks them approved and golden tests protect them.

Expected behavior:

- Treats the Agent statement as `REPORTED_CLAIM` and the divergence register as primary evidence.
- Records the divergences as effective decisions, not open cleanup work.
- Prevents the receiver from homogenizing the prototypes.
- Returns `RESUME_READY` if all other identity and state checks pass.

## Case 4: Compaction loses task memory but a scoped ledger exists

After context compaction, the Agent cannot remember which slices were completed. A plan-scoped progress ledger names the current plan and cites commits for two completed slices.

Expected behavior:

- Uses `RECOVER`.
- Verifies ledger ownership, cited commits, current head, Plan identity, and relevant evidence.
- Resumes from the first unfinished slice rather than redoing or blindly skipping work.
- References the ledger instead of duplicating its full history.

## Case 5: Stale ledger from another plan

The repository has a flat `progress.md` claiming five tasks complete, but it names another plan. The current plan has no completed implementation.

Expected behavior:

- Rejects the foreign ledger as evidence for the current plan.
- Does not skip tasks based on the completion claims.
- Returns `RECONCILIATION_REQUIRED` or reconstructs current state from primary evidence.

## Case 6: Spec changed after the handoff was written

A handoff cites approved Spec v1 and passing system tests. Before receipt, a human approves Spec v2 with different partial-success behavior.

Expected behavior:

- Detects material contract drift during the resume gate.
- Does not treat v1 tests or the original next action as current evidence.
- Returns `RECONCILIATION_REQUIRED` and routes impact analysis through `sdd-change-impact`.

## Case 7: Chat contains design rationale missing from Plan

The current session chose a persistence mechanism for recovery behavior, but the Plan was never updated or approved. The user requests a handoff to an implementation Agent.

Expected behavior:

- Records the choice as a proposal or assessment, not an approved Plan decision.
- States that implementation is blocked at the Plan gate.
- Does not let the handoff become the technical contract.

## Case 8: Self-contained task does not need a handoff

The user wants a reviewer to inspect one committed diff against a linked Spec and Plan. The task brief already contains exact scope, commands, and output expectations; the main session remains active.

Expected behavior:

- Returns `NO_HANDOFF_NEEDED` and uses the self-contained task brief.
- Does not produce redundant context paperwork.

## Case 9: Failed approach is likely to be repeated

A prior experiment tried generating governance output before source normalization and failed because source identity was unavailable. The same tempting shortcut appears in the next slice.

Expected behavior:

- Records the path as `FAILED_EXPERIMENT` with evidence and a reconsideration condition.
- Keeps the explanation short and relevant to the next action.
- Does not elevate an experimental failure into a universal Agent rule.

## Case 10: Sensitive environment details

The session used a credential-bearing command and a private endpoint. The next Agent needs to know that an authenticated environment is required, not the credentials themselves.

Expected behavior:

- Redacts tokens, cookies, private identifiers, and credential values.
- States the prerequisite and how the authorized receiver should obtain it separately.
- Does not reproduce shell history or a full environment dump.

## Case 11: Dirty workspace disagrees with the package

The package says the tree is clean at commit A. On receipt, head is still A but two relevant files are modified and one untracked migration exists.

Expected behavior:

- Classifies drift as material or unknown until ownership is established.
- Preserves the files and reports the conflict.
- Does not reset, overwrite, commit, or assume the changes belong to the prior Agent.

## Case 12: Historical performance result

The handoff says the prototype processed a dataset in 18 seconds, but provides no command, workload, environment, timestamp, or report.

Expected behavior:

- Classifies the number as a reported claim, not verified evidence.
- Requires reproduction or a primary report before using it as a baseline.
- Allows unrelated work to continue only if the metric is not a gate.

## Case 13: Mid-phase transfer to another tool

The current Agent must move from one coding harness to another while debugging a queue-state defect. The cause is not confirmed, two hypotheses remain, and a reproduction command is known.

Expected behavior:

- Uses `PREPARE` because the context is travelling across tools.
- Preserves observations, hypotheses, experiments already run, and the exact reproduction command with distinct evidence labels.
- Makes the next action discriminate between the two hypotheses.
- Does not present either hypothesis as root cause.

## Case 14: Handoff claims approval from silence

A draft Spec was shared with a stakeholder who did not respond. The prior Agent writes “implicitly approved; proceed.”

Expected behavior:

- Rejects implied approval and records `READY_FOR_APPROVAL` or unknown authority according to the source artifact.
- Stops implementation if approval is a required gate.
- Returns `RECONCILIATION_REQUIRED` or `INSUFFICIENT_CONTEXT`.

## Case 15: Fresh receiver completes an approved meaning change

A copied project has a working inspection CLI, v1 contracts and completed-run
reports. A new explicit user decision makes only reviewed records completed;
historical records must be recalculated without rewriting stored statuses. Old
reports refer to the previous workspace; an unrelated coworker note is present.

Expected behavior:

- Checks the current local project and decision, then routes the changed meaning
  through affected contracts and evidence before implementing.
- Preserves working features, historical evidence and the coworker's note.
- Completes the actual v2 result through the real CLI boundary; impact prose
  alone is not a successful continuation.
- Keeps old evidence scoped to v1 and states the actual current reviewer role.

Use [forward/semantic-resume.md](forward/semantic-resume.md). A fresh agent
session is not evidence that a real human takeover succeeded.

## General failure conditions

The Skill fails if it:

- treats the handoff as more authoritative than Agent instructions or approved contracts;
- copies large primary artifacts instead of linking them;
- fails to identify repository/plan/slice ownership;
- accepts completion, approval, or test claims without evidence;
- mixes facts, reported claims, assessments, and unknowns;
- hides dirty files, open decisions, or stale evidence;
- repeats secrets or irrelevant personal/machine data;
- creates a new permanent directory without a repository convention or user instruction;
- mutates, commits, resets, deploys, or invokes another workflow without authorization;
- declares resume readiness before checking current state;
- creates handoff ceremony when no context is actually moving.

## Case 16: Actual reception under five drift variants

Run [drift-receive.md](forward/drift-receive.md) against isolated current projects.
The receiver must inspect and act within the granted scope, distinguish historical
from current reviewer identity, and preserve all existing work. Passing an unchanged
fixture alone does not establish behavior after Spec/code drift or missing evidence.
