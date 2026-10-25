# SDD Verification Design

## Header

```yaml
outcome: VERIFICATION_DESIGN_READY | NEEDS_SPEC | NEEDS_PLAN |
  HUMAN_DECISION_REQUIRED | INSUFFICIENT_BASELINE
primary_mode: FEATURE | BUG_REGRESSION | REFACTOR_SAFETY_NET |
  QUALITY_ATTRIBUTE | SEMANTIC_EVAL
spec_baseline: <path, version, status>
plan_baseline: <path, version, status>
scope: <feature/change/slices>
prepared_at: <timestamp and timezone>
```

## 1. Baseline and limits

- Applicable Agent instructions: ...
- Approved behavior sources: ...
- Technical invariants and interfaces: ...
- Existing test assets and commands inspected: ...
- Historical reports and dates: ...
- Evidence not available: ...
- Explicit non-goals: ...

## 2. Verification strategy

### Evidence lines

| Line | Purpose | Boundary | Default oracle | Gate |
|---|---|---|---|---|
| Deterministic product | ... | ... | ... | ... |
| Real integration | ... | ... | ... | ... |
| DFX | ... | ... | ... | ... |
| Semantic quality | ... | ... | ... | ... |

Delete lines that are genuinely not applicable; do not merge unlike evidence into one pass/fail result.

### Risk priorities

| Risk ID | Failure/consequence | Why likely or hard to detect | Reversibility | Priority | Required evidence |
|---|---|---|---|---|---|
| R-001 | ... | ... | ... | ... | ... |

## 3. Proof-obligation register

| Obligation | Source | Observable proposition | Risk | Evidence line | Status |
|---|---|---|---|---|---|
| VO-001 | FR-... / AC-... / Plan invariant | ... | R-... | Deterministic | DESIGNED |

Allowed evidence status: `DESIGNED | IMPLEMENTED_NOT_RUN | CURRENT_RUN | HISTORICAL | BLOCKED | NOT_APPLICABLE`.

## 4. Contract-to-evidence matrix

| Contract item | Obligation | Case IDs | Layer | Oracle | Data | Environment | Gate | Gap |
|---|---|---|---|---|---|---|---|---|
| FR-... / AC-... | VO-... | VT-... | system | cross-state invariant | minimal-positive | offline Linux | PR | ... |

Every mandatory item needs an evidence route or an explicitly approved deferral.

## 5. Case portfolio

### VT-001 — <behavioral name>

- Traces to: ...
- Risk and failure prevented: ...
- Layer and why it is the lowest faithful layer: ...
- Setup/preconditions: ...
- Stimulus: ...
- Oracle and assertions: ...
- Negative or counterexample: ...
- Test double and contract: ...
- Data/fixture identity: ...
- Isolation and cleanup: ...
- Environment/marker: ...
- Expected command or runner: ...
- Frequency/gate: ...
- Evidence retained: ...
- Sensitivity check, if high risk: ...

Repeat for cases whose differences affect setup, oracle, layer, or diagnosis. Parameterize simple input variants instead of copying the whole case.

## 6. Test-double contracts

| External boundary | Real protocol assumed | Substitute scenarios | Contract protection | What it cannot prove | Real smoke |
|---|---|---|---|---|---|
| ... | ... | success/transient/blocking/malformed/hang | CT-... | semantic quality | SM-... |

## 7. Data design

| Data ID | Class | Triggered behavior | Construction/source | Sensitive? | Version/hash | Output isolation |
|---|---|---|---|---|---|---|
| DATA-001 | minimal positive | ... | deterministic factory | no | ... | temporary root |

Keep minimal, representative, semantic-eval, and scale data separate.

## 8. Environment matrix

| Environment | Obligations/cases | Dependency mode | Frequency | Owner | Current coverage |
|---|---|---|---|---|---|
| Offline development | ... | substitute | per change | ... | ... |
| Linux release | ... | real/minimal | release | ... | ... |
| Windows release | ... | real/minimal | release | ... | ... |

## 9. Quality-attribute protocol

Include only when applicable.

```yaml
version_and_commit: ...
working_tree_state: ...
dataset_id_and_hash: ...
workload_and_denominator: ...
dependency_or_model_identity: ...
concurrency: ...
timeouts_and_retries: ...
host_and_network: ...
repetitions: ...
metrics_and_percentiles: ...
regression_threshold: ...
resource_or_error_budget: ...
evidence_retention: ...
```

State which conditions would make results incomparable.

## 10. Gates and failure triage

| Gate | Included evidence | Excluded/why | Failure owner routing | Blocking rule |
|---|---|---|---|---|
| Local | affected DT + contract | real model/cost | product/test/fixture | ... |
| PR | offline suite + affected system | scale | ... | ... |
| Scheduled | UI/stability/env | ... | ... | ... |
| Release | smoke/DFX/semantic | ... | ... | ... |

Do not call a subset “full”. Preserve failures as product, contract, test, data, environment, semantic, DFX, or unavailable evidence.

## 11. Gaps and decisions

| Item | Type | Owner | Blocking effect | Required decision/evidence |
|---|---|---|---|---|
| ... | SPEC / PLAN / THRESHOLD / ENVIRONMENT / COST / RISK | ... | ... | ... |

## 12. Next action

- Smallest next action: ...
- Integration point with Plan/slice: ...
- Human review required: ...
- After implementation, convergence evidence expected: ...
