# Original check records implementation plan

**Goal:** Preserve original proof-check output and tested source/test identity
through retries and test revisions, while receipts cite the actual observation.

**Basis:** The user's continuing optimization request and the original-output
loss documented in [stable-card results](STABLE-CARD-ANCHORS-RESULTS.md).
Control is `d315674`; its runtime is byte-identical to tested `660ad2c`.

**Design:** Use the existing recorder for proof-bearing foreground commands when
the current task authorizes an appendable Markdown log and Python is available.
Keep existing project capture/receipt formats where required. Each actual run
gets a fresh role-bearing ID; roles cite observations instead of retyping facts.

## Scope and constraints

- Change only Implement main instructions, its recorder guide, receipt shape and
  existing execution-model clarification, plus maintainer cases/results. No new API, automatic IDs, log
  initialization behavior, dependencies, source copies or mandatory files.
- Proof-bearing commands are RED/baseline, GREEN and required regression. Search,
  file reads and incidental probes do not become another logging requirement.
- Existing project capture with equivalent evidence takes precedence. Preserve
  self-contained required fields, frozen bytes and current write authority.
- Capture actual argv/cwd, complete output, actual child exit and relevant
  production/test/fixture identities before later edits. Hashes identify tested
  bytes; they do not recover historical source contents.
- One actual invocation may cover multiple roles. A later invocation gets a new
  record even when its command is identical. Preserve earlier failed attempts.
- Record successful capture separately from a check passing. Incomplete capture
  cannot establish a successful check.

## Work and acceptance

- [ ] Freeze five fresh control developments, identical initial inputs and prompt,
  before evaluating a new candidate. Existing lost-output cases establish RED.
- [x] Replace named-tool selection with bounded, authorized proof-check capture.
- [x] Make receipt check fields point to the real invocation; preserve required
  inline formats. Keep the capture API unchanged.
- [x] Independently review source before freezing the candidate.
- [ ] Run five fresh matched candidate developments. Primary: all thirty logical
  core roles have retrievable complete original output and matching production
  and test identities. Check actual invocations separately from logical roles,
  wrong failures, repaired tests and later reruns. No overwritten originals.
- [ ] Observe complete child stdout/stderr independently in both arms. Compare
  existing recorder records with actual child processes and native tool results.
  Observe original content at first persistence, not only the final snapshot.
- [ ] Preselect t1–t3 from both arms for two new readers each, same control
  runtime. Distinguish raw recovery, summaries, identity and current applicability.
- [ ] Check self-contained/frozen layouts and project-pinned capture fallback
  without authorizing new files or weakening evidence requirements. Report
  unavailable-Python behavior only if that environment is actually exercised.
- [ ] Measure duplicate detail, mutations, whole-flow requests/input/cache/output
  and tool-return bytes. Record actual gains, regressions and selection differences;
  no lower-cost claim follows from fewer lines or recorder adoption alone.
- [ ] Run the exact final candidate's standard regression and required local
  checks, using explicit registered DeepSeek Flash. Do not accept a new baseline.
- [ ] Keep, revise or drop the method from the observed evidence, and record
  unresolved guards before integration into the development branch.

## Deferred

Automatic IDs are not an observed blocker: all sixty-two prior explicit recorder
calls supplied valid distinct IDs. Compact verification output is a separate
cost experiment. This batch changes neither mechanism.
