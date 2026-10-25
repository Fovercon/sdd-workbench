# Project overview and requirement–slice–verification views

## Authority and impact

The user requested this change on 2026-10-26: improve the project overview and
requirement–task–verification mainline, add regressions and actual browser checks,
and show a working result. This authorizes local implementation and verification;
it does not authorize publication, live skill installation or a release.

- FACT baseline: v0.3.0, commit 7c79aad; project-view.md owns derived observations,
  source checks, stage bindings and immutable versions.
- FACT defect: generic records do not expose individual requirements, slice execution
  or verification coverage. Evidence state cannot express execution state.
- REQUEST: engineers can see goal/scope, delivered work, blockers, verification gaps
  and a concrete next action, with inspectable supporting sources.
- Route: SPEC / FLOW_FORWARD; this is an additive display/data contract.
- IMPACT_READY; approved for propagation by the user's explicit request above.

## Bounded contract and acceptance

1. Optional structured `work` observations provide a source-bound brief,
   requirements with acceptance examples, slices with explicit requirement and
   dependency links and execution status, and checks with results and slice links.
2. Existing observations remain valid. Missing structured records show unknown or
   missing coverage; prose is never parsed into fabricated task state or counts.
3. Overview shows goal, scope, bounded counts, open blockers and next action.
   Spec exposes requirements and acceptance; Tasks exposes TODO/DOING/BLOCKED/DONE
   and actual dependency links; Converge shows each requirement's slice, code and
   check chain, including gaps. No aggregate completion percentage or auto-approval.
4. Check PASS is a recorded runtime result, distinct from acceptance/approval.
   Missing implementation, incomplete slices, absent checks, FAIL/NOT_RUN/UNKNOWN,
   changed/missing linked sources and returned upstream stages prevent green coverage.
   Every declared slice and every acceptance condition for a requirement needs
   an applicable passing check. Each check maps explicit 1-based acceptance indexes
   using acceptance_refs; absent mappings remain gaps.
5. All structured subjects remain reachable in the evidence pane and plain text.
   Links support Unicode, keyboard navigation, deep links and browser history.
   Offline/no-JS preserves content. No remote resource or new package dependency.
6. This increment retains the design gallery, source identities, feedback behavior
   and immutable bundles. It does not implement live task tracking, auto-execution,
   automatic document parsing, history redesign or remaining stage-specific views.

## Design and slices

A strict optional item extension avoids a second project ledger. `workstream.py`
validates typed relationships, acyclic dependencies and derives conservative
coverage from inspected items. `workstream_view.py` renders readable semantic HTML;
its CSS is scoped to enriched lifecycle boards. Existing navigation/evidence links
are reused. Derived coverage is calculated on render/recheck, never persisted as
human approval in the observation JSON.

Sequence: data contract and conservative computation → overview/Spec/Tasks/Converge
views → source-linked authoring guidance → deterministic regressions and Chrome
flows → fresh model authoring evaluation → actual evidence-backed preview.

## Verification and limits

Required regression inputs include fresh/missing/changed sources, partial slice
coverage, unexecuted/failed checks, DONE versus evidence state, dependency cycles,
wrong-role/dangling links, return to Spec, escaped untrusted text, legacy input,
immutable update, Unicode deep links, narrow screens and no JavaScript.
Run the package checker, root and Router unit suites, existing diagram/feedback
browser regressions and new mainline browser flows. Inspect captured screenshots.
A fresh native agent must author observations from independent source files with
runtime skill instructions; report its exact invocation and observed result.
Browser checks do not establish first-use comprehension by human engineers.
