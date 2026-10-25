# 首版验证范围

日期：2026-10-25。此记录覆盖从上游提取并独立打包的 `0.1.0`，不构成新的模型行为评测。

| 检查 | 本机结果 |
|---|---|
| Skill Creator 结构校验 | 12 个 skills 全部通过 |
| 套件、安装与发行回归 | Python 3.12 下 17 项通过 |
| 随包 router 单元与集成检查 | Python 3.12 下 107 项通过 |
| 静态答复浏览器回归 | 49 项通过 |
| Mermaid 设计图浏览器回归 | 91 项通过 |
| 本机反馈浏览器回归 | 36 项通过 |
| Codex 插件目录解析 | CLI 0.164.0-alpha.11.1 识别 `sdd-workbench@sdd-workbench`，版本为 `0.1.0` |
| 发行包 | 可重复构建、逐文件验证、解压后安装通过 |
| 本地 Markdown 链接 | 未发现不存在的相对文件链接 |

安装测试在临时目录运行，覆盖全套安装、旧安装迁移、已存在内容冲突、本地修改保护、
升级和回退、已移除 skill 的恢复、复制中断、回执提交后中断、并行写入、损坏备份和
未知编辑保护。未更改维护者当前使用的 skills，也未代替用户提交项目反馈。

浏览器使用 Playwright 1.62.1 与本机 Chrome，覆盖桌面与窄屏，并核对无远端资源
请求、源码保留、版本/来源绑定、回执持久化及工程状态不被反馈冒充批准。

远端 CI 另行验证 Linux Python 3.10/3.12/3.13、Windows 安装回归和 Chromium
浏览器回归；以 GitHub Actions 对实际提交的运行结果为准。

本次没有改变 SDD 阶段的工作流语义。两份评测文档仅调整历史材料的外部引用，
原始模型演练按固定的上游提交链接留存。自动化测试不替代后续方法变化需要的
forward 行为评测。

## 四项审查修复验证（0.1.1）

日期：2026-10-25。基于提交 `e66d4868327bf29ba68825dbe6aeca5cb8d21e4c`
后的当前工作树，覆盖授权模板、LOCAL Finish、缺失领域评测扩展路由和本机来源链接。
修复验证最初在 `0.1.0` 的未发布工作树上完成；随后由新补丁版本 `0.1.1` 承载。
发布准备通过版本工具同步清单、更新安装示例，并去除发行测试对首版版本号的固定断言。
验证不修改维护者的实际安装。远端发布与跨平台 CI 结果以该版本的 GitHub Actions 为准。

| 检查 | 结果 |
|---|---|
| `python3 tools/package.py check` | 通过 |
| `python3 -B -m unittest discover -s tests` | 20 项通过，含 3 项跨文件合同枚举回归 |
| `python3 -B -m unittest discover -s skills/sdd-workflow-router/tests` | 112 项通过，含 5 项来源查看回归 |
| `SDD_BROWSER_CHANNEL=chrome npm run test:browser` | 静态答复 49、Mermaid 91、本机反馈 46 项通过 |
| Skill Creator `quick_validate.py` | 12 个 skills 通过 |
| 本地 Markdown 链接 | skills 内 103 个链接检查通过 |
| `git diff --check` | 通过 |

本机为 macOS、Python 3.11.14、Playwright 1.62.1 与 Chrome 155.0.8059.85。结构校验首次因
缺少 PyYAML 未能运行，在隔离临时目录安装 PyYAML 6.0.3 后通过，没有修改全局 Python。
新增合同枚举检查和来源打开检查先在旧资产上产生了对应失败，再在修复后通过。
枚举检查属于结构证据，不是模型行为证明。

来源回归覆盖真实浏览器打开、刷新、HTML 按文本展示、变化后拒绝读取，以及 HTTP
层的原版指纹、历史版本、缺失文件、未引用文件、二进制和跨项目符号链接拒绝。
静态看板与回执保持原字节；原有反馈重试、并发、重启及审批隔离回归继续通过。

实际 Agent 演练按 [contract-handoff 协议](../skills/sdd-workflow-router/evals/forward/contract-handoff.md)
在隔离目录执行。actor 仅收到请求、原始材料和 entrypoints/references/runtime 快照，
未收到评测答案、修复理由或另一版本输出；原始 trace、命令日志、输入和快照指纹在本次任务的
临时评测档案中保留，不进入发行包。对排序后的运行时 skill 文件哈希表再做 SHA256：

- 旧快照：`dd3ee26f11d951287d8dd6ecf086807b38dfa9d36063ccf76c18c8f57081270c`
- 新快照：`2086ee573be0efbc389f101457f4030cfc7419c8c2ad525bf954ac275e4ebc1b`

| 场景 | 实际结果 |
|---|---|
| 同输入旧/新 clear 实施与本地交付 | 两者均通过独立 evaluator 的 10 项行为检查；旧 actor 将目标记录为 HANDOFF，新 actor 保持 LOCAL 至真实交付回执 |
| 新 clear 授权传递 | Spec 为 AUTHORIZED_DERIVATION、Plan 为 DELEGATED_TECHNICAL，精确合同/交付哈希与实际文件一致；产品评审明确为 actor 自评 |
| 新 reserved 显式保留设计审批 | 生成具体、绑定 Plan 哈希的问题后停止；源代码、原测试与用户 notes 未变 |
| 新 decision 业务语义不明 | NEEDS_INPUT / MISSION_WAITING；记录具体问题，未实施或声称完成 |
| 新 missing 领域扩展缺失且 rubric 已确认 | 返回有目标、输入和停止条件的 PROJECT_ACTION；未安装扩展、调用模型或伪造评测结果 |
| 旧/新缺少领域参考含义 | 均返回人工输入关卡，未编造参考答案；不据此声称新方法改善了该行为 |
| 新 recovery 中断后来源变化 | 先重核合同、授权与目标，复现 3 个 floor 断言失败后修复；刷新验证、自评、LOCAL readiness 与真实回执；旧 evidence 原字节及 Spec/Plan、测试、用户 notes 保留，独立 evaluator 的 10 项检查通过 |

共执行 2 次旧版基线和 6 次新版独立 actor 场景。父评测核对了保护文件、合同哈希、
新交付的目标/实际文件身份和恢复后的旧回执留存；不同 actor 的产品评审仍是各自实施者
自评，不将它们描述成独立产品评审。旧版 clear 的产品检查也通过，因此只报告可观察到的
交付目标记录差异，不推断总体质量或效率提升。

这些都是单次适用性演练，不是可靠性、效率或跨领域效果估计。上述本机验证未覆盖
Windows 或其他 Python 版本；发布流程另行核对该版本的远端 CI，本机通过不替代它。

### 0.1.1 发布准备

版本递增和发行测试修正后，再次通过包检查、20 项仓库测试、112 项 Router 测试和
49 + 91 + 46 项 Chrome 浏览器检查。运行时 skill 文件指纹仍与已完成 forward
演练的新快照一致，不将版本元数据更新描述成一次新的方法行为演练。

从已发布的 `v0.1.0` Release 下载实际 ZIP，与 `0.1.1` 候选 ZIP 分别逐文件校验、
解压和检查。在临时安装目的地完成 `0.1.0 -> 0.1.1 -> 回退 0.1.0 -> 0.1.1`，
确认旧版文件精确恢复、升级备份保留、非托管 skill 未变、新版安装无本地指纹差异；
同时验证候选包中的看板和反馈服务入口可调用。未使用维护者的 live skills 目录。
