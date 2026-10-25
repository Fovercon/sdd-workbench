# Held-out recovery pilot

Maintainer evaluation protocol, not an actor instruction or a new product gate.
Keep this file, preparers, probes, mutant identities and expected answers outside
actor context. Inputs are a small synthetic record browser, with no upstream
application, private archive, credentials or real user data dependency.

## Independently reproducible inputs

From a clean checkout (or extracted release ZIP), create a new temporary parent.
The commands below use `/temporary/trial` as that existing parent; choose an actual
writable temporary path. Do not prepare into a live project or installed skills.

```sh
python3 skills/sdd-verification-design/evals/forward/prepare_recovery.py --output /temporary/trial/project --variant preserving --mode execute --skills skills --snapshot /temporary/trial/skills --receipt /temporary/trial/inputs.json
python3 -B -m unittest discover -s /temporary/trial/project
python3 skills/sdd-verification-design/evals/forward/probe_recovery.py /temporary/trial/project
```

The preparer freezes input and runtime skill SHA256s in an evaluator-owned receipt
outside the actor project. It copies only entrypoints/references/runtime resources
to the skill snapshot, excluding evals, tests, probes and caches. Generated projects
contain application code, HTML, synthetic state, original tests, author-approved
synthetic Spec/Plan, ordinary request, rules and a protected note. They do not contain
variant names, scoring oracles or implementation flags describing the defect.
Original fixture source is in [inputs/recovery_app.py](inputs/recovery_app.py),
[inputs/recovery.html](inputs/recovery.html), and
[inputs/test_recovery_baseline.py](inputs/test_recovery_baseline.py).

Variants `preserving`, `lossy`, `stale-error` and `combined` keep the same request,
contracts, seed state and original tests. The evaluator applies only the indicated
controlled parser/UI mutation; actor workspaces use neutral directory names.
The original suite passes every variant. The stronger public oracles must still
separate preserving behavior from the lossy or stale-error behavior.

## Actual actors

1. Prepare independent temporary roots for execution and `--mode design` actors.
   Freeze the chosen Skill snapshot and model/settings before dispatch.
2. Give each actor only its own project, runtime skill snapshot and ordinary
   instruction to carry out REQUEST.md. Do not reveal probes, variant identity,
   suspected defects, another actor's output or this rubric. Explicitly supply a
   preinstalled browser runtime read-only if it is outside the project.
3. Execution actor uses `sdd-converge-review`: actually selects and runs checks of
   ordinary behavior, data preservation and error recovery. It may create isolated
   probes/copies but must preserve supplied source/tests/state/contracts/notes and
   must not repair the original product. Record commands, outputs, browser evidence,
   findings/return stages and unexecuted items.
4. Design actor uses `sdd-verification-design`: writes a faithful verification design,
   concrete inputs, oracles and contract traceability without running/implementing
   tests or claiming execution. Record its designed evidence separately.
5. After actors stop, compare protected-file hashes and inspect raw trace/artifacts.
   Score product and actor separately. If only the evaluator finds a defect, record
   an actor miss. A green original suite does not erase a held-out failure.

## Evaluator-owned oracles

- Persistence: seed known records, verify public GET and POST retain identities,
  then stop/start a **new server process** and verify the same persisted records.
  This is distinct from historical experiments that only created another Ledger
  instance. Duplicate record IDs must be rejected without changing storage bytes.
- Ambiguous state: write syntactically valid JSON with conflicting `records` values,
  then attempt public read and append. Both must reject with a meaningful error,
  preserving the complete original bytes. The lossy variant must fail these checks.
  Duplicate-key rejection is this synthetic fixture's contract, not a universal
  policy for every JSON consumer. `probe_recovery.py` runs only in temporary copies.
- UI recovery: use a real temporary HTTP server and browser; submit a reversed date
  range, observe its operation-specific error, correct the range, verify returned
  record IDs **and** removal of that stale error. Preserve DOM observations for
  both states; source text or HTTP 200 alone is insufficient. The stale-error and
  combined variants must fail the semantic UI oracle while restoring the rows.
- Scope control: Verification Design Case 18 and the Code Review
  [local label fixture](../../../sdd-code-review/evals/forward/repair-handoff.md)
  have no UI/persistence; do not require browser/restart/full-stack checks there.

Run `python3 -B -m unittest discover -s tests -p test_forward_fixtures.py` for the
fixture and public HTTP sensitivity suite. With the repository's pinned Playwright
and an installed browser, run `SDD_BROWSER_CHANNEL=chrome npm run test:forward-browser`
(or `chromium` in CI) for real rendered recovery across all variants and two widths.
Optional `SDD_RECOVERY_EVIDENCE=/temporary/evidence` retains screenshots and DOM
observations outside the package. These are deterministic product/oracle checks;
they do **not** run or establish Agent behavior. No package installation is needed
for the Python fixture/probe; browser dependencies are installed separately.

Compare Skill versions only with identical inputs/settings and fresh actors. One
pilot tests applicability, not reliability, causality, time or token savings. If the
browser is unavailable, report NOT RUN with its recovery condition. Stop temporary
servers, close self-created browser tabs and retain raw failures plus input/Skill hashes.

## Evidence and historical provenance

Current maintained results are recorded in [VALIDATION.md](../../../../docs/VALIDATION.md).
The [frozen upstream evidence](https://github.com/Fovercon/AI-Native-SDD/blob/0dc9414de8d7081bc8c425fe3593dcf44ce3c315/05-notes/2026-10-12-sdd-skill-optimization/evidence/)
is optional historical provenance only; access may be restricted. It is not needed
to run this protocol. The synthetic fixture does not reconstruct or claim to
reproduce the historical application results, and old archives are not repackaged.
