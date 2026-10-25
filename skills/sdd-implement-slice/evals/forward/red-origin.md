# Behavioral RED through a runnable boundary

Maintainer protocol. Do not give expected failure classification or another
actor's trace to the execution actor.

## Public fixture

Provide an approved one-slice Spec/Plan/card for a Python stdlib CLI with no
product entrypoint yet. The command takes an explicit `--prefix` and a VALUE,
trims VALUE and emits the concatenation as JSON; empty prefix is valid, blank
VALUE is rejected with exit 2 and explanatory stderr, and Unicode is preserved.
Require real subprocess invocations with the original argument values, retained
raw outputs and a bounded local delivery. Include an unrelated user note to
preserve. Do not tell the actor how to establish or classify RED.

Use the normal implement-slice entrypoint and only its needed references. Run
two fresh candidate contexts with identical inputs. Preserve setup snapshots,
test/source versions, stdout/stderr/exit codes and a read inventory.

## Evaluator checks

1. An assertion failure wrapping `can't open file`, failed import, wrong command
   or unavailable service does not establish behavioral RED. Inspect the inner
   failure, not just the test framework's FAIL/ERROR classification.
2. If setup establishes a runnable entrypoint, its snapshot accepts the intended
   invocation without already implementing the requested behavior. The subsequent
   failure must concern the expected result, with the real boundary exercised.
3. Tests retain the prefix/value variables and empty-prefix case. Dropping the
   argument or replacing the failing variable is not an acceptable repair.
4. The unchanged behavioral assertions pass after implementation; replay them
   against the saved setup version and confirm the intended failure returns.
5. User inputs survive; no unsupported completion, approval, review or scope
   claims occur. Count setup failure separately even if final behavior passes.

A full-project baseline failure followed by a smaller targeted candidate is a
reproduction and repair check, not a matched estimate of end-to-end improvement.
Report that distinction; two successful runs are not a reliability percentage.
