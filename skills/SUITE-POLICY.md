# AI 辅助 SDD Skill 套件治理政策

本政策管理 `skills/` 中的方法资产，目标是在覆盖完整 SDD 闭环的同时控制触发噪声、上下文体积、文档仪式和维护成本。它不是项目 `AGENTS.md`，不会自动成为业务仓库的开发约束。

## 1. 核心原则

### 1.1 一个时刻只有一个主要 Skill

主要 Skill 对当前工作结果负责。其他 Skill 只能是：

- 在主要 Skill 之前解决一个真实前置问题；
- 在主要 Skill 之后接收其明确结果；
- 提供一个按风险触发的辅助设计；
- 记录后续建议，不在同一动作中自动展开。

不允许用“完整流程”为理由同时加载所有 Skill。

### 1.2 Skill 推荐不等于调用，调用不等于授权

- Router 的诊断操作只推荐；`RUN` 在已授权任务内持续执行，每轮只调用一个主要阶段能力。
- 阶段 Skill 只完成自己的输出合同并返回控制流程；RUN 核对状态后继续下一阶段或下一片。
- 文件修改、命令执行、提交、外部调用和破坏性动作分别服从用户与仓库授权。
- `READY`、`APPROVED`、`COMPLETE`、`CONVERGED` 和 `READY_FOR_HUMAN_ACTION` 保持各自语义，不能互相替代。

### 1.3 按风险缩放活动，不按模板补齐文档

项目需要的是明确责任和证据，不是固定数量的 Markdown 文件。

- 已有有效合同不重复生成。
- 低风险局部变化不强制创建独立验证设计。
- 没有上下文边界不创建 handoff。
- 没有交付目标不运行 Finish readiness。
- 没有可复盘的学习问题不生成 retrospective。
- 空的 Spec、Plan、Tasks 和报告不算进度。

### 1.4 通用方法与领域扩展分开

通用 SDD Skill 不包含单 MML、特性治理或其他领域语义。领域规则进入：

- 项目 Spec/Plan；
- 领域 Skill；
- 领域评测 profile、样本和 Rubric。

领域 Skill 不进入通用主链，也不能用一个领域的评测结果宣称跨领域有效。

## 2. 上下文预算

默认工作集为：

```text
项目 AGENTS.md
+ 当前主要 Skill 的 SKILL.md
+ 当前工作的权威合同
+ 当前主要 Skill 明确要求的一份相关 reference
```

只有任务确实进入某种模式时才读取该模式的 reference。评测用例用于开发和回归 Skill，不应在普通使用时整体加载。

禁止：

- 为“以防万一”加载所有阶段 Skill；
- 把整个会话、完整 Git 历史或所有项目文档复制进上下文；
- 让 Router 复述每个下游 Skill 的完整方法；
- 在多个 Skill 中复制同一业务合同。

## 3. Skill 分类与激活

### `CORE_STAGE`

只在项目达到该阶段且前置条件满足时激活。阶段完成后返回，不在同一阶段 Skill 中混入下一阶段；已授权 RUN 由控制流程继续，不重复逐阶段索取授权。

### `CONTROL`

只解决流程入口、项目初始化或阶段识别问题。用户已给出明确、适用的阶段请求时，不增加控制层。

### `CONDITIONAL`

必须有可观察触发器，例如合同传播、多层验证风险、上下文边界或复盘学习问题。不能因为“可能有帮助”而调用。

### `DOMAIN`

必须同时匹配业务领域、输入模型和评测目标。领域扩展不得改变通用 Skill 的语义。

当前分类以 [`CATALOG.md`](CATALOG.md) 为准。

## 4. 流程深度

流程深度根据风险和现有资产选择，不作为新的 Skill。

### `BOUNDED`

适用于合同明确、影响局部、可逆、已有充分验证的工作。直接进入当前阶段，避免重跑完整前序流程。

### `STANDARD`

适用于正常新功能或中等复杂变化。使用 Requirements、Plan、逐 Slice Implement 和 Converge；只有存在交付目标时才进入 Finish。

### `HIGH_ASSURANCE`

适用于高后果、难回滚、多边界或非确定性工作。在标准路径上按需增加 verification design、更强独立评审、真实环境证据和明确人工关卡。

流程可以轻量，但以下硬约束不随深度取消：

- Agent 指令和用户授权；
- 产品含义不能由实现自行决定；
- 新仓库产物布局使用套件默认（`design/` 契约目录），有既有约定或用户指示时跟随并写入 AGENTS.md，不得每次运行自创布局；
- 被替代的已批准合同必须可恢复：物理版本文件或已提交 git 基线二选一；无留痕的改名替换不允许；
- 核心域语义必须有据：产品主要价值所依赖的领域语义（数据格式、规则含义、领域术语）只能来自用户决策、用户提供物或仓库证据；缺失即 `NEEDS_INPUT`，不得以假设或"可替换参考实现"名义编造放行；提示词完整不等于决策完整；
- 用户显式保留的人工门禁最高：`AUTHORIZED_DERIVATION` 与 `DELEGATED_TECHNICAL` 不能满足用户点名要求的批准；推导与委托授权必须显式声明，不得从"完整交付"语气推断；
- 不能覆盖或丢弃不明归属的工作；
- 完成声明必须有当前证据；
- 外部和破坏性动作必须满足自己的授权政策。

## 5. 新 Skill 准入门槛

新候选必须同时回答：

1. 问题是否在多个任务中重复出现？
2. 现有 Skill 为什么无法通过一个模式、reference、模板或 eval case 承载？
3. 该能力是否包含需要上下文判断的重复方法，而不只是固定格式？
4. 输入、输出、停止条件和授权边界是否清楚？
5. 自动触发是否能用简短且有区分度的 description 表达？
6. 是否有不同类型的正向、反向和边界评测场景？
7. 它会增加多少上下文、选择和维护成本？
8. 效果不好时如何合并、降级或退役？

以下情况优先不创建 Skill：

- 只出现一次的项目问题；
- 可以成为现有 Skill 的 eval case；
- 只是一个稳定文档骨架，应做成模板；
- 属于业务合同，应进入 Spec/Plan；
- 属于仓库长期约束，应进入 `AGENTS.md`；
- 只是对现有 Skill 的不同叫法；
- 需要的只是一个确定性脚本。

## 6. 生命周期

```text
IDEA
  -> CANDIDATE
  -> ACTIVE
  -> REVISE / MERGE / DEPRECATE
  -> RETIRED
```

### `IDEA`

只有问题描述，不进入目录和 Router。

### `CANDIDATE`

记录适用假设、现有案例和晋级条件，不创建可自动发现的 Skill 目录。

### `ACTIVE`

具有明确 description、边界、输出合同、评测用例和维护责任。加入 Catalog，必要时接入 Router。

### `DEPRECATED`

保留迁移说明和替代能力，不再作为推荐路径。Router 和 Catalog 先移除正式路由，再决定是否删除目录。

### `RETIRED`

没有独立使用价值且迁移完成。删除前确认没有 Skill、模板、案例或外部文档引用。

## 7. 合并优先于拆分

满足任一条件时，优先把能力并入现有 Skill：

- 触发条件和前置合同相同；
- 输出属于同一阶段合同；
- 用户通常必须连续调用两者才能获得一个完整结果；
- 两者主要差异只是风险深度或输出格式；
- 新能力可以由一个模式或 reference 隔离，而不增加普通路径上下文。

只有在触发、输入、权限、停止条件或评测目标存在稳定差异时，才保留独立 Skill。

## 8. Description 治理

每个 description 必须包含：

- 它做什么；
- 何时使用；
- 一个能阻止相邻 Skill 误触发的关键排除条件。

Description 不应：

- 罗列所有能力；
- 使用“任何开发任务”“确保质量”等兜底词；
- 同时声称拥有多个 SDD 阶段；
- 因为任务提到测试、评审或文档就自动触发专项 Skill。

修改 description 后，应重新运行该 Skill 的结构校验，并检查 Catalog 与 Router 是否仍一致。

## 9. 依赖与路由政策

- 阶段 Skill 可以推荐下一能力；只有 Router RUN 在任务授权内承担连续调用。
- Router 保存阶段、结果状态、选择规则和 RUN 控制协议，不复制下游完整工作流。
- 条件 Skill 不得成为所有主阶段的强制依赖。
- 领域 Skill 不得成为通用 Skill 的必需依赖。
- Skill 引用另一个 Skill 时，应说明触发条件和授权边界。
- 当被引用 Skill 不存在时，退化为清楚的项目动作，不编造能力。

## 10. 评测与健康指标

每个 Active Skill 至少维护：

- 正常场景；
- 相邻 Skill 容易误路由的反例；
- 证据不足或人工关卡；
- 权限、脏工作区或外部动作边界；
- 不应执行的过度流程场景。

套件维护重点观察：

| 指标 | 要回答的问题 |
|---|---|
| Trigger precision | 该 Skill 是否只在真正适用时触发？ |
| Route correction rate | 使用后是否频繁发现应该换另一个 Skill？ |
| Artifact usefulness | 输出是否直接被下游消费，而不是闲置文档？ |
| Duplicate guidance | 同一规则是否在多个 Skill 中漂移？ |
| Context footprint | 普通任务实际加载了多少指令和参考资料？ |
| Eval stability | 修改后是否破坏已有关键场景？ |
| Bypass frequency | 用户是否经常绕开该 Skill，原因是过重还是不适用？ |

没有实际记录时使用定性判断，不编造百分比或收益数据。

## 11. 定期整理

在以下时机审查套件：

- 新增两个以上 Skill 后；
- Router 路由表明显增长时；
- 多个 Skill 开始重复相同边界；
- 用户频繁跳过某个 Skill；
- retrospective 多次指出流程过重；
- 某个领域扩展开始影响通用主链。

整理顺序：

1. 检查 Catalog 分类和实际触发；
2. 收紧 description；
3. 把固定结构移入模板；
4. 把条件细节移入 reference；
5. 合并同阶段重叠能力；
6. 将领域内容移出通用 Skill；
7. 标记 Candidate、Deprecated 或 Retired；
8. 更新 Router 和评测场景。

## 12. 闭环执行与回归

RUN 的任务授权、合同派生、技术委托、证据失效、连续推进、实际交付和方法维护见 [执行协议](sdd-workflow-router/references/closed-loop-model.md)。`AUTHORIZED_DERIVATION` 和 `DELEGATED_TECHNICAL` 是独立的授权依据，不伪装成人逐文件批准；项目强制人工门禁仍适用。

控制规则测试与模型行为演练分别记录；结构校验不能代替两者。当前结果见 [上游闭环验证记录](https://github.com/Fovercon/AI-Native-SDD/blob/0dc9414de8d7081bc8c425fe3593dcf44ce3c315/05-notes/2026-10-09-sdd-closed-loop-validation.md)。本仓库套件版本由 plugin.json 管理，每个 Git 标签对应一份不可变发行包；验证及发布流程见 [版本发布说明](../docs/RELEASING.md)。历史模型演练不替代当前版本的验证。

## 13. 当前冻结决策

- 当前主链保持五个阶段 Skill，不继续拆分 TDD、测试编写或执行卡。普通代码评审按 2026-09 准入决策独立为 `sdd-code-review`（`CONDITIONAL`，仅限无已批准规格基线的评审；有基线仍由 converge-review 承载，见 CATALOG 准入记录）。
- Bootstrap、Router、verification design、change impact、handoff 和 retrospective 均按条件触发。
- `governance-skill-eval` 保持领域扩展，不升级为通用测试阶段。
- `sdd-pattern-transfer` 暂留 Candidate，未满足跨领域晋级条件前不创建。
- 下一轮新增 Skill 前，优先通过现有 Skill 的模式、reference、模板或 eval case 解决。
