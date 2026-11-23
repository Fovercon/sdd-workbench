# Checkpoint helper

Use these commands and fields when maintaining an actual checkpoint. For a new
one, the full installation includes [loop-state.example.json](../evals/loop-state.example.json).
In a runtime without examples, use the field table below. Store the checkpoint
in the project's established task or evidence location. Give the checkpoint's
absolute path when calling from another directory. File references inside the
checkpoint resolve relative to `--root`. The helper uses the Python 3 standard library.

```bash
python3 /path/to/sdd-workflow-router/scripts/sdd_loop.py identity /path/to/project/loop.json --root /path/to/project
python3 /path/to/sdd-workflow-router/scripts/sdd_loop.py status /path/to/project/loop.json --root /path/to/project
```

`identity` computes hashes from actual files. After executing and assessing work, the Agent records these identities in receipts. Never update a receipt's baseline without rerunning the relevant work. `status` returns exactly one route or stop; the Agent executes, updates the checkpoint with truthful evidence, then calls it again. `COMPLETE` is a checkpoint consistency result, not independent verification that the descriptions, authorization or semantic claims are true.

Required checkpoint fields:

| Field | Content |
|---|---|
| `schema` | `1` |
| `mission` | Intent; authorization source; `continuous`; `technical_delegation`; `delivery` target/destination/authorized; `maintain_method`. |
| `mandatory` | Nonempty unique engineering acceptance IDs required for convergence. Keep delivery-dependent acceptance in the named Finish target and verify it in the actual delivery receipt; never drop an obligation to pass a gate. The Spec retains the complete chain. |
| `observed`, `conflicts`, `pending_decisions`, `change_pending` | Actual recovery/ownership/decision/impact state. |
| `budget` | `steps`, `max_steps`, `no_progress`, `max_no_progress`; integers, positive limits. |
| `contracts` | `spec` and `plan`, null until created. Each has `path`, `sha256`, `basis`, `sources`, `quality_passed`. Spec basis is `USER_APPROVED` or `AUTHORIZED_DERIVATION`; Plan basis is `USER_APPROVED` or `DELEGATED_TECHNICAL`. |
| `slices` | ID, dependency IDs, linked `acceptance`, `done`, and receipt after closure. Receipt has contract identity and hashed report. |
| `source_files` | Nonempty exact relevant source/configuration/test/dependency/asset manifest before verification. Include generated deliverables when their content matters. Review the manifest against actual diff and project policy. |
| `verification` | Null or baseline, command(s), integer `exit_code`, covered acceptance IDs and hashed report. This aggregates all required checks, not merely a selected passing subset. |
| `review` | Null or baseline, `outcome`, covered IDs, findings and hashed report. Findings have `id`, `severity`, `status`, `route`; unresolved ones route to `IMPLEMENT`, `PLAN` or `REQUIREMENTS`. Use `CLOSED`, or `ACCEPTED`/`DEFERRED` with a current decision receipt: baseline, hashed report, actual `authority_source`, and `policy_allows=true`. Without that evidence the helper stops for a decision. The controller must verify the source and policy, not invent risk acceptance. |
| `finish` | Null or delivery identity, `ready`, hashed report and optional receipt. Receipt has delivery identity, `verified` and hashed result report. LOCAL still needs an actual deliverable receipt. |
| `learning` | Hashed short `record`, `changed_assets` list and regression if assets changed. Regression has method identity, `passed` and hashed report; include old/new results and behavior evaluation limits. |

An artifact reference is `{"path":"evidence/report.md","sha256":"actual sha256"}`. Source identity includes current Spec/Plan hashes and every source-file path/hash. Delivery identity additionally includes the target and destination. Method identity includes all changed method assets. Missing/changed report files invalidate that gate. Historical slice reports remain valid process records as source evolves, but their contract identity must still match; final whole-scope checks are current.

The helper deliberately fails closed on malformed checkpoints, cycles, unknown dependencies and unsafe paths. It cannot discover an omitted file, omitted requirement, fabricated report, secretly weakened test or false authorization. The controller and reviewer must audit those claims. Do not add a mandatory JSON ledger to a trivial task when an existing task record suffices; apply the same invariants directly.
