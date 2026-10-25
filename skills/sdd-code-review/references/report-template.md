# Code Review Report Template

Adapt this template to the repository. Preserve the outcome, evidence labels, severity, and scope semantics; omit empty optional sections instead of filling them with boilerplate.

```markdown
# Code Review

## Header

**Outcome:** REVIEW_COMPLETE | SPEC_BASELINE_FOUND | NO_MATERIAL_CODE_CHANGE | INSUFFICIENT_SCOPE
**Mode:** DIFF | AREA
**Subject:** <repository, diff range / commits / paths>
**Scope boundary:** <what is in and out of this review>
**Evidence basis:** READ-ONLY | READ + RUN (checks listed below)

## Baseline Used

| Source | Detail | Weight |
|---|---|---|
| Agent rules | <AGENTS.md path, applicable scope> | applicable constraint |
| Declared intent | <tests / docs / commit messages referenced> | TEST_ASSERTED / DOCUMENTED / COMMIT_STATED / UNKNOWN |
| Approved contract | none found | this is a baseline-less review |

## Findings

### CR-001 — <short consequence-focused title>

- **Severity:** BLOCKER | HIGH | MEDIUM | LOW
- **Pass:** Correctness | Security | Maintainability | Test quality | Hidden assumptions
- **FACT:** <file:line, command result, observed behavior> (READ | RUN | REPORTED)
- **ASSESSMENT:** <what is wrong and why>
- **Consequence:** <concrete impact>
- **Suggestion:** <smallest safe fix direction>
- **Intent reference:** <contradicted intent source, if any>

### Summary

| Severity | Count |
|---|---:|
| BLOCKER | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |

## Checks Run

| Check | Exact command | Result | Note |
|---|---|---|---|
| Focused tests | `<command>` | PASS / FAIL / NOT RUN | <failure classification> |
| Type / lint | `<command>` | PASS / FAIL / NOT RUN | <scope> |

## Open Product Questions

| # | Observed behavior | Interpretations | What changes | Suggested route |
|---|---|---|---|---|
| Q1 | <behavior> | <options or UNKNOWN intent> | <impact of the choice> | requirements |

## Out-of-Scope Observations

- <adjacent issue noticed; not part of this review>

## Recommended Next Actions

1. <bounded fix authorization for CR-…, owner: user>
2. <route for OPEN_PRODUCT_QUESTION or structural findings, if the user chooses>
```

## Compact Response Form

For a small review, a durable file may be unnecessary. Keep the same semantics in a shorter response:

```markdown
Outcome: REVIEW_COMPLETE (READ-ONLY) — diff 4f2a..9c11, 6 files.

Findings
1. [HIGH][Security] CR-001 uploaded filename escapes target dir
   FACT: upload.py:88 (READ); ASSESSMENT: `..` survives join on POSIX; Consequence: arbitrary overwrite; Suggestion: normalize + allowlist root.
2. [MEDIUM][Test quality] CR-002 rerun test asserts call count only
   FACT: test_rerun.py:31 (READ); …

Open product question: retry policy on partial failure — intent UNKNOWN.
Checks: none run (not authorized). Next: authorize fixes separately.
```
