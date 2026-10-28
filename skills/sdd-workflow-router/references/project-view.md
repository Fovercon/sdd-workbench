# Project view: generate and update

## Contents

- [Choose the operation](#choose-the-operation)
- [Author from sources, through the public interface](#author-from-sources-through-the-public-interface)
- [Read only the requested mode](#read-only-the-requested-mode)
- [Evidence and stage meaning](#evidence-and-stage-meaning)
- [Run and interpret results](#run-and-interpret-results)
- [Preserve history](#preserve-history)
- [Verify and deliver](#verify-and-deliver)

A requested board is a derived offline snapshot. It explains progress, responsibilities,
next actions and evidence; it does not approve work, run business tests or replace
project contracts. A new lifecycle, approved Spec or architecture tool is not a prerequisite.

## Choose the operation

| User request | Operation |
| --- | --- |
| Ask status/next action without requesting a board | Diagnose read-only; do not create view files |
| Create a view | Read bounded project sources, author observations, `render` |
| Check changed sources | `check --summary`; no writes |
| Follow declared downstream dependencies of selected items | `trace --changed-id ID`; no writes, no board required |
| Refresh a view while retaining history | `update` to a fresh sibling directory |
| Save feedback directly in a board | Use [human-decisions.md](human-decisions.md) and the bundled loopback service |
| Implement, approve or release | Owning stage and actual authorization; VIEW grants neither |

Use the project's existing artifact convention or the user's destination. State the
chosen output path if none exists. For a large repository, select and label the relevant
subsystem; do not read every project document, archived plan or log as background.

## Author from sources, through the public interface

1. Read applicable project instructions and the current facts needed for this board.
   Keep actual scope, source versions, unknowns and pending human questions distinct.
2. Run the bundled CLI's **`describe`** command once for accepted fields, role/stage
   bindings and required values. It is a read-only authoring guide, not a source check.
3. Read only the relevant mode below. Write one small observation JSON; compute raw
   file SHA256 values in code from files actually read, rather than hand-copying the
   same fingerprint throughout a long tool call. A helper may fill mechanics, never facts.
4. Run **`check --summary`** on the draft, then `render`. Fix reported errors through
   the public contract first. Do not inspect renderer/validator internals before a
   concrete unresolved failure; normal authoring should not reverse-engineer the tool.
5. Keep full observations and receipts in their files. Inspect bounded record fields
   against the sources, and perform the actual browser checks requested/available.

Do not dump generated HTML, embedded Mermaid/JavaScript, the full receipt or repeated
`view.md` into context. The renderer writes the exact snapshot and integrity receipt;
printing them again does not verify business meaning or a browser flow. For a failing
source check, redirect full `check` JSON to a file and retrieve only the affected items.
Read a targeted implementation module only when a real tool defect remains unresolved.

## Read only the requested mode

| Needed content | Reference |
| --- | --- |
| Goal/scope, requirements, slices/dependencies and acceptance mapping | [project-view-mainline.md](project-view-mainline.md) |
| Rules, clarification, implementation/test records, delivery and usage | [project-view-stage-details.md](project-view-stage-details.md) |
| Mermaid design or standalone diagram artifacts | [project-view-design.md](project-view-design.md) |
| Module relationships, repository maps and business/data flows | [project-view-structure.md](project-view-structure.md) |
| Real scoped decision/approval or requested direct feedback | [human-decisions.md](human-decisions.md) |

Simple file nodes linked to tasks need only `describe`'s file-node contract. They do
not require the full repository-map reference. Do not load the diagram/structure
modes just because the renderer supports them. The lifecycle JSON template is an
optional example, not another required document or a source of real decisions.

## Evidence and stage meaning

Use stable item IDs. Set a concrete `next` on the selected `next_id`, aligned with
scope and dependencies. A nonblocking human question does not outrank dependency-ready
technical work merely because it awaits a person. Source identity problems take priority.
Without `next_id`, unresolved progress records retain input ordering.

Each source names an actual root-relative file, positive line and raw-byte SHA256.
Cite all load-bearing contract, code and report baselines for a claim. Missing or
unverifiable sources remain UNKNOWN even when the submitted state says passed.
Hash agreement proves identity, not approval, semantic correctness or completeness.
Do not include secrets, unrelated source contents or invented roles/decisions.

Use the eight exact stage names returned by `describe`; do not rename the vocabulary.
With `lifecycle`, bind every used stage and the current stage to an existing sourced
`progress` item with the same stage. These bindings are assessments of actual records,
not a parallel ledger or automatic approval. A binding's meaning and authority belong
in its note and source. Without lifecycle, existing plain observations retain their layout.

Test evidence can appear during Implement. Align needs no fabricated module map or
test totals. Plan diagrams remain planned until actual implementation evidence supports
new observations. Retain later-stage records when returning upstream; source/stage
warnings withdraw their current support while preserving historical results. Record
real return reasons and invalidated contracts in an impact item and update reason.

Write titles/notes in the user's language: concrete behavior, input/result, material
limit and one useful next action. Keep case-sensitive symbols and actual paths intact;
put technical detail in its field/detail pane. Preserve stable IDs and source references
when rewriting labels. Do not rename evidence-backed observations “验收通过”, simulate
human approval or hide gaps. Design-specific bilingual views and pairing use their mode reference.

## Run and interpret results

Locate `scripts/project_view.py` relative to the selected skill, not a personal home.

```sh
python3 /path/to/sdd-workflow-router/scripts/project_view.py describe
python3 /path/to/sdd-workflow-router/scripts/project_view.py check --summary --root /path/to/project --input observations.json
python3 /path/to/sdd-workflow-router/scripts/project_view.py trace --root /path/to/project --input observations.json --changed-id R1
python3 /path/to/sdd-workflow-router/scripts/project_view.py render --root /path/to/project --input observations.json --output /path/to/project/artifacts/view-v1
python3 /path/to/sdd-workflow-router/scripts/project_view.py update --root /path/to/project --previous /path/to/project/artifacts/view-v1 --output /path/to/project/artifacts/view-v2
```

Every version contains `index.html`, `view.md`, exact input `snapshot.json` and final
`receipt.json`. Paths outside the declared root, including escaping symlinks, are
rejected. Use an explicit common root for multiple repositories and label omissions;
similar filenames never prove cross-repository calls.

Exit 0: listed source identities match. Exit 2: source identities are changed/missing/
unverifiable; rendering may still produce an honest warning view. Exit 1: input/output/
lineage error; do not claim a valid new delivery. `describe` performs no verification.
`--summary` only shortens check output: recorded states stay unchanged and omitted IDs
are explicitly counted. Full `check` JSON remains available. Neither mode runs tests,
checks all business obligations, grants approval or proves project completion.

### Query existing dependencies

When observations already exist, `trace` reuses their links rather than requiring
another trace table. Repeat `--changed-id` for shared constraints or multiple
selected records. It returns the input SHA256, all item IDs, direct dependencies
and reached-via links: `CHANGED_INPUT`, `REACHED`, or `NO_RECORDED_PATH`.
No graph or board is written. Do not create a view just to analyze a small change.

Traversal follows requirement/slice/check links, slice dependencies, implementation
IDs and stage-detail record IDs. Structure relationship records depend on both
endpoints; a module arrow does not make the target module a contract dependent.
`related_ids` only pairs views for navigation and is excluded. Plan decisions and
other relationships not represented by these fields still need source inspection;
do not coerce them into the wrong record type to obtain a complete-looking graph.

The selected change is hypothetical input. Actual `freshness`, original state and
recorded test result remain separate: a proposed change can reach a current PASS,
and a missing source stays UNKNOWN. Exit 2 concerns sources in the entire snapshot,
including items outside the selected paths. File hashes cover whole files, so an
unrelated same-file record may also become STALE. Do not refresh old hashes to
recover green status. `NO_RECORDED_PATH` does not prove independence or UNCHANGED;
missing links require investigation. Neither reachability nor source identity
chooses an owning stage, invalidates a contract, executes tests or grants approval.

## Preserve history

Existing output paths cannot be overwritten. An interrupted directory without a valid
receipt is incomplete: preserve it and choose a fresh name. `update` without `--input`
reuses the exact prior observations and only rechecks sources; it cannot refresh expected
fingerprints or promote old judgments. Receipts bind input/output hashes, source checks,
previous receipt identity and observation changes; old bundles must remain intact.

For an actual judgment change, read the changed sources and affected decisions/tests,
revise observations and time while keeping stable subject IDs, then use `update --input
revised.json --reason "what was re-read and why the judgment changed"`. Changed observations
or source-root relocation require a reason; this assessment does not create approval.
Business/contract drift still belongs to change-impact or the owning stage.

A trustworthy history is made when events happen. If process observation was requested,
create the initial view at the actual stage, then new versions for material stage,
contract, handoff or verification changes. Do not reconstruct a false early snapshot
after implementation or add boards to every small task. Reopen an intact prior version
for rollback; never overwrite it. If no parent is trustworthy, render fresh and state
the lineage limitation.

## Verify and deliver

Use the exact generated HTML in a real browser when available. Check requested content,
next action, pending/unexecuted/planned states, source details and one actual source
link, keyboard/deep links and a narrow viewport. For a repository map, follow function
→ file and compare it with the actual code; for diagrams check primary artifact links,
relations and source invalidation. Scope checks to the actual requested modes.

Look at the rendered result, not only its HTML. If the controller owns browser checks
or a browser is unavailable, report that boundary and do not predict success. Requested
screenshots capture the actual generated page at meaningful milestones; preserve PNG,
snapshot path/hash, capture time and viewport, inspect the image and keep failed versions.
A source inspection or retrospective mockup is not browser/screenshot evidence.

The page is a snapshot, not a monitor. Moving it does not move its cited sources;
recheck/regenerate for a new root. Return the HTML link, actual scope/verification,
remaining unknowns and predecessor link. Handoff may reference the bundle but still
rechecks current primary contracts before implementation continues.
