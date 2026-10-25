# Context Handoff Model


## Contents

- [1. Handoff is a pointer layer](#1-handoff-is-a-pointer-layer)
- [2. Information authority](#2-information-authority)
- [3. What belongs in the package](#3-what-belongs-in-the-package)
- [4. Handoff versus adjacent artifacts](#4-handoff-versus-adjacent-artifacts)
- [5. Boundary decision](#5-boundary-decision)
- [6. Identity tuple](#6-identity-tuple)
- [7. Freshness and drift](#7-freshness-and-drift)
- [8. Resume gate](#8-resume-gate)
- [9. Negative knowledge](#9-negative-knowledge)
- [10. Minimum viable handoff](#10-minimum-viable-handoff)


Use this model to decide what belongs in a handoff, how much to trust it, and whether continuation is safe.

## 1. Handoff is a pointer layer

The SDD artifact chain remains authoritative:

```text
Agent rules
  -> approved Spec
  -> approved Plan and ADRs
  -> Tasks and current execution card
  -> repository state and implementation
  -> tests and eval evidence
  -> convergence and Finish evidence
```

The handoff points into this chain and adds transient state that the durable contracts normally do not hold. It must not restate enough content to become a competing contract.

## 2. Information authority

| Level | Type | Examples | Receiver treatment |
|---|---|---|---|
| 1 | Applicable authority | Agent rules, explicit human approval, approved Spec/Plan | Read directly; conflicts block continuation |
| 2 | Observable repository evidence | Commit, current diff, code, reproducible test output | Verify identity and freshness |
| 3 | Verified handoff claim | Claim checked against a cited Level 1/2 source | Useful navigation; source still wins |
| 4 | Reported claim | Prior Agent statement, historical result, conversation memory | Recheck before relying on it |
| 5 | Assessment | Rationale, suspected cause, recommendation | Evaluate independently |
| 6 | Unknown | Missing status, unclear owner, unavailable environment | Preserve explicitly; do not infer |

A more recent handoff does not outrank an older approved contract. Recency affects freshness, not authority.

## 3. What belongs in the package

Include information when at least one is true:

- it tells the receiver which primary source controls;
- it prevents work from being repeated, skipped, overwritten, or performed in the wrong workspace;
- it preserves a material rationale not captured in an approved artifact;
- it identifies an unfinished state, decision gate, safety boundary, or known hazard;
- it makes the next action independently executable.

Exclude:

- general project introductions already in README or INDEX;
- full chat history, full diffs, large logs, or copied contract text;
- speculative future tasks unrelated to the next objective;
- generic coding advice already in Agent instructions;
- credentials, tokens, cookies, private personal data, or unnecessary machine details;
- “everything that happened” chronology when current state and decisions are enough.

## 4. Handoff versus adjacent artifacts

| Need | Correct artifact |
|---|---|
| Define desired product behavior | Spec |
| Define architecture and implementation strategy | Plan / ADR |
| Decompose approved work | Tasks / execution card |
| Record frequent execution progress | Plan-scoped progress ledger |
| Analyze downstream consequences of change | Change-impact report |
| Prove completed implementation matches contracts | Convergence report |
| Move/reconstruct active context across a boundary | Context handoff |

A handoff may reference all of these but owns none of their semantics.

## 5. Boundary decision

Prefer, in order:

1. **Continue** when the next phase needs the current reasoning as a primary source and usable context remains.
2. **Clear** when the current context is irrelevant to the next work.
3. **Handoff** when context must move to another session, Agent, tool, person, directory, or repository.
4. **Delegate from a self-contained brief** when a bounded task can run separately and the main context should remain intact.
5. **Compact/recover** when the same work continues but context capacity or interruption requires reconstruction.

This order is guidance, not a permission model. The environment may provide different context mechanisms.

## 6. Identity tuple

A package should be uniquely associated with:

```text
repository root
+ worktree/workspace
+ branch or revision
+ plan/change identifier
+ slice/task identifier
+ contract baseline
```

Not every field exists in every project. The remaining fields must still distinguish the package from concurrent work. A package with the right repository but the wrong plan is foreign.

## 7. Freshness and drift

Mark package freshness using its creation time plus evidence anchors. On receipt, compare:

- Agent instruction changes;
- Spec/Plan approval version or content hash;
- branch and head movement;
- dirty and untracked files;
- completion ledger updates;
- test/eval environment or dependency changes;
- new human decisions and review findings.

Classify drift:

- `NONE`: anchors and relevant state match.
- `EXPECTED`: cited work advanced in the stated direction; refresh is enough.
- `MATERIAL`: contract, scope, identity, completed-work claim, or safety boundary differs.
- `UNKNOWN`: freshness cannot be established.

`MATERIAL` leads to `RECONCILIATION_REQUIRED`. `UNKNOWN` leads to reconciliation or `INSUFFICIENT_CONTEXT`, depending on whether primary sources can resolve it.

## 8. Resume gate

`RESUME_READY` requires all of the following:

- package identity matches the active workspace and objective;
- applicable Agent instructions were re-read;
- authoritative contract baselines exist and match or have an explained, accepted update;
- claimed completed work is supported by observable evidence;
- current dirty state is understood and will not be overwritten;
- unresolved product, authority, security, migration, or scope decisions are not hidden;
- one bounded next action and its stop conditions are clear.

Do not require all historical details. Require enough current truth to avoid a confidently wrong continuation.

## 9. Negative knowledge

Record a rejected path only when its repetition is plausible and costly. Use:

```text
Rejected path: <approach>
Status: REJECTED | SUPERSEDED | FAILED_EXPERIMENT
Reason: <contract decision or observed failure>
Evidence: <source>
Reconsider only if: <condition>
```

Do not turn an untested preference into a rejected path.

## 10. Minimum viable handoff

For a small continuation, the package may contain only:

- identity and objective;
- three to five ordered source pointers;
- current verified state;
- unresolved decision or hazard, if any;
- one next action and stop conditions;
- receipt checklist.

Add detail in proportion to drift risk, parallel work, irreversibility, and the cost of rediscovery.
