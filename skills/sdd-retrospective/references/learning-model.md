# SDD Retrospective Learning Model

Use this model to turn project evidence into proportionate method changes without rewriting history or accumulating brittle rules.

## 1. Two different closure loops

```text
Delivery loop
Spec -> Plan -> Slice -> Implement -> Converge -> Finish
  ^                  |               |
  +---- change impact+---------------+

Learning loop
delivery evidence -> retrospective -> asset proposal -> authorized adoption
       ^                                      |
       +----------- future evaluation --------+
```

Delivery closure asks whether the product change meets its contracts. Learning closure asks whether the development system should change and how that change will be evaluated later. Neither substitutes for the other.

## 2. Evidence labels

| Label | Meaning | Example |
|---|---|---|
| `FACT` | Directly observed in an identifiable artifact or reproducible result | A commit adds production code before its regression test |
| `REPORTED` | Stated by a participant or prior summary but not independently verified | “The first implementation took two hours” |
| `ASSESSMENT` | Interpretation supported by named facts | Existing tests covered the happy path but not queue entry ownership |
| `HYPOTHESIS` | Plausible explanation or improvement that still needs testing | Smaller execution cards may reduce context drift |
| `UNKNOWN` | Evidence is absent, contradictory, stale, or incomparable | Productivity improvement without a baseline |

Keep quotes short and necessary. A later reconstruction can be useful evidence, but label it as reconstructed and corroborate central claims with primary artifacts.

## 3. Evidence strength

Rate evidence relative to the claim, not by artifact prestige.

| Strength | Criteria |
|---|---|
| `STRONG` | Multiple current, independent, directly relevant sources or a controlled comparison support the claim |
| `MODERATE` | One direct source or several consistent indirect sources support a bounded claim |
| `WEAK` | Self-report, single anecdote, incomplete trace, unmatched comparison, or unclear baseline |
| `CONTRADICTORY` | Material sources disagree and no authority rule resolves them |

Examples:

- A failing regression before a fix plus a passing run after it is strong evidence that the test detects that defect under the recorded conditions.
- “Twenty findings versus zero” supports the bounded claim that the independent review found issues missed by the existing self-review in that run. It does not alone prove a universal percentage improvement.
- A UI that feels faster is weak evidence of performance improvement without a frozen workload and baseline.

## 4. Event and decision chain

Record only events that explain the outcome or learning:

| Field | Meaning |
|---|---|
| Expected | Contract, plan, rule, or hypothesis in effect at the time |
| Action | What was actually done |
| Result | Observable outcome |
| Detection | Test, review, user, log, or later analysis that exposed it |
| Response | Correction, deferral, acceptance, or no action |
| Evidence | Precise source and identity |
| Confidence | Evidence strength for the recorded relationship |

Distinguish event time, detection time, and documentation time. A later note that accurately reconstructs earlier work is not contemporaneous evidence.

## 5. Deviation classification

| Class | Meaning |
|---|---|
| `BENEFICIAL` | Departing from the intended process improved an evidenced outcome or removed disproportionate ceremony |
| `NEUTRAL` | Different execution with no material observed effect |
| `COSTLY` | Added avoidable effort, delay, or rework |
| `RISKY` | Weakened correctness, safety, traceability, recovery, or decision control, even if no incident occurred |
| `UNKNOWN` | Effect cannot be established |

Process compliance is not the goal by itself. A lightweight path may be beneficial for a low-risk prototype; skipping a required safety gate remains risky even when the demo succeeds.

## 6. Cause taxonomy

Assign one earliest primary cause and any material contributors:

- `INTENT_UNCERTAINTY`: product outcome or acceptance meaning was not decided;
- `CONTRACT_GAP`: approved Spec omitted, contradicted, or obscured required behavior;
- `DESIGN_GAP`: state, ownership, interface, data, recovery, migration, or verification architecture was inadequate;
- `SLICE_OR_PLAN_GAP`: work was ordered, bounded, or described in a way that hid dependencies or completion evidence;
- `EXECUTION_DISCIPLINE`: an adequate agreed workflow existed but was not followed;
- `VERIFICATION_GAP`: oracle, layer, data, sensitivity, environment, or independent review failed to expose risk;
- `CONTEXT_OR_HANDOFF`: identity, decisions, scope, or state were lost or contaminated across work boundaries;
- `TOOL_OR_ENVIRONMENT`: capability, reliability, platform, dependency, or automation limitation shaped the outcome;
- `PROCESS_FIT`: workflow ceremony was too heavy, too light, or poorly matched to risk;
- `LOCAL_IMPLEMENTATION_DEFECT`: contracts and controls were adequate, but a bounded implementation defect occurred;
- `EXTERNAL_CHANGE`: dependency, stakeholder decision, environment, or upstream system changed;
- `UNKNOWN_CAUSE`: evidence does not support a stronger conclusion.

“Human error” and “AI error” are actors, not useful root causes. Continue until the explanation identifies a controllable condition, but stop before speculation.

## 7. Finding record

Each material finding should contain:

- stable ID;
- positive or negative nature;
- evidence label and strength;
- expected versus actual result;
- primary cause and contributors;
- detection point and earlier opportunity;
- consequence and affected scope;
- recurrence signal;
- current containment or unresolved exposure;
- candidate learning and competing explanation.

Do not combine unrelated causes merely because they appeared in the same iteration.

## 8. Recurrence and promotion states

### Recurrence signal

| Signal | Meaning |
|---|---|
| `ONE_OFF` | One bounded occurrence with no broader evidence |
| `REPEATED_LOCAL` | Recurred in one repository, workflow, or domain |
| `CROSS_CONTEXT` | Appeared across repositories, teams, tools, models, or materially different tasks |
| `SYSTEMIC` | Directly caused or enabled by a shared process, rule, template, or platform |
| `UNKNOWN` | Population or history is insufficient |

### Promotion state

| State | Meaning |
|---|---|
| `RETAIN_LOCAL` | Keep as project evidence, backlog, or note |
| `CANDIDATE` | Worth another run or review before adoption |
| `PROPOSE_PROJECT_PROTECTION` | Evidence supports a bounded project rule/test/template change |
| `PROPOSE_SHARED_ASSET` | Recurrence and generality support a reusable Skill/template/eval change |
| `CONFIRM_EXISTING_ASSET` | Existing rule or Skill already covers the lesson and evidence confirms its value |
| `REVISE_OR_REMOVE` | Existing asset is ineffective, misleading, conflicting, or disproportionate |
| `NO_PROMOTION` | Unsupported, obsolete, redundant, or harmful |

Promotion is a proposal until the appropriate human owner approves and a separate workflow applies it.

## 9. Promotion criteria

Evaluate:

1. **Evidence**: Does the claim have enough direct support?
2. **Consequence**: What happens if the lesson is ignored?
3. **Recurrence**: Is the condition repeated or shared?
4. **Generality**: Can the lesson be stated without embedding one project's accidental details?
5. **Stability**: Is it likely to remain true as tools and architecture change?
6. **Actionability**: Can an Agent or developer follow it at the right moment?
7. **Testability**: Can compliance or benefit be observed?
8. **Cost**: What ceremony, runtime, maintenance, or false-positive burden does it add?
9. **Ownership**: Who maintains, approves, and removes it?
10. **Conflict**: Does an existing rule, Skill, contract, or test already own it?

Normally require recurrence before proposing a shared process rule. Permit a single-event exception for high-consequence safety, security, irreversible data, or authorization failures when the control is clear, proportionate, and testable.

## 10. Asset routing

| Destination | Put here | Do not put here |
|---|---|---|
| `AGENT_RULE` | Durable repository-wide constraints and mandatory Agent conduct | feature semantics, one-off commands, long tutorials |
| `SPEC` | Product behavior, scope, acceptance, terminology, and business policy | architecture choices or generic Agent workflow |
| `PLAN` | Architecture, interface, state, data ownership, recovery, migration, and verification design | unresolved product semantics or generic Agent workflow |
| `SKILL` | Repeatable procedure requiring contextual judgment | fixed boilerplate or one bug workaround |
| `TEMPLATE` | Stable artifact shape, required fields, reusable checklist | complex decisions hidden as boxes to tick |
| `TEST_OR_EVAL` | Executable failure, boundary, counterexample, or sensitivity check | vague principle without oracle |
| `BUSINESS_PROFILE` | Domain rubric, fixtures, representative cases, semantic thresholds | generic platform correctness |
| `PROJECT_BACKLOG` | Local debt, feature follow-up, missing evidence, environment work | universal methodology claims |
| `KNOWLEDGE_NOTE` | Rationale, history, trade-off, rejected approach | mandatory rule with no enforcement path |

Prefer the smallest destination that changes future behavior. One lesson may have a primary asset plus a supporting eval, but avoid copying the same prose into every artifact.

### Common routing examples

- A Spec omitted partial-success semantics -> revise Spec; add an acceptance/eval case if recurrence risk is material.
- Production code preceded tests despite an existing TDD rule -> execution-discipline finding; strengthen the execution receipt or eval case before duplicating the rule.
- Independent review repeatedly finds contract gaps missed by self-review -> shared convergence practice plus behavioral eval.
- A stable report structure is repeatedly recreated -> template, not Skill.
- A feature-specific MML reference rule -> business profile or Spec, not global `AGENTS.md`.
- Unsafe deletion was possible without explicit authority -> project Agent rule and destructive-path eval may be justified after one high-consequence occurrence.

## 11. Action priority

Prioritize separately from promotion level. Suggested qualitative ordering:

1. unresolved safety, security, data, authorization, or contract exposure;
2. controls that prevent repeated high-cost rework or false delivery claims;
3. recurring workflow friction with a low-cost fix;
4. reusable success patterns with evidence;
5. hypotheses requiring a controlled experiment;
6. explanatory notes with no immediate behavior change.

Do not fabricate numerical ROI. If effort or benefit is estimated, label assumptions and avoid false precision.

## 12. Future validation

Every proposed asset change should define:

- next qualifying use case or population;
- expected observable behavior;
- baseline or counterfactual when comparison matters;
- evidence to retain;
- success, failure, and removal criteria;
- review date or trigger;
- owner.

Examples:

- A new execution-card field succeeds if the next three applicable Slices contain a valid RED reason and no test-after exception is hidden.
- An independent review rule succeeds if contract findings are measured separately from self-review and review cost remains proportionate.
- A semantic rubric remains a candidate until it is tested on holdout governance samples and repeatability is reported.

## 13. Retrospective quality gate

The package is ready only when:

- central claims cite identifiable evidence;
- facts, assessments, hypotheses, and unknowns are visibly separated;
- incomplete or contradictory evidence limits the conclusion honestly;
- successes and failures both receive causal scrutiny;
- every promoted item has one primary destination and scope;
- project-specific semantics are not generalized into global rules;
- existing assets are checked before new ones are proposed;
- immediate delivery work is separated from method improvement;
- follow-up changes remain unexecuted unless separately authorized;
- adopted candidates have a future validation and removal path.
