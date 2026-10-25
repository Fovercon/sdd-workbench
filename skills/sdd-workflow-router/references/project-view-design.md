# Project view: design diagrams

Read only when authoring design/Mermaid or standalone diagram records. Common
fields, source boundaries and commands remain in [project-view.md](project-view.md).

| Field | Meaning |
| --- | --- |
| Diagram `artifact` | Root-relative path to a separately delivered `.html` diagram. Sources must cite the HTML and its load-bearing basis; it is never embedded, rewritten or treated as a code node |
| Design `mermaid` | Exact Mermaid source copied verbatim from the cited contract section; flowchart, sequence, state, class and ER diagrams render inline with the bundled offline Mermaid engine |
| Design `technical_mermaid` | Optional exact source of a corresponding technical view from cited design material; collapsed under technical details, preserving code identifiers and signatures |
| Design/Diagram `related_ids` | Optional pairing between a contract-bound design view and a delivered standalone diagram of the same subject; declare it once on either item, links render on both sides |

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
