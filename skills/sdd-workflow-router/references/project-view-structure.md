# Project view: repository structure

Read only when explaining module relationships or business/data flows. A simple
file node used by a task needs only the common fields in [project-view.md](project-view.md).

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
