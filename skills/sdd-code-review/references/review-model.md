# Baseline-less Code Review Model

Use this model to keep reviews consistent across projects. Project-specific severity or review policies take precedence when they are stricter. This model deliberately reuses the vocabulary of `sdd-converge-review`'s review model (evidence labels, severity scale) so findings can travel between the two skills without translation.

## 1. Relationship to convergence review

| | `sdd-converge-review` | `sdd-code-review` |
|---|---|---|
| Baseline | Approved Spec / Plan / Tasks exist | No approved specification governs the subject |
| Question | Does the implementation converge with its contracts? | What engineering risks does this code carry? |
| Coverage | Contract coverage matrix, mandatory-item verdicts | Finding list; no requirement-coverage claim |
| Decision | CONVERGED / NOT_CONVERGED / … | REVIEW_COMPLETE (a delivered review, not an approval) |
| Product meaning | Judged against the approved Spec | Never judged; surfaced as `OPEN_PRODUCT_QUESTION` |

A review of contracted work must go to convergence review. A request to "review this PR" where an approved Spec exists for that change is `SPEC_BASELINE_FOUND`, not a lighter path around the contract.

## 2. Evidence Types

Label important statements so observation and interpretation do not blur.

| Type | Meaning | Example |
|---|---|---|
| `FACT` | Directly observed in the diff, file, command output, or repository state | `handlers/upload.py:88` joins a user-supplied path without normalization |
| `ASSESSMENT` | Reviewer interpretation derived from one or more facts | Uploaded filenames can escape the target directory on platforms where `..` survives |
| `UNKNOWN` | Evidence is absent, stale, contradictory, or could not be obtained | Behavior under concurrent uploads was not run and cannot be established by reading |

Every finding records its evidence basis:

| Basis | Meaning |
|---|---|
| `READ` | Established by reading code/config only; runtime behavior not exercised |
| `RUN` | Established by a command executed during this review, with recorded result |
| `REPORTED` | Taken from the author's description, CI status, or issue text; not independently checked |

A `RUN` fact outranks a `READ` fact about runtime behavior. A `READ`-only review must say so in its header, not in a footnote.

## 3. Declared Intent

Without a Spec, "what was this supposed to do" is reconstructed from intent sources. Classify, never promote to authority:

| Level | Source | Weight |
|---|---|---|
| `TEST_ASSERTED` | An existing test actually asserts the behavior | Strongest available intent signal; still written by the same authors |
| `DOCUMENTED` | README, docstring, ADR, or API docs state the behavior | Explains intent; may be stale |
| `COMMIT_STATED` | Commit message or PR description states the purpose | Explains intent; often incomplete |
| `UNKNOWN` | No source expresses the intended behavior | Findings must not assume one |

Do not convert any intent level into a requirement. A test asserting wrong behavior is a finding about the test, not proof of correctness. When intent is `UNKNOWN` and the behavior matters, record an `OPEN_PRODUCT_QUESTION`.

## 4. Finding Severity

Severity expresses consequence, not implementation effort. A one-line defect can be `BLOCKER`; a large refactor can be `LOW`.

| Severity | Use when |
|---|---|
| `BLOCKER` | Data loss, serious security exposure, corruption, or a defect certain to break a primary workflow |
| `HIGH` | A correctness or security defect on an important path, likely to trigger under realistic use, with significant impact |
| `MEDIUM` | Bounded correctness, compatibility, observability, or maintainability risk; main workflow can complete |
| `LOW` | Minor risk, clarity issue, or local improvement with no immediate delivery impact |

Without a contract, "certain to break" and "likely" are assessments: cite the facts that justify the rating and downgrade honestly when usage frequency is unknown.

## 5. Finding Record

| Field | Required content |
|---|---|
| ID | Stable identifier such as `CR-001` |
| Severity | BLOCKER / HIGH / MEDIUM / LOW |
| Pass | Correctness / Security and robustness / Change-risk maintainability / Test quality / Hidden assumptions |
| FACT | Exact file/line, command result, or observed behavior, with evidence basis (READ / RUN / REPORTED) |
| ASSESSMENT | What is wrong and why, citing the facts |
| Consequence | Concrete user, data, security, operation, or maintenance impact |
| Suggestion | Smallest safe direction of fix; not a redesign |
| Intent reference | Which declared-intent source (if any) the behavior contradicts |

Avoid combining unrelated problems into one finding. Combine repeated instances only when they share the same cause, consequence, and fix direction.

## 6. OPEN_PRODUCT_QUESTION

Record as a question, never as a defect or a decision:

- the observed behavior;
- the viable interpretations found in intent sources (or their absence);
- what changes depending on the answer;
- why it cannot be settled by reading more code.

Route it to the requirements workflow when the user chooses to formalize the work. Do not let the volume of questions turn a review into an interrogation — cap at what materially changes risk or fixes.

## 7. Routing Rules

| Discovery during review | Route |
|---|---|
| An approved Spec/convergence baseline governs the subject | `SPEC_BASELINE_FOUND` → `sdd-converge-review` |
| Unresolved product behavior that matters | `OPEN_PRODUCT_QUESTION` → requirements workflow (user decides) |
| Structural problem that local patches will worsen | Note in finding; suggest planning route instead of recommending another patch |
| Fixes wanted | Recognize an existing explicit repair request; conclude this read-only review, then hand off to the authorized implementation workflow without requesting the same permission again. If no repair authorization exists, stop after the findings. |
| Adjacent out-of-scope issues | List; do not expand the review |

## 8. Gate Rules

- A reading review cannot verify runtime behavior; claims about execution must be `RUN` or remain `ASSESSMENT`/`UNKNOWN`.
- Passing checks do not erase `READ`-based findings; green tests do not certify unasserted behavior.
- Silent conversions are forbidden: "not run" never becomes "pass"; `REPORTED` never becomes `FACT` without checking.
- Existing tests count as evidence only for what they actually assert.
- Secrets found in code are referenced by location, never reproduced in the report.
- Findings without a concrete consequence are dropped or downgraded to `LOW` clarity notes; style preference is not a finding.
- The review reports the subject as it is; it does not approve, merge, or promise quality.
