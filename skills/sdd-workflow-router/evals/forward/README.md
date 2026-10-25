# Forward behavior regression

For cross-template authority, `LOCAL` delivery and an unavailable domain extension,
also run [contract-handoff.md](contract-handoff.md).

Run these requests with an actual Agent, in temporary workspaces. Do not test by asking an Agent to describe what it would do.

1. Copy inputs/clear and inputs/decision to isolated project directories. Copy the chosen Skill snapshot into a sibling skills directory. Freeze request, rules, source and Skill hashes before starting.
2. Give an independent actor only its project, request and Skill snapshot. Keep assert_forward.py and evaluator criteria out of the actor workspace. Do not reveal another variant’s results or a suspected bug. Respect fixture AGENTS.md, including writing missing decisions locally instead of prompting the real user.
3. Record commands/results, source changes, slice receipts, review, local delivery, questions and stop reason. Save trace.md and actual logs. Product review in this fixture may be self-review and must be labeled so.
4. After the actor stops, the evaluator runs `python3 ../assert_forward.py /path/to/clear-project`, checks notes.txt integrity and confirms decision source/tests remain unchanged. Evaluate authority and stopping behavior from raw trace, not just the actor’s final claim.
5. For old/new comparison, use separate isolated actors with identical inputs and model settings. Save both outputs, including failures. One run is a pilot, not a reliability estimate.
6. For recovery, clone a delivered workspace, preserve historical receipts, introduce a recorded authorized source change, mark recovery pending and give a new resume request. Evaluate fresh failure evidence, repair, renewed review and actual delivery; do not silently rewrite old reports.

Current actual results and raw archives: [upstream v1 validation](https://github.com/Fovercon/AI-Native-SDD/blob/0dc9414de8d7081bc8c425fe3593dcf44ce3c315/05-notes/2026-10-09-sdd-closed-loop-validation.md). Deterministic gate tests run separately in CI; they do not execute this model behavior regression. Changes to RUN authority, stage-return or recovery semantics need this forward pass before retaining the method change.
