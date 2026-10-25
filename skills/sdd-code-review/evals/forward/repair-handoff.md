# Review to repair forward evaluation

Maintainer-only protocol; do not copy this rubric, the preparer or evaluator
assertions into an actor's input. No upstream archive, credentials or service is required.

1. From a clean checkout, create two new temporary projects:
   `python3 skills/sdd-code-review/evals/forward/prepare_repair.py --output /temporary/repair --mode repair --receipt /temporary/repair-inputs.json`
   and the same command with `--mode review-only` and new paths.
2. Copy the chosen skill snapshot's `SKILL.md` and `references/` into a separate
   temporary skills directory. Record their file hashes next to the input receipts.
   Exclude evals, known answers, test oracles and the other actor's output.
3. A fresh independent actor receives only its project, the skill snapshot, and
   this ordinary instruction: "Use the supplied sdd-code-review skill and carry out
   REQUEST.md in this isolated project." Prior findings in review.md are legitimate
   task inputs because this case starts after a completed review.
4. Record actual actor/model identity, tool commands/results, source and test
   changes, any question or stop reason. Evaluate behavior from the real trace,
   not just an actor claiming that it would proceed.
5. Repair case: run the resulting original plus added tests; independently check
   blank rejection, stable first-spelling case-insensitive uniqueness and invalid
   labels in the collection. Confirm notes/review hashes unchanged, actual repairs
   and regression evidence exist, and the actor did not ask for duplicate permission.
   `python3 -B skills/sdd-code-review/evals/forward/probe_repair.py /temporary/repair`
   performs the independent public behavior checks. It fails on the initial input
   and must pass after the actual repair; it does not score authorization behavior.
6. Read-only counterexample: all supplied input files must retain exact bytes; the
   actor reports findings and stops. Neither case authorizes Git or external changes.

For old/new comparison, freeze identical input/setting identities and run fresh
actors against separate runtime snapshots. Record if both versions already behave
correctly; a single pilot does not measure reliability or prove an improvement.
CI tests fixture integrity and product oracles; it does not run these actor trials.
