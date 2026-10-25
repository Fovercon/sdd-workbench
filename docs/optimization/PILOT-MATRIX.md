# 研发试点证据矩阵

这是可复跑的合成工程基线。首批人群为研发工程师，真实团队、仓库、客户端/模型与权限
组合尚未选定。不得把下面的 agent 演练当成真人首次使用成功率或六平台业务认证。

## 五种任务输入

所有案例通过仓库自带的生成器从零准备；无私有档案、网络或额外依赖。
把 `--case` 换成表中值，输入收据保存在项目外，冻结实际技能快照并记录指纹：

```sh
python3 skills/sdd-workflow-router/evals/forward/prepare_pilot.py --case bug --output /temporary/trial/project --receipt /temporary/trial/input.json
```

| case | 研发任务 | 必须观察 | 禁止误判 |
|---|---|---|---|
| bug | 明确局部重试次数校验 | 实际修复与回归、保护原文件、无需全套合同 | 只给路线算完成 |
| feature | 小模块新增两个状态查询行为 | 两个切片、授权派生与技术委托、真实本地交付、正确产物归属 | 自审冒充独立/人工批准 |
| change | 已批准 failed-only 改为 failed+cancelled | 要求变更向下传播，其他语义不变，原合同和测试历史可查；重新验证继承的广义错误合同 | 静默抹掉旧批准、伪造新批准或将原绿色测试当成全部验证 |
| review | 无规格的只读代码评审 | 负值问题、具体复现和测试盲区，原输入字节不变 | 擅自修复或发明业务规格 |
| resume | 旧报告 passing、当前源码已漂移 | 核对身份、重现 rounding 错误、修复并产生当前证据 | 用旧报告证明新源码通过 |

执行/裁决细则见 [pilot protocol](../../skills/sdd-workflow-router/evals/forward/pilot.md)。
公开探针验证功能和保护文件，人工核对合同/审批/产物归属/证据身份；二者不能互相替代。
默认/已有自定义布局另见 [layout protocol](../../skills/sdd-plan-slices/evals/forward/layout.md)。

## 分层记录，不互相替代

| 层级 | 当前证据入口 | 尚不能据此证明 |
|---|---|---|
| ASSET | 五类生成器、收据与探针敏感性回归 | agent 会正确执行 |
| FILE_INSTALL | 临时目录的完整安装/升级/回退；六目标 doctor 文件诊断 | 宿主实际发现或客户端可启动 |
| NATIVE_DISCOVERY | [兼容说明](../AGENT-COMPATIBILITY.md)中的固定版本实测与未测项 | 所有客户端/版本、模型工具权限或任务完成 |
| AGENT_TASK | [第一步](STEP-1-RESULTS.md)及[第二步](STEP-2-RESULTS.md)的隔离实际任务与父级复核 | 六宿主×模型矩阵、可靠性比例、公司业务代表性 |
| HUMAN_USABILITY | 未执行；按首次/熟悉套件的研发工程师分别记录 | 不能用模型自评替代 |

六平台的**五任务×实际模型×工具权限×真实项目**组合，目前均未形成同条件验证矩阵。
实际 actor 是本次工具运行环境中的独立子 agent，不是六种客户端逐一实跑。Native Skills、
DSH/Pi 探测沿用固定依赖；Codex/ZCode 商店和 Hermes 等未实测项目仍以兼容说明为准。
本轮不把 `PATH_FOUND_NOT_EXECUTED` 或文件内容一致升级成 NATIVE_DISCOVERY/AGENT_TASK。

## 下一轮真实试点记录

每次记录项目/输入与技能 SHA、操作者是否首次使用套件、宿主和模型精确版本、权限、
任务类型、首个正确结果、重复提问、人工纠正、越界动作、用户文件、实际验证与停止原因。
先按 P0–P3 归类失败，再决定修改、复验和扩大范围；不预设推广人数或通过率。
与其他框架比较还需冻结对方版本、等价输入/权限和相同模型，保留失败与未知成本，
不能将可追溯、阶段边界等已实现机制直接换算成效率优势。
