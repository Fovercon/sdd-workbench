# SDD Workbench

面向 AI 编程代理的规格驱动工程工作台。一次安装 12 个 skills，覆盖需求、设计、逐片实现、验证与交付；内置中文设计图看板与本机反馈入口。

安装整套后，代理仍按当前工作选择主要 skill，无需一次加载全部流程。

## 安装

### Codex 插件

支持插件的 Codex 客户端可以添加本仓库作为插件源，安装 **SDD Workbench**。
支持下列命令的 CLI 可执行：

```sh
codex plugin marketplace add Fovercon/sdd-workbench --ref v0.1.0
codex plugin add sdd-workbench@sdd-workbench
```

插件包含全部 12 个 skills 及其脚本和资源。不同客户端的插件入口可能不同；
可在插件目录中选择 SDD Workbench 源后安装。安装后新开一轮对话使用。
格式依据 [OpenAI 插件打包说明](https://developers.openai.com/plugins/build/plugins)。

### Python 整套安装

需要 Python 3.10+ 和 Git；安装器本身无第三方依赖。可在 macOS、Linux 和
Windows 的终端使用。下面以首个版本为例：

```sh
git clone --branch v0.1.0 --depth 1 https://github.com/Fovercon/sdd-workbench.git
cd sdd-workbench
python3 tools/install.py install
```

最后一条命令安装整套 skills，默认位置为 `$CODEX_HOME/skills`，未设置时使用
`~/.codex/skills`。Windows 如使用 `python` 命令，可将上面的 `python3` 替换为 `python`。
也可以下载 [Release ZIP](https://github.com/Fovercon/sdd-workbench/releases)，解压后执行同一安装命令。

已有同名且内容不同的 skills 时，安装器会停止；希望迁移旧安装时，显式执行：

```sh
python3 tools/install.py install --adopt
```

旧内容会先备份；无关 skills 不受影响。安装状态和备份默认放在安装目录旁的
`.sdd-workbench/` 中，请保留此目录。自定义安装位置使用 `--dest /path/to/skills`，
后续操作也要使用同一位置。插件安装与 Python 安装二选一，避免重复发现同名能力。

## 开始使用

在项目对话中直接说明工作目标，例如：

- “用 SDD Workbench 看看这个项目目前在哪个阶段，下一步做什么。”
- “把这个需求整理成可评审的规格，再做技术设计和任务拆分。”
- “按当前执行卡完成这一片功能，验证后报告结果。”
- “生成项目看板，显示设计图，并允许在本机提交反馈。”

也可显式调用 `sdd-workflow-router` 或具体阶段 skill；插件客户端可能为名称
加上套件前缀。项目规则、当前合同与用户授权始终有效。

## 套件内容

| Skill | 作用 |
|---|---|
| `sdd-project-bootstrap` | 建立或检查项目规则、真源与开发基线 |
| `sdd-workflow-router` | 判断当前阶段、推进已授权任务、生成看板 |
| `sdd-requirements-contract` | 整理需求、澄清意图与验收条件 |
| `sdd-plan-slices` | 技术设计、设计图、任务切片与执行卡 |
| `sdd-implement-slice` | 实现并验证一个已批准的功能切片 |
| `sdd-converge-review` | 对照规格、设计和实现判断是否收敛 |
| `sdd-finish-readiness` | 检查具体交付、集成或发布动作是否就绪 |
| `sdd-verification-design` | 设计与风险对应的验证证据 |
| `sdd-change-impact` | 识别变更归属和下游影响 |
| `sdd-code-review` | 对无规格基线的代码进行工程评审 |
| `sdd-context-handoff` | 跨会话、代理或工具交接上下文 |
| `sdd-retrospective` | 从实际工作中提炼方法改进 |

详细边界见 [能力目录](skills/CATALOG.md)，方法维护规则见
[套件政策](skills/SUITE-POLICY.md)。

## 更新、回退与恢复

插件用户可切换插件源到目标版本后重新安装整套插件。Python 用户可在 Git
检出新版本后再次执行 `install`，或从目标版本 ZIP 中运行安装器：

```sh
git fetch --tags origin
git checkout v0.1.0
python3 tools/install.py install
python3 tools/install.py status
```

上面的版本号是示例，升级时替换为实际发布的目标标签。每个版本作为一个整体安装，
版本和每个 skill 的文件指纹一并记录。本地修改会阻止覆盖；确需覆盖时可加
`--force`，安装器仍会先保存当前内容。回退最近一次安装/更新：

```sh
python3 tools/install.py rollback
```

安装中断时，安装器保留恢复记录并阻止下一次写入。先保留新产生的本地修改，
然后执行：

```sh
python3 tools/install.py recover
```

恢复会保留已完整提交的安装，或恢复到操作前的内容。多目录替换期间不要启动新的
代理会话；安装完成后再开始使用该版本。

## 项目看板

看板由项目真实材料生成，不自带某个业务项目的数据。Mermaid 引擎已随包携带，
支持流程图、时序图、状态图、类图和实体关系图的离线图形渲染。

静态 HTML 支持阅读和复制反馈；直接保存反馈需要启动随包的本机服务。
详见 [看板生成说明](skills/sdd-workflow-router/references/project-view.md) 和
[本机反馈说明](skills/sdd-workflow-router/references/human-decisions.md)。
反馈提交更新的是反馈回执状态，具体调整仍需代理或维护者后续处理。

## 开发与发布

```sh
python3 tools/package.py check
python3 -B -m unittest discover -s tests
python3 -B -m unittest discover -s skills/sdd-workflow-router/tests
python3 tools/package.py build
```

发行包默认写入 `dist/`，包含完整插件、Python 安装器、逐文件指纹和
`SHA256SUMS`。版本发布流程见 [RELEASING.md](docs/RELEASING.md)，变更见
[CHANGELOG.md](CHANGELOG.md)，第三方组件见 [版权声明](THIRD_PARTY_NOTICES.md)。
