# Requirements Contract Model

## 1. Artifact states

| State | Meaning | Permitted next step |
|---|---|---|
| `NEEDS_INPUT` | A missing fact, authority, or product decision blocks a sound contract | Investigate facts or continue the decision frontier |
| `READY_FOR_APPROVAL` | The contract passes the quality gate but no human has approved this exact version | Human review and approval or requested revision |
| `APPROVED` | An authorized human explicitly approved this exact version | Technical planning may begin |
| `AUTHORIZED_DERIVATION` | In authorized RUN, quality-checked obligations faithfully map to explicit user intent with no new material decision, no core-domain semantic resting on an assumption, and no user-reserved approval gate covering the contract; policy permits this route | Technical planning may begin; do not claim exact-file human approval |
| `SUPERSEDED` | A newer contract version was approved | Historical reference only |

`DRAFT` may be used while editing, but it is not a handoff outcome. Never infer approval from silence, prior approval of another version, successful validation, implementation already existing, or a user asking to “continue”.

For `AUTHORIZED_DERIVATION`, record the exact file hash, every obligation’s decision source, the RUN mission authorization and quality-gate result. Unresolved business semantics, scope additions, material assumptions, any core-domain semantic grounded only in an assumption, or a user-reserved/project-required approval gate prohibit this state. It is not inferred from silence, a generic “continue”, or the completeness of the request’s wording. A new explicit user requirement may authorize its faithful derivation without another identical approval question.

## 2. Statement classes

| Class | Definition | Example |
|---|---|---|
| `FACT` | Verified current-state or external evidence | Existing tasks persist their status in `progress.json` |
| `USER_DECISION` | Product intent explicitly selected by an authorized human | A restarted running job becomes paused and awaits confirmation |
| `ASSUMPTION` | Provisional premise, visible with owner and validation point | Operators have access to the existing task identifier |
| `OPEN_QUESTION` | Unresolved decision or unavailable information | Whether successful records remain committed after one record fails |
| `CONSTRAINT` | Binding limit from policy, compatibility, operations, or Agent instructions | Uploaded archives must be treated as untrusted input |

Current implementation is not proof of desired intent. A test is not a requirement source unless the project treats it as an approved behavioral contract.

## 3. Product decision versus discoverable fact

Investigate before asking:

- existing file locations and naming conventions;
- current API behavior and state transitions;
- nearby tests and established vocabulary;
- applicable Agent instructions and ADRs;
- documented platform limits.

Ask a human when the answer selects:

- the format, content, or rules of the primary domain data the product exists to process — request a sample or reference specification when none is available;
- who may perform an action;
- what partial success means;
- which data is authoritative or retained;
- retry, cancellation, recovery, or conflict semantics;
- compatibility or deprecation promises;
- privacy, security, audit, or approval policy;
- acceptable risk, quality threshold, or business priority.

The Agent may recommend an option and explain evidence. It may not make the decision by hiding it in an assumption.

## 4. What belongs in the requirements contract

Include an item when a stakeholder, external consumer, operator, regulator, or downstream acceptance review depends on the behavior.

Examples:

- “A failed governance command can be rerun without repeating preprocessing.”
- “A restarted running job is shown as paused until an operator confirms continuation.”
- “An uploaded archive containing traversal paths is rejected without writing outside the task area.”
- “Progress does not report 100% before all required commands reach an accepted terminal state.”

Move an item to Plan when it only describes an interchangeable internal solution.

Examples:

- which Python class owns queue recovery;
- which database table or JSON helper stores the state;
- whether polling or event dispatch implements progress updates, unless consumers contractually depend on the mechanism;
- exact source paths, function signatures, thread layout, or library choice.

Some choices have both layers. State the external promise in the contract and defer the internal realization to Plan.

## 5. Requirement and acceptance rules

### Functional requirement

A functional requirement should:

- use a stable identifier such as `FR-001`;
- name one binding observable obligation;
- identify the actor or system responsibility when ambiguous;
- avoid combining unrelated behavior with “and”;
- avoid implementation detail unless it is itself an external constraint;
- link to one or more acceptance scenarios.

### Acceptance scenario

An acceptance scenario should state:

- relevant initial state and permissions;
- triggering action or event;
- externally observable result;
- state or data effects that matter to stakeholders;
- negative evidence when absence matters, such as “no file is written outside the task directory”.

Not every invariant needs verbose Given/When/Then prose. A state table, decision table, schema, example pair, or measurable assertion may be clearer.

### Non-functional requirement

Define the workload, environment, measurement, threshold, and failure interpretation when claiming performance or reliability. Do not invent values for “fast”, “high availability”, “large batch”, or “user-friendly”.

For AI-generated outputs, separate:

- deterministic structure and safety constraints;
- semantic quality dimensions;
- representative inputs or a sampling strategy;
- scoring rubric and passing rule;
- human review or escalation where judgment remains necessary.

## 6. Blocking questions

An open question blocks approval when a different answer changes any of:

- user-visible results or workflow;
- the correctness of a mandatory obligation depends on domain semantics whose defining artifact is unavailable;
- stored data meaning, authority, retention, or loss behavior;
- security, privacy, authorization, or audit obligations;
- failure, retry, recovery, cancellation, or concurrency semantics;
- external compatibility;
- acceptance evidence or success threshold;
- committed scope or priority.

Technical choices with stable product behavior belong at the Plan design gate rather than blocking the requirements contract.

## 7. Readiness gate

A contract is `READY_FOR_APPROVAL` only when:

1. mandatory scope has stable identifiers;
2. every mandatory requirement is testable and linked to evidence;
3. material normal, error, boundary, permission, and recovery behavior is specified;
4. terms and state/data meanings are consistent;
5. no blocking product question remains;
6. assumptions are visible and safe to approve as assumptions;
7. non-goals and deferrals are explicit;
8. applicable constraints and source provenance are recorded;
9. no unapproved technical design is presented as product intent;
10. the exact version is ready for human review.

## 8. Downstream contract chain

Use stable traceability:

```text
Requirement FR-x
  -> Acceptance AC-x.y
  -> Plan responsibility / invariant
  -> Behavior slice S-x
  -> Implementation evidence
  -> Verification evidence
  -> Convergence coverage row
```

When a requirement changes, invalidate only the affected downstream links, but do not claim unaffected links remain valid without checking shared contracts and dependencies.


## 9. Small revisions without parallel records

For a bounded revision, put the decision source, changed obligations, affected
links and next action once in the existing Spec revision section or existing
change record. Reference an existing scoped glossary entry instead of copying
its definition into every record; keep the acceptance obligations in Spec.
Do not add a separate decision/impact/handoff document when those facts already
have a suitable home. If an external receipt is needed to hash the final Spec,
keep it to identity, authority and pointers; do not repeat the business decision
table there. Preserve prior versions. Explicitly distinguish an inherited citation
from a source actually inspected: if the cited original is unavailable, retain
that uncertainty even when its term or decision stays unchanged. Compactness
must not remove the information required to resume or verify the change.
