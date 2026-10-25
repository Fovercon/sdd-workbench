# AI 辅助 SDD Skill 目录

本目录管理当前可用的 SDD Skill、适用条件和相邻边界。它是维护与选用指南，不是每次开发都要加载的运行合同；项目开发仍以仓库 `AGENTS.md` 和当前阶段合同为准。

## 最小加载原则

一次工作通常只加载：

```text
项目 AGENTS.md
+ 一个主要 Skill
+ 当前 Spec / Plan / Slice
+ 一个确实需要的参考文件
```

如果用户已经明确当前阶段和目标，直接使用对应 Skill。阶段不清楚时用 `sdd-workflow-router` 诊断；完整工程任务需要持续推进时用其 `RUN` 模式。阶段 Skill 返回控制流程，由 RUN 在任务授权内连续推进；每轮仍只加载一个主要阶段能力。

## 分类

| 类别 | 含义 | 使用规则 |
|---|---|---|
| `CORE_STAGE` | 日常研发主链中的阶段能力 | 一个时刻只使用一个 |
| `CONTROL` | 流程入口或项目级控制能力 | 入口、初始化、状态不清或授权连续执行时使用 |
| `CONDITIONAL` | 由风险、变化或上下文事件触发 | 不进入固定主链 |
| `DOMAIN` | 特定业务领域扩展 | 只有领域和评测目标匹配时使用 |

## 当前 Active Skill

| Skill | 类别 | 何时使用 | 何时不用 | 主要输入 | 主要输出 | 修改边界 |
|---|---|---|---|---|---|---|
| [`sdd-project-bootstrap`](sdd-project-bootstrap/SKILL.md) | `CONTROL` | 新仓库；`AGENTS.md` 缺失、过期或冲突；建立 Stage 0 | 每个普通需求开始时；定义功能行为或架构 | 仓库结构、规则、清单、CI、测试和文档 | Agent 规则草案/审计、真源图、命令证据 | `DISCOVER/AUDIT` 只读；`CREATE/REFRESH` 需明确写授权；不能自批 |
| [`sdd-workflow-router`](sdd-workflow-router/SKILL.md) | `CONTROL` | 阶段/阻塞不清；完整任务需要持续开发、验证、修复和交付 | 只要求单个明确阶段且无需控制流程 | 用户目标、合同状态、仓库和证据 | 一个主要 Skill、人关或项目动作 | 诊断只读；RUN 连续执行已授权工作，保留阶段门禁 |
| [`sdd-requirements-contract`](sdd-requirements-contract/SKILL.md) | `CORE_STAGE` | 新产品意图；影响分析路由后的需求修订；形成可批准 Spec | 技术设计、任务拆解、实现和完成态评审 | 需求来源、决策、现状证据、Agent 规则 | 可追溯需求合同和批准状态 | 可更新需求产物；人批准或 RUN 中忠实推导已明确意图；不自造业务选择 |
| [`sdd-plan-slices`](sdd-plan-slices/SKILL.md) | `CORE_STAGE` | Spec 有效且授权依据明确，需要设计合同、垂直 Slice 和当前执行卡 | 需求尚未稳定；上下文包交接；完成态评审 | 有效 Spec、授权来源、架构事实、接口和测试现状 | Plan、Tasks、一个当前执行卡 | 只规划，不实施、提交或发布 |
| [`sdd-implement-slice`](sdd-implement-slice/SKILL.md) | `CORE_STAGE` | 一个执行卡已批准并授权实现 | 创建 Plan；批量执行整个待办；判断整体收敛 | 当前 Spec/Plan/执行卡、工作区和验证要求 | 一个 Slice 的代码/测试增量和执行回执 | 每次只完成当前 Slice；RUN 返回后继续；动作按已有授权核对 |
| [`sdd-converge-review`](sdd-converge-review/SKILL.md) | `CORE_STAGE` | 实现范围完成或到达评审里程碑，需要判断合同是否收敛 | 无 Spec 基线的普通代码评审；框架对比 | Agent 规则、Spec、Plan、Tasks、实现和验证证据 | 收敛结论、覆盖矩阵和回流阶段 | 评审与路由，不代替风险接受或发布授权 |
| [`sdd-finish-readiness`](sdd-finish-readiness/SKILL.md) | `CORE_STAGE` | 已收敛基线准备 PR、合并、发布、部署、交接、归档或清理 | 实现还未收敛；直接执行外部动作 | 精确源/产物身份、收敛证据、目标政策 | 目标就绪结论和受保护动作序列 | 不创建 PR、合并、发布、部署或清理 |
| [`sdd-verification-design`](sdd-verification-design/SKILL.md) | `CONDITIONAL` | 多层边界、恢复、并发、迁移、安全、性能、跨平台或模型质量需要专门证据设计 | 低风险修改已有充分局部验证；实际编写/执行测试 | 已批准 Spec、足够的 Plan、风险和现有测试 | 证明义务、分层用例、Oracle、环境和门禁 | 只设计防护网，不执行或判定收敛 |
| [`sdd-change-impact`](sdd-change-impact/SKILL.md) | `CONDITIONAL` | 提议、发现或评审问题可能改变已批准合同和下游证据 | 明确且非语义的局部机械变化；直接实施 | 当前批准基线、变化描述和现有证据 | 最早归属阶段、影响矩阵和更新序列 | 只分析，不批准或实施变化 |
| [`sdd-code-review`](sdd-code-review/SKILL.md) | `CONDITIONAL` | 无已批准规格基线的具体 diff、提交区间、PR 或代码区域需要工程评审（临时 review、合并前把关、接手陌生代码） | 该工作受已批准 Spec 管辖（用 sdd-converge-review）；修改代码；批准合并或发布 | 具体评审对象、仓库规则、已声明意图（测试、文档、提交说明） | 带严重级别与证据的发现清单和边界说明 | 只评审不修改；不发明需求；不判定收敛或授权合并 |
| [`sdd-context-handoff`](sdd-context-handoff/SKILL.md) | `CONDITIONAL` | 工作跨会话、Agent、工具、仓库或中断恢复 | 同一会话正常阶段切换；自包含执行卡 | 权威合同、工作区、决策和瞬态状态 | 可核验交接包或恢复结论 | 不替代合同、进度或行动授权 |
| [`sdd-retrospective`](sdd-retrospective/SKILL.md) | `CONDITIONAL` | 里程碑、事故、重复返工、方法实验或周期复盘 | 普通状态查询、收敛或 Finish 判断 | 项目合同、历史、测试、评审和结果证据 | 学习包和方法资产变更提案 | 不自动修改 Agent 规则、Skill、模板、测试或合同 |

领域扩展 `governance-skill-eval` 不随本通用套件分发。

## 相邻边界审计

| 容易混淆的能力 | 选择规则 |
|---|---|
| Router 与任一阶段 Skill | 阶段/归属不清时诊断；完整授权任务用 RUN 连续推进；单阶段明确请求直接使用阶段 Skill |
| Bootstrap 与 Requirements | Bootstrap 定义 Agent 怎样工作和真源在哪里；Requirements 定义产品应该做什么 |
| Requirements 与 Change Impact | 新意图直接进入 Requirements；修改已有批准基线且下游可能失效时先做 Change Impact |
| Plan 与 Context Handoff | Plan 保存稳定技术合同和 Slice；Handoff 只搬运/恢复瞬态工作上下文 |
| Verification Design 与 Implement | 前者设计证明义务和防护网；后者在当前 Slice 中编写并运行所需测试和实现 |
| Verification Design 与 Governance Eval | 前者验证产品实现；后者评测治理 Skill 的业务内容质量 |
| Converge 与 Finish | Converge 判断实现是否符合合同；Finish 判断一个具体交付动作是否准备好 |
| Code Review 与 Converge | 有已批准 Spec 基线用 Converge（判定收敛）；无基线的临时或合并前评审用 Code Review（只出分级发现，不判收敛、不授权合并） |
| Finish 与 Retrospective | Finish 面向当前交付基线；Retrospective 面向未来开发方法改进 |
| Bootstrap Refresh 与 Retrospective | Retrospective 提出规则变化；Bootstrap 在单独授权和影响检查后应用仓库级规则变化 |

## 常用路径

### 已有合同下的边界清楚修改

```text
AGENTS.md
  -> sdd-implement-slice
  -> sdd-converge-review（达到声明的评审范围时）
```

不重新生成 Requirements 和 Plan；合同发现或设计缺口再回流。

### 标准新功能

```text
sdd-requirements-contract
  -> sdd-plan-slices
  -> sdd-implement-slice（逐 Slice）
  -> sdd-converge-review
  -> sdd-finish-readiness（只有具体交付目标时）
```

### 高保障变化

```text
sdd-requirements-contract
  -> sdd-plan-slices
  -> sdd-verification-design
  -> sdd-implement-slice
  -> sdd-converge-review
  -> sdd-finish-readiness
```

高保障条件包括但不限于持久化、并发、恢复、迁移、安全、性能、模型语义质量、真实外部依赖和跨平台行为。

### 变化、恢复和方法改进

```text
合同变化/实现发现 -> sdd-change-impact -> 返回最早归属阶段
跨上下文继续      -> sdd-context-handoff -> 恢复到原阶段
项目经验沉淀      -> sdd-retrospective -> 单独批准方法资产变化
```

## 当前合并决策

为控制数量，以下能力保持合并，不再拆成独立 Skill：

| 已合并能力 | 当前归属 |
|---|---|
| Align、需求盘问、Spec 编写与批准 | `sdd-requirements-contract` |
| Plan、Tasks、依赖图与当前执行卡 | `sdd-plan-slices` |
| TDD、行为保持重构、局部测试和 Slice 回执 | `sdd-implement-slice` |
| 规格覆盖、验证证据和双轴实现评审 | `sdd-converge-review` |
| PR、合并、发布、部署、交接、归档和清理的就绪评估 | `sdd-finish-readiness` 的目标模式 |

除非出现跨任务重复、现有 Skill 无法承载且有独立评测证据，不创建 `sdd-tdd`、`sdd-write-tests`、`sdd-task-card` 或类似细粒度重复 Skill。

准入记录（2026-09）：`sdd-code-review` 从上述限制名单中豁免并创建为 `CONDITIONAL` Skill。依据：无规格基线的临时评审（看 diff / PR、接手陌生代码）是重复出现的真实场景；`sdd-converge-review` 的边界明确排除它（无基线时只做有限工程评审并返回 `INSUFFICIENT_EVIDENCE`），无法通过模式或 reference 承载；两者在触发、输入和停止条件上稳定差异——有无已批准 Spec 基线，判收敛还是只出发现清单。

## 项目视图（Router 的可选操作）

需要可点击的项目概览时，使用 `sdd-workflow-router` 的 `VIEW`：
展示当前进展、下一步、模块关系和可追溯证据；来源变化后生成新版本并保留上一版。
[生成与更新说明](sdd-workflow-router/references/project-view.md)和随包 Python 脚本可在后续项目直接使用，无需案例目录或额外绘图插件。

普通状态查询仍使用只读 `STATUS`；视图不替代合同、任务记录或交接核验。
本次不新增 `sdd-project-view`：同一批来源已经归 Router 负责，展示/刷新差异可以由一个可选操作和 reference 隔离。
按需加载该 reference，不增加所有阶段的固定文件要求。

## Candidate Backlog

候选项不参与自动发现和正式流程路由。

| 候选 | 当前状态 | 已有证据 | 晋级条件 |
|---|---|---|---|
| `sdd-pattern-transfer` | `CANDIDATE` | 单 MML 到特性治理的同族系统迁移 | 至少用若干非治理场景验证 `REUSE/ADAPT/REBUILD/EXCLUDE` 判断仍成立，并证明无法由 Requirements + Plan 简单承载 |

## 维护入口

- 套件准入、上下文预算、合并和退役规则：[`SUITE-POLICY.md`](SUITE-POLICY.md)
- 每个 Skill 的详细边界、模板和行为评测：对应目录中的 `SKILL.md`、`references/` 和 `evals/`
