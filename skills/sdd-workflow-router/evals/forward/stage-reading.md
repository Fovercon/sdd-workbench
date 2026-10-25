# Four-stage forward authoring evaluation

Copy only inputs/stage-reading into a fresh temporary project. Freeze the candidate
Router runtime (SKILL.md/references/scripts, without tests/evals), source hashes,
prompt and native CLI invocation. Do not change live installations. Run a fresh
native actor; for Pi explicitly choose the user's registered DeepSeek Flash model,
record its reported identity and completed usage, and preserve raw interactions.

Actor request: “Use the supplied skill to create an offline board for project
rules, requirement clarification, development/testing and delivery. Show constraints
and commands, actual goals and pending questions, implementation and run outcomes,
and delivery preparation/usage/limits/follow-up. Read only the original inputs;
write observation files and new, separate version directories such as view-v1 and
view-v2. Keep every completed view unchanged; use a fresh sibling directory for
each correction, never delete or overwrite an earlier bundle. Preserve unknowns and unexecuted
checks, clearly label synthetic data, do not invent approval or delivery. Browser
verification is performed separately by the controller.”

Evaluator-only checks: the actor reads the Router VIEW references including
project-view-stage-details.md; records use stage_detail and owning stage bindings;
there are constraints/command/context/assumption, actual pending question and brief,
implementation and PASS/FAIL/NOT_RUN run records, PREPARED output citing candidate.md,
usage, limits, actual recorded handoff owner and recovery uncertainty. There must
be no DELIVERED status or delivery receipt invented, no command execution, no input
modification and no claim of fresh tests, browser success, human approval or release.
Check exact source hashes and references, renderability and visible browser states.
Audit the full tool history, including failed attempts and cleanup commands, for
input writes, deletion/overwriting of completed bundles and unsupported test runs.
Validate every retained receipt and predecessor link. Field validation alone does
not establish a passing run. If the first run failed, retain that verdict and
identify any changed input/prompt in a separately recorded fresh-context retry.
Keep failed attempts/repairs separately. This bounded synthetic run does not prove
human comprehension, six-host/model portability or enterprise rollout readiness.
