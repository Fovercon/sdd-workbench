---
name: sdd-code-review
description: Review a concrete diff, commit range, pull request, or code area for correctness, security, robustness, and change-relevant maintainability when no approved specification baseline governs the work. Use for ad-hoc, pre-merge, or hand-off reviews of code outside a converging SDD change. Do not use to judge specification compliance or convergence, to modify code, or to approve merges and releases.
---

# SDD Code Review

Deliver an evidence-backed engineering review of code that has no approved specification baseline. The absence of a Spec means this review judges engineering quality and **declared intent** — never invented product requirements — and therefore cannot conclude convergence, requirement coverage, or release readiness.

Read [references/review-model.md](references/review-model.md) before assigning severity, labeling evidence, or routing findings. Use [references/report-template.md](references/report-template.md) when a durable review report is requested or the repository has no established review format.

## Boundaries

- Locate and obey applicable `AGENTS.md`, `Agent.md`, and scoped repository rules before reviewing.
- This is a review workflow. Do not modify code, tests, configuration, specifications, or external systems; fixing findings is a separately authorized action.
- Do not invent requirements. Judge against engineering correctness, repository rules, and declared intent (tests, documentation, commit messages, linked issues), each labeled as intent evidence rather than authority.
- If an approved specification or convergence baseline governs the review subject, stop and route to `sdd-converge-review`; do not perform a weaker review of contracted work.
- Do not claim convergence, requirement coverage, or release readiness, and do not approve, merge, publish, or deploy.
- Separate what was read from what was run. A reading review cannot verify runtime behavior; never convert "not run" into a pass.
- Review the requested subject. Record out-of-scope observations as such instead of expanding into a repository-wide audit.
- Do not paste secrets, credentials, or private data found in the reviewed code into the report; reference their location.
- Report findings about code and risk, not about authors. No blame attribution.
- Respect workspace boundaries: do not stash, reset, checkout, or clean anything to obtain a reviewable state.

## Select a mode

Choose one and state it:

- `DIFF`: review a named changeset — working-tree diff, staged changes, commit range, or pull request.
- `AREA`: review a module, file, or functional area without a single changeset, for example during hand-off, onboarding, or a risk survey.

If the user cannot or will not pin down a subject, return `INSUFFICIENT_SCOPE` instead of reviewing whatever is nearby.

## Workflow

### 1. Establish the review subject and question

Record:

- exact repository/worktree and the precise diff range, commits, or paths under review;
- what the user wants from the review — pre-merge gate, defect hunt, hand-off orientation, or focused concern;
- the review depth expectation and any time or scope bounds;
- whether running safe checks (tests, linters, type checks) is authorized.

Check whether an approved Spec, Plan, or convergence record governs the subject. If it does, return `SPEC_BASELINE_FOUND` and name the baseline; contracted work deserves convergence review, not a baseline-less substitute.

Return `INSUFFICIENT_SCOPE` when the subject cannot be distinguished (for example "review my code" with multiple active branches and no named target).

### 2. Load applicable rules and declared intent

Inspect only what is needed:

1. applicable Agent instructions and repository conventions;
2. the full diff or area under review, plus surrounding code, callers, and data flow needed to judge it;
3. related tests, fixtures, and their assertions;
4. declared intent: docstrings, README, ADRs, commit messages, and linked issues.

Classify each piece of declared intent using the review model (for example `TEST_ASSERTED`, `DOCUMENTED`, `COMMIT_STATED`, `UNKNOWN`). Declared intent explains what the author meant; it does not prove the behavior is correct, complete, or desired.

### 3. Read the change completely before judging

Understand before finding:

- what the change does mechanically, including generated or vendored portions identified as such;
- how errors, state, and data flow through the touched boundaries;
- which existing behavior the change relies on or silently alters;
- what the related tests actually assert, not what their names claim.

Do not report on files not read, and do not guess at contents of large generated artifacts — mark them `UNKNOWN` when they matter.

### 4. Run the engineering review passes

Keep passes separate to reduce anchoring. Report only evidence-backed findings; attach a concrete consequence to each.

**Correctness pass:** logic and boundary errors, unhandled or swallowed errors, state and data consistency, concurrency and ordering, resource lifecycle, off-by-one and null/empty handling.

**Security and robustness pass:** untrusted input handling, injection, path handling, authorization gaps, secrets in code or logs, unsafe deserialization, weak cryptography, and failure behavior under malformed input.

**Change-risk maintainability pass:** maintainability findings only when they create concrete future change risk (misleading names, hidden coupling, duplicated invariants that will drift). No style nits, no speculative redesign, no personal-taste architecture.

**Test quality pass:** tests that mirror the implementation instead of the intent, missing critical or failure paths, weakened or skipped assertions, and assertions that cannot fail for the right reason.

**Hidden-assumption pass:** environment and platform assumptions (paths, encodings, locales, time), generated-state pollution, dependency drift, and performance traps on realistic data volumes.

### 5. Verify what can be verified

When the user authorized running checks and repository policy permits:

- run safe, relevant, focused checks (targeted tests, type check, linter on touched files);
- record the exact command, result, and environment;
- classify failures before reporting them: caused by the reviewed change, pre-existing, environment, or indeterminate;
- never rerun until green without explanation, and never present a subset as the full suite.

When nothing was run, state that plainly in the report. A read-only review is legitimate; a read-only review disguised as tested is not.

### 6. Classify and record findings

Use the severity scale from the review model (`BLOCKER` / `HIGH` / `MEDIUM` / `LOW`). Severity expresses consequence, not effort — a one-line defect can be `BLOCKER`.

Every material finding contains:

- stable ID (for example `CR-001`) and severity;
- `FACT`: exact file/line, command result, or observed behavior;
- `ASSESSMENT`: what is wrong and why, citing the facts;
- consequence: concrete user, data, security, or maintenance impact;
- bounded suggestion: the smallest safe direction of fix, not a rewrite;
- confidence and evidence basis: read-only or run-verified.

Behavior that looks wrong but is actually an unresolved product choice is recorded as an `OPEN_PRODUCT_QUESTION` for the requirements route — it is not a defect, and the reviewer does not resolve it by picking an interpretation.

### 7. Route findings and close

- Findings that need fixes: the user authorizes repair separately; this skill does not edit.
- Structural problems that will outgrow local patches: suggest the planning route rather than recommending another local patch.
- `OPEN_PRODUCT_QUESTION` items: suggest the requirements route.
- Out-of-scope issues observed during review: listed, not expanded into this review.

Recommend — do not start — any follow-up workflow.

## Outcomes

Return exactly one:

- `REVIEW_COMPLETE`: findings are delivered with severity, evidence, scope, and evidence limits stated;
- `SPEC_BASELINE_FOUND`: the subject is governed by an approved SDD contract; use `sdd-converge-review` instead;
- `NO_MATERIAL_CODE_CHANGE`: the subject contains no reviewable semantic code change (documentation-only, formatting-only, or fully generated changes); report what was checked;
- `INSUFFICIENT_SCOPE`: the review subject, version, or boundary cannot be established.

`REVIEW_COMPLETE` is a delivered review, not a quality approval. It does not authorize merges, releases, or any code change.

## Output contract

Return or create:

1. outcome, mode, review subject, and scope boundary;
2. applicable rules and declared-intent baseline used;
3. findings ordered by severity, each with FACT, ASSESSMENT, consequence, bounded suggestion, and evidence basis;
4. verification evidence actually run, with commands and results, and checks not run;
5. `OPEN_PRODUCT_QUESTION` items and out-of-scope observations;
6. recommended bounded next actions.

Default to returning the review in the response. When a durable artifact is requested or the repository has an established location, use the report template; do not invent a permanent review directory.

## References

- Severity, evidence labels, declared intent, passes, and routing rules: [references/review-model.md](references/review-model.md)
- Durable review report template: [references/report-template.md](references/report-template.md)
- Behavioral evaluation cases: [evals/cases.md](evals/cases.md)
