# Project view: generate and update


## Contents

- [Select the smallest operation](#select-the-smallest-operation)
- [Establish observations](#establish-observations)
- [Run the bundled renderer](#run-the-bundled-renderer)
- [Update without erasing history](#update-without-erasing-history)
- [Verify and deliver](#verify-and-deliver)


Use for a requested visual project overview or maintenance of an existing one.
The output is a derived, offline view: current progress, readable module responsibilities
and next action first, selectable details alongside. The complete connection diagram,
source files and fingerprints are available in expandable sections.
It does not approve work, execute product changes, or replace project records.
For requested direct feedback submission, use the optional loopback service in
[human-decisions.md](human-decisions.md). It adds a durable feedback receipt overlay
to the immutable view; static/offline files retain their conversation route.

## Select the smallest operation

| Request | Action |
| --- | --- |
| “项目现在怎样了？” | Normal STATUS; answer from sources without creating files |
| “生成项目视图 / 展示进展和模块关系” | VIEW: collect bounded observations, then `render` |
| “来源变了，检查是否还能用” | `check`; report changed/missing evidence |
| “更新视图，保留旧版” | `update`; create a new version directory |
| “直接在看板提交反馈，刷新后还能看到” | Render with the current renderer, start `feedback_server.py`, preserve the separate state directory and deliver the live local URL |
| Implement a feature, approve scope, release | Owning SDD stage; the view grants no authority |

## Establish observations

Read applicable repository instructions and the requested scope. Use an existing
artifact location or the user's destination. State a sensible output directory if
none exists; do not make a new progress ledger or copy contracts. For a large
repository, select the relevant subsystem and label the boundary honestly.

Inspect current requirements/decisions, tasks, code and verification evidence as
needed. Record established facts and unknowns separately. New projects may show
planned modules as `design`; do not portray them as implemented code. File hash
agreement proves identity, not approval, semantic correctness or completeness.
For tests or decisions, cite all load-bearing source baselines (including the
contract/code when relevant), so changing them invalidates dependent judgments.

Create a small observation JSON using this data contract:

| Field | Meaning |
| --- | --- |
| `project_id` | Stable identity across versions; a different project starts a new view |
| `title`, `scope`, `captured_at` | Plain title, explicit coverage/omissions, observation time |
| `next_id` | Optional ID of the actual next-action item; that item must include a concrete `next` |
| `items` | Observations; can be empty when nothing is established |
| Item `id`, `label` | Stable unique identifier and human-readable name |
| Item `view` | `progress`, `diagram`, `design`, `capability`, `structure`, or `impact` |
| Item `kind` | `approved_contract`, `design`, `code_observation`, `runtime_evidence`, `assessment` |
| Item `state` | `SATISFIED`, `PENDING_HUMAN`, `GAP`, `STALE`, `CONFLICT`, `BLOCKED_EXTERNAL`, `NOT_APPLICABLE`, `UNKNOWN` |
| Item `note`, `next` | Optional explanation and concrete next action/decision; use actual roles from project context |
| Item `next_label` | Optional short action heading, e.g. “查看运行示例”, when the record label describes an already completed check; does not change state or priority |
| Item `sources` | List of `{path, line, sha256}`; paths relative to `--root`, positive line number, SHA256 from files actually read |
| Structure `group`, `sublabel` | Optional module grouping and short file/responsibility label |
| Structure `from`, `to` | Both present for an observed or planned relation; point to existing structure-node IDs |
| Structure `file` | Optional actual file path relative to `--root`; must also appear in that node's sources. A file appears as one node, even if it serves several functions |
| Capability `implementation_ids` | Optional file-node IDs implementing this function; the capability must cite each linked file. Both directions are navigable |
| Diagram `artifact` | Root-relative path to a separately delivered `.html` diagram. Sources must cite the HTML and its load-bearing basis; it is never embedded, rewritten or treated as a code node |
| Design `mermaid` | Exact Mermaid source copied verbatim from the cited contract section; flowchart, sequence, state, class and ER diagrams render inline with the bundled offline Mermaid engine |
| Design `technical_mermaid` | Optional exact source of a corresponding technical view from cited design material; collapsed under technical details, preserving code identifiers and signatures |
| Design/Diagram `related_ids` | Optional pairing between a contract-bound design view and a delivered standalone diagram of the same subject; declare it once on either item, links render on both sides |
| Item `decision` | Source/version-bound question with `id`, `kind`, `prompt`, `owner`, `scope` and explicit `options` for approval/choice; see human-decisions.md |
| Item `decision_ref` | Owning item ID for a shared decision; used by several design views so the user answers one scoped gate |
| Item `review_note` | Optional short summary of already received feedback; cite the actual response in sources and do not portray it as acceptance of the new version |

Choose the actual next action from scope and dependencies, then set `next_id` when
several unfinished items compete. A deferred business decision does not outrank
ready technical work merely because it awaits a person. Make the headline,
`next_id` and the selected item's `next` agree. Source identity problems still
come first and override this selection; without a selection the first unresolved
progress record is shown in input order.

For an engineer-facing overview and the requirement → slice → implementation →
verification reading path, use the optional typed `work` extension in
[project-view-mainline.md](project-view-mainline.md). It provides goal/scope,
acceptance conditions, execution columns with dependencies/blockers and a coverage
matrix. Author individual source-bound records; missing relationships remain gaps.
Keep execution status, recorded test result and evidence/approval state distinct.

For stage-specific rules, clarification, implementation/test records and delivery,
read [project-view-stage-details.md](project-view-stage-details.md). Its optional
`stage_detail` records organize constraints, commands, context, test runs, outputs,
usage and follow-up without inventing missing progress or delivery facts.

Optional snapshot `context`, `headline`, `summary`, `map_note` control display text.
Use the user's language and familiar project terms. Defaults are Chinese. Empty
or unverifiable sources become UNKNOWN, even when the submitted state says passed.
Do not include secrets or unrelated source contents in observations.

### Follow the SDD stages when the user wants process visibility

For a lifecycle experiment or a request to follow development from requirements
through delivery, use the optional stage view. It keeps the project title visible,
then shows the current stage and next action, the fixed stage navigation, the
selected stage's actual records, and source details. Do not require this view or
new records for every small change.

Use these exact names and order:

| Stage | Chinese subtitle | Relevant content when available |
| --- | --- | --- |
| `Constitution` | 项目规则 | Rules, constraints, verified commands |
| `Align` | 需求澄清 | Intent, terms, choices and unresolved questions |
| `Spec` | 需求规格 | Scope, behavior and acceptance conditions |
| `Plan` | 方案设计 | Planned business flows, structure, storage and verification |
| `Tasks` | 任务拆分 | Behavior slices, dependencies and current execution card |
| `Implement` | 开发与测试 | Actual code, running behavior and test evidence |
| `Converge` | 对照验收 | Requirement-by-requirement review, evidence and gaps |
| `Finish` | 交付收尾 | Delivery, operation, handoff and rollback |

Do not invent a different stage vocabulary for each project. Test evidence appears
as it is obtained during Implement; it need not wait for Converge. Align has no
empty module map or fabricated test totals. Plan diagrams remain explicitly
planned until implementation evidence supports new observations. Business flows
and code structure stay separate diagrams with distinct labels and sources.

Add this object to an otherwise normal observation JSON:

```json
"lifecycle": {
  "current_stage": "Align",
  "stage_items": {
    "Constitution": "project-rules",
    "Align": "intent-clarification"
  }
}
```

Each `stage_items` value identifies an existing `progress` item with the matching
`stage` and at least one source. The current stage must be bound. Stage bindings
are ordinary assessments of the cited baseline, not a second ledger or automatic
approvals. Cite all load-bearing contracts, approvals and results in these items;
a later implementation cannot prove an earlier gate. The stage record's meaning,
authority and limits belong in its note and source document.

An item may include `stage` using one of the eight exact names. With `lifecycle`
present, every used stage must have a binding. Items without a stage remain
accessible as project-wide records. Do not use stage tags as a way to silently
hide existing evidence. Unknown stage names, unmatched or missing bindings,
source-free bindings and unrecognized lifecycle fields are rejected. Without
`lifecycle`, old inputs keep the previous layout.

Earlier stages with current `SATISFIED` bindings display “已有阶段证据”, not
automatic human approval. Changed/missing binding sources invalidate that
stage's displayed claim. If the current binding becomes stale or unknown, the
header says “当前阶段需核对”. Unentered stages show “未开始”. When returning
upstream, retain later-stage bindings and records: they show “待重新核对” rather
than masquerading as never started or still complete. Record the return reason
and invalidated downstream artifacts in an impact item and update reason.

[The stage-view observation template](project-view-lifecycle-template.json)
shows the minimal shape. Replace its placeholder paths and hashes with actual
read sources before rendering. It intentionally carries no invented approval,
code, test counts or module structure.

### Show the plan's design views on the board

For pending approvals, choices or missing inputs, provide an actionable question
and reply route using [human-decisions.md](human-decisions.md). Several views can
share a single gate. Board selection creates a response draft for explicit
submission in the project conversation; it does not approve or alter a contract.
Optional `feedback` can instead be submitted directly through the explicitly
started local feedback service. The overlay updates feedback receipt status only;
it never changes an engineering state or marks a stage approved.
The controller records the actual human decision and generates the next snapshot
after checking the exact baseline. Use specific labels (design review, requirement
confirmation or missing input) instead of calling every gate a business decision.

When the project's Plan carries the design-view set (system context, business
flow, structure, data/state, module designs), surface each view as one `design`
item instead of leaving it buried in the contract file:

- `view: "design"`; `kind: "design"`, or `approved_contract` only when citing an
  approved plan baseline; `stage: "Plan"` in lifecycle mode;
- `label` in everyday language (系统上下文图 / 业务流程图 / 模块结构图 /
  数据与状态图 / 模块设计·<模块名>); `note` states which question the view answers;
- `mermaid` copied **verbatim** from the plan section — never redrawn, merged or
  improved on the board side;
- `sources` citing the plan section (path, line, SHA256), plus the design review
  record when one exists; `state` reflects the design gate: `PENDING_HUMAN`
  while review is outstanding, `SATISFIED` only with a current approval basis.

The board embeds the pinned Mermaid 12.2.0 browser engine, its license and a
consistent theme; it loads no CDN, remote fonts or diagram service. Flowcharts,
sequence diagrams (`alt`/`loop` included), state diagrams, class diagrams and ER
diagrams are rendered as SVG. Other engine-supported types may be used when
appropriate and must be visually verified. Python generation still uses only
the standard library; consuming the interactive diagrams requires a modern
browser with JavaScript. The bundle adds about 5 MiB only to boards with designs.

Each view offers zoom, fit, enlarged reading, SVG export and the original source.
Long diagrams scroll within their canvas rather than truncating labels. The
enlarged view retains the source record's state. Invalid/unsupported definitions
show a local error and preserved source without blocking other diagrams. With
JavaScript disabled the exact source remains readable. Board-controlled theme
and security settings cannot be overridden with diagram init directives or YAML
configuration; such definitions show their source and a diagnostic instead.

Rendering never edits the Mermaid; after the Plan changes, re-read it and generate
a new version. A rendered picture is not design approval: unapproved views stay
visually distinguishable, and the Plan remains the single source of the design.
Use notes to state scope/level and the question each diagram answers. Select views
by design concern, including runtime interaction, data, state, interfaces,
deployment or trust boundaries when relevant; the overview set is not a ceiling.
Missing design detail must be resolved in the Plan rather than invented by VIEW.

### Reading and language

Default UI headings use the user's language. In Chinese projects, stage labels,
diagram titles, roles, actions and state descriptions are Chinese; canonical stage
codes remain stable in data and source references. Preserve proper product names,
API methods, case-sensitive symbols and file paths where they are actually needed.
Do not alternate translated and raw labels arbitrarily or blanket-change casing.

Author Chinese aliases/labels in cited design material; never rewrite an old
contract or replace arbitrary SVG text to translate code identifiers. A readable
overview and optional `technical_mermaid` expose two levels from the same review
material. The overview explains responsibilities; technical details retain literal
types, signatures and state IDs. The renderer may localize the standard sequence
frame notation labels (branch, loop, etc.) in the reading view only.

Design views form a gallery with a topic index and one selected view. On a narrow
screen the index becomes a compact chooser. Preserve deep links and all records;
with no JavaScript every source remains readable. Put optional feedback after the
reading area; show actual blocking questions explicitly. Avoid a large form ahead
of the diagram, three equal-weight submission actions, raw JSON in a copied reply,
or approval jargon for a cosmetic suggestion. Evidence and historical diagrams
remain accessible in quiet, expandable sections.

A design view and a delivered standalone diagram may describe the **same
subject at different fidelities** — the design view is the contract snapshot
(what was planned; invalidated when the plan changes), the diagram is the
delivered explanation (how it works now; carries its own receipts). When both
exist, pair them once with `related_ids` on either item; both cards then link
to each other. Pairing is navigation, not shared evidence: each side keeps its
own sources, states and freshness, and one side going stale never contaminates
the other.

### Save development history when it actually happens

When the user asks to observe the process, create the first snapshot at the first
actual stage. Do not reconstruct an apparent Align snapshot after finishing the
implementation. Add a new immutable version after a stage transition, requirement
change, context handoff, or material verification result. A new version links its
predecessor; use the existing snapshot/receipt chain instead of creating a parallel
progress ledger. This is a bounded process-observation mode, not a requirement
to generate a dashboard for every small task.

When screenshots are requested, capture the **actual generated HTML in a browser**
at these milestones. Preserve the PNGs next to the experiment evidence, recording
the snapshot path, HTML hash, capture time and viewport dimensions. Use consistent
dimensions for comparison; capture a narrow viewport when checking responsiveness.
Inspect the saved image before claiming visual verification. A textual description,
HTML source inspection or retrospective mockup is not screenshot evidence.
Preserve failed or awkward versions as historical observations; improve the next
version rather than overwriting them.

### Write for the team reading the board

Write `headline` as a concrete result, `summary` as what people can now do and the
material limit, and `next` as one useful action. Module `label` names a capability;
`note` briefly explains its input, result or responsibility. Keep task codes,
function names and necessary technical distinctions in details or `sublabel`.
For example, “当前结果投影” becomes “查看每条命令最近一次的结果”; “检查点恢复”
becomes “中断后接着处理”, with the actual supported interruption scope explained
in the note. Do not merely substitute jargon mechanically: re-read its meaning.

Use the default function list for first reading, then expand the complete module
connections when needed. Code calls, data dependencies and user workflow are
different; name the actual relation and never invent a sequence to simplify it.
Do not hide gaps or changed sources, call evidence-backed observations “验收通过”,
or present simulated decisions / AI handoffs as human acceptance. Preserve stable
IDs and all source references when rewriting labels. An empty impact section is
omitted instead of adding a placeholder.

### Make structure correspond to the repository

A feature list is not a repository architecture. Read the directory and actual
entry points/imports/calls before authoring a structure view. Name the specific
repository/subsystem being shown, especially for an experimental clone.

Use `capability` for what the product does and `structure` with `file` for its
actual files. Keep the capability label in everyday language; show file names
and paths in the structure map. Link functions to file nodes with
`implementation_ids`. Several functions sharing one file do not become several
independent modules. For a new unimplemented design, use the existing design
observations; do not claim planned paths are current files.

Each file node cites that exact file. Each connection cites the inspected call,
read/write or other relationship and explicitly names its meaning. A simple
directed chain is drawn with labeled arrows; branches and cycles retain explicit
endpoint connections, rather than being flattened into a fictional sequence.
Sample inputs, tests and handoff documents appear at their real locations.
Describe generated data separately from source files; a path pattern in code is
not evidence that a runtime file currently exists. The selected file tree is a
bounded map, not an automatically inferred complete repository inventory.

Legacy observations without file identity still render as conceptual module
maps. Do not relabel those as repository structure. When replacing a conceptual
graph, explain the reclassification/removal in the update reason and preserve the
previous bundle. Merely changing a label or refreshing hashes cannot establish a
file-to-function relationship.

### Explain how the project works, separately from file ownership

When people ask how the project works, a file tree or call graph alone is
insufficient. Show two distinct reading paths: components and their code/data
boundaries; and business input → checks/transformation → saved result → use/export.
Add a separate recovery flow when branches would obscure that main path.
Read the actual entry points, storage operations and relevant tests first.
For failures, explain which input is rejected, what is saved, what retries,
whether retry starts a new attempt, and what an interrupted attempt skips when
continued. State unsupported recovery boundaries. Do not imply an arrow from
one file to another is the user's workflow, or label ordinary code as an AI agent.

If the user requests Archify and it is available, use its skill to author,
deliver and browser-check standalone diagrams. Otherwise use an appropriate
available renderer; the board needs no externally installed runtime dependencies. Preserve exact
delivered HTML/specification/receipts. Use full-size viewers, not a compressed
diagram inside the detail column, and keep the existing file/function mapping
as a supplementary reference. Review default legends for misleading labels.

Attach each delivered diagram as an item with `view: "diagram"`, its own stable
ID, plain-language question/label, short explanatory `note`, and `artifact`.
Cite the HTML, diagram specification, delivery/check receipts, and all code,
contracts or tests carrying its claims in `sources`. Include a node-to-source
mapping when diagram-native evidence links are unavailable. Never invent a
repository remote to enable a renderer's source feature. Source identity checks
do not prove geometry, visual quality or business correctness.

The board lists these diagrams separately, with “打开图示” and “查看依据”.
Only `SATISFIED` diagrams with current sources get the primary open link;
changed/missing sources remain visible and their historical files remain in
the evidence details. `update` without new input invalidates outdated diagrams;
it does not regenerate them or reapprove their meaning. Re-read affected sources,
generate a new diagram and then update the observations with a reason. Keep
the predecessor and its diagrams intact. Artifact links are relative to the
new board; preserve that directory relationship when transferring files.

For example, after actually reading the registration implementation, create a
minimal observation (run from that project's root and adapt scope/state to what
was found):

```python
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
source = Path("src/register.py")
observation = {
    "project_id": "equipment-loan", "title": "设备借用", "scope": "仅设备登记模块",
    "captured_at": datetime.now(timezone.utc).isoformat(),
    "items": [{"id": "register", "label": "设备登记", "view": "structure",
        "kind": "code_observation", "state": "SATISFIED", "group": "设备借用",
        "note": "登记设备后返回借用编号。", "sources": [{"path": str(source), "line": 1,
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}]}]
}
with Path("observations.json").open("x", encoding="utf-8") as output:
    json.dump(observation, output, ensure_ascii=False, indent=2)
```

This establishes only an observed module, not completed development. A planned,
unimplemented module instead cites its plan with its actual design/gap state.

## Run the bundled renderer

Locate `scripts/project_view.py` relative to this skill, not a developer's home
directory or a past case. Requires Python 3.10+ standard library only.

```bash
python3 /path/to/sdd-workflow-router/scripts/project_view.py check --root /path/to/project --input observations.json
python3 /path/to/sdd-workflow-router/scripts/project_view.py render --root /path/to/project --input observations.json --output /path/to/project/artifacts/view-v1
python3 /path/to/sdd-workflow-router/scripts/project_view.py update --root /path/to/project --previous /path/to/project/artifacts/view-v1 --output /path/to/project/artifacts/view-v2
```

Each version contains `index.html`, `view.md`, the exact input `snapshot.json` and
a final `receipt.json`. Existing outputs cannot be overwritten. An interrupted
directory without a valid receipt is incomplete; preserve it and use a fresh
output name. Source paths outside the declared root, including escaping symlinks,
are rejected. For multiple repositories choose their explicit common source root
and label each group; do not infer cross-repository calls from similar names.

Exit `0`: all listed sources match. Exit `2`: the view was generated but some
sources are changed/missing/unverifiable; surface the gap and next investigation.
Exit `1`: input, output or lineage error; no valid new delivery may be claimed.
Generation does not run tests, infer all architecture, or perform business review.

## Update without erasing history

`update` without `--input` reuses the exact previous observations and only checks
sources again. It never updates expected fingerprints or promotes old judgments.
Changed/missing source identity invalidates affected nodes and their relations.
The new view links its predecessor; its receipt binds previous receipt identity,
input/output hashes, source checks and added/removed/modified observation IDs.

For a real change, first read the changed sources and affected decisions/tests.
Revise observations with actual new evidence and observation time, keeping stable
IDs where the subject is unchanged. Then use `update --input revised.json --reason
"what was re-read and why the judgment changed"` with the other arguments above.
A changed observation set or source-root relocation requires a reason. The reason
is a recorded assessment, not proof of human approval. Changed business intent or
invalidated contracts still belong to change-impact/the owning stage.

The preceding bundle must be intact. A modified old HTML/snapshot cannot be
silently treated as a trusted parent; preserve and investigate it. Roll back by
opening any intact previous `index.html`, not overwriting the latest one. If no
trustworthy parent exists, render a fresh view and state that lineage limitation.

## Verify and deliver

Open the exact generated HTML when a browser is available. Check the progress and
next action, the default module list, expanded diagram and every relation,
expanded evidence and one actual evidence link, keyboard selection/return and
a narrow viewport. Check that planned/unverified work remains identifiable without
opening the diagram. For a repository map, also follow a function to its actual
file and back, and compare the displayed paths with the repository. For attached
diagrams, follow every primary link to the exact delivered artifact, inspect
node details and source evidence, and verify that changing code or the diagram
invalidates its observation. Look at the rendered result, not only HTML
source. If browser verification is unavailable, report that limitation explicitly.
Scripts, styles and data are embedded; original evidence links need the source
files at their current local paths. Recheck/regenerate after moving to a new root.

Small grouped DAGs use automatic SVG layout. DAGs deeper than three levels use
vertical layers of up to three modules, with skip edges routed outside the nodes;
the existing node/edge and total-height limits still apply. Larger, cyclic or cross-group
structures use readable grouped modules and explicit endpoint relationships;
all records remain selectable. Do not shrink text or omit relationships just to
claim a one-screen graph. Long labels remain complete in details and accessible
labels. The page is a snapshot, not a live monitor.

Return the HTML link, scope, what was actually verified, remaining unknowns and
previous-version link when present. Distinguish view generation from project
completion. Reference this bundle during handoff, while still rechecking the
primary contracts and source evidence before continuing work.
