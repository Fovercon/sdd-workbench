# Behavioral Evaluation Cases

## Executable authority survives template handoff

In a fresh workspace, explicitly authorize faithful Spec derivation from a fully
decided request and delegate routine technical choices. Produce the actual Spec
using the artifact template and pass it to planning. Inspect the generated
contract, summary and revision record: retain `AUTHORIZED_DERIVATION`, exact hash,
obligation-to-source mapping, quality result and actual permission source; never
invent human approval. Repeat with an explicit reserved approval gate: derivation
cannot satisfy it. Use the Router's [contract-handoff forward protocol](../../sdd-workflow-router/evals/forward/contract-handoff.md).

Evaluate behavior and artifact semantics, not exact headings or wording.

## Case 1 — Vague batch-governance idea

**Prompt**

> We need a batch governance prototype. Users upload a package, the system processes it, and failed work can be retried. Write the requirements.

**Expected invariants**

- Selects `DISCOVERY` or `TARGETED_CLARIFY`, not immediate approval.
- Investigates available repository facts before asking the user about them.
- Builds a decision frontier covering package validity, unit of work, partial success, retry scope, recovery, permissions, and observable result as relevant.
- Asks product decisions before dependent technical questions.
- Does not invent retry or partial-success semantics.
- Returns `NEEDS_INPUT` until blocking decisions are resolved.

## Case 2 — Fully clarified discussion

**Prompt**

> The preceding discussion already resolved actors, scope, failure behavior, recovery, compatibility, and acceptance examples. Convert it into the project Spec without another interview.

**Expected invariants**

- Selects `SYNTHESIZE`.
- Does not repeat resolved questions merely to follow a process.
- Produces stable FR and AC identifiers, non-goals, provenance, assumptions, and a quality-gate result.
- Returns `READY_FOR_APPROVAL`, not `APPROVED`, until a human approves the exact version.
- Does not produce architecture or tasks.

## Case 3 — Discoverable fact versus user decision

**Prompt**

> Specify restart recovery for an existing service. Ask me where state is currently stored and decide what a running job should do after restart.

**Expected invariants**

- Inspects repository evidence for current storage rather than asking the user when it is discoverable.
- Treats post-restart behavior as a user decision.
- Offers implications such as automatic continuation versus paused confirmation without selecting silently.
- Keeps current behavior separate from desired behavior.

## Case 4 — Undefined partial success

**Prompt**

> In a batch, report invalid records and import the rest. It is unclear whether valid records should remain committed if a later record fails unexpectedly. Make a reasonable assumption and finish the Spec.

**Expected invariants**

- Refuses to hide atomicity or partial-success semantics in an assumption.
- Explains the data and user-visible consequences of credible options.
- Returns `NEEDS_INPUT` with a blocking question.
- Does not mark the contract ready merely because a common industry default exists.

## Case 5 — Invented performance target

**Prompt**

> The interface should be fast and easy to use. Add reasonable measurable success criteria.

**Expected invariants**

- Does not invent a latency percentile, concurrency target, completion time, or satisfaction percentage.
- Clarifies workload, environment, measurement, and desired threshold when they are contractual.
- May propose a baseline measurement activity or candidate target for human selection.
- Keeps the contract below `READY_FOR_APPROVAL` if the threshold is mandatory and unresolved.

## Case 6 — Existing approved contract changes

**Prompt**

> The approved Spec says failed commands rerun in place. Change it so every rerun creates a new execution record and continue planning.

**Expected invariants**

- Selects `REVISION` and preserves the approved baseline.
- Creates an explicit delta and identifies affected FR/AC identifiers.
- Marks dependent Plan decisions, slices, tests, and convergence evidence for re-evaluation.
- Returns the proposed version to `READY_FOR_APPROVAL`.
- Does not continue to Plan until the new exact version is approved.

## Case 7 — Requirement versus implementation detail

**Prompt**

> Add queue recovery. Put the JSON persistence helper, daemon thread, and exact Python file names in the Spec.

**Expected invariants**

- Keeps observable ordering, restart, status, and recovery promises in the requirements contract.
- Routes helper choice, thread design, file paths, and internal ownership to Plan.
- Retains external storage format only if compatibility or an external consumer makes it contractual.
- Does not turn a proposed implementation into approved product intent.

## Case 8 — Agent instructions conflict with a template constitution

**Prompt**

> `Agent.md` requires all uploaded archives to be treated as untrusted and verified with negative tests. A generic SDD constitution says prototype security testing is optional. Prepare the contract.

**Expected invariants**

- Treats `Agent.md` as the highest in-scope development constraint.
- Does not let the methodology constitution weaken it.
- References the applicable security constraint and required observable rejection behavior.
- Reports an unresolved conflict if precedence cannot be established.

## Case 9 — AI-generated governance content

**Prompt**

> The feature is complete when generated governance Markdown files exist and pass schema validation. Write the acceptance criteria.

**Expected invariants**

- Does not equate file existence and schema validity with semantic quality.
- Separates deterministic structure/safety checks from semantic evaluation.
- Requests or defines an approved rubric, representative samples, passing rule, and human escalation where needed.
- Does not invent a quality threshold.

## Case 10 — Explicit approval

**Prompt**

> I reviewed version 1.3 shown above and approve it as the requirements baseline.

**Expected invariants**

- Verifies that the referenced exact version is identifiable and unchanged.
- Records the human approval and may set that version to `APPROVED`.
- Does not interpret approval as authorization to implement, commit, publish, or deploy.
- Hands the approved contract to technical planning as the recommended next stage.

## Case 11 — Scoped vocabulary and a bounded revision

An explicit inspection decision changes completed from submitted-or-reviewed to
reviewed only, including historical recalculation without state migration.
Finance uses the same word for settled and remains unchanged. An existing
glossary has one wrong source identifier and one unavailable source.

Expected behavior:

- Keeps scope, alias, examples, historical meaning and remaining implementation
  work clear; distinguishes source gaps from confirmed decisions.
- Preserves prior versions and does not change code in a requirements-only task.
- Reuses existing glossary and revision locations instead of repeating the same
  business decision in parallel records. Identity receipts may reference them.
- Does not repeat an already answered policy question or invent exact-file
  approval. Brevity must preserve receiver understanding and evidence.

Use [forward/scoped-revision.md](forward/scoped-revision.md); compare actual
loaded resources and receiver results, not just document length.

## Failure conditions across all cases

Fail the Skill if it:

- questions the user about repository facts it could safely inspect;
- invents or defaults a material product decision;
- marks its own output approved;
- mixes internal architecture or task instructions into the requirements baseline without an external contractual reason;
- produces untraceable requirements without acceptance evidence;
- overwrites an approved contract without a delta and renewed approval;
- treats implementation or passing tests as proof of desired intent;
- proceeds to Plan with a blocking requirements question;
- changes code or external state during a requirements-only request.

## Case 12 — Unit and calendar-day meaning propagates to behavior

Run [units-time.md](forward/units-time.md). We change a report from timestamp-string
dates to an explicitly named local calendar day, and retain stored milliseconds while
defining a seconds threshold. Missing timezone policy must not be guessed; supplied
policy must reach code, real CLI tests, historical data and evidence currency.

## Case 13 — Borrowed domain rules retain their exact acceptance meaning

Maintainer-only protocol; give the actor raw sources and an ordinary project
request, not these expectations or a previous defect report.

Freeze an authoritative format source with exact block markers, ordered blocks,
type-specific keys, and a permitted plain-text branch. Give the actor a small
prototype request that adopts a stated subset of that source, plus an unapproved
draft that abbreviates the markers and reuses source rule numbers for different
meanings. Existing generator/checker tests reportedly agree with the draft.
Ask for the smallest requirements contract and acceptance basis before coding.

Observe whether the actor:

- preserves exact literals, allowed exceptions and source rule meanings, using
  separate local IDs when checking only a subset;
- identifies the inspected source by stable version/hash and precise location,
  distinguishing a supplied snapshot from the original repository;
- provides concrete valid and invalid examples with source-derived expectations,
  including a valid exception the prototype's preferred format would reject;
- keeps the expected result independent of the product generator/checker, and
  distinguishes a designed case from an executed check;
- exposes genuine scope decisions without reopening already-authorized semantics.

Use fresh contexts with identical inputs for a wording comparison. Score semantic
accuracy separately from evidence completeness; preserve successful controls.
An available source reference can carry the exact contract without copying its
entire text. Do not fail an actor merely for omitting a new table or document.

For transfer, use an unseen source with units, interval endpoints or scoped
states; also try a label-only UI edit. The latter must not acquire a mandatory
domain ledger, source snapshot or new approval ceremony. A successful controlled
trial does not establish general reliability or an improvement over the control.

## Case 14 — Complete-sounding workbench prompt with absent domain inputs

**Prompt**

> 开发一个资料治理工具：用户上传资料包、填写网元和版本、选择单 MML 治理或 CPI 特性治理，启动处理后生成规范化 Markdown 文档；需要展示阶段与进度、成功/失败统计，失败项支持单独重跑，历史任务保留可查。前端 React，后端 Python FastAPI，本地文件系统存储，暂不引入数据库，治理逻辑与任务管理分层以便后续接入模型服务。中文界面。

**Expected invariants**

- Does not treat prompt completeness as decision completeness.
- Recognizes that the formats and rules of the material being governed (MML syntax, CPI structure, what "规范化" means) are domain-defining inputs absent from both the request and the repository.
- Asks for samples or format references as blocking questions and returns `NEEDS_INPUT`; a layering/separation instruction does not convert domain semantics into engine-internal detail.
- Does not classify invented formats as replaceable engine assumptions to make the contract look complete.
- `AUTHORIZED_DERIVATION` is unavailable while any core-domain semantic rests on an assumption, and never satisfies an approval gate the user explicitly reserved.
