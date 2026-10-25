# SDD Project Bootstrap Model

Use this model to create project instructions that are accurate enough to act on, concise enough to load repeatedly, and stable enough to govern more than one feature.

## 1. Stage 0 contract

```text
external/system/user instructions
              |
      repository AGENTS.md
              |
    scoped nested instructions
              |
Spec -> Plan -> Tasks -> code/tests -> evidence -> Finish
```

Repository Agent instructions govern how work is performed. They point to project contracts; they do not replace them.

## 2. Statement evidence

| State | Meaning | May be written as a current rule? |
|---|---|---|
| `VERIFIED_REPOSITORY_FACT` | Directly observed in current repository structure/configuration | Yes, within observed scope |
| `DECLARED_NOT_EXECUTED` | Current documentation/configuration declares it, but Bootstrap did not run it | Yes, with wording that does not imply a pass |
| `EXECUTED_EVIDENCE` | Run against the identified baseline with recorded result/environment | Yes, retaining freshness limits |
| `PROPOSED_CONVENTION` | New owner-facing choice not yet approved | Draft only |
| `CONFLICT` | Relevant sources disagree | No, until reconciled |
| `UNKNOWN` | Evidence cannot establish the claim | No; record as a gap |

Repository code can reveal actual structure, but it does not alone prove desired product intent or approval.

## 3. Command evidence

| State | Meaning |
|---|---|
| `DECLARED` | Found only in current documentation or human instruction |
| `STATICALLY_VERIFIED` | Matches a manifest, task runner, CI workflow, script entry point, or tool configuration |
| `EXECUTED_PASS` | Ran successfully on the exact recorded baseline and environment |
| `EXECUTED_FAIL` | Ran and failed; preserve failure details and classify before documenting it as usable |
| `BLOCKED` | Could not run because an explicit dependency, environment, credential, platform, time, or permission gate was unavailable |
| `UNKNOWN` | No trustworthy command could be identified |

`STATICALLY_VERIFIED` is often sufficient for a Bootstrap instruction. Do not incur network, cost, destructive effects, or long execution merely to upgrade the label.

Record variants only when the repository supports them. A fallback command copied from generic ecosystem knowledge remains `PROPOSED_CONVENTION`, not a verified project command.

## 4. Source-of-truth ownership

| Question | Correct owner |
|---|---|
| How must an Agent work in this repository? | root/scoped Agent instructions |
| What behavior should the product provide? | approved Spec and acceptance scenarios |
| How will the system satisfy it? | Plan, ADR, interface/data/operational contracts |
| What bounded work happens next? | Tasks and current execution card |
| What happened during implementation? | source, tests, receipts, repository state |
| Does implementation match contracts? | convergence evidence |
| Is a named delivery action prepared? | Finish evidence |
| What did the team learn for future work? | retrospective learning package and approved asset updates |

When a repository uses other filenames, map responsibilities rather than imposing these names.

## 5. Durability filter for Agent instructions

Include a rule only when most of these are true:

- it applies to repeated work in the file's scope;
- it changes Agent behavior at a predictable trigger;
- it is supported by repository evidence or explicit owner policy;
- it is stable across multiple features;
- an Agent can tell whether it complied;
- it belongs at repository or subtree scope;
- its maintenance cost is proportionate to its risk;
- no better-owned Spec, Plan, test, template, or tool configuration exists.

Examples that usually belong:

- read `design/*-Requirements-Spec.md` before changing governed behavior;
- use the locked package manager and named test command;
- treat task data and uploaded archives as untrusted/generated state;
- do not create tags or deploy without explicit authorization;
- bug fixes require a regression test under the current project policy.

Examples that usually do not belong:

- a current feature's button text;
- one task's target files;
- an unapproved future database design;
- a long language style guide already enforced by tooling;
- a personal filesystem path to a Skill;
- “write clean code” without project-specific action or check.

## 6. Instruction quality

Prefer rules with this shape:

```text
When <trigger>, perform <required action>, then verify <observable evidence>.
```

Not every rule needs literal formatting, but it should answer what changes Agent behavior.

Weak:

```text
Ensure high quality and follow best practices.
```

Actionable:

```text
For behavior changes, update the applicable approved Spec first, establish a focused failing test for the agreed behavior, and run the affected contract tests before reporting completion.
```

Avoid over-specifying mechanics that differ by task. Link to a maintained coding standard or test guide only when the path is repository-relative, available to intended Agents, and authoritative.

## 7. Instruction layering

### Root file

Use for repository-wide:

- project and source-of-truth map;
- shared commands and gates;
- cross-cutting workflow and safety;
- version/release rules;
- nested-scope map.

### Nested file

Use only for meaningful subtree differences:

- another language/toolchain;
- generated or vendored source restrictions;
- distinct test/build commands;
- stronger data/security constraints;
- subsystem-specific ownership or architecture rules that remain stable.

Nested rules inherit root rules. State intentional overrides; do not copy the root text into every subtree. The narrower file cannot weaken higher-priority external or repository safety constraints without authorized policy.

## 8. Minimal SDD convention

A project needs responsibility mapping more than a fixed folder tree. Establish:

- where approved product intent lives;
- where technical decisions and Slices live;
- how artifact identity, approval, and supersession are marked;
- how one current execution card is selected;
- where verification/convergence evidence is retained;
- which human gates apply;
- how a changed contract invalidates downstream evidence.

If the repository has no convention, propose one fitting its existing layout. A small repository may use a single `design/` area and named files. A larger project may use change-scoped directories. Do not create empty artifacts or require the same layout across all projects.

## 9. Safety and data boundary discovery

Look for evidence of:

- secrets and sample configuration;
- uploads, archives, external documents, model output, and other untrusted inputs;
- generated output, caches, logs, build artifacts, and persistent task state;
- migrations, database writes, destructive scripts, and cleanup commands;
- network calls, paid models, credentials, and external services;
- personal, confidential, regulated, or production data;
- supported operating systems and platform-specific behavior;
- release, tag, push, publish, and deployment procedures.

State what an Agent must protect and when authorization is required. Do not expose example secrets or assume ignored files are safe to read, modify, or delete.

## 10. Audit finding classes

| Class | Meaning |
|---|---|
| `BLOCKER` | Rule conflict or false instruction could cause destructive, unauthorized, insecure, or materially incorrect work |
| `HIGH` | Missing/stale instruction is likely to cause contract, build, test, data, or delivery failure |
| `MEDIUM` | Significant friction, ambiguity, scope confusion, or maintainability risk |
| `LOW` | Bounded clarity or usability improvement |

Examples:

- personal absolute coding-standard path unavailable to other developers: HIGH when mandatory work depends on it;
- stale test command that silently skips the actual suite: HIGH;
- duplicated project overview: LOW unless contradictions exist;
- missing warning for destructive historical-data cleanup: BLOCKER when such a command is exposed.

## 11. Refresh and change control

Refresh when:

- manifests, commands, module boundaries, generated-state locations, or supported platforms change;
- repository policy or approved method changes;
- a retrospective proposes an evidence-backed rule change;
- an instruction points to a removed path or unavailable dependency;
- repeated Agent behavior shows the rule is ambiguous or undiscoverable;
- the instruction grows enough to obscure high-value constraints.

Before applying a change:

1. compare old rule, current repository fact, and proposed rule;
2. identify active work and evidence relying on the old rule;
3. preserve rationale for consequential changes;
4. route contract impact when necessary;
5. obtain approval for the exact new baseline;
6. define how future work will validate the change.

Do not regenerate the entire file from a template when a local patch preserves more verified knowledge.

## 12. Approval model

Use these distinct states:

- `DRAFT`: prepared by an Agent or human but not approved;
- `READY_FOR_APPROVAL`: validated against current repository evidence;
- `APPROVED`: exact content approved by authorized owner;
- `SUPERSEDED`: replaced by a later approved baseline;
- `STALE`: repository changes invalidate one or more load-bearing rules;
- `CONFLICTED`: applicable rules disagree and cannot both be followed.

Approval should identify the content version, hash, commit, review record, or another unambiguous baseline. Editing an approved file produces a new draft unless repository policy defines a reviewed-change mechanism.

## 13. Bootstrap quality gate

A baseline is ready for approval only when:

- repository identity and instruction scope are clear;
- current authoritative sources and precedence are mapped;
- commands are exact and carry truthful evidence states;
- generated, persistent, sensitive, and untrusted data boundaries are explicit where material;
- external, destructive, release, and deployment actions retain their authorization gates;
- SDD responsibilities and human gates are clear without empty ceremony;
- feature semantics and architecture details remain in their owning contracts;
- personal paths, missing tools, contradictions, and stale guidance are removed, resolved, or exposed;
- proposed rules are concise, durable, and actionable;
- existing user changes and project conventions are preserved;
- unknowns and unexecuted checks are visible;
- exact approval state and next step are reported.
