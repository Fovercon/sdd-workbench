# SDD Project Bootstrap Artifact Templates

Adapt these sections to verified repository facts. Omit irrelevant sections rather than filling them with generic advice.

## A. Root Agent instruction template

```markdown
# Repository Guidelines

## Repository map and scope

- <verified source, test, documentation, generated-state, and subsystem locations>
- <nested instruction scopes, if any>

## Sources of truth

Fresh-repository default: contract artifacts live under `design/` — `design/spec.md`, `design/plan.md`, `design/tasks.md`, evidence under `design/reports/`. Follow an established repository convention or an explicit user instruction when one exists, and record the chosen location here so later runs stay consistent; never invent a different layout per run. A superseded approved version must stay recoverable — keep physical version files (`spec-v2.md`) or a committed git baseline; renaming a sole current file without either is not allowed.

- Agent workflow and safety: `<path>`
- Product requirements and acceptance: `design/spec.md` or established pattern
- Architecture and interfaces: `design/plan.md` or established pattern
- Tasks/current Slice: `design/tasks.md` or established pattern
- Verification and delivery evidence: `design/reports/` or established pattern
- Conflict/supersession rule: <rule>

## Development workflow

- Before <behavior-changing trigger>, <required Spec/Plan/change-impact action>.
- Implement one <project work unit> at a time and retain <required evidence>.
- Do not <known invalid shortcut>; verify <observable gate>.

## Contract approval gates

- Requirements Spec: owner approval required by default; `AUTHORIZED_DERIVATION` only when the mission explicitly permits derived contracts and every core-domain semantic is grounded in user-provided evidence.
- Plan/design: owner approval required by default; `DELEGATED_TECHNICAL` only for choice classes the user explicitly delegated.
- Approval gates the user explicitly reserved cannot be satisfied by either derived status.
- Domain-defining inputs (samples, formats, rules) absent from the repository are blocking questions, never assumptions.

## Build and verification commands

- Setup: `<exact command>` — <evidence state/conditions>
- Focused verification: `<exact command>` — <selection rule>
- Full offline gate: `<exact command>` — <evidence state>
- Conditional gates: <system/UI/model/performance/platform command and trigger>
- Unknown or externally blocked gates: <honest limitation>

## Coding and design boundaries

- <locally enforced conventions or authoritative repository-relative guide>
- <module/ownership rules that apply broadly>
- <generated/vendor file policy>

## Data, security, and external actions

- Treat <external inputs> as untrusted; <required handling>.
- Do not commit or expose <sensitive/generated/persistent state>.
- Require explicit authorization before <external/destructive/release actions>.

## Version, review, and delivery

- <version authority and synchronization set>
- <required review/evidence>
- <release/deployment boundary and verification>
```

Do not include evidence-state annotations in the final instruction when they make it noisy; retain them in the Bootstrap evidence record. Wording in the instruction must still avoid claiming that an unexecuted command passed.

## B. Bootstrap evidence record

```markdown
# SDD Project Bootstrap Record

## Header

- Mode: `DISCOVER | CREATE | AUDIT | REFRESH`
- Outcome:
- Repository/worktree:
- Source baseline:
- Write authorization:
- Prepared at/by:

## Existing instruction hierarchy

| File/source | Scope | Authority/approval | State | Notes |
|---|---|---|---|---|
|  |  |  |  |  |

## Repository fact map

| Area | Fact | Evidence source | Evidence state | Confidence/limits |
|---|---|---|---|---|
| Structure |  |  |  |  |
| Toolchain |  |  |  |  |
| Tests |  |  |  |  |
| Generated/state data |  |  |  |  |
| External dependencies |  |  |  |  |
| Version/delivery |  |  |  |  |

## Source-of-truth map

| Responsibility | Current owner/path | Approval/version rule | Conflict handling | Gap/proposal |
|---|---|---|---|---|
| Agent instructions |  |  |  |  |
| Requirements |  |  |  |  |
| Plan/ADR |  |  |  |  |
| Tasks/Slice |  |  |  |  |
| Verification/convergence |  |  |  |  |
| Finish/release |  |  |  |  |

## Command catalog

| Activity | Command | Evidence state | Source/result | Environment/conditions |
|---|---|---|---|---|
| Setup |  |  |  |  |
| Focused test |  |  |  |  |
| Full offline gate |  |  |  |  |
| Lint/type/build |  |  |  |  |
| Local run/smoke |  |  |  |  |
| Conditional/release gate |  |  |  |  |

## Safety and state boundaries

| Boundary | Protected/unsafe material | Required Agent behavior | Authorization/gate | Evidence |
|---|---|---|---|---|
| Secrets |  |  |  |  |
| External input |  |  |  |  |
| Generated/persistent state |  |  |  |  |
| Destructive action |  |  |  |  |
| Network/model/external service |  |  |  |  |
| Release/deployment |  |  |  |  |

## Minimal SDD convention

- Artifact locations/pattern:
- Approval and supersession:
- Current Slice identity:
- Verification/convergence evidence:
- Human gates:
- Change-impact rule:
- Handoff/retrospective location, if established:

## Audit findings or proposed delta

| ID | Severity | Existing text/state | Evidence | Proposed change | Affected work |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Validation and approval

- Paths checked:
- Commands executed:
- Commands not executed and why:
- Conflicts/unknowns:
- Draft identity/hash:
- Approval state/owner:
- Next step:
```
