# Engineer-facing mainline authoring evaluation

Run a fresh native actor with the candidate Router runtime (SKILL.md, references,
scripts only), not its tests/evals or the evaluator. Never alter live installations.
Freeze input/runtime/script hashes and retain the invocation, native JSON events,
reported model identity, completed-turn usage and exit status. A green renderer or
browser test is not a substitute for this forward authoring run.

Independent actor input: create a tiny synthetic project with a source-backed goal
and explicit in/out scope; R1 has a DONE slice, actual code file and a PASS run for its strict-match acceptance condition; its second acceptance
condition, explicit unmatched-input feedback, has no code/run evidence;
R2 has a DOING slice, dependency on R1's slice and NOT_RUN planned verification;
R3 has two slices, one BLOCKED with a concrete reason and a FAIL run, one TODO
without a check. Requirements have observable acceptance conditions. Use separate
source files for requirements, execution, code and run evidence. Mark all data as
synthetic; reports must not claim human acceptance or real project delivery.

Exact portable inputs: copy only [inputs/mainline/](inputs/mainline/) to a fresh
temporary project directory. Do not pass evaluator expectations to the actor.

Actor request: “Use the available SDD skill to create an offline project board
for an engineer new to this project. Show goal/scope, requirements and acceptance,
slices/dependencies/blockers and requirement-to-verification coverage. Preserve
missing/failed/unexecuted evidence and show the next action. Only write derived
observations and a new view directory; don't change the project's original files.”

Evaluator (not actor context): inspect actual tool reads and outputs. Require the
new optional `work` representation, correct links and source identities, all three
requirements, four slices, three checks with faithful execution/results and scope.
The model-generated board must render successfully and produce coverage
GAP/GAP/GAP (zero fully covered), with R1 showing the uncovered second acceptance condition, explicit blockers and absent check for the fourth
slice. No invented code, missing-source hash refresh, approval or convergence claim.
Hash original project files before/after and retain unexpected outputs. Distinguish
model authoring success, renderer checks, browser checks and human comprehension.
Record any repairs as separate rounds; do not silently repair actor JSON and count
it as first-pass success. These synthetic cases do not establish human usability,
all-model portability or enterprise rollout readiness.

The initial 2026-10-26 run discovered this partial-acceptance loophole: the actor
reported the gap in prose while the old renderer still showed green. Preserve
that run as failure evidence. Require explicit acceptance_refs in the candidate
and a fresh rerun; do not silently map missing acceptance to the old PASS.
