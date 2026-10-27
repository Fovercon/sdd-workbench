# Synthetic job-store planning fixture

Use Python standard library on a single Linux host, a local filesystem and two
independent processes. External services/dependencies and remote filesystems are
excluded. Planning-only; SPEC.md is product authority, design/plan.md is design,
design/tasks.md owns slices and any draft current card. No human Plan approval yet.
Inspect sources and tests, do not execute project tests or modify existing files.
Only create design/plan.md, design/tasks.md and optionally design/plan-receipt.json.
No external writes, sibling trial/controller metadata reads, network, installation,
background processes, Git commits/push or publication. Supplied skill references
in ../runtime are readable. Preserve legacy.json and user-notes.txt exactly.
