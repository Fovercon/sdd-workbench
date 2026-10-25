# Human decisions: question, response and continuation


## Contents

- [Establish the question](#establish-the-question)
- [Conversation route](#conversation-route)
- [Offline board route](#offline-board-route)
- [Keep feedback lighter than approval](#keep-feedback-lighter-than-approval)
- [Direct feedback on a local board](#direct-feedback-on-a-local-board)


Use for an actual unresolved human gate in RUN, routing or VIEW. Distinguish
approval, a product/design choice, and missing information. Design review is not
automatically a business decision. Do not ask again for authority already given.

## Establish the question

Identify a stable decision ID, its owning item/stage, the exact sources/versions,
the person who may answer, and the scope/consequence of their answer. Present
the smallest concrete question that clears this gate. Give real alternatives and
their consequences; do not invent business choices or offer approval as a way
around absent domain evidence. Ask for the missing artifact or decision instead.
An unanswered question has no selected default. Missing question content is a
clarification gap, not an invitation to fabricate approval options.

## Conversation route

Use an available question/input UI when useful; otherwise ask a concise question
in chat with the artifact link, stable ID, version and scoped choices. Accept a
clear natural-language answer; users need not type JSON or hashes. An option such
as "approve this Plan" covers only the exact disclosed Plan and scope. An answer
like "looks good" about a picture must not approve an entire implementation.

On reply:

1. Resolve it to the pending question; clarify only material ambiguity. Check the
   current checkpoint, source hashes and version. If the baseline changed, show
   the relevant delta and ask about the current subject rather than transplanting
   an old approval.
2. Establish the actual human's intent/authority from the conversation. A file,
   browser draft, checked radio, generated answer or technical validation alone
   supplies none of that authority. An explicitly submitted answer in the user's
   message can supply it; do not demand a redundant second confirmation.
3. Record the user's exact decision, ID, scope, artifact identities and actual
   conversation evidence in the owning stage's existing decision/review record.
   Do not create a new global ledger or mark other pending gates satisfied.
4. Approval updates only a ready subject within the user's authority. Requested
   changes route to their owning stage (impact analysis if downstream contracts
   may be invalidated). Deferral remains pending. Input is inspected for adequacy
   before it can clear an input gate. Never treat every response as SATISFIED.
5. Continue the already-authorized work or present the next real decision. If a
   board is maintained, read the updated sources and generate a new version with
   the decision receipt cited; retain prior versions. A STATUS-only question does
   not authorize unrelated implementation.

## Offline board route

Attach `decision` to the item owning the gate. Views sharing one gate use
`decision_ref: "<owning item ID>"` instead of repeating approval forms. Include
all load-bearing sources in that gate's references. A board does not invent a
question from a status, nor does a decision reference merge source freshness.

```json
"decision": {
  "id": "D-PLAN-01",
  "kind": "approval",
  "prompt": "是否批准这份 Plan 的接口与恢复设计？",
  "owner": "项目所有者",
  "scope": "只覆盖所引 Plan 版本；不批准尚缺领域输入的需求或发布动作。",
  "options": [
    {"id":"approve","label":"批准当前版本","description":"以所引版本作为本范围设计基线。","effect":"APPROVE"},
    {"id":"changes","label":"需要修改","description":"说明修改内容，再修订和评审。","effect":"REQUEST_CHANGES","requires_note":true},
    {"id":"defer","label":"暂缓","description":"保留此关口，继续其他已就绪工作。","effect":"DEFER"}
  ]
}
```

Kinds are `approval`, `choice`, `input`, `feedback`. Approval/choice/feedback has 2–8 explicit options;
only approval may offer `APPROVE`. Other effects are `REQUEST_CHANGES`, `DEFER`,
`ANSWER`. Input omits options and accepts free text. `requires_note` is optional.
Sources are mandatory. Malformed questions and dangling references are rejected.
Old pending records without metadata show a clarification request, not guessed
approve buttons. Stale, unknown or resolved gates have disabled answer controls.

In static/offline mode, the user selects/fills an answer, then generates, copies or downloads it and
explicitly submits it in the project conversation. The board labels it a draft;
it never turns a badge green, writes a project file or sends a message. Its
response includes project, exact snapshot SHA256, item/decision IDs, answer and
note. The browser does not establish reviewer identity. No remote service,
clipboard permission or persistent browser storage is required; manual copy and
plain chat remain available. Drafts reset on page reload.

## Keep feedback lighter than approval

Use `feedback` for optional reactions to a diagram, writing or presentation. It
is not a human gate and may stay on a `GAP` or `SATISFIED` observation. It can offer
`ANSWER`, `REQUEST_CHANGES` or `DEFER`, never `APPROVE`. Do not ask a user to approve
the same styling again after they already requested changes: record that response,
make the authorized changes and offer an optional feedback entry on the new view.

The normal form has one primary action: submit directly when the local feedback
service is active, or copy a short natural-language reply in static/offline mode.
Show the note field when a selected option needs explanation;
keep preview/export, ownership and technical identifiers under secondary details.
Keep options and scope concrete and brief. Optional feedback stays collapsed until
requested; actual approval gates remain explicit. No submitted/approved claim is
made by copying. The reply carries a short decision/version reference automatically;
the user does not have to type IDs, hashes or JSON.

For a short reply, resolve the ID and version prefix against the current snapshot,
normalize to the same full response fields if using the validator, and apply the
conversation procedure above. Check ambiguity or version drift before recording
anything; an agent must not reconstruct a fresh approval from an old reply. The
advanced response-file export retains the complete snapshot hash for tooling.

Check a submitted JSON response read-only against the **current** view:

```bash
python3 /path/to/sdd-workflow-router/scripts/decision_response.py --root /path/to/project --view /path/to/current-view --response /path/to/response.json
```

The helper verifies immutable-view receipts, question/option identity and all
gate/linked-view source hashes. `RESPONSE_VALIDATED` is a technical result with
`requires_human_authority: true`; it never records approval. Then use the
conversation procedure above. A browser file attached without submission intent
is a draft to inspect; ask only if that intent is genuinely missing.

## Direct feedback on a local board

Use when the user requests feedback submission without copying into chat. This
supports `kind: feedback` only. Approval, choices and input gates retain their
conversation route. Start a real local service; never show a saved badge based
only on a browser selection, draft generation or localStorage.

1. Render/update a new view with the current packaged renderer; never patch the
   previous HTML or receipt in place. Its receipt must retain the original source
   root and all gate/linked-design fingerprints.
2. Start the stdlib service on loopback, with a separate persistent state directory:

   ```bash
   python3 /path/to/sdd-workflow-router/scripts/feedback_server.py --root /path/to/project --view /path/to/new-view --state /path/to/board-feedback --port 0
   ```

   The first output line gives the live URL. Open/deliver that URL. An ordinary
   `http.server` or a file URL keeps offline copy behavior. Preserve the state
   directory across restarts; restart with the same arguments to recover feedback.
   The service is local to this machine and must remain running for new saves.
   Source links on served current/history pages open a read-only UTF-8 text
   viewer on the same service. It exposes only files cited by that exact bundle,
   checks the original fingerprints on every read, rejects changed/missing or
   binary sources, and never executes source HTML/scripts. Arbitrary project
   paths and the feedback database are not exposed. Static files retain their
   original local file links; immutable board files are never patched.
3. The user explicitly chooses an option and clicks **提交反馈**. The server checks
   immutable receipt identity, exact snapshot/question/option, required explanation,
   current gate and linked sources, and the last seen feedback revision. It writes
   a SQLite transaction containing the scoped exact answer, original source hashes,
   time and submission ID. Same-origin/session checks protect the write endpoint;
   no arbitrary source editing or network listener is provided.
4. Only a committed response displays **已反馈** / **已收到，待调整** /
   **已暂缓反馈**, the answer, note and time. Refresh and service restart restore
   the receipt. **修改反馈** appends a revision and retains history. Retries after a
   lost response reuse the submission ID; another tab cannot overwrite an unseen
   revision. Source changes block new submissions and mark existing receipts as
   requiring source rechecking. A new snapshot has its own feedback scope, even
   when the state directory is reused; no old acceptance is transplanted.
5. The badge is feedback receipt state, separate from `state`, `effective_state`,
   stage approval and implementation completion. “待调整” means received, still
   awaiting work. Saving does not invoke an agent, send chat/email, revise Plan or
   perform the requested adjustment. Never promise automatic work or notifications
   without a separately authorized executor.

For later handling, inspect `feedback.sqlite3` in the stated state directory;
the `feedback.record` JSON retains every revision with `authority: feedback_only`.
Use a read-only SQLite connection (`mode=ro`), select by exact project/version and
sequence, and recheck the cited sources before routing adjustments. Record the
actual resulting stage work in its owning records and generate a new view. A
feedback receipt or “这版可以” about presentation never authorizes project approval.
The ledger contains user feedback; keep its paths out of public hosting and expose
only the specific board and allowlisted diagram artifacts through this service.
