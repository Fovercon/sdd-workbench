# Held-out recovery pilot

This is a maintainer evaluation protocol, not an actor instruction or a new
product gate. Keep this file, probes and suspected defects outside actor context.

## Inputs and actors

Freeze the ordinary request, approved contracts, rules, application/tests and
skill identity before dispatch. Use synthetic data and separate temporary roots.
For the upstream ledger example, obtain historical application snapshots from
[the frozen upstream evidence](https://github.com/Fovercon/AI-Native-SDD/blob/0dc9414de8d7081bc8c425fe3593dcf44ce3c315/05-notes/2026-10-12-sdd-skill-optimization/evidence/): A at `sdd-ledger`, B at
`superpowers-ledger/app`. Those application snapshots are not bundled in this suite. Copy only runtime, tests and relevant contracts; exclude
comparison reports, historical defect/review answers and personal data.

The public request is a local-handoff convergence review: select and execute
necessary checks of everyday behavior, data preservation and error recovery.
An execution actor receives `sdd-converge-review` SKILL.md/references, not these
evals. A verification-design actor instead proposes faithful cases using its
own skill and must not claim it executed them. Record the two outcomes separately.

Compare versions only with identical inputs/model settings in fresh actors.
Archive read inventory, tool outputs, source changes and stop reason. A single
pilot tests applicability, not reliability, causality, time or token savings.

## Evaluator-owned oracles

1. Persistent state: seed a known valid record, then a syntactically valid but
   conflicting state-bearing representation. Check public read and attempted
   save plus original bytes/record identity. For the ledger fixture, duplicate
   `records` with `[old_record]` followed by `[]`; rejection must leave all bytes
   unchanged. Reuse the comparison's `probes.py` for A/B core/HTTP checks. Its
   “restart” name means a new Ledger instance, not a new process.
2. UI recovery: start a real temporary service and browser; enter an invalid
   date range, observe error, correct it, then check recovered row identities and
   that operation's error visibility. Preserve DOM/state evidence for both steps.
   HTTP success or JavaScript text is insufficient for rendered recovery.
3. Sensitivity: the accepted-preserving version and a known lossy/stale-error
   version must differ on those observable oracles. Do not repair the original
   product. Mutations, if needed, belong only in evaluator copies.
4. Scope control: use the pure local validation case (Case 18) as a counterexample
   to mandatory browser/restart/full-stack activity.

Score product and actor separately. A green original suite plus a failing
held-out oracle is useful evidence. If only the evaluator detects the defect,
record an actor miss; if the browser is unavailable, mark the UI line NOT RUN
with its recovery condition. Never convert a written plan into executed proof.

Stop temporary servers and close self-created browser tabs. Retain raw failures,
unexecuted items and the exact fixture/skill hashes alongside the result.
