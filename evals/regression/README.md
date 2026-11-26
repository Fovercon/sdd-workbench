# 三层评测与验收回归(Suite Regression Harness)

维护者工具,位于源码仓库内、**不属于安装包/插件输入**(打包为白名单制,本目录在白名单之外;
`test_protocol.py` 会在 CI 中持续断言这一点)。本框架不安装客户端、不修改任何线上 skill、
不建立操作系统级沙箱。运行产物默认写入仓库之外的 `~/.sdd-regression/`(用户主目录下,仓库之外)
(防止执行者经目录穿越读到套件源码、语料与隐藏测试;可用环境变量
`SDD_REGRESSION_ARTIFACTS` 重定向)。执行者对父目录仍具备指令级可见性,这一残留风险
随报告声明;如需强隔离请自行套容器。

## 快速开始

```sh
python3 evals/regression/run.py --probe              # 单槽位冒烟:验证 Pi 事件解析
python3 evals/regression/run.py --profile smoke      # 1 任务 × 2 条件 × 1 trial
python3 evals/regression/run.py --profile quick      # L1 前 30 例 + 2 任务 × 2 × 2
python3 evals/regression/run.py --profile standard   # 全量:L1 76 例 + 9 任务 × 5 条件 × 3 trial
python3 evals/regression/run.py --profile standard --suite-ref worktree  # 冻结未提交的工作区 skills
python3 evals/regression/run.py --profile standard --ablate sdd-plan-slices   # 追加消融条件
python3 evals/regression/run.py --accept <run_id>    # 显式将某次运行定为验收基线
python3 -B -m unittest discover -s evals/regression -p "test_*.py"            # 离线自检(无模型)
```

模型按 AGENTS.md 固定为显式 `deepseek/deepseek-flash`;每次运行的 manifest 记录
`pi --version`、`pi --list-models deepseek` 原始输出、套件 git ref 与运行时快照哈希,
`backend_revision` 未上报时如实记 `NOT_REPORTED`。历史运行保留其当时记录的模型身份。

## 三层结构

- **L1 触发/路由**(`corpus/l1/`,76 用例,11 个合成项目状态):prompt 一律不点名 skill,
  触发只取决于描述与项目状态。skill "触发" 的判定依据是执行者读取了运行时目录中该 skill
  目录下的文件(启发式;原始 events.jsonl 全量留档可人工复核)。产出:per-skill
  precision/recall、相邻混淆对、负例误触发、结果枚举纪律。
- **L2 端到端**(`corpus/tasks/`,两类任务):**code 类**(6 个 Python 标准库任务,领域
  中立)含 PRD/约束(执行者可见)、起始仓库、隐藏 unittest(评测者专用)、oracle(必须
  100% 通过隐藏测试、起始树必不过——由自检持续验证);**process 类**(3 个:歧义草稿→
  澄清、测试全绿但验收未决的收敛陷阱、规格变更→影响分析先行)按 task.json `process`
  的 criteria 裁决:答复 must/must-not 正则(语义宽度,枚举纪律归 L1 管)、产物正则
  (路径支持精确与 glob)、提问数、可选隐藏测试,按
  `weights` 归一加权为 0–1 分(过程贡献可直接计分,裸模型难以饱和)。条件:
  baseline(无 skill)/ full(12,organic)/ core5(5 核心阶段)/ no-router /
  **directed**(同 full 的 skill 集,prompt 强制先读 router SKILL.md 并走 SDD 流程;
  强制措辞是标定结果:软引导实测与 organic 等价)。organic 回答"套件会不会被自然
  采用"(实测 deepseek-flash 下为 0),directed 回答"被实际使用时带来什么与多大开销";
  另报告 skill 目录常驻 input 开销(full−baseline 每请求 input 差)。判定:隐藏测试
  partial credit(code)/ criteria 加权分(process)、pass^k / pass@k、normalized gain、
  按条件 token/时长、skill 调用率。
- **L3 过程质量**(离线,吃 L2 产物,零模型调用):规格 FR/AC 追溯覆盖率、歧义词扫描、
  产物与结果枚举存在性、执行者自建测试(可见)与隐藏测试的差距(reward-hacking 代理)、
  "全部通过"声明与实测不符的编造计数。`--judge` 可选:单裁判 LLM 按
  完整/无歧义/一致/正确 四维给 spec/plan 打分,单裁判偏差随结果记录。

## 验收回归

`config/gates.json` 定义阈值(L1 router recall≥0.8、负例精确率≥0.9、枚举纪律≥0.9;
L2 full 对 baseline 无宏观回归、增益过半、最差任务 Δ≥−0.25、token 开销≤3×;
directed 调用率=1、无宏观伤害、token≤8×;L3 编造=0、追溯≥0.8、可见/隐藏差距≤0.5)。
每次运行自动与当前 accepted 运行对比,报告门回退/恢复与各条件 Δ。验收基线的设定是
显式人工动作(`--accept`),报告不代替该决定。单次运行是试点而非可靠性估计;所有比率
均附原始计数,负向结果照报。

## 成本与断点

标准档 = 76(L1)+ 135(L2:9 任务 × 5 条件 × 3 trial,含 directed)次 Pi 运行,并行 3
约 1.5–3 小时(directed 档单次较重,约 4–8 分钟);smoke 约 15 分钟。槽位清单
`slots.json` 支持中断续跑(`--retry-errors` 可重排错误槽位);已产生 `result.json` 的
槽位不会重复计费。超时默认:L1 600s、L2 按任务 1800s。跑批前建议先 `--probe` 确认本机
Pi 的事件 schema 可被 `runner/events.py` 解析(解析器对未知形态降级为计数,不静默丢弃)。

## 解读边界

- 触发判定依赖"读文件"启发式与事件流完整性;skill 未被读取不代表模型未受益于其元数据。
- L2 任务为小型标准库任务,饱和后区分度下降,需持续补充任务(新增任务包只需照
  `corpus/tasks/<id>/` 结构放置,自检会强制 oracle 100%/起始 0% 两条底线)。
- 单 provider、单裁判的偏差随结果声明;结论以多 trial、跨条件的原始计数为准。

## L1 校准与原始日志重判

L1 的 `fired` 是**成功读取的暴露证据**,不是阶段执行或产品正确性的证明。
原生 read 需要成功结果;bash 仅识别成功调用中最后一个可判定的字面 cat/head/tail/sed,
支持开头的字面 cd。目录清单、路径打印、搜索模式、heredoc、失败读取与未知生命周期
事件不作为确认读取。更早的复合命令读取、管道输入和动态 shell 保留为未分类证据,
需要查原始日志,不能把检测器未识别直接解释为模型漏触发。

`may_also` 允许的邻居不扣读取集合命中或精确率,严格集合一致率单独报告。
VIEW/人工反馈记录不适用诊断枚举;已授权评审后修复允许阶段接续。
一行 README 改名无需先调用 Router。真实文案修改和找不到对象分开使用夹具。
14-holdouts 中的独立近义与负例不用于反复调 description。

```sh
python3 -B evals/regression/rejudge.py ~/.sdd-regression/runs/原运行ID
```

重判只读取原运行的 `slots.json` 中冻结的用例及原始事件,写到全新的归档目录;
保留来源文件/评分代码哈希,不覆盖旧结果、不调用模型、不更改索引或 accepted 基线。
这是**原用例口径下的检测器/判分修正**:旧 VIEW 用例若未声明枚举豁免,仍保留旧要求;
不偷偷引入今天的夹具或新预期。新语料的模型运行另行记录,其分数不能与旧 72 例
直接相减并宣称行为提升。旧事件缺少结果证据时无法确认读取,需人工复核。

## 2026-11-26 评测器修正

- 可见测试在可丢弃的项目副本中按原相对路径执行,只选择新建/变更的测试文件;
  同名文件不再扁平覆盖,夹具、`__file__` 相对 CLI 路径及显式 Python 包的相对导入保留。
  内部软链接重映射到副本;外部/循环链接抛出 `EVALUATOR_ERROR`,不静默计为产品测试失败。
  该副本不是任意 Python 的操作系统沙箱,不能保证隔离故意硬编码的外部绝对写入。
- text-diff 的未来公开合同明确区分: `render` 不含末尾换行,CLI 对非空结果追加
  一个换行、空结果不输出字符。oracle/隐藏测试同步此区分,CLI 既有非空输出期望保留。
- change-request 的未来入口明确: `delay_before` 是接受任意正整数的纯退避值查询,
  第6/9次均返回30;实际重试预算仍为5次。原隐藏期望不变,oracle 对极大查询先封顶
  以免指数溢出。原历史任务没有收到这条公开边界,不能用新提示回判旧实现违规。
- 用量按 assistant `message_end` 单计,同轮 `turn_end` 镜像不再累加。没有该轮
  `message_end` 用量时保留 `turn_end` 旧格式回退;仅有单个 `result` 用量且全流无
  其他用量时才回退。非 assistant、流式增量不计费,不同真实请求即使数值相同也照计。
  总 token 包含输入、缓存读写和输出。未知/缺失用量以 `complete=false` 和未分类数
  标明,成本汇总与比率为 `null`,不把它当免费或通过成本门槛。

这些是评测器/未来语料合同修正,没有调用新模型或覆写旧报告、索引、accepted。
旧标准运行的正式门值原样保留。新旧同一日志的用量差属于统计修正,不是模型降本。
