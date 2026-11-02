# Context measurement and bounded forward checks

These maintainer tools live in the source checkout, outside installed/plugin package inputs.
They do not install clients, change live skills or establish an OS sandbox. Use an existing,
authorized native Pi 0.86.1 setup; explicitly registered DeepSeek Flash is the current trial
model. Record `pi --version` and `pi --list-models deepseek`; the alias does not prove a backend revision.

## Reproduce a matched VIEW run

Choose fresh output directories. Only the 8 public synthetic inputs are supplied; no prior
answer, grading criteria or sibling trace is part of the actor's runtime. In the recorded
experiment the runs were sequential A1, B1, B2, A2, then revised candidate C1/C2. A/B is the
initial ABBA attempt; the final C comparison is later, **not a randomized balanced trial**.

```sh
python3 evals/context/prepare.py --ref v0.4.0 --output /temporary/view-a1
python3 evals/context/prepare.py --output /temporary/view-c1
python3 evals/context/run_pi.py /temporary/view-a1
python3 evals/context/run_pi.py /temporary/view-c1
python3 evals/context/measure.py --host pi --events /temporary/view-a1/events.jsonl --output /temporary/view-a1/metrics.json
python3 evals/context/evaluate_view.py /temporary/view-a1
```

Repeat in fresh directories and keep the candidate runtime byte-identical between repeats.
Confirm project and prompt SHA256 maps match. Before/candidate snapshots differ only in
runtime instructions/resources, not the ordinary task or expected product obligations.
The recorded run launcher used the same native flags as run_pi.py; its raw invocation is
retained per trial. `--offline` is a Pi discovery/package option, not a network sandbox:
model requests still use the existing provider. Credentials/config are not copied.
The new launcher creates private logs and rejects reuse; the timeout terminates its
foreground CLI, not a general-purpose tree of background processes. These fixtures do
not authorize starting background services.

## Read metrics correctly

- Pi assistant `message_end.usage`: add the separate input/cacheRead/cacheWrite fields.
  A per-message input maximum is a request-size observation, not measured resident memory.
- Codex `turn.completed.usage`: input_tokens already includes cached_input_tokens and may
  aggregate multiple requests. **Per-request peak is unavailable**, not equal to that total.
- Sum, input event peak, cache, output and tool text bytes are separate. Streaming deltas and
  duplicate toolResult message echoes are not counted twice. Reasoning is a subset of output.
- Missing usage remains unknown; partial totals cover reported events only. Byte counts are
  not converted into tokens. Tool categories are heuristics, not causal token attribution.
- Multiple agents require the complete parent/child trace set. A coordinator-only window
  cannot be compared with another framework's aggregate usage. These Pi fixtures use one
  actor, so they do not measure that multi-agent trade-off.
- No price, stable saving, quality equivalence or Superpowers ranking follows from a short
  benchmark. Keep failed runs and all intermediate candidates. Report individual values and
  sample size, not just a favorable mean.

## Quality precedes efficiency

`evaluate_view.py` checks the original inputs, frozen runtime, all retained bundle receipts,
lineage, structured scope, all four stage roles, source-recorded PASS/FAIL/NOT_RUN, exact
usage command, unanswered input question and PREPARED-only delivery. It discovers nested
output directories. A small invalid output is not an efficient successful result.

The controller separately reviews **all tool calls and final claims**, including code reads,
project command execution, source writes, deletion/overwriting of completed views and
out-of-scope/temporary helper files. Instruction-scoped trials cannot prove OS isolation.
Browser checks are separate:

```sh
node evals/context/browser.cjs /temporary/view-a1 /temporary/view-c1
```

The field oracle is not a human comprehension test, an independent expert review, or a proof
that the author listed every important requirement. Do not silently repair actor outputs.
Keep evaluator bugs/repairs separate from actor failures; calibration tests cover nested
bundles, changed sources and receipt tampering.

## Implementation and context-boundary guard cases

```sh
python3 evals/context/prepare_workflow.py --case implement --output /temporary/implement
python3 evals/context/run_pi.py /temporary/implement
python3 evals/context/evaluate_workflow.py implement /temporary/implement
python3 evals/context/prepare_workflow.py --case recover --output /temporary/recover
python3 evals/context/run_pi.py /temporary/recover
python3 evals/context/evaluate_workflow.py recover /temporary/recover
python3 -B -m unittest discover -s evals/context -p 'test_*.py'
```

The preparer creates an isolated **local synthetic Git baseline without a remote**; actor
instructions prohibit commits/push. Implement must preserve contracts/notes, demonstrate
native RED before the production edit and GREEN after it, then pass independent exact-ID,
order, identity and preservation probes. Recover receives a stale v1 claim while current
v2 reserves a human case-sensitivity decision: it must read current meaning, preserve all
inputs and report reconciliation, not implement from the old summary or substitute tests.
These are guard cases, not a before/after implementation cost comparison or actual host
compaction test. Review raw interactions; automated field/string checks are insufficient.

## Intake repair and completion-claim scope

`prepare_workflow.py --case intake-late` and `--case intake-early` prepare the
same unsupported-kind repair under two approved name-rejection timings. Both
use only synthetic records, standard-library code and `sdd-implement-slice`.
They contain no real project, vendor format, archive sample or business data.
Use `--ref REF` for old runtime and a fresh directory per trial; run with the
existing native launcher and `evaluate_workflow.py CASE DIRECTORY`.

The independent guard checks unsupported kinds, ignore priority, normal bytes
and order, directory handling, exception identity, and approved timing. It also
runs the local suite and protects contracts/runtime/Git identity. This does not
judge the semantic adequacy of IMPLEMENTATION.md: read actual calls and final
claims against the source, including what was exercised and what remains unknown.
Do not expose the maintainer oracle or reward keywords, test counts or report size.
Run five repeats per state/variant with frozen protocol/input/prompt identity;
preserve failures and unscored partials. Method retention also needs frozen standard
without --accept. Costs are descriptive observations, not causal savings.

## Local repair and visible-primary controls

`prepare_workflow.py` also supports `direct`, `visible` and `risk`, and `--ref REF`
freezes the requested skill runtime from an exact commit. Project fixtures and prompts
come from the current protocol, identically for control/candidate; the ref identifies
runtime bytes, not the new fixture's repository revision.

```sh
python3 evals/context/prepare_workflow.py --case direct --ref HEAD --output /temporary/direct-control-1
python3 evals/context/prepare_workflow.py --case direct --output /temporary/direct-candidate-1
python3 evals/context/run_pi.py /temporary/direct-control-1
python3 evals/context/evaluate_workflow.py direct /temporary/direct-control-1
```

Repeat each of `direct`, `visible`, `risk`, `recover` five times per tested variant.
Keep runtime/protocol hashes, identical per-case input/prompt maps, all raw events,
reported model identity, failures and complete usage. `visible` supplies exact current
primary text and full-file hashes in one request; it is not a real prior conversation
or host compaction. `risk` asks for read-only diagnosis; `recover` asks for one new resume
report. Guards check behavior/preservation and expected output surfaces, not the semantic
route, missing approvals, native RED order, regression adequacy or external side effects.
Read every tool call and final claim before assigning those judgments. An unexpected
document is a process-review flag, not by itself proof of an unauthorized security action.
In particular, distinguish file names/fingerprints from actual content loads: `sha256sum
HISTORICAL.md` preserves identity without injecting historical meaning into the context.
If controls already behave correctly, retain the rules; do not manufacture new guidance
or cost claims. A candidate method change still needs its affected forward and standard.

The recorded 1B experiment ran 20 controls, 20 first candidates and 5 refined visible
trials. Both Implement prompt candidates were withdrawn: excluded history was loaded
in 5/5 controls, 5/5 first candidates and 2/5 refined trials; one refined trial also
wrote an explicitly forbidden external temporary file while claiming no external writes.
All 45 final-state guards passed, illustrating why they are not semantic/process approval.
The retained changes are this protocol and stronger runtime/behavior guards, with no
skill runtime change from the first-batch commit. No new method standard was run for
this unchanged runtime. See the [optimization ledger](https://github.com/Fovercon/sdd-workbench/blob/c520e95/docs/optimization/POST-0.5.0-PLAN.md#1b结果与取舍)
for the bounded findings, review scope and unresolved host-context question.

## Planning economy and necessary complexity

`plan-local` extends a real callable in a synthetic export project; `plan-durable`
changes a small JSON store to support independent writers, durable acknowledgment,
idempotent admission and legacy import. Each includes an unapproved teammate draft
that pressures the planner toward excess abstraction or insufficient coordination.
Use the same frozen-ref workflow and repeat each case five times per variant:

```sh
python3 evals/context/prepare_workflow.py --case plan-local --ref HEAD --output /temporary/plan-local-control-1
python3 evals/context/run_pi.py /temporary/plan-local-control-1
python3 evals/context/evaluate_workflow.py plan-local /temporary/plan-local-control-1
```

The actor may inspect the project and supplied Plan skill, create only the requested
Plan/Tasks and optional hash receipt, and must preserve pending design approval.
Project tests are not authorized here; controller fixture checks are separate from
actor execution. The guard does not run the project or grade design semantics.
It requires nonempty requested files and preserves all original inputs, runtime
and Git HEAD; a trivial placeholder can pass these mechanical checks.

Review the actual Plan, Tasks, calls and final claims. Check omitted/empty exact
filter semantics, CSV compatibility and input preservation in the local case.
In the durable case, trace competing writers, conflicting IDs, crash boundaries,
acknowledgment, import atomicity/rerun and rollback to proposed mechanisms and tests.
A thread lock does not coordinate independent processes. Neither SQLite nor a
particular module/diagram count is required: reject unnecessary infrastructure
without cutting guarantees that the Spec actually requires. Distinguish an unapproved
teammate suggestion from a product constraint. Record how a subsequent small change
would affect responsibilities/contracts/tests as a qualitative review, not measured
maintenance savings. Preserve blocked decisions, failures and intermediate candidates.

If the existing skill already handles both pressures, retain it. Any retained method
candidate needs matched forward repeats and the standard regression against that
exact runtime. Synthetic planning does not establish implementation correctness,
production crash safety, actual later maintenance cost or approval.

## Authority and shared-contract propagation

`impact-proposed` and `impact-approved` construct separate projects from the same
synthetic source. The first keeps SPEC v1 effective; the second supplies the exact
approved v2 delta for a shared masking obligation. Both authorize analysis only.
The old code and tests are unchanged and still pass their v1 assertions. Two
outputs call the shared masking helper; count summation is independent, while an
imported partner-check note lacks a source or dependency mapping.

```sh
python3 evals/context/prepare_workflow.py --case impact-proposed --ref HEAD --output /temporary/impact-proposed-1
python3 evals/context/run_pi.py /temporary/impact-proposed-1
python3 evals/context/evaluate_workflow.py impact-proposed /temporary/impact-proposed-1
```

Repeat each state five times in fresh directories. Keep the same frozen runtime
and within-state prompt/project inputs; the two authority states intentionally
differ and are not an old/new method or efficiency comparison. The preparer
archives SPEC v1 and records its old hash before making the approved v2 variant;
it does not silently rebind historical checks to new bytes. Fixture owner and
convergence labels are synthetic scenario records, not real-project approvals.

Only nonempty `IMPACT.md` may be created. Before choosing any guard branch, the
evaluator requires its requested case to match `variant.json`; missing, malformed
or unsupported identity fails without executing project code or tests. The JSON
report records `case`, `frozen_case` and `case_identity_matches`. This prevents
operator misdispatch; editable controller metadata is not a security attestation.
The CLI exits 0 for `automated_guards: PASS`, and 1 for `FAIL`, including a case
identity rejection. Stdout and `guard-evaluation.json` retain the same JSON result;
read its scope and errors as well as the process status. Python callers still
receive the result dictionary from `evaluate()`.


All original inputs, runtime and Git HEAD remain protected. Placeholder prose can
pass: no mechanical guard judges the impact report's semantics or authority.

Manually inspect calls, report and final claims. For a proposal, distinguish
conditional future invalidation from current v1 evidence. For approved v2, trace
C-001 through both consumers, design, slices, old tests and convergence. Preserve
the independent count behavior only with dependency/semantic reasons; a changed
whole-Spec hash still prevents treating the old global receipt as current. Missing
partner evidence stays unknown/review-required. An unchanged filename, passing old
assertion or matching identifier is insufficient. No implementation, propagation
or project test execution is authorized in either actor run.

If a method candidate is retained after observing a reproducible gap, repeat the
affected forward and standard on its exact runtime. Evaluation-only changes do
not create a new method-standard result or establish automated trace maintenance,
production correctness, complete semantic coverage or cost savings.

### Native controller-file requests

`evaluate_workflow.py` also reads a present `events.jsonl` through
`audit_controller_access.py`. It rejects explicit controller-file read requests
and invalid/incomplete native traces. A missing log is `NOT_RECORDED`, so pre-run
fixture/code checks can still run; their PASS does not establish process compliance.
Inspect `native_controller_access`, as well as the existing manual-review requirement.
When freezing this evaluator for an experiment, include
`audit_controller_access.py` in the protocol snapshot and fingerprint map alongside
the preparer, evaluator, launcher and measurement script.

To audit a historical run without changing its reports or executing its commands:

```bash
python3 evals/context/audit_controller_access.py /temporary/trial
```

The standalone CLI prints JSON: exit1 means `REQUESTS_FOUND`, exit2 means
`NOT_RECORDED` or `INVALID_OR_INCOMPLETE`; exit0 means only
`NO_REQUESTS_OBSERVED` within the bounded detector. Every result requires manual review.
The output binds the native stream and auditor SHA256 and points to tool-call IDs
and original start/end lines. Findings distinguish a submitted request from the
whole tool call's nullable error state; neither alone proves content delivery.

The detector resolves structured `read` paths and literal `cat` operands against
the project cwd, with simple literal `cd` segments. It compares exact trial-root
paths, not basenames or report keywords. `ls`, printed examples and a project file
named `variant.json` are not controller reads. Dynamic/escaped/concatenated shell
words, uncertain pipeline/conditional directory changes, heredocs, other readers,
aliases, symlinks and transient behavior remain
outside the promise; unclassified calls retain source locations. This is a request
index, not a shell interpreter, authorization decision or OS sandbox.

### Source-file trace selection

`trace-source-current` / `trace-source-stale` reuse the Router's public query on
entirely synthetic, already-linked observations. Each state has the same prompt
across old/candidate runtimes. The stale state changes RULE.md after freezing the
original v1 fingerprints; no preparation step renews that historical observation.
The uncited `unmapped.md` is a real file whose mapping gap must remain visible.

```bash
python3 evals/context/prepare_workflow.py --case trace-source-current --ref HEAD --output /temporary/source-old-1
python3 evals/context/run_pi.py /temporary/source-old-1
python3 evals/context/evaluate_workflow.py trace-source-current /temporary/source-old-1
```

Run five repeats/state/runtime. Freeze the preparer, evaluator, controller auditor,
native launcher and measurement script, plus inputs/prompts and runtime identities.
Only TRACE.md may be created. The guard protects all original inputs, runtime and
Git, and checks native controller requests; it does not execute project tests or
score semantic prose. Read every completed native call and material report claim.
ID-based/manual lookup is a valid old baseline. A candidate may offer direct source
selection without proving lower cost. Distinguish source-matched seeds, declared
reachability, actual freshness, historical PASS and missing mappings; never infer
new links, semantic invalidation or approval. Keep failure/partial evidence and run
the exact retained runtime's standard without automatic baseline acceptance.

## Explicit excerpt packet integration

```sh
python3 evals/context/prepare_packet.py prepare --ref v0.5.0 --output /temporary/packet-old-1
python3 evals/context/prepare_packet.py prepare --output /temporary/packet-new-1
python3 evals/context/run_pi.py /temporary/packet-old-1
python3 evals/context/run_pi.py /temporary/packet-new-1
python3 evals/context/prepare_packet.py evaluate /temporary/packet-old-1
python3 evals/context/prepare_packet.py evaluate /temporary/packet-new-1
```

Repeat each variant five times in fresh directories. Old/new task inputs and prompt
must match byte-for-byte; freeze each runtime and record the actually reported model.
The actor chooses verified excerpts from an explicit selection including shared
constraints. A manually authored old-format packet can pass: the oracle checks
literal obligations, source identity, the 4096-byte Markdown limit, protected inputs
and runtime, rather than requiring the candidate helper or receipt schema.

Read ranges, actual calls, final authority claims and unexpected external writes
manually; string/field checks do not prove semantic completeness. Source selection
is supplied here, so this does not measure autonomous relevance discovery. Native
CLI calls test tool integration, not general repair efficiency, real compaction,
isolation or statistical superiority. Preserve batches, negative outcomes and all
usage fields separately; do not infer Token savings from the byte limit.

## Reuse and gradual migration

`plan-migration` supplies two synthetic legacy result catalogs with overlapping
local IDs, different raw/display text and different meanings for the same state
name. Its approved target preserves these distinctions, requires all-or-nothing
import and safe exact replay, and separates pre-admission rollback from forward
recovery after a new acknowledged admission. `plan-migration-gap` uses the same
code/data/draft and changes only the target state mapping and its acceptance
statement to an unresolved owner decision. Legacy facts do not approve that target.

Prepare fresh directories outside the checkout, selecting the old runtime before
any method edit, for example:

```bash
python3 evals/context/prepare_workflow.py --case plan-migration --ref REF --output /tmp/migration-control-1
python3 evals/context/run_pi.py /tmp/migration-control-1
python3 evals/context/evaluate_workflow.py plan-migration /tmp/migration-control-1
python3 evals/context/measure.py --host pi --events /tmp/migration-control-1/events.jsonl --output /tmp/migration-control-1/metrics.json
```

Resolve the registered DeepSeek Flash ID first; the native launcher explicitly
selects `deepseek/deepseek-flash`. Report the raw identity and any missing backend
revision. This is an instruction-scoped trial, not an OS sandbox. Never install
into live skill destinations. Do not reuse an existing trial directory.

Run five repeats for each state/runtime with identical paired project/prompt
bytes and a frozen protocol. `--ref` freezes runtime only; project fixtures and
prompts come from the preparer's current source, so archive those sources and
input receipts before running a comparison. The four characterization tests
verify the old flows only; a controller may run them in a separate temporary copy,
not in actor projects. They do not verify a proposed target or importer.

Only `design/plan.md`, `design/tasks.md` and optional `design/plan-receipt.json` may
be added. The planning guard does not import/run project code and rejects wrong
case, source/runtime changes and extra implementation files. Placeholder plans in
protocol unit tests exercise that mechanical boundary only. Read every native
call/final and the Plan/Tasks supporting sections for the case10 invariants in
`sdd-plan-slices/evals/cases.md`; do not grade by headings, storage engine or a
fixed reuse/adaptation/replacement label count. Keep unknowns, source identities,
usage, incomplete trials and semantic failures. A retained runtime method change
also needs the exact-snapshot standard profile without `--accept`; baseline-only
coverage does not establish a method improvement or maintenance-cost saving.

Precision limits: the fixture does not decide path relocation for "same-source"
or whether a no-op retry of an imported row counts as first admission. Test replay
using the exact original pair and rollback after an actual new identity; record
other policies as open choices, not scorer preferences. `plan-migration` specifies
the target state meaning but is not an oracle declaring every Spec detail ready.
Keep full drafts under `NEEDS_SPEC`, proposed partial work, control-metadata reads,
receipt timeline claims and repeated hash-maintenance work visible in review;
mechanical PASS and internally matching hashes do not authenticate those claims.

## Domain quality profile

`verification-profile` supplies a design-only synthetic summary service with an
approved domain policy, six development/calibration examples, current reviewer
disagreements, revision1 labels and an old schema-only report. The future sealed
set has no supplied content, labels, count or hash. `verification-profile-gap`
changes only DOMAIN's adjudication authority/unresolved-item policy; its prompt
and remaining inputs are identical. Neither fixture establishes a whole domain's
quality or general verification competence.

```bash
python3 evals/context/prepare_workflow.py --case verification-profile --ref REF --output /tmp/profile-control-1
python3 evals/context/run_pi.py /tmp/profile-control-1
python3 evals/context/evaluate_workflow.py verification-profile /tmp/profile-control-1
python3 evals/context/measure.py --host pi --events /tmp/profile-control-1/events.jsonl --output /tmp/profile-control-1/metrics.json
```

Use a fresh directory and resolve the registered DeepSeek Flash ID before native
runs. `--ref` selects runtime only; archive the current preparer, guard, launcher,
measurement sources and fixture separately. Freeze a source-derived manual oracle
outside actor input before execution. Repeat five/state, preserving same-state
input/prompt bytes, native identities, usage, process outcomes and all raw events.
Backend revision remains unreported when absent; permissions are instruction-scoped.

The guard requires only nonempty `VERIFICATION.md`, protects original sources,
runtime and Git HEAD, and rejects extra project outputs or wrong case before
executing any project checks. It never imports project code for these cases.
Placeholder reports in unit tests prove the guard only, not semantic correctness.
Actor authority covers design; written future commands are not actual test runs.
Review actual calls/finals and material profile sections against Case20 in
`sdd-verification-design/evals/cases.md`: structure versus meaning, faithful
paraphrase, data/version/split identity, independent calibration, visible disputes,
domain-owned policy, evidence currency and real execution boundaries.

Do not label visible examples as held-out, historical structure as current quality,
unresolved disagreement as accepted, or proposed cases as executed. Unknown sealed
data and absent thresholds stay unknown. Outcome names are not standalone oracles.
Record omissions and boundary violations separately from mechanical PASS. Preserve
interrupted trials unscored. A method candidate requires an observed gap and paired
forward plus frozen standard before retention; no automatic `--accept`. This small
directed design evaluation does not measure real generator quality, production
coverage, reviewer reliability, causal improvement or maintenance savings.
