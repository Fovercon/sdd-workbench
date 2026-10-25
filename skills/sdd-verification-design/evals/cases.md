# Behavioral Evaluation Cases

Evaluate the resulting verification decisions and artifacts, not exact wording or heading order.

## Case 1: New rerun behavior in the MML prototype

The approved requirement says rerunning one selected failed command must skip preprocessing, preserve successful and unselected records, replace the original failed record, and avoid duplicate output names.

Expected behavior:

- Derives separate obligations for selection, preservation, preprocessing bypass, record replacement, output identity, and final state reconciliation.
- Uses focused state/store or component checks plus a public-API system flow with state-and-file assertions.
- Includes partial failure before recovery, not only a direct happy-path rerun.
- Traces evidence to the requirement and Plan state/persistence contracts.

Failure signals:

- Tests only that the rerun endpoint returns 200.
- Treats file existence as proof that prior successful records were preserved.

## Case 2: Feature platform complete governance flow

A feature package goes through upload, eight preprocessing steps, governance, result listing, and ZIP download. The system uses persisted metadata, manifest, progress, API projections, and output files.

Expected behavior:

- Selects a backend system test through public APIs because correctness spans multiple stages.
- Uses cross-representation invariants: step count, units, progress records, result count, output path, and terminal state agree.
- Uses an isolated deterministic package and temporary task root.
- Keeps a smaller DT/contract portfolio for individual parsing and schemas.

## Case 3: Deterministic fake model/kernel boundary

Offline tests must cover success, rate limit, authentication failure, missing output, malformed output, partial failure, and hang without external network or token cost.

Expected behavior:

- Keeps the real owned platform, queue, persistence, bridge, and output collection path.
- Replaces only the external/model execution boundary.
- Requires explicit scenario selection and adapter/contract protection.
- States that the substitute cannot prove real connectivity or semantic quality and adds a separate small real smoke line.

## Case 4: Platform function versus governance quality

The platform reliably produces readable Markdown, but stakeholders also need confidence that annotations, parameter meaning, dependencies, and Jinja content are correct.

Expected behavior:

- Creates separate deterministic platform and semantic-quality evidence lines.
- Uses structural/schema checks in the platform gate.
- Uses a representative quality data set and explicit rubric for semantic meaning.
- Does not fail routine offline platform regression because a model phrased equivalent content differently.

## Case 5: Refactoring a complex output builder

A large deterministic output builder mixes Schema, YAML, Jinja, ordering, merging, deduplication, Macro projection, and Markdown rendering. Aggregate coverage is 66%, but the target branch has weak protection.

Expected behavior:

- Uses `REFACTOR_SAFETY_NET`.
- Plans Characterization Tests and small representative golden samples before extraction.
- Combines byte-sensitive golden checks only where formatting is contractual with parse/schema/invariant checks.
- Requires affected DT, contracts, system flow, full regression, and no coverage drop while prioritizing the modified high-risk branch.
- Does not claim 66% coverage makes the refactor safe.

## Case 6: Tolerated legacy defect during refactoring

Current persistence briefly exposes a terminal top-level state before its phase and scheduler projections settle. The refactoring task is behavior-preserving; a separate future design intends atomic terminal commits.

Expected behavior:

- Labels the observed window as tolerated/known rather than approved ideal behavior.
- Characterizes durable final state without converting the defect into a permanent product contract.
- Keeps the atomicity correction in a separate change/Plan decision.

## Case 7: User-visible queue bug

An implementation bypasses the FIFO queue for one start action although the Spec and Plan clearly require queueing.

Expected behavior:

- Uses `BUG_REGRESSION` and does not revise product intent.
- Designs the lowest faithful regression around submission/scheduler collaboration.
- Adds a system case with multiple tasks because ordering, public API, and persisted state cross boundaries.
- Includes a counterexample that would fail if direct execution is restored.

## Case 8: Path-traversal upload rejection

An archive may contain paths escaping the task root. The contract requires rejection, no processing submission, cleanup, isolation from existing tasks, and a user-readable error.

Expected behavior:

- Includes adversarial deterministic data.
- Verifies response, filesystem boundary, queue non-entry, cleanup, and unrelated-task isolation.
- Treats this as a high-risk negative system obligation, supported by focused low-level archive tests.

## Case 9: Historical performance report

A report says 350 commands at concurrency 8 completed in 79 minutes with P95 near 199 seconds. It predates the current commit and does not record the exact model version.

Expected behavior:

- Classifies it as `HISTORICAL`, useful as a bounded comparison but not current proof.
- Preserves workload, denominator, concurrency, timeout/retry, and evidence limitations.
- Requires a clean baseline, exact dependency/model identity, repetitions, percentiles, error/Token/resource measures for a new claim.
- Does not extrapolate the result to concurrency 16/50 or much larger data.

## Case 10: Coverage target without risk basis

A stakeholder asks the Agent to “make coverage 80%” but supplies no feature scope or risk model.

Expected behavior:

- Treats 80% as a requested metric, not evidence sufficiency.
- Inspects hotspots, uncovered branches, and mandatory contract/risk gaps.
- Requests a decision only if 80% is intended as an organizational gate; otherwise proposes risk-focused work without inventing a threshold.
- Does not add trivial tests solely to raise the number.

## Case 11: Browser state and static HTML checks

Existing tests search HTML and JavaScript text for button labels and function names. The contract requires that button availability follows task state and that downloads work in a real browser.

Expected behavior:

- Retains useful static checks only for static contracts.
- Designs browser functional cases for click behavior, state changes, navigation, and download.
- Avoids coupling the user-behavior oracle to private JavaScript function names or CSS fragments.

## Case 12: Cross-platform atomic writes and process cleanup

The product supports Linux and Windows. It atomically writes task metadata and must terminate subprocess trees on pause and shutdown.

Expected behavior:

- Uses local deterministic tests for policy and platform-specific branches.
- Requires native supported-OS evidence for file locking and process-tree behavior that mocks cannot prove.
- Separates daily offline gates from scheduled/release environment gates.
- Makes untested supported combinations visible.

## Case 13: Semantic evaluator uses the same model

The implementation model is proposed as the sole judge of its own generated governance output using a vague 1–5 score.

Expected behavior:

- Rejects self-judgment as the sole quality gate.
- Requires explicit business-linked criteria, representative strata, calibration examples, independent review/judge, and disagreement handling.
- Keeps deterministic schema, prohibited-content, and safety rules as separate hard gates.

## Case 14: Contract change with old green tests

Spec v2 changes partial-success semantics, while all tests written for v1 remain green.

Expected behavior:

- Treats v1 tests as stale for the changed obligations.
- Routes the delta through `sdd-change-impact` and redesigns affected cases/oracles.
- Does not weaken or preserve old assertions merely to keep the suite green.

## Case 15: Real model test in every commit

A developer proposes calling the paid remote model with a large fixture on every local and PR run to make tests “more realistic.”

Expected behavior:

- Keeps deterministic protocol/error behavior in the offline gate through a contract-checked substitute.
- Places minimal real connectivity in an authorized environment/release smoke gate.
- Places representative semantic quality and scale in separate scheduled/specialized runs.
- Records credential, cost, rate-limit, and flakiness constraints without exposing secrets.

## Case 16: Parseable input with ambiguous persistent state

A local file product must preserve existing records when the stored input cannot
be trusted. Its parser accepts syntactically valid input with conflicting values
for one state-bearing field. A later save can discard an earlier record.

Expected behavior:

- Derives the oracle from the approved preservation contract, not parse success.
- Plans a fixture with known prior state; checks read and attempted write public
  outcomes plus the complete original bytes or contractually preserved state.
- A controlled lossy version must fail that oracle. The conflicting JSON field
  is fixture detail, not a universal policy for every JSON consumer.

## Case 17: Error followed by successful correction

A browser flow reports a rejected filter. Correcting it restores results but
leaves the previous error displayed. The contract requires usable recovery.

Expected behavior:

- Plans the actual error → correction → recovered result and operation-specific
  message transition; checks both results and prompt consistency.
- Uses a real browser boundary for this flow, not source-name/text assertions.
- Tests sensitivity with a version that leaves the stale error visible.
- Does not clear unrelated active errors or add browser checks to non-UI tasks.

Cases 16/17 share the maintainer-only execution protocol in
[forward/recovery.md](forward/recovery.md); design alone does not execute it.

## Case 18: Low-risk local validation

A pure label-normalization function gains rejection of blank input; paths,
exception contract and nearby tests are known, with no persistence or UI.

Expected behavior:

- Chooses the focused public-function regression and existing offline suite.
- Reuses the current card's evidence; no separate verification document, browser,
  restart experiment or external reviewer merely to fill a layer portfolio.
- Preserves validation and a genuine behavior-failing RED; small scope is not
  permission to omit the required assertion.

## General failure conditions

The Skill fails if it:

- derives desired behavior only from current code;
- requires all layers for every change or relies only on unit tests;
- treats test count or line coverage as contract coverage;
- confuses system function, semantic quality, performance, and real integration;
- uses a mock so broad that it bypasses the product behavior under test;
- uses a fake dependency without protecting its protocol contract;
- relies only on status, file existence, or exact generated prose where stronger oracles are required;
- omits negative, partial-success, recovery, or isolation cases for high-risk stateful behavior;
- invents thresholds, environments, approvals, or release gates;
- reports historical or blocked evidence as current pass;
- proposes using historical user data or sensitive information as a default fixture;
- implements, runs, mutates, commits, or changes external systems without separate authorization;
- decides convergence instead of handing actual evidence to `sdd-converge-review`.

## Case 19: Source-derived acceptance after a session handoff

Maintainer-only protocol; keep scoring and suspected defects outside actor input.

Provide a user-authorized source, a derived Spec that cites it, and an unreviewed
Plan. The source requires exact format markers but permits one document type to
use plain steps. The Plan interprets block names as Markdown headings and forces
those steps into a code fence. A generator and checker reportedly agree. Ask a
fresh actor for the minimum verification design before implementation.

Expected behavior:

- checks the cited source, rejects the incompatible Plan, and preserves the
  allowed input branch instead of encoding the Plan's interpretation as truth;
- makes the applicable source identity/location, obligation, concrete example
  and expected result traceable in the existing verification artifact;
- uses an independent positive example plus a targeted invalid variant to
  distinguish the source contract from mutually agreeing product components;
- makes any missing Spec/AC precision explicit and hands it back to its owner;
  does not silently redefine the contract or invent a new human decision;
- reports designed evidence honestly and keeps unrelated checks outside scope.

Judge the actual gap, not an outcome keyword: `NEEDS_PLAN` is valid when the
Spec already incorporates an unambiguous source and the Plan contradicts it.
`NEEDS_SPEC` is appropriate when the product obligation itself is unresolved.

In an authorized isolated execution trial, replay those examples against a known
incorrect implementation and a source-conforming version. Preserve actual
outputs; an evaluator detecting a defect is not an actor detection. Separately
test a source revision with an effective-time boundary: invalidate affected old
expectations while retaining cases for still-supported old records. Include a
small UI-copy counterexample to detect unnecessary verification ceremony.
