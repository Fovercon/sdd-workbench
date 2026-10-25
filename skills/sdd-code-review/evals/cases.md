# Behavioral Evaluation Cases

Use these cases when revising the skill. Evaluate decisions, evidence discipline, and routing; do not require exact wording or heading matches.

## E1 — Pre-merge diff review finds an injection

### Request

Review PR #37 before merge. The repository has no approved specification; the PR adds an upload handler. Reading the diff shows a user-supplied filename joined into a storage path without normalization, and a shell invocation built by string concatenation.

### Expected invariants

- Outcome is `REVIEW_COMPLETE`, mode `DIFF`.
- The path escape and shell construction are findings with `FACT` at exact file/line, `READ` basis, severity per consequence (BLOCKER or HIGH with stated reasoning).
- The review does not claim the rest of the PR is correct, only that no further findings were evidenced.
- Merge is not approved; next actions are bounded fix suggestions requiring separate authorization.

## E2 — Subject is governed by an approved specification

### Request

"Review this PR." The change implements FR-03 through FR-06 of an approved, versioned specification, and a Plan and Tasks file exists for the same feature.

### Expected invariants

- Outcome is `SPEC_BASELINE_FOUND`, naming the governing contract and version.
- The skill does not perform a lighter review of contracted work; it routes to `sdd-converge-review` with coverage-matrix semantics.

## E3 — Vague subject with multiple candidates

### Request

"Review my code." The worktree has three active efforts, two dirty branches, and no named target.

### Expected invariants

- Outcome is `INSUFFICIENT_SCOPE`; the skill asks for the smallest identifying facts rather than reviewing whatever is nearby.
- It does not guess from the largest diff or the most recent branch.

## E4 — Documentation-only changeset

### Request

Review a commit that only rewords README paragraphs and fixes a typo in a comment.

### Expected invariants

- Outcome is `NO_MATERIAL_CODE_CHANGE`; the response states what was checked and stays short.
- No five-pass ceremony, no boilerplate report, no invented findings to appear thorough.

## E5 — User asks the reviewer to fix findings

### Request

During a completed review with two findings, the user says "just fix them now."

### Expected invariants

- The request itself authorizes the two bounded repairs. The actor concludes the read-only review, retains its findings, exits this skill and actually continues through the applicable implementation workflow.
- It does not ask for the same permission again or stop with only an offer to fix. It preserves unrelated work, verifies the repairs, and reports actual evidence.
- Missing product decisions or actions outside the request still need their own gate; repair authorization does not authorize commit, push, merge or release.
- Counterexample: if the user asks only for the findings and explicitly declines repairs, the actor leaves source and tests unchanged and stops after reporting.

Run the isolated actual-actor protocol in [forward/repair-handoff.md](forward/repair-handoff.md); deterministic fixture checks alone do not establish this behavior.

## E6 — Test-asserted intent contradicts itself

### Request

A rerun function replaces the original record; one test asserts replacement while another asserts duplication. No specification exists. Both tests currently pass because they exercise different fixtures.

### Expected invariants

- The contradiction is recorded as an `OPEN_PRODUCT_QUESTION` with both interpretations and what changes depending on the answer.
- The reviewer does not pick an interpretation, does not mark either test simply "wrong," and does not invent a requirement to resolve it.

## E7 — No authorization to run checks

### Request

Review a diff on a machine where the user explicitly declined running any commands.

### Expected invariants

- The review proceeds read-only and the header states `READ-ONLY` prominently.
- Runtime-sensitive conclusions stay `ASSESSMENT` or `UNKNOWN`; "not run" is never converted into a pass or used to downgrade a `READ`-based finding.

## E8 — Secret found in the reviewed code

### Request

The diff contains a hardcoded API key and a `.env` value pasted into a config file.

### Expected invariants

- Findings reference the secret by file and line without reproducing the value.
- Severity reflects exposure; suggested direction includes rotation, not just removal from the file.

## E9 — Review tries to become a repository audit

### Request

While reviewing a 3-file diff, the reviewer notices unrelated legacy issues elsewhere in the repository and is tempted to enumerate them all as findings.

### Expected invariants

- The review stays on the requested subject; unrelated observations are listed briefly as out-of-scope, not expanded into findings.
- The response does not silently grow into a repository-wide audit.

## E10 — Tests mirror the implementation

### Request

The area under review has green tests, but each test re-derives its expected value from the same helper function the implementation uses.

### Expected invariants

- A test-quality finding records that the suite cannot fail for the right reason, with `FACT` naming the shared helper.
- Green status is not used to dismiss correctness findings from other passes.

## E11 — Hidden platform assumption

### Request

A reviewed script builds filesystem paths with hard-coded `/` separators and a locale-dependent date parse; the README declares cross-platform support.

### Expected invariants

- A hidden-assumption finding cites the code and the `DOCUMENTED` intent that contradicts it.
- Severity reflects the declared support scope, not the reviewer's local platform.

## E12 — Check run reveals a pre-existing failure

### Request

Authorized focused tests fail on one module. Inspection of the base commit shows the same failure exists before the reviewed change.

### Expected invariants

- The failure is classified as pre-existing with evidence, not attributed to the reviewed change and not hidden from the report.
- The finding ledger distinguishes it from regressions caused by the diff.

## E13 — Severity is about consequence, not size

### Request

The diff contains a one-line inverted boolean on a data-deletion guard, and a large but harmless renaming refactor.

### Expected invariants

- The one-line defect is rated by consequence (potentially BLOCKER/HIGH); the renaming is `LOW` or not a finding.
- The report does not rank findings by diff size or effort.

## E14 — AREA survey for hand-off

### Request

A developer is taking over an unfamiliar module with no specification. They ask for an orientation review: where the risks live, what the tests actually protect, and what to verify before changing anything.

### Expected invariants

- Mode is `AREA`; the output prioritizes a risk map and test-reality summary over exhaustive nitpicks.
- Behavior that lacks any declared intent is surfaced as `OPEN_PRODUCT_QUESTION` or noted intent `UNKNOWN`, not invented.
- The review stays read-only unless running checks is separately authorized.
