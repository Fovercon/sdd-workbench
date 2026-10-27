# Context measurement and bounded forward checks

These maintainer tools live in the source checkout, outside installed/plugin package inputs.
They do not install clients, change live skills or establish an OS sandbox. Use an existing,
authorized native Pi 0.86.1 setup; explicitly registered DeepSeek Flash is the current trial
model. Record `pi --version` and `pi --list-models deepseek`; the alias does not prove a backend revision.

## Reproduce a matched VIEW run

Choose fresh output directories. Only the 8 public synthetic inputs are supplied; no prior
answer, grading criteria or sibling trace is part of the actor's runtime. In the recorded
experiment the runs were sequential A1, B1, B2, A2, then revised candidate C1/C2. A/B is the
initial ABBA attempt; the final C comparison is later, **not a randomized balanced trial**.

```sh
python3 evals/context/prepare.py --ref v0.4.0 --output /temporary/view-a1
python3 evals/context/prepare.py --output /temporary/view-c1
python3 evals/context/run_pi.py /temporary/view-a1
python3 evals/context/run_pi.py /temporary/view-c1
python3 evals/context/measure.py --host pi --events /temporary/view-a1/events.jsonl --output /temporary/view-a1/metrics.json
python3 evals/context/evaluate_view.py /temporary/view-a1
```

Repeat in fresh directories and keep the candidate runtime byte-identical between repeats.
Confirm project and prompt SHA256 maps match. Before/candidate snapshots differ only in
runtime instructions/resources, not the ordinary task or expected product obligations.
The recorded run launcher used the same native flags as run_pi.py; its raw invocation is
retained per trial. `--offline` is a Pi discovery/package option, not a network sandbox:
model requests still use the existing provider. Credentials/config are not copied.
The new launcher creates private logs and rejects reuse; the timeout terminates its
foreground CLI, not a general-purpose tree of background processes. These fixtures do
not authorize starting background services.

## Read metrics correctly

- Pi assistant `message_end.usage`: add the separate input/cacheRead/cacheWrite fields.
  A per-message input maximum is a request-size observation, not measured resident memory.
- Codex `turn.completed.usage`: input_tokens already includes cached_input_tokens and may
  aggregate multiple requests. **Per-request peak is unavailable**, not equal to that total.
- Sum, input event peak, cache, output and tool text bytes are separate. Streaming deltas and
  duplicate toolResult message echoes are not counted twice. Reasoning is a subset of output.
- Missing usage remains unknown; partial totals cover reported events only. Byte counts are
  not converted into tokens. Tool categories are heuristics, not causal token attribution.
- Multiple agents require the complete parent/child trace set. A coordinator-only window
  cannot be compared with another framework's aggregate usage. These Pi fixtures use one
  actor, so they do not measure that multi-agent trade-off.
- No price, stable saving, quality equivalence or Superpowers ranking follows from a short
  benchmark. Keep failed runs and all intermediate candidates. Report individual values and
  sample size, not just a favorable mean.

## Quality precedes efficiency

`evaluate_view.py` checks the original inputs, frozen runtime, all retained bundle receipts,
lineage, structured scope, all four stage roles, source-recorded PASS/FAIL/NOT_RUN, exact
usage command, unanswered input question and PREPARED-only delivery. It discovers nested
output directories. A small invalid output is not an efficient successful result.

The controller separately reviews **all tool calls and final claims**, including code reads,
project command execution, source writes, deletion/overwriting of completed views and
out-of-scope/temporary helper files. Instruction-scoped trials cannot prove OS isolation.
Browser checks are separate:

```sh
node evals/context/browser.cjs /temporary/view-a1 /temporary/view-c1
```

The field oracle is not a human comprehension test, an independent expert review, or a proof
that the author listed every important requirement. Do not silently repair actor outputs.
Keep evaluator bugs/repairs separate from actor failures; calibration tests cover nested
bundles, changed sources and receipt tampering.

## Implementation and context-boundary guard cases

```sh
python3 evals/context/prepare_workflow.py --case implement --output /temporary/implement
python3 evals/context/run_pi.py /temporary/implement
python3 evals/context/evaluate_workflow.py implement /temporary/implement
python3 evals/context/prepare_workflow.py --case recover --output /temporary/recover
python3 evals/context/run_pi.py /temporary/recover
python3 evals/context/evaluate_workflow.py recover /temporary/recover
python3 -B -m unittest discover -s evals/context -p 'test_*.py'
```

The preparer creates an isolated **local synthetic Git baseline without a remote**; actor
instructions prohibit commits/push. Implement must preserve contracts/notes, demonstrate
native RED before the production edit and GREEN after it, then pass independent exact-ID,
order, identity and preservation probes. Recover receives a stale v1 claim while current
v2 reserves a human case-sensitivity decision: it must read current meaning, preserve all
inputs and report reconciliation, not implement from the old summary or substitute tests.
These are guard cases, not a before/after implementation cost comparison or actual host
compaction test. Review raw interactions; automated field/string checks are insufficient.

## Explicit excerpt packet integration

```sh
python3 evals/context/prepare_packet.py prepare --ref v0.5.0 --output /temporary/packet-old-1
python3 evals/context/prepare_packet.py prepare --output /temporary/packet-new-1
python3 evals/context/run_pi.py /temporary/packet-old-1
python3 evals/context/run_pi.py /temporary/packet-new-1
python3 evals/context/prepare_packet.py evaluate /temporary/packet-old-1
python3 evals/context/prepare_packet.py evaluate /temporary/packet-new-1
```

Repeat each variant five times in fresh directories. Old/new task inputs and prompt
must match byte-for-byte; freeze each runtime and record the actually reported model.
The actor chooses verified excerpts from an explicit selection including shared
constraints. A manually authored old-format packet can pass: the oracle checks
literal obligations, source identity, the 4096-byte Markdown limit, protected inputs
and runtime, rather than requiring the candidate helper or receipt schema.

Read ranges, actual calls, final authority claims and unexpected external writes
manually; string/field checks do not prove semantic completeness. Source selection
is supplied here, so this does not measure autonomous relevance discovery. Native
CLI calls test tool integration, not general repair efficiency, real compaction,
isolation or statistical superiority. Preserve batches, negative outcomes and all
usage fields separately; do not infer Token savings from the byte limit.
