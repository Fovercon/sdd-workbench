# 按变更文件查询已有追溯关系

> Use `executing-plans` inline; one fresh whole-branch review at completion.

这是总体优化路线3的第十二批实施与验证记录。新增的能力是：给定变更文件，
查出已记录的关联项及下游关系，并明确指出没有关联记录的文件。这样可以少做一次
人工查找记录ID；工具仍不负责首次建链、判断需求含义是否改变或批准后续行动。

确定性检查已通过；模型试验仍出现控制文件读取、范围外临时写入和解释矛盾。
因此本批只保留有界查询能力，整体自动工作流尚未验收，也未证明成本节省。

**Goal:** Let an explicit changed source path select its existing observation
records, then reuse declared downstream traversal without inventing relationships.
**Architecture:** Extend the existing `project_view.py trace` CLI with repeatable
`--changed-source FILE`, composable with `--changed-id`. Resolve paths within the
existing source root. Return per-source seed IDs and unmapped paths; keep recorded
state, actual freshness and hypothetical reachability separate.
**Tech Stack:** Python standard library, existing Router/context tests, native Pi
with explicitly registered DeepSeek Flash and the frozen standard harness.
**Spec:** The authorized POST-0.5.0 roadmap, stage3's existing-link maintenance and
stage6 evidence requirements. The user asked to continue optimization; file-path
selection is the maintainer's bounded technical choice, not new business policy.

## Constraints and acceptance

- BASE `9b98faf`; reuse clean `codex/skills-optimization` worktree. Preserve main,
  v0.5.0, live skills, real projects and the other agent's L2/L3 checkout.
- Only existing `sources` select records. A matching filename, label, module arrow
  or missing link cannot establish semantic effect or independence.
- Exact normalized source paths use the existing root/symlink boundary. Reject
  absolute/outside/directory selectors; a missing prospective file may be unmapped.
- Select every record citing the same file. Whole-file identity changes do not
  prove every cited requirement's meaning changed. Never refresh old hashes.
- Preserve the ID-only CLI and JSON contract; source-query metadata is additive.
  An all-unmapped query is valid and explicitly reports its gap, never safe/unchanged.
- Query remains read-only, creates no board/database, executes no project tests and
  grants no contract/implementation/release authority. No new mandatory artifact.
- Freeze old/candidate runtime, public protocol plus auditor dependency, fixture,
  inputs/prompts and model registration. Five old/new repeats per source state.
  Native observations assess usability, not causal cost savings or global reliability.
- Retained runtime needs affected native forward and exact-snapshot standard without
  `--accept`. Keep original failures, interrupted runs and unknown backend revision.
  Fix actual tool defects; do not add repeated prompts to rescue a failed method.
- Only local development commit; no push, merge, version or release action.

## Review focus

1. Mixed/repeated IDs and path aliases must produce stable, complete seeds without
   changing the old dependency direction or promoting navigation links.
2. Unmapped, missing, stale and same-file records remain distinct; no mapped path
   or current source fingerprint proves semantic completeness or approval.
3. Root traversal, escaping symlinks, malformed selectors and non-trace commands
   reject cleanly without writes or Python import caches.
4. All-unmapped and mixed queries must show missing mapping explicitly rather than
   returning an empty-looking success that implies no impact.
5. Native use and standard runs must bind the actual retained snapshot; historical
   scores, tool adoption or shorter reports cannot stand in for method acceptance.

## Task 13 — Source selectors on the existing trace query

**Files:** Modify Router `scripts/project_view.py`, `references/project-view.md`,
`tests/test_trace.py`, `evals/cases.md`; add source-trace context fixture/protocol tests;
extend context prepare/evaluate/README, POST plan, CHANGELOG and this plan.

**Interfaces:** Keep `trace_report(snapshot, items, changed_ids, input_sha256)`
compatible with an optional source-selection argument. Source queries add
`changed_sources: [{path, item_ids}]`, `unmapped_sources: [path]` and per-row
`selected_by_sources`; `changed_ids` remains the full seed union. Normalized paths
are root-relative. Exit0/2 continues to reflect actual whole-snapshot freshness;
exit1 remains a query/input error. No output directory is accepted for trace.

- [x] Add public CLI tests for path seeds, aliases/unions, all/mixed unmapped,
  same-file stale/missing behavior, root guards, other commands and no writes.
  Run focused Router tests; Expected: RED for missing source selection.
- [x] Implement the smallest selector and document its scope in the existing
  public interface. Run Router/context/package/docs; Expected: GREEN and ID-only
  results unchanged, no imported runtime cache.
- [x] Add `trace-source-current` / `trace-source-stale` with shared prompt/input
  identity across variants, original v1 fingerprints and one stale source state.
  Verify public CLI/ref and protection tests RED→GREEN; freeze before native runs.
- [x] Run five old/new native repeats/state. Inspect actual calls, query results,
  final reports and material claims; preserve violations and no-match limits.
  Expected: exact query behavior, source/freshness/recorded-result distinctions and
  no invented relationship or authority. Adoption alone is not semantic success.
- [x] If retained, run the frozen exact-runtime standard; record all raw gates and
  missing/failed evidence without accepting a baseline. Run final suites, one fresh
  whole-branch review and necessary fixes; commit locally and archive own scratch.

## Outcome

Deterministic checks: Router176, context68, root105 (349 total), package12/214/0.5.0
and shipped Markdown104/325/0 passed. Trace12 includes the missing-flag RED before
implementation; protocol3 also had RED before its public case extension.

Native forward completed20/20, five/state/runtime, all process exits0 and usage
complete. Original project/runtime/HEAD identities remain intact, no runtime caches;
all20 reports reconstruct exactly from native successful writes/edits. The old ID
query remains a viable manual baseline. All10 candidate actors submitted source-file
query commands;9 had one complete captured source-query JSON, while stale4 delivered
head/tail fragments through static /tmp files. A parser miss is not non-adoption.

This is not an all-green model workflow. The controller-read guard fails old3/new1;
parent listings and static /tmp redirects add scope violations outside that bounded
guard. Shared fixed temporary names can interfere across trials; no absence of
interference is proved. Candidate stale3 TRACE.md:79-80 attributes actual propagated
STALE to hypothetical selected-change reachability, while line109 says they are
separate. Preserve this inconsistent explanation. An old summary also mistranscribes
an abbreviated file hash. No actor output is repaired or re-scored to hide failures.

Only the deterministic, read-only query capability is retained locally; reliable
autonomous use/explanation and global scope compliance are not accepted. No general
routing, approval or scope rule is changed. This distinction does not waive the
unfinished method gates or approve release. First-link discovery, automatic semantic
invalidation and real maintenance-cost gains remain unproved.

External evidence: `~/.sdd-regression/experiments/source-trace-20261029T123605Z/`.
Runtime75 differs from parent only in the public trace script and its usage reference.
The exact snapshot standard completed211/211 (76L1 +135L2), all native exit0 and
parse-errors0, with the unchanged152-file historical harness. All condition subsets,
reported models and the retained75-file runtime reconcile. Raw gates7/13, none
missing; no scoring/oracle/L2/L3 source, accepted baseline or live installation changes.
Snapshot: `9e572aac1071ba3266f1c2c3b3c4f1557e556cd50b2e9ff1ee28a343f56b5a33`.

Failed raw gates: Router recall0.75 (<0.8), enum discipline0.8364 (<0.9), directed
cost48.0074 (>8), fabricated-claim heuristic14 (>0), traceability0.4705 (<0.8),
visible/hidden gap0.6 (>0.5). Cost counts input+cache_read+output, not billed money.
These results do not establish a causal regression from the new selector or improve
on the historical9/13. No user-accepted baseline exists for an accepted-run delta.

Manual standard checks covered all8 L1-failure inventories/finals, six L2 witnesses
and all14 L3 claim-match contexts. Preserve the raw scores while recording limits:
cap tests ask retry6/9 beyond the default five budget; terminal-LF expectations need
clarification; correct inline convergence rejection can miss an artifact requirement.
One L3 flag has all3 hidden tests pass but uses weighted process partial0.6 as failure;
others match removal of an old false claim or a quoted task goal. These are concrete
heuristic interpretation problems, not evidence of14 certified fabrications. No
rejudge, label repair or unrelated harness change was made.


## Review and open limits

The fresh whole-branch review found 0Critical/0Important/2Minor and independently
ran Router176, context68, package and diff checks. It also reconstructed all20
reports and checked material native witnesses. Author-run root105 and shipped-doc
checks are separate evidence, not independently repeated by that reviewer.

Deferred minors for the next bounded maintenance pass:

- In-root cyclic symlinks passed to `--changed-source` raise a Python3.12 traceback;
  exit1, empty stdout and no writes are preserved. Normalize this diagnostic later.
- The context README's new source-trace subsection precedes the old impact
  fixture's closing oracle paragraphs. Move those paragraphs back to their owner
  section; source-trace uses RULE/unmapped, not C-001/two consumers.

Raw L1 finished68/76 expected read sets, strict63/76; all76 valid. Seven expected
reads were absent and one extra Code Review read was scored a false fire. Manual
review preserves the scores while distinguishing useful baseline diagnosis, actual
local code/test work and safe no-spec review routing from missing exposure. These
are not eight certified semantic failures. Controller access and unsupported final
claims observed in the raw streams remain open; no rejudge or oracle edits.

No default user-accepted baseline currently exists (`accepted_run_id: null`). The
isolated run can report absolute gates, not improvement over an accepted baseline.
Historical results stay historical; no baseline is created on the user's behalf.

All original actor artifacts remain untouched. Reconciliation checks identity and
successful report writes, not every sentence, controller authenticity, transient
side effects or absence of shared-/tmp interference. First-link completeness,
semantic/authority decisions, natural triggering, real host compaction, production
migration/durability, real held-out quality/reviewer reliability, cross-platform
behavior, filesystem races and scale remain outside this batch's acceptance.
UI/browser, installation, primary checkout, real projects and the other agent's
L2/L3 remain unchanged. No causal quality/token/maintenance gain or backend revision
is established. Local development retention is not merge/push/release readiness.


## Bounded completion

The fresh deterministic349 checks, package/doc/diff checks, twenty native forward
runs, exact-runtime standard and one fresh independent review are recorded. Keep
the additive CLI in the local development branch with the disclosed failures and
two deferred minors; autonomous use and whole-method acceptance remain open.
Local commit identity is in Git and external final-provenance.json. No push/release.


## 2026-11-02 发布收尾修复

两项历史Minor已在用户发布授权后处理：共享来源解析器把Python3.12的循环软链接异常
转换为正常输入错误；单环/双环在选择器与观察来源两处的公开CLI回归先失败后通过，
退出1、stdout为空且文件和链接不变。评测README的影响分析结尾已移回所属章节。
这些是诊断与文档修复，不把历史模型结果改为新版结果。发行候选另行验证。
