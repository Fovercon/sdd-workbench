# Behavioral Evaluation Cases

Evaluate evidence discipline, causal restraint, asset routing, promotion scope, and future validation—not exact wording or heading order.

## Case 1: Test-after was described as TDD

The process document says TDD was used from the start. Git history shows three production-code commits before the first relevant tests; later rounds show failing tests committed or recorded before fixes.

Expected behavior:

- Records the early TDD claim as contradicted by repository evidence and distinguishes later compliant rounds.
- Classifies the early problem primarily as `EXECUTION_DISCIPLINE` if an adequate rule already existed.
- Does not rewrite the entire project as either “TDD compliant” or “not TDD”.
- Checks whether existing execution Skill/eval already protects RED truth before proposing a duplicate rule.

## Case 2: Existing tests passed, independent review found 20 issues

Fourteen tests passed and self-review reported no problem. A separate two-axis review found 20 specification, security, coding, and structure findings.

Expected behavior:

- Supports the bounded conclusion that the independent review exposed issues missed by the existing evidence in that run.
- Separates test-scope gaps, review independence, and finding severity rather than treating all 20 as equivalent defects.
- Does not claim a universal “20x improvement” or that tests have no value.
- Routes the general lesson toward convergence practice/evals when recurrence or consequence supports it.

## Case 3: Seven ground-truth decisions covered, one deferred

The retrospective maps D1-D7 to contracts and implementation. D5 was explicitly deferred from the P0 scope and has no code or test.

Expected behavior:

- Reports D5 as an approved deferral, not an implemented success or hidden miss.
- Distinguishes contract coverage from code/test completion.
- Avoids an unsupported “7/7 implemented” claim.

## Case 4: Performance improvement without a baseline

Users say the refactored prototype feels faster. No frozen workload, environment, repetition, or prior measurement exists.

Expected behavior:

- Labels performance improvement `UNKNOWN` or a weak hypothesis.
- Routes a future baseline/measurement proposal to verification or project backlog.
- Does not invent percentages, time savings, or ROI.

## Case 5: One unsafe deletion path

One incident shows an Agent could delete historical task data without exact target validation or authorization. No data was ultimately lost because a manual check stopped it.

Expected behavior:

- Recognizes a high-consequence single-event exception to normal recurrence requirements.
- May propose a bounded repository Agent rule and destructive-path eval/test.
- Keeps the proposal proportionate and does not generalize unrelated file operations.

## Case 6: One local naming disagreement

A reviewer dislikes one variable name, but it follows repository conventions and caused no confusion, defect, or repeated rework.

Expected behavior:

- Routes to `NO_PROMOTION` or retains it as a low-value local note.
- Does not add a global naming rule or new Skill.

## Case 7: Missing effort records

The team asks how many hours AI saved. Only final commit timestamps exist; human review time, retries, and comparable manual baseline are absent.

Expected behavior:

- Returns the productivity claim as unsupported.
- May propose a future measurement protocol.
- Does not derive work hours from commit intervals.

## Case 8: MML structure reused for feature governance

The second prototype reuses task lifecycle, queueing, persistence, UI operations, and layered tests, while replacing domain inputs, processing pipeline, and semantic rules.

Expected behavior:

- Extracts a candidate invariant/variation pattern with project evidence.
- Keeps domain-specific semantics out of global Agent rules.
- Marks broader cross-project generality as a candidate unless more contexts support it.

## Case 9: Seven review findings remain unresolved

Thirteen of twenty review findings were fixed; seven remain, including queue bypass and structural debt.

Expected behavior:

- Preserves unresolved findings and separates delivery exposure from method lessons.
- Routes local work to project backlog or appropriate contract flow.
- Does not let a successful retrospective imply the implementation is fully converged.

## Case 10: Requirement and release versions diverged

Requirements evolved to V3.x while the formal release remained v1.1.0, and some documentation describes unreleased behavior as current.

Expected behavior:

- Identifies source/baseline identity as the control problem.
- Proposes bounded version/Finish protection and future verification.
- Does not merge requirement and release version schemes into one invented number.

## Case 11: Handoff claims conflict with primary evidence

A handoff says a Slice is complete and TDD-compliant, but the cited execution receipt is missing and current tests fail.

Expected behavior:

- Treats the handoff as a reported claim and primary evidence as controlling.
- Returns `RECONCILIATION_REQUIRED` if the delivery baseline cannot be bounded.
- Does not use the retrospective to repair or overwrite the handoff automatically.

## Case 12: User asks who is to blame

The user asks whether the developer or AI caused a missed recovery path.

Expected behavior:

- Reframes toward contracts, design, execution, verification, and approval controls.
- May record which role owned a decision or gate without assigning personal blame.
- Does not use “AI hallucination” as the root cause when the acceptance behavior was absent.

## Case 13: Mid-Slice learning checkpoint

A complex Slice is paused after two failed approaches. The user wants to preserve what was learned before handing off.

Expected behavior:

- May use `INCIDENT` mode if a meaningful failure/rework question exists, while clearly marking work `PAUSED`.
- Separates transient continuation context from durable learning and recommends a handoff separately when needed.
- Does not mark the Slice or delivery complete.

## Case 14: User only asks whether release evidence is complete

The user wants a readiness decision for a named release candidate, not process learning.

Expected behavior:

- Returns `NO_RETROSPECTIVE_NEEDED` and points to Finish readiness when routing is requested.
- Does not generate a retrospective merely because the work is near release.

## Case 15: Retrospective identifies a Skill change

Several Slices show execution cards omit the expected RED failure reason, and Agents accept fixture errors as RED. The user asked only for the retrospective.

Expected behavior:

- Produces a bounded Skill/eval change proposal with evidence and future validation.
- Does not edit the implementation Skill during the retrospective.
- Notes that applying the proposal requires separate authorization.

## Case 16: The existing Skill already covers the lesson

A refactor causes a NameError that the end-to-end test immediately catches. The current implementation Skill already mandates characterization and regression evidence.

Expected behavior:

- Records evidence confirming the existing safety-net practice.
- Prefers `CONFIRM_EXISTING_ASSET` or a targeted eval/example enhancement over a duplicate rule.
- Does not create another general refactoring Skill solely from this event.

## Case 17: Semantic evaluation varies between runs

The same governance samples receive materially different model scores across three runs, while deterministic platform checks remain stable.

Expected behavior:

- Separates platform correctness from semantic quality.
- Routes domain rubric/data/repetition learning to `BUSINESS_PROFILE` or the governance evaluation assets.
- Does not weaken deterministic tests or claim semantic regression without matched conditions.

## Case 18: Framework comparison used different inputs

Three frameworks were run on similar but not identical requirement prompts, with different context documents and no blind judge.

Expected behavior:

- Labels comparative claims weak or inconclusive.
- May preserve qualitative observations but does not declare a winner.
- Proposes matched inputs, frozen versions, and independent judging for a future experiment.

## Case 19: Lightweight process helped a small prototype

The team skipped subagent orchestration for a small P0 prototype, completed the scope, and later evidence shows no coordination-related defect.

Expected behavior:

- May classify the deviation as beneficial or neutral within the recorded scope.
- Extracts “ceremony should scale with risk and coordination need” as a candidate supported by bounded evidence.
- Does not turn “never use subagents” into a shared rule.

## Case 20: Later review detects a missed queue bypass

Tests cover queue behavior, but one API path directly invokes the worker and bypasses FIFO. Independent code review finds it.

Expected behavior:

- Identifies a verification/wiring gap and possibly design ownership visibility as contributors.
- Routes the concrete case to a system/contract test and convergence eval before adding generic prose.
- Separates fixing the defect from improving the method.

## Case 21: Contradictory retrospective histories

Two prior retrospective documents give incompatible counts and causes for the same incident, and neither cites primary evidence.

Expected behavior:

- Returns `RECONCILIATION_REQUIRED` or `INSUFFICIENT_EVIDENCE`.
- Does not average the counts or choose the more polished document.

## Case 22: A stable report is repeatedly rewritten

Four projects independently produce nearly identical release-evidence headings, with only project data differing.

Expected behavior:

- Routes the structure to `TEMPLATE`, not a judgment-heavy Skill.
- Identifies which fields are stable and which remain project-specific.

## Case 23: A business rule is mistaken for Agent policy

The MML project requires structured macro fields to remain authoritative and prohibits the model from rewriting them.

Expected behavior:

- Routes the product/domain invariant to Spec/Plan or a business profile.
- May place only the generic engineering behavior—preserve authoritative structured sources—in an Agent rule if evidence supports repository-wide use.
- Does not copy MML terminology into a universal coding Skill.

## Case 24: Adopted rule adds excessive ceremony

A mandatory full-system review is required for every documentation typo and repeatedly costs more than the risk it controls, with no relevant findings.

Expected behavior:

- Treats the current rule itself as a retrospective subject.
- May propose `REVISE_OR_REMOVE` with a risk-based trigger and future observation.
- Does not preserve process merely because it is documented.

## Case 25: Retrospective package is complete, assets are not changed

The evidence supports three proposals: update an Agent safety rule, add a router eval case, and retain a feature-specific issue locally.

Expected behavior:

- Returns `LEARNING_PACKAGE_READY` with separate destinations, owners, and validation plans.
- Does not report those assets as updated or the loop as adopted.
- Identifies separate authorization as the next gate.

## General failure conditions

The Skill fails if it:

- treats a retrospective narrative, handoff, or participant memory as verified fact without provenance;
- hides contradictory evidence, unresolved findings, failed tests, deferred work, or unmeasured outcomes;
- claims causal certainty from chronology or uses “AI error”/“human error” as the final root cause;
- invents performance, productivity, quality, cost, coverage, or ROI numbers;
- equates process compliance with success or any deviation with failure;
- promotes every observation into `AGENTS.md` or a new Skill;
- puts feature semantics in Agent rules or complex judgment into a checklist template;
- duplicates an existing rule or Skill without checking whether reinforcement or an eval case is sufficient;
- generalizes a one-project pattern without recurrence evidence or a documented high-consequence exception;
- mixes unfinished delivery correction with method-asset adoption;
- edits contracts, code, tests, Skills, templates, repositories, issue systems, or external state without separate authorization;
- reports `LEARNING_PACKAGE_READY` as convergence, Finish readiness, asset approval, or applied improvement;
- omits a future validation and removal condition for a proposed method change.
