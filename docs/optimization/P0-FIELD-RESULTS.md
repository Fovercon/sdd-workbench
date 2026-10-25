# P0：真实仓库与实际宿主验证

状态：执行中，2026-10-26。已完成两个公开真实源码任务 × Codex/Pi 的实际客户端执行与父级复核；用户随后指定 ConfigurationGovernanceService，并要求两宿主从零实现相关业务、保留交互与 token 证据。公司业务原型的范围/委托确认及执行结果另行追加，不能用前四个样本代替。

## 输入与执行证据

源码评测入口为 source checkout 下 `evals/real-tasks/`，不进入插件发布包：

- `prepare.py` 从固定 Git 提交生成外部隔离项目、普通任务说明、用户文件保护标记与逐文件 SHA 收据；runtime 单独冻结为 v0.3.0 提交 `7c79aad193269b1daae4dfe08f102cb815955d78`，排除 runtime evals/tests。
- `probe.py` 核对原文件、Git 身份、技能快照和具体行为；明确要求额外的语义裁决。
- `usage.py` 汇总 native 完成事件，生成可读交互记录；不累计 streaming delta，不把 reasoning 再加进 output，不将本地估价当账单。
- `README.md` 包含准备、隔离、执行、复核和失败保留协议；`test_protocol.py` 验证输入一致、探针敏感性、只读保护与 usage 口径。

同一任务的两个宿主得到相同输入与 runtime 文件 SHA。编码任务用真实故障提交 `2093cc9ca463862a57577a235152196ea5d9cb03`；审查任务用真实已发布 JS provider 及原 Node 测试。未向 actor 提供预期补丁、已发布修复或父级探针。

原始 JSONL、stderr、exact argv、退出状态、actor 源码/回归/trace、父级探针、重跑日志和 usage 单独保留在本地试点目录。工作仓库 `.eval-artifacts/p0-field/` 保存准备与环境记录；不将这些真实运行状态混入 package inputs。

| 宿主 | 实际版本与模型 | 隔离和限制 |
|---|---|---|
| Codex CLI | 桌面应用自带 `0.164.0-alpha.11.1`；沿用已配置的请求模型 `gpt-6.1-sol` / high；JSONL 未报告后端具体模型修订 | ephemeral、ignore-user-config，命令行禁用已发现的 home skills，只用本地 frozen runtime；workspace-write、network=false；显式读取项目 AGENTS；无 live skill 写入 |
| Pi | `0.86.1`；完成消息实际报告 provider `deepseek` / model `deepseek-v4-pro`；后端修订未报告 | no-session、关闭隐式 extensions/skills/templates/themes/context，以 `--skill` 加载 frozen runtime；read/bash/edit/write；指令范围限制，不是 OS 沙箱 |

PATH 中原 Codex 0.125.0 缺原生可执行文件而 ENOENT；临时 npm prefix 的同版本 version/help 最终均为 -9、无输出，原因未确认。保留失败，没有修改全局安装；后续用实际发现且可启动的桌面 bundled CLI。不能由本次结果外推任意 Codex 版本。

## 独立裁决

| 任务/宿主 | 实际交付 | 父级复核与结论 |
|---|---|---|
| 编码 / Codex | 实际先复现后修复，补 7 项回归；读取指定 Router 正文，明确使用已授权局部修复通路 | installer/doctor/review 的 cp1252 JSON Unicode 往返及文档默认解码检查通过；原文件/用户文件/runtime 保护通过。额外观察：human stdout 使用反斜杠转义，未达到已发布版中文可读输出。不得宣称全部五项探针通过 |
| 编码 / Pi | 修复为统一 UTF-8 stdio，补 2 项回归；自身回归通过；未观察到读取适用 skill 正文 | 独立消费端按 cp1252 解码时，三种 JSON 仍不能还原中文，失败保留。人类 UTF-8 输出、文档解码和文件保护通过；主任务不能算通过 |
| JS 审查 / Codex | 读取指定 code-review 正文及 reference；只新增 trace 与探针；12 项额外 Node 探针，无强行发现产品缺陷 | 原 4 项、额外 12 项父级复跑通过，原输入字节不变；区分 allowlist 与本地 symlink 替换、测试缺口与缺陷、适配器与未执行的真实 DSH 生命周期。该范围审查完成 |
| JS 审查 / Pi | 原 4 项及多组独立探针，原文件不变；实际发现 12 个 skill 描述，但未观察到读取审查 skill 正文 | 探针可复跑；报告将路径 allowlist 概括为“路径穿越不可能”，未限定本地树替换；null candidate 等未有上游合同支撑，不升级为产品缺陷。需重检方法采用与结论边界，不能由绿色测试直接判通过 |

父级在完整许可环境中补跑：Codex 编码候选 root 102、Router 112 及浏览器 49+91+46；Pi 编码候选 root 97、Router 112；两个审查候选的原 Node 回归及新增探针均通过。它们不覆盖三项失败的 cp1252 数据往返，也不抹掉 actor 原始失败。

评测自身也有修正：初版文档探针只处理 omitted encoding，漏掉 Python 的 `locale` 参数，产生假绿；保留初版后修正并用故障提交/已发布修复校准，五项均能正确 RED/GREEN。UTF-8 human 输出是发行行为对照，普通任务未规定其具体编码，因此记录为额外可读性观察，不作为四项明确义务的隐藏门槛。

初版隔离说明把 network 一概禁止，但原仓库必跑回归包含 loopback HTTP，存在输入约束冲突：Codex 被沙箱阻止后如实保留失败并显式跳过；Pi 跑完原回归，未受同类 OS 约束。不能据此比较两宿主能力。后续全栈试点明确区分 loopback 测试、外部网络与客户端模型调用，并记录实际沙箱差异。普通系统临时目录与要求 project 临时子目录的字面约束也需要明确，不能假装哈希检查能看到所有瞬时写入。

## 原生 token 记录

只统计已报告的完成事件；Codex 按 `turn.completed.usage`，Pi 按每个 assistant `message_end.message.usage`。下表输入含缓存：Pi 为 input+cacheRead+cacheWrite，Codex 原生 input_tokens 已含缓存。推理为 output 子集，未重复求和。

| 样本 | 输入（含缓存） | 其中缓存读 | 输出（含已报告推理） | 原生 usage 事件 |
|---|---:|---:|---:|---:|
| 编码 / Codex | 1,793,236 | 1,724,544 | 21,698 | 1 turn |
| 编码 / Pi | 3,451,802 | 3,395,968 | 43,104 | 57 messages |
| 审查 / Codex | 381,346 | 340,352 | 10,763 | 1 turn |
| 审查 / Pi | 876,311 | 852,736 | 35,539 | 26 messages |

这里包括多次请求重复发送的上下文，不是独立资料的 token 量。模型、tokenizer、权限、工具行为和上下文使用不同，没有无套件对照；不能据此声称套件省 token、某宿主更高效、估算真实账单或可靠性比例。中断/未报告请求的消耗仍可能缺失。

## 用户指定业务仓库

已只读克隆用户指定的 ConfigurationGovernanceService，固定 HEAD `0eda413d16e5f62ffd9a2c983c84d8a3d99524b2`，并禁用该本地参考克隆的 push URL。已核对 README、Agent/UI 规则、需求、任务用例及 API 文档：这是面向资料人员的本地配置治理工作台，包含单 MML/CPI 特性治理、规范性校验和映射翻译，技术栈为 FastAPI + React 18/TypeScript/Vite。

首轮 BRIEF 提议：两个独立空目录完成相同的三个纵向切片——CPI 范围选择、任务执行与恢复、配置快照与交付核验；从零代码，沿用真实业务规则，明确为离线模拟执行器，不搬原产品实现。已准备独立 venv 和锁定的前端依赖，未运行上游安装/部署脚本。

用户已选 Codex/Pi 并要求完整交互、使用情况、token、实现效果记录。首轮范围与显式需求派生/技术委托问题已发出；确认前不启动依赖这些决定的实现。公司原型结果未产生，P0 尚未整体关闭。

后续更新：用户已明确确认范围与委托，两客户端已启动。继续记录见
[指定业务背景的双宿主从零实现](P0-COMPANY-TRIAL.md)；上段保留发问时的历史状态。
