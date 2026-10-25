# Convergence Report Template

Adapt this template to the repository. Preserve the decision, evidence labels, coverage status, return stage, and human-gate semantics; omit empty optional sections instead of filling them with boilerplate.

```markdown
# Convergence Review

## Decision

**Decision:** CONVERGED | NOT_CONVERGED | INSUFFICIENT_EVIDENCE | HUMAN_DECISION_REQUIRED

**Primary reason:** <one evidence-backed sentence>

**Next loop:** SPEC | PLAN | IMPLEMENT | FINISH | HUMAN GATE

## Review Baseline

| Artifact | Reviewed baseline | Authority / limitation |
|---|---|---|
| AGENTS.md | <path, revision> | <applicable scope> |
| Spec | <path, version> | <signed/current/stale/unknown> |
| Plan / ADR | <paths> | <current/conflicting/missing> |
| Tasks | <path> | <reviewed scope> |
| Implementation | <commit/diff/paths> | <working tree limitations> |
| Verification | <commands/reports/date> | <fresh/historical/blocked> |

## Material Findings

### CVG-001 — <short outcome-focused title>

- **Severity:** BLOCKER | HIGH | MEDIUM | LOW
- **Contract:** <requirement or rule>
- **FACT:** <file:line, command result, report, or observed behavior>
- **ASSESSMENT:** <why the evidence does not converge>
- **Consequence:** <concrete impact>
- **Return stage:** SPEC | PLAN | IMPLEMENT | FINISH
- **Closure evidence:** <what must be observed to close it>

## Contract Coverage

| Contract item | Implementation evidence | Verification evidence | Status | Gap / return stage |
|---|---|---|---|---|
| FR-01 <summary> | <file:line> | <test/report> | VERIFIED | — |
| FR-02 <summary> | <file:line> | <test/report> | PARTIAL | <gap> / IMPLEMENT |

### Coverage Summary

| Status | Count |
|---|---:|
| VERIFIED | 0 |
| PARTIAL | 0 |
| MISSING | 0 |
| CONTRADICTED | 0 |
| UNREQUESTED | 0 |
| UNVERIFIABLE | 0 |
| NOT_APPLICABLE | 0 |

## Verification Evidence

| Check | Exact command or source | Result | Currency / limitation |
|---|---|---|---|
| Focused tests | `<command>` | PASS / FAIL / BLOCKED | <fresh, date> |
| Full suite | `<command>` | PASS / FAIL / HUNG / NOT RUN | <details> |
| Integration/E2E | <command/report> | <result> | <environment> |
| Semantic eval | <dataset/rubric> | <result> | <sample and judge limits> |
| Performance | <report> | <result> | <workload boundary> |

## Evidence Limits and Unknowns

- UNKNOWN: <missing, stale, contradictory, or blocked evidence>

## Residual Risks and Human Decisions

| Risk or decision | Evidence | Owner | Required action |
|---|---|---|---|
| <item> | <fact> | <role/person> | Accept / reject / clarify |

## Smallest Next Loop

1. <highest-priority closure action>
2. <verification that proves closure>
3. Re-run convergence review for the affected contract rows.
```

## Compact Response Form

For a small change, a durable file may be unnecessary. Keep the same semantics in a shorter response:

```markdown
Decision: NOT_CONVERGED — FR-03 recovery is implemented but has no restart evidence.

Findings
1. [HIGH][IMPLEMENT] FR-03 ...
   FACT: ...
   ASSESSMENT: ...
   Closure: ...

Coverage: 8 VERIFIED, 1 PARTIAL, 0 MISSING, 1 UNVERIFIABLE.
Verification: focused tests pass; restart scenario not run.
Next loop: add restart integration evidence, then re-review FR-03 only.
```
