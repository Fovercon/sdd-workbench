# Real repository task protocol

These source-checkout evaluators are outside the plugin package inputs. They
generate derived public source snapshots in a new external directory, never a live
skill installation. They are not company projects, human usability evidence,
framework comparisons, or proof of six-host task compatibility.

## Frozen inputs

| Case | Real source baseline | Ordinary request | Independent checks |
|---|---|---|---|
| encoding | `2093cc9ca463862a57577a235152196ea5d9cb03` | Reproduce and repair Windows legacy-encoding failures across Python CLI I/O and documentation regressions | Parsed Unicode JSON over cp1252 pipes for installer/doctor/review, UTF-8 human output, simulated legacy file decoding; original regressions and scope review |
| adapter | `7c79aad193269b1daae4dfe08f102cb815955d78` | Read-only engineering review of the actual JavaScript DeepSeek provider and Node tests | Original Node suite, source and user-file hashes, executable independent reproductions for findings; evidence may support zero findings |

Runtime skills default to the released `7c79aad` snapshot, separately from the
application source. The actor gets runtime instructions/resources, not runtime
evals or tests. Application source still contains its own tests and eval assets;
the actor must not inspect evaluator receipts, sibling trials or held-out probes.
The real source was not reduced to a toy module. Source adaptations are explicit:
an appended isolation policy, ordinary task request and synthetic preservation
note. Every original source, derived input and runtime file has a SHA-256 receipt.

## Preparation and deterministic calibration

Run from a source checkout containing the pinned commits (fetch them separately if
using a shallow clone). Choose a fresh path outside the checkout:

```sh
python3 -B evals/real-tasks/prepare.py --case encoding --host pi --output /temporary/encoding-pi
python3 -B evals/real-tasks/prepare.py --case encoding --host codex --output /temporary/encoding-codex
python3 -B -m unittest discover -s evals/real-tasks -p 'test_*.py' -v
```

Use `--case adapter` for the read-only task. Same-case `inputs` and `runtime_skills`
maps must match across hosts. `--suite-ref` changes the evaluated runtime, never
the pinned task source. Record the resolved commit; do not compare floating refs.
Existing outputs are rejected, and the generator never installs a client or skill.

The calibration regression requires all five encoding probes to fail on the real
pre-fix source and pass on the released repair. It also checks host input equality,
runtime/oracle separation and detection of read-only source changes/additions.
This establishes probe sensitivity, not agent performance. Three JSON roundtrips
and document decoding are mandatory task obligations. UTF-8 human stdout is an
additional release-parity observation: the ordinary request did not prescribe its
encoding, so that observation is reported without silently imposing another gate.

## Native execution

Choose a host/model already authorized for the project. Do not install clients,
change global settings, copy credentials or select another provider silently.
Record the executable and actual `--version`/`exec --help` output first. Freeze the
invocation, stdout JSONL, stderr, exit code, tool outcomes and runtime read evidence
outside `project/`. Use the same ordinary request in each fresh project; do not
reveal the evaluator or expected patch to the actor.

For Pi 0.86.1, the trial used existing default model configuration and these native
flags, with `project/` as cwd:

```text
pi --offline --no-session --mode json --no-extensions --no-skills
   --skill <trial>/runtime-skills --no-prompt-templates --no-themes
   --no-context-files --tools read,bash,edit,write --print <prompt>
```

The prompt explicitly says to read `AGENTS.md` and `REQUEST.md`, identifies the
supplied runtime, and excludes sibling trials/evaluator files. `--offline` disables
startup network operations, not model calls. Pi's tool scope here is an instruction
boundary, not an OS sandbox. Inspect the `system.sections.skills` event and actual
tool events; discovery of 12 descriptions does not prove use of a skill body.

For Codex 0.164.0-alpha.11.1, the trial used the observed desktop-bundled executable,
`exec --ignore-user-config --ephemeral --json --sandbox workspace-write`,
`approval_policy="never"`, `project_doc_max_bytes=0`, `web_search="disabled"`,
`sandbox_workspace_write.network_access=false`, and explicit model/effort from the
existing configuration. `project_doc_max_bytes=0` suppresses implicit Agent
documents; the prompt explicitly instructs reading the project's `AGENTS.md`.
No `HOME` or `CODEX_HOME` overrides are used; existing auth remains client-owned.
Discovered home skill paths are disabled through invocation-only `skills.config`
entries. A harness-created `project/.agents/skills` symlink points to the frozen
runtime. Record this extra link separately from the shared task input receipt.
Do not count that allowed harness link as an actor modification.

Native host/version/model/permissions differ, so these runs provide individual
compatibility evidence rather than a controlled model or host ranking. Do not use
the desktop's collaboration subagents as substitutes for native host execution.

## Independent adjudication

After the native process ends, run the evaluator from the source checkout, with
an output path outside the actor project:

```sh
python3 -B evals/real-tasks/probe.py --trial /temporary/encoding-pi --output /temporary/encoding-pi/probe.json
```

Then independently rerun the actor's relevant regressions and any review probes.
Check native events, not just the final answer: actual skill body and reference
reads, tools/errors, regression failures before the fix, final patch scope,
protected inputs and actual verification. For review, distinguish reproducible
contract defects from optional hardening, unverified external integration and
test gaps. A green original Node suite cannot certify a review's findings.

`deterministic_pass` deliberately does not decide semantic success. Classify each
run separately as completed, failed, interrupted, blocked, or requiring recheck;
record unsupported claims and counterevidence. Preserve failures, guided follow-ups
and retries in separate directories. Missing native/model evidence is `NOT_RUN` or
`BLOCKED`, never inferred from installation or discovery.

`usage.py --host pi|codex --events <trial>/events.jsonl --output <trial>/usage.json
--interaction <trial>/interaction.md` preserves native field names, counts only
completed usage events, and creates a readable view alongside the unchanged raw
stream. It does not treat client completion, native token estimates or green tools
as a semantic verdict. Missing usage fields remain missing.

## Remaining company trial

Before using company data, obtain the repository/task, stack, expected behavior,
protected scope, hosts/models, model-network policy and reserved approvals from
the owner. Begin with one real bug and one API/data or multi-file change. Keep
company code, raw client events and actual feedback databases outside package
inputs. Record project representativeness and first-time human use separately.
