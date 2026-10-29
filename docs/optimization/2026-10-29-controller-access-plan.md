# 原生评测的控制文件读取检查

> Use `executing-plans` inline; one fresh whole-branch review at completion.

**Goal:** Stop final-file and code guards from hiding explicit requests to read
controller-owned trial metadata. Preserve raw event locations for adjudication.
**Architecture:** Add a small read-only Pi event auditor beside the existing context
protocol. Resolve structured `read` paths and literal `cat` operands against the
trial's project cwd, including simple shell `cd` segments. Integrate observed read
requests into the existing workflow guard; never equate no matches with compliance.
**Tech Stack:** Python standard library, existing unittest and recorded Pi streams.
**Spec:** User instruction to continue the integrated POST-0.5.0 roadmap, stage6;
Task11's preserved controller-content reads and the evaluator's missing history check.
The bounded audit mechanism is the maintainer's implementation choice.

## Global constraints

- BASE `267d4d1`, existing clean `codex/skills-optimization` worktree. No primary
  checkout, other agent's L2/L3, runtime skills, live installation or release changes.
- The caller's project/runtime remain the authorized actor inputs. Fixed controller
  paths belong to the trial root; a project file sharing a basename is not one.
- Do not execute logged commands or deserialize tool arguments as executable code.
- Record requests, completion metadata and raw start/end lines separately. A submitted
  command and a non-error completion do not prove a particular file's contents reached
  the actor. Do not call a filename listing or quoted example a content read.
- Detection is bounded: arbitrary shell, dynamic paths, other readers, aliases,
  symlinks and transient behavior still require manual review. No OS sandbox claim.
- No new model experiment, method prompt, accepted baseline, push, merge or release.
  Historical actors, guards and human adjudications stay byte-identical. Replay into
  a new external experiment directory, not the source trials.

## Review focus

1. Quoted paths, basename collisions, runtime reads and metadata filenames printed
   by `echo`/`ls` must not be mislabeled as read requests.
2. `cd` plus literal multi-file `cat`, semicolon/newline segments and failed or pending
   calls must retain accurate request and completion scope, not invented success.
3. Dynamic/subshell/heredoc syntax is outside the parser's promise; unknown remains
   unknown instead of being silently certified as safe.
4. Malformed/truncated events and orphan/duplicate tool records cannot masquerade as
   a complete, clean process trace. Missing logs still permit fixture-only code checks.
5. The real historical replay must verify raw digests and exact witnesses; an updated
   audit cannot rewrite the old model trial or establish model improvement.

## Task 12 — Bound controller read requests to native source events

**Files:** Add `evals/context/audit_controller_access.py` and
`evals/context/test_controller_access.py`; extend `evaluate_workflow.py`, its CLI
regression, context README, POST plan, CHANGELOG and this plan. No runtime skill change.

**Interfaces:** `audit(run: Path) -> dict`, read-only. Result contains native stream
SHA256 and auditor SHA256, status `NOT_RECORDED`, `REQUESTS_FOUND`,
`NO_REQUESTS_OBSERVED` or `INVALID_OR_INCOMPLETE`, findings with native tool ID,
start/end line, resolved requested controller path, and nullable tool error state.
Every result requires manual review; none certifies absence of other reads.
CLI `audit_controller_access.py RUN` prints JSON; exit1 for found requests, exit2 for
missing/invalid/incomplete trace, exit0 for no bounded matches (not acceptance).
`evaluate()` keeps its existing result/exit contract, adds the audit result, fails
on requests or an invalid present trace, and explicitly marks absent logs unknown.

- [x] Write CLI/integration regressions: correct code and protected bytes with a
  forbidden literal read request must fail; structured reader and path countercases,
  completion scope, broken event streams, missing logs and read-only behavior.
  Run context tests; Expected: RED for the missing audit behavior, not fixture errors.
- [x] Implement the smallest bounded auditor and call it from the workflow evaluator.
  Run new and full context suites; Expected: GREEN, existing fixture-only cases work.
- [x] Replay all20 Task11 streams read-only, bind digests and literal witnesses, and
  compare with preserved old PASS guards. Expected: all three previously confirmed
  trials expose read requests; other results remain bounded/manual, not safe labels.
- [x] Run root/router/context, package/docs/diff, then one fresh whole-branch review
  and necessary fixes. Record remaining roadmap work and limits; commit locally,
  archive this plan's scratch only. Expected: green checks and no runtime diff.

## Outcome

The original evaluator returned PASS for a correct intake repair with unchanged
protected bytes plus a submitted controller read. New integration guards reproduce
that omission; quoted separators/dynamic cd and concatenated words also had explicit
RED before their path-classification fixes. Initial context61/61 passed.

Read-only replay of all20 Task11 streams found the three previously confirmed trials:
control/intake-late/2 (3 requests), candidate/intake-late/4 (4), and
candidate/intake-early/3 (5). Each new finding has raw native start/end lines and a
tool-call ID; the original events, report and historical PASS guard digests match.
The other17 have no bounded matches, not process acceptance. No event stream is
classified invalid/incomplete in this historical sample.

External replay: `~/.sdd-regression/experiments/controller-access-20261029T115355Z/`.
This batch improves deterministic evaluation evidence; there is no new model run,
runtime method, forward/standard result, accepted baseline or cost-gain claim.
The broader optimization roadmap remains unfinished.

## Independent review and fix pass

One fresh whole-branch review returned 0 Critical, 3 Important, 0 Minor. All three
were reproduced by new tests before one fix pass: (1) pipeline/conditional cd could
invent a controller path; (2) an earlier terminal event could mask unfinished later
agent/message/tool activity; (3) a completion could contradict its start's tool name.
Uncertain cwd now remains unclassified, later activity resets the terminal state,
and contradictory completions cannot supply a finding's completion evidence.
The public evaluator regressions also reject the latter malformed traces. Context
65/65 passed after fixes; root105/105 and router171/171 also passed: 341 total.
Package remains12skills/214files/0.5.0. There is no second review; fixes are checked
by RED/GREEN regressions and the fresh full suite. No deferred Minor finding.

After the fix, replay still finds exactly the same3 trials/12 requests. Initial
replay records remain in the external experiment, with the final replay stored
separately. All original events/reports/old guards and runtime75 still match.

Review limits remain: arbitrary/dynamic shell, other readers/aliases/symlinks;
actual content delivery; full Pi payload validation; authenticity/deleted logs,
OS isolation/transient effects; concurrent mutation/large-stream limits; exhaustive
historical semantic adjudication; old standard/provenance acceptance; model/causal/
cost/backend claims; natural trigger/real compaction/first-link maintenance; real
migration/durability/held-out quality/reviewer reliability; unchanged UI/installation;
excluded primary checkout/live skills/real projects/L2/L3; merge/push/release and
overall-method readiness. These are not certified by this deterministic repair.

Local development commit identity is recorded by Git and the external provenance.
The development branch/worktree is retained; no push, release or live installation.
