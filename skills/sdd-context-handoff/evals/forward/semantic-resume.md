# Fresh-session continuation across a semantic change

Maintainer protocol. Actors receive only the normal project and current request,
not this evaluator's answer or other actors' traces.

## Public fixture and continuation

First deliver a small inspection CLI from a blank workspace: add, submit, review,
list and summary; JSON persistence; valid draft → submitted → reviewed transitions;
invalid actions and failed saves preserve existing data. Explicit v1 business
policy counts submitted or reviewed records as completed. Freeze the delivered
project, tests, contracts and actual command evidence.

Copy that project into a new workspace for a fresh receiver. Preserve old report
paths as historical identities and add a colleague's unrelated unfinished note.
The user explicitly changes completion to reviewed only, including historical
recalculation without changing stored statuses; other behavior remains. Authorize
the bounded implementation and local delivery, not commits or deployment.

The receiver uses context-handoff and the normal stage route, checks current
facts and completes the actual change. Preserve earlier evidence rather than
rewriting its commands or claiming it covered the new rule.

## Evaluator checks

- Current request and local copied source outrank an old path's progress claims.
- Correct existing features and the colleague's note survive; only affected
  contract, implementation, tests and evidence are revised.
- A submitted historical record changes from completed to incomplete in summary,
  while its stored state and bytes remain unchanged after a read.
- A reviewed record remains completed; new records and valid transitions still
  work through separate real subprocesses. Invalid transitions/corrupt input
  preserve bytes. Verify expected output, not merely successful exit status.
- V1 evidence remains historical for changed semantics. Review identity is
  explicit; an old/self-review is not represented as current independent review.
- Replay the old v1 implementation against the v2 oracle and confirm it fails for
  the changed business result, then run the same oracle against the new version.

This fixture exercises a fresh agent session, changed requirements and unrelated
work, not every drift combination or real human handoff. Separately run unchanged
contracts, code-only drift, missing external evidence and real-developer takeover
before claiming those cases pass. Human participants cannot be replaced by agents.
