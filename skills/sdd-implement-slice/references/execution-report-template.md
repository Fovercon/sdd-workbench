# Slice Execution Receipt

## Compact record

For a small slice, append one receipt with a stable ID/revision to an existing
process log. Reference the exact current card and baseline record instead of
copying their unchanged fields. Use this shape; expand the sections below only
for information the referenced records or compact receipt cannot carry:

```markdown
## receipt-s02-v1
- Outcome / slice / mode / start-end: <actual state and timestamps>
- Card / authority / contract: <exact record IDs, versions/hashes and exclusions>
- Workspace baseline: <root, branch/head or file identity, relevant dirty state>
- Actual surface / deviations: <changed files, card validation and impact>
- Checks: <RED or baseline, GREEN, regression: command, cwd, exit/result,
  raw output record, source/environment identity, skips and limits>
- Findings / risks: <including wrong-failure attempts, classification and route>
- Closure / next: <stop-condition evidence, task update, remaining action>
```

Keep original failed output and superseded receipts reachable; a planning-only
card does not gain implementation authority from a receipt. On resume, verify
the referenced card, contracts and files before reusing evidence. Progress must
not change frozen Spec/Plan. If a checkpoint hashes a receipt's entire file,
freeze that file and use separate receipts; appending to it invalidates the old
reference. Navigation IDs do not replace hashes or renew checks.

## Header

```yaml
outcome: SLICE_COMPLETE | NEEDS_SPEC | NEEDS_PLAN |
  HUMAN_DECISION_REQUIRED | WORKSPACE_RECONCILIATION_REQUIRED |
  ENVIRONMENT_BLOCKED | SLICE_INCOMPLETE
slice_id: <Sxx>
objective: <one observable behavior>
execution_mode: RED_GREEN | CHARACTERIZE_PRESERVE | BEFORE_AFTER
started_at: <timestamp and timezone>
finished_at: <timestamp and timezone or not finished>
authorization: <exact implementation authority and excluded actions>
```

## 1. Contract and workspace baseline

| Item | Identity/status | Evidence |
|---|---|---|
| Agent instructions | ... | path/scope |
| Spec | ... | approved version/hash |
| Plan | ... | approved version/hash |
| Tasks/slice | ... | dependency state |
| Execution card | ... | version/time |
| Verification design | ... | obligations/cases |
| Repository/worktree | ... | resolved root |
| Branch/head | ... | source anchor |
| Starting dirty state | ... | relevant status/diff |
| Ledger/handoff | ... | identity/currentness |

Explicit non-goals/later slices: ...

## 2. Card validation

- Objective and stop condition executable: ...
- Paths/symbols/commands verified: ...
- Stale mechanical details corrected: ...
- Contract or design gaps: ...
- Selected mode and rationale: ...

## 3. Change surface

| Path/symbol | Class | Intended change | Actual change | Ownership/conflict |
|---|---|---|---|---|
| ... | REQUIRED / SUPPORTING / MECHANICAL_DEVIATION / UNRELATED | ... | ... | ... |

Unexpected generated/temporary state: ...

## 4. Pre-change evidence

### RED or baseline check

| Obligation | Command/observation | Expected | Actual | Validity conclusion |
|---|---|---|---|---|
| VO-... | ... | expected assertion failure/current golden | ... | valid RED / wrong failure / baseline green |

Do not omit a passing-immediately or wrong-failure investigation.

## 5. Implementation cycles

| Cycle | Behavior increment | Production change | Test/evidence change | GREEN result | Refactor |
|---|---|---|---|---|---|
| 1 | ... | ... | ... | ... | ... |

## 6. Verification evidence

| Role | Contract/case | Exact command or observation | Result | Baseline/environment | Limits/skips |
|---|---|---|---|---|---|
| focused GREEN | ... | ... | PASS/FAIL/BLOCKED | ... | ... |
| contract | ... | ... | ... | ... | ... |
| system/UI/eval | ... | ... | ... | ... | ... |
| full regression | ... | ... | ... | ... | ... |

Checks not run and why: ...

## 7. Findings and routing

| Finding | Classification | Evidence/consequence | Load-bearing? | Action/route |
|---|---|---|---|---|
| ... | SLICE_REGRESSION / PREEXISTING_FAILURE / TEST_OR_FIXTURE_DEFECT / ENVIRONMENT_FAILURE / CONTRACT_DISCOVERY / OUT_OF_SCOPE_FINDING | ... | yes/no | ... |

## 8. Slice closure

- Observable outcome demonstrated by: ...
- Stop condition: satisfied / not satisfied
- Mandatory evidence current: ...
- Scope remained bounded: ...
- Existing user work preserved: ...
- Deviations and authority: ...
- Remaining non-blocking risks: ...
- Task/ledger update: ...
- Commit status: not requested / authorized and recorded / not created

## 9. Next action

- Recommended next slice or convergence step: ...
- Do not begin automatically: ...
- Human/upstream decision needed: ...
