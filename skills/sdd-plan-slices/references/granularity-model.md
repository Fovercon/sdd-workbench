# Planning Depth and Slice Quality


## Contents

- [Select planning depth](#select-planning-depth)
- [Design view floor by depth](#design-view-floor-by-depth)
- [Separate the three levels](#separate-the-three-levels)
- [Vertical slice test](#vertical-slice-test)
- [Common slicing failures](#common-slicing-failures)
- [Example: governance batch execution](#example-governance-batch-execution)


## Select planning depth

Use the lightest mode that still makes the work safe to review and execute.

| Mode | Use when | Durable artifacts | Current execution card |
|---|---|---|---|
| `LIGHT` | Local, reversible change; known pattern; one boundary; low operational risk | Concise Plan delta and a small set of slices | Verified file/symbol, RED/GREEN checks, completion evidence |
| `STANDARD` | Multiple modules or boundaries; new state or interface; moderate uncertainty; brownfield impact | Full Plan sections, dependency graph, vertical slices, risks and verification | Exact interfaces and verified paths for the current slice |
| `DETAILED` | Security, migration, recovery, concurrency, irreversible data effects, cross-platform behavior, or autonomous agent handoff | Full Plan plus explicit state/failure contracts, rollout and rollback, decision records | Stepwise RED/GREEN/refactor checks, focused and regression commands, evidence requirements |

Escalate the mode when any of these increase:

- consequences of being wrong;
- number of system boundaries or consumers;
- uncertainty about existing behavior;
- difficulty of rollback or recovery;
- concurrency or ordering sensitivity;
- distance between planner and implementer;
- amount of work delegated without immediate human feedback.

Do not select `DETAILED` merely because a change touches many lines. Do not select `LIGHT` merely because the requested behavior sounds simple.

## Design view floor by depth

Every depth still produces a reviewable design; only the breadth differs:

| Mode | Required design views |
|---|---|
| `LIGHT` | Prose boundary statement; a diagram only where a relationship would otherwise be misread |
| `STANDARD` | System context view; end-to-end business flow view (success path plus principal failure/retry path); structure/module view with responsibilities and dependency direction; data/state view |
| `DETAILED` | STANDARD views plus, for each non-trivial module, an interface-level design with class or sequence views and explicit state/failure contracts |

A plan that names only directories, files, and tasks does not meet the floor at any depth.

The floor is coverage, not a diagram quota. At STANDARD, give each consequential
cross-boundary journey a sequence or equivalent precise interaction contract,
including the principal rejected/failed outcome. At DETAILED, make the relevant
interface inputs/outputs/errors, concurrency and persistence boundaries, transition
guards and recovery paths reviewable for every non-trivial module. Class diagrams
are appropriate for real types/protocols; procedural modules may use sequence or
component views with interface tables. Never invent an object model to fill a slot.
Select data, deployment and trust-boundary views from actual risks using
[design-views.md](design-views.md); record justified omissions in the Plan.

## Separate the three levels

### Plan: stable design contract

The Plan records decisions that later implementation must preserve: responsibilities, interface semantics, invariants, state transitions, failure behavior, migration, security, and verification strategy.

The Plan should survive routine file moves and refactors. Exact paths are useful for impact analysis, but they are not the contract itself.

### Tasks: behavior and dependency map

Tasks explain what observable increment is delivered, what it depends on, and how acceptance will be demonstrated. They link Spec requirements to implementation work.

Tasks should survive small implementation changes. Avoid full code listings and speculative symbol-level instructions across the entire backlog.

### Execution card: precise current instructions

The execution card is deliberately short-lived. It may contain exact verified files, symbols, commands, and test names because it is created immediately before the slice is executed.

Update or discard the card when the repository changes. Do not mistake it for a permanent architecture record.

## Vertical slice test

A strong slice satisfies all of the following:

1. **Observable**: completion changes a user-visible result, an API response, a persisted state, an operational signal, or another acceptance-observable outcome.
2. **Traceable**: it links to one or more Spec requirement identifiers.
3. **Cross-layer where needed**: it includes the minimum data, logic, interface, presentation, and test changes needed for the behavior.
4. **Independently verifiable**: its evidence does not depend on an undefined later “testing phase”.
5. **Bounded**: one focused execution context can complete and review it.
6. **Dependency-explicit**: prerequisites and consumers are named; the graph remains acyclic.
7. **Reversible enough**: rollback or safe-disable behavior is stated when the consequence warrants it.
8. **No placeholders**: execution-critical behavior is decided or explicitly blocked.

## Common slicing failures

| Failure | Example | Correction |
|---|---|---|
| Horizontal phases | Build all storage, then all APIs, then all UI, then test | Deliver one end-to-end behavior at a time |
| Test-later planning | A final task says “add unit and integration tests” | Put RED and acceptance evidence in each slice |
| Overspecified durable plan | Every task embeds complete proposed code | Keep contract stable; detail only the current execution card |
| Invented repository detail | Plan names unverified files and commands | Inspect first or state responsibility without false precision |
| Hidden product decision | Planner selects partial-success semantics | Return to Spec or request a human decision |
| Foundation as a project | Weeks of framework work precede any behavior | Build only the foundation required by the first tracer slice |
| Artificial microtasks | Mechanical edits are split to meet a minute target | Split at independently verifiable behavior boundaries |
| Giant behavior task | “Implement job processing and recovery” | Separate queue admission, execution, persistence, restart recovery, and rerun behaviors |

## Example: governance batch execution

Do not create one task named “implement the runner” or horizontal tasks for database, backend, UI, and tests.

First define the durable contracts:

- accepted job states and allowed transitions;
- FIFO or other ordering semantics;
- persistence boundary and restart behavior;
- failure isolation and rerun semantics;
- status-query consistency and evidence.

Then slice by behavior, for example:

1. Accept one valid governance job and expose its queued state.
2. Execute queued jobs in the specified order and expose progress.
3. Persist state transitions and restore an interrupted queue after restart.
4. Isolate a failed item and rerun it according to the approved failure contract.

Each slice carries its own state/API/test changes and acceptance evidence.
