# SDD Workbench maintenance

This repository is the release source for the SDD Workbench suite. Preserve each
skill's stage boundaries and use the smallest relevant workflow. Installing the
suite does not require loading every skill into a project conversation.

- Reserve `main` for validated release integration. Make skill optimizations,
  documentation drafts and evaluation-framework changes on `codex/*` development
  branches; check the current branch before editing. Select release-ready changes
  for review before merging into `main`. Preserve existing history and tags.
- Keep reusable skills in `skills/`. Project examples, actual feedback databases,
  personal paths, presentations and upstream experiment archives are not package inputs.
- `plugin.json` owns the suite version. `tools/package.py bump VERSION` updates
  the Codex compatibility projection. Do not edit published tags or reuse a version
  for different release contents.
- Keep the skill list in `suite.json` aligned with actual directories. Preserve
  bundled Mermaid bytes and its notices unless explicitly upgrading that dependency.
- The Python installer owns only its recorded skill directories. Preserve unmanaged
  skills and user edits, retain upgrade backups, and recover incomplete transactions
  before further writes. Test installation under temporary destinations.
- Do not change the developer's live skill installation while testing releases.
- For packaging-only changes, run `python3 tools/package.py check`,
  `python3 -B -m unittest discover -s tests`, and the bundled router unit suite.
  UI or local feedback changes also need the relevant real browser regressions.
- A green structural or deterministic suite does not establish model behavior.
  Method changes require the affected forward evaluation described in the skills.
- Method changes also feed the regression harness maintained on the development
  branch: run `python3 evals/regression/run.py --profile standard` there against
  the exact candidate skill snapshot. It measures trigger, end-to-end and process
  layers against any accepted baseline; artifacts default to `~/.sdd-regression/`
  outside the repository unless `SDD_REGRESSION_ARTIFACTS` redirects them. Marking
  a new accepted baseline with `--accept` stays an explicit user decision.
- For future Pi runs, use the user's preferred DeepSeek Flash model. Resolve the
  registered ID before execution (currently `deepseek/deepseek-flash`), specify it
  explicitly, and record the reported identity; the alias alone does not establish
  a backend revision. Keep historical runs under their actual recorded models.
- Release with the tagged workflow after checks pass. Publishing or pushing requires
  the user's existing authorization; do not infer it from a status inquiry.
