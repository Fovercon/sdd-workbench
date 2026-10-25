# Design views: selection and depth

Read for STANDARD or DETAILED planning. Choose views to answer concrete design
questions; a portfolio of attractive overview boxes is insufficient. Keep the
views in the existing Plan, cite Spec obligations, and avoid duplicating facts.

## Select by concern

| Concern | Suitable view | Reviewable content |
|---|---|---|
| System boundary | Context / flowchart / C4 | Actors, external systems, inputs/outputs, system and trust boundaries |
| User journey | Business flow / activity-style flowchart | Trigger, decisions, observable outcomes, primary failure/retry branches |
| Static architecture | Component / flowchart / C4 | Responsibilities, dependency direction, public boundaries, external adapters |
| Runtime collaboration | Sequence | Actual participants, calls, meaningful inputs/returns, sync vs background work, failure or timeout/retry paths |
| Persistent data | ER / typed data model | Identity, relationships/cardinality, required fields, owner, persistence and consistency rules; JSON/files are valid entities |
| Lifecycle | State | States, triggers, guards, effects, forbidden transitions, terminal/recovery states |
| Module interfaces | Class / sequence plus interface table | Real types/protocols, operations, typed inputs/outputs/errors, collaborators and invariants |
| Deployment and operations | Deployment-style flowchart / architecture | Processes, runtime placement, ports/protocols, persistent volumes, restart and availability boundaries |
| Security-sensitive flow | Trust-boundary / data-flow view | Untrusted input, validation, authorization, sensitive data movement and failure handling |

Context and structure can share a diagram only if boundaries and responsibilities
remain clear. Business flow and runtime sequence answer different questions:
which outcomes occur, and how components collaborate to produce them. A state
machine cannot replace a data model. Split a large view by concern or zoom level;
provide a named connection to the enclosing view instead of shrinking labels.

## Depth that a reviewer can test

- **STANDARD**: establish the four overview concerns from SKILL.md and add precise
  interaction details for consequential boundaries. An API label alone is not an
  interface: give meaningful input, result and rejection semantics in a nearby
  table or sequence. State why other concerns are not applicable when their
  omission could conceal a material risk.
- **DETAILED**: follow each non-trivial module down to its public contracts and
  critical collaboration. Show the main success path and relevant alternative
  paths (`alt`, `opt`, `loop`, guards). Identify who owns a write/transaction/lock,
  what happens after interruption, and what remains invariant. Link each detail
  to a Spec scenario or technical risk and its planned verification.
- **LIGHT**: keep the existing light route. Do not add a diagram catalog to a
  reversible local change simply because the renderer can draw it.

Use actual method/type/state names only when verified or explicitly proposed in
the design. Do not pass off a code observation or newly drawn explanation as an
approved Plan. Label proposed additions and route consequential discoveries to
their owning stage. Domain semantics still require authoritative grounding.

## Language and reading levels

For a Chinese-facing review, use Chinese role, action and state labels consistently.
Retain case-sensitive technical names in interface detail, tables or an explicitly
paired technical diagram; do not arbitrarily translate code symbols or change their
casing. Aliases in diagram source can make an overview readable without changing
the underlying identity. A Chinese responsibility overview does not replace the
typed interface/signature and failure details required at DETAILED depth. Cite both
levels, and let a maintained board disclose technical detail on request.

## Before passing the design gate

Check coverage of critical journeys/modules and compare diagrams with interfaces,
state tables and prose. Review especially:

- participants that disappear between acceptance and implementation;
- success-only sequences masking rejection, concurrency or partial failure;
- states without entry/exit conditions, writes without an owner, retries without
  idempotence, and data structures without stable identity;
- generic class boxes that omit the operations responsible for the behavior;
- contradictory names, arrow directions or state transitions across views.

Record a compact concern → view → contract detail → verification mapping in the
Plan. Missing core-domain input or a consequential unresolved choice stays a gate;
neither a new diagram nor a polished board supplies its answer.
