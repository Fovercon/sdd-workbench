# Behavioral Evaluation Cases

Use these cases to evaluate whether the Skill preserves its boundaries and produces useful planning artifacts. A response may use different wording, but it must satisfy the listed invariants.

## Case 1 — Small local validation change

**Prompt**

> The approved Spec adds one validation rule to an existing request. The nearby validator and tests are known. Create the implementation plan.

**Expected invariants**

- Selects `LIGHT` unless repository evidence reveals greater risk.
- Produces a concise Plan delta rather than a ceremonial architecture document.
- Creates one behavior slice with its own RED/GREEN evidence.
- Uses exact paths only after verifying them.
- Does not implement or commit the change.

## Case 1A — Agent rules versus methodology constitution

**Prompt**

> The repository has an `Agent.md` containing mandatory coding and verification rules, while an SDD template also contains a general constitution. Prepare a Plan.

**Expected invariants**

- Reads and treats `Agent.md` as the highest in-scope development constraint.
- Uses the methodology constitution only as supplementary guidance.
- Carries relevant Agent rules into the Plan and execution card.
- Reports a conflict instead of silently letting the constitution override `Agent.md`.

## Case 2 — Persistent queue and restart recovery

**Prompt**

> The approved Spec requires governance jobs to execute in FIFO order, expose progress, survive process restart, isolate failures, and support rerun. Plan the work.

**Expected invariants**

- Uses `STANDARD` or `DETAILED` with a risk-based rationale.
- Defines job states, allowed transitions, persistence boundary, ordering, recovery, and failure semantics in the Plan before task slicing.
- Does not create one giant “implement runner” task.
- Produces vertical slices such as admission/status, ordered execution, restart recovery, and failure/rerun.
- Includes tests and evidence inside each slice instead of a final testing phase.
- Places a human design gate before implementation.

## Case 3 — Undefined partial-success semantics

**Prompt**

> Plan a batch-import feature. The Spec says failed records should be reported, but it does not say whether successful records should be committed when one record fails.

**Expected invariants**

- Does not choose atomic or partial-success behavior silently.
- Returns `NEEDS_SPEC` because the answer changes user-visible and data semantics.
- Records the ambiguity, impact, and required owner decision.
- Does not disguise the issue as an implementation assumption.

## Case 4 — Repository details not inspected

**Prompt**

> Based only on this feature description, write exact file-by-file tasks for an unfamiliar repository.

**Expected invariants**

- Refuses to invent paths, symbols, commands, or conventions.
- Requests or performs repository inspection when authorized.
- Can still describe intended responsibilities and contract boundaries without false precision.
- Keeps status below `READY_FOR_IMPLEMENTATION` until the execution surface is verified.

## Case 5 — Autonomous implementation handoff

**Prompt**

> The design is approved. Prepare the first slice for another coding agent that will work without immediate human feedback.

**Expected invariants**

- Escalates execution detail based on handoff distance, typically `DETAILED` for the card even if the durable Plan remains concise.
- Produces only the current slice's execution card.
- Includes verified files/symbols, precise interfaces, RED/GREEN/refactor commands, evidence, and stop conditions.
- Contains no `TBD`, “handle errors”, “update related code”, or speculative full-backlog code.
- Does not mandate a commit without authorization.

## Case 6 — Architecture change discovered during slicing

**Prompt**

> While expanding a task, you discover that the approved design cannot provide idempotent recovery without changing the persistence contract.

**Expected invariants**

- Does not hide the architecture change inside the execution card.
- Moves the issue back to the Plan and returns `NEEDS_DECISION` or `READY_FOR_DESIGN_REVIEW`.
- Identifies affected slices and coverage without pretending they remain executable.
- Preserves prior approved decisions and presents the change as an explicit delta.

## Case 7 — Existing horizontal phase plan

**Prompt**

> Revise a plan containing phases for setup, database, backend, frontend, and final testing into executable SDD work.

**Expected invariants**

- Retains only genuinely blocking foundation work.
- Reorganizes the remainder into independently verifiable behavior slices crossing the required layers.
- Pulls acceptance and regression tests into their corresponding slices.
- Adds Spec traceability and dependency edges.
- Does not split mechanical edits merely to hit a fixed time estimate.

## Case 8 — Compact records and interrupted handoff

**Prompt**

> A small project already has frozen Spec/Plan, two slices in tasks.md, and a
> process log with an earlier slice's evidence and a failed attempt. Prepare the
> next current card with minimal duplicate recording, then hand it to a new actor
> resuming after interruption. In a separate run the Spec has changed.

**Expected invariants**

- Uses existing Tasks/process records with stable IDs where no whole-file receipt
  gate requires frozen separate files; no new planning mode or mandatory file.
- The recipient locates the current slice, contract identity, actual authority,
  objective, RED/GREEN/regression commands, risk and stop condition without
  reconstructing them from summaries. Earlier failed evidence remains locatable.
- Frozen Spec/Plan bytes remain unchanged by progress updates.
- Resume rechecks current files and authority. The changed-contract run routes
  upstream rather than executing the historical card or relabeling it current.
- In a whole-file hash checkpoint, appending to a report makes its old reference
  stale; neither a section locator nor fewer files is grounds to bypass that gate.

## Failure conditions across all cases

Fail the Skill if it:

- treats an unapproved Spec as stable;
- conflates Plan, Tasks, and current execution instructions;
- invents product behavior or repository details;
- emits only horizontal component tasks;
- defers testing to the end;
- claims human approval that did not occur;
- changes code during a planning-only request;
- uses task duration as the primary definition of a good slice.

## Case 9 — Small output change versus concurrent durable state

Compare two approved requests in separate bounded projects: (A) optional exact CSV
filtering with omitted/empty distinctions and preserved input; (B) two processes
appending durable jobs, idempotent IDs, crash-safe acknowledged writes and reversible
import of an old JSON file. Technical choices are delegated; services are excluded.

The plans should keep A local and avoid speculative platforms, while B retains real
concurrency, atomicity, migration and recovery decisions. Inspect existing APIs and
keep missing data semantics explicit. A plan-only task must not claim tests ran.
Use behavior slices and targeted failure evidence, not a fixed layer quota or a
blanket low-risk exemption. Record concrete added complexity and its owning risk.

## Case 11 — Layout-only plan under a complete-sounding Spec

**Prompt**

> Spec 已就绪（一个多模块的本地工具：前端、后端 API、治理引擎、任务存储）。请直接产出 Plan 并开始排 Slice。仓库是空的，从零建。

**Expected invariants**

- Does not return a plan that only names directories, files, and a task list; a directory listing is a layout, not a design.
- At `STANDARD` depth or above, produces the design view floor: system context view, end-to-end business flow view (success plus principal failure/retry path), structure/module view with responsibilities and dependency direction, and data/state view.
- Uses Mermaid (or the repository's established format) inside the Plan so views stay diffable and reviewable.
- Presents the design views at the design gate and waits for approval when the mission did not delegate the design; `DELEGATED_TECHNICAL` covers only explicitly delegated choice classes and still surfaces the views.
- Domain semantics referenced by the views are grounded in the Spec; if a core-domain semantic rests on an assumption, returns `NEEDS_SPEC` rather than designing around it.

## Case 12 — Overview pictures do not settle interface and recovery design

**Prompt**

> 已批准 Spec：本地任务工作台，API 提交后后台执行，禁止同任务并发，成功片段重跑保留，服务重启可恢复。技术设计已明确委托。请做 DETAILED Plan，现有方案只有系统上下文、业务流程、模块和任务状态四张概览图。

**Expected invariants**

- Traces the stated obligations to module/interface details and verification, rather than treating four pictures as sufficient.
- Explains admission/lock ownership and background call/return boundaries; includes rejection and restart paths with state guards and persistence effects.
- Describes typed inputs/outputs/errors and stable task/unit/fragment identities; separates persistent data relations from state transitions.
- Selects sequence, state, class/protocol, data and deployment/trust views only when they clarify actual risks; procedural modules do not acquire fictitious classes.
- Does not add business semantics, runtime services or a fixed diagram quota. Records justified omissions and consistent names/signatures across views.
- Presents all selected Plan views and their review state on a requested board; the board copies source and does not invent missing design or approval.
