# SDD Workbench

面向 AI 编程代理的规格驱动工程工作台。一次安装 12 个 skills，覆盖需求、设计、逐片实现、验证与交付；内置中文设计图看板与本机反馈入口。

安装整套后，代理仍按当前工作选择主要 skill，无需一次加载全部流程。

## 安装

### 六平台代理共用一套 skills

推荐在终端执行这一行（需要 Node.js 20+ 和 Git）：

```sh
npx skills@1.7.4 add https://github.com/Fovercon/sdd-workbench/tree/v0.2.0 -g -a codex hermes-agent zcode opencode pi -y
```

此命令使用 [Vercel Skills CLI](https://github.com/vercel-labs/skills)，将全部 12 个 skills
及资源放在 `~/.agents/skills`。Codex、OpenCode、Pi 和 DeepSeek Harness
0.2.1-rc.2 的文件系统 provider 可直接发现此目录；Hermes、ZCode 通过链接使用同一份内容。
DeepSeek 尚无该 CLI 的 agent ID，因此命令没有虚构 `--agent deepseek`。
Windows 创建链接受系统权限影响时，CLI 可能回退为复制；可改用下面的 Python 安装。

只给某个平台安装，或使用平台原生插件入口：

| 平台 | 一行安装命令 |
|---|---|
| Codex | `npx skills@1.7.4 add https://github.com/Fovercon/sdd-workbench/tree/v0.2.0 -g -a codex -y` |
| Hermes | `npx skills@1.7.4 add https://github.com/Fovercon/sdd-workbench/tree/v0.2.0 -g -a hermes-agent -y` |
| Z.ai ZCode | `npx skills@1.7.4 add https://github.com/Fovercon/sdd-workbench/tree/v0.2.0 -g -a zcode -y` |
| DeepSeek Harness | `dsh plugin --profile cli add 'github:Fovercon/sdd-workbench#v0.2.0'` |
| OpenCode | `npx skills@1.7.4 add https://github.com/Fovercon/sdd-workbench/tree/v0.2.0 -g -a opencode -y` |
| Pi Agent | `pi install git:github.com/Fovercon/sdd-workbench@v0.2.0` |

原生插件仍读取仓库中的同一个 `skills/`，不维护平台专用指令副本。DeepSeek 命令中的
`cli` 是 profile 名，可换成实际使用的 profile；需要 Harness 0.2.1-rc.2。
如已通过共享目录安装，无需再装同一套原生插件。安装后重启客户端或重新加载 skills。
路径、版本和实测边界见 [平台兼容与验证](docs/AGENT-COMPATIBILITY.md)。

### 原生插件源

支持插件命令的 Codex 客户端也可执行：

```sh
codex plugin marketplace add Fovercon/sdd-workbench --ref v0.2.0 && codex plugin add sdd-workbench@sdd-workbench
```

ZCode 可在 Settings → Plugins → Create marketplace 中填写
`https://github.com/Fovercon/sdd-workbench`，然后安装 SDD Workbench。
仓库提供 `.codex-plugin/`、`.agents/plugins/`、`.zcode-plugin/`、根 marketplace、Pi package
和 DeepSeek bundle 元数据。ZCode 官方入口为界面操作，终端一行安装使用上面的 Skills CLI。

### Python 整套安装

需要 Python 3.10+ 和 Git；安装器无第三方依赖，支持 macOS、Linux、Windows：

```sh
git clone --branch v0.2.0 --depth 1 https://github.com/Fovercon/sdd-workbench.git
cd sdd-workbench
python3 tools/install.py install --agent all
```

`all` 为六个平台各安装一份受回执管理的完整副本；若希望只有一个公共目录，使用
`--agent shared`，并按兼容说明配置 Hermes、ZCode 的入口。也可以下载
[Release ZIP](https://github.com/Fovercon/sdd-workbench/releases/tag/v0.2.0)，解压后运行安装器。
Windows 可将 `python3` 替换为 `python`。

可指定 `--agent codex hermes zcode deepseek opencode pi` 中的一个或多个。
不传 `--agent` 保留旧行为：安装到 `$CODEX_HOME/skills` 或 `~/.codex/skills`。
`--dest /path/to/skills` 和 `--state /path/to/state` 只接受单目标。
`--home /temporary/base` 可指定隔离基目录，并忽略平台环境变量，适合测试。

安装器会保护无关 skills 和用户编辑。旧的同名内容不同时停止；显式使用 `--adopt`
可先备份再迁移。回执和备份位于各目标旁的 `.sdd-workbench/`，请保留。
同一目录选择一种安装管理方式；Vercel CLI 与原生插件不使用 Python 的回执和备份。

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
git checkout v0.2.0
python3 tools/install.py install --agent all
python3 tools/install.py status --agent all
```

上面的版本号是示例，升级时替换为实际发布的目标标签。每个版本作为一个整体安装，
版本和每个 skill 的文件指纹一并记录。本地修改会阻止覆盖；确需覆盖时可加
`--force`，安装器仍会先保存当前内容。回退最近一次安装/更新：

```sh
python3 tools/install.py rollback --agent all
```

安装中断时，安装器保留恢复记录并阻止下一次写入。先保留新产生的本地修改，
然后执行：

```sh
python3 tools/install.py recover --agent all
```

后续命令应选择与安装时相同的 `--agent`、`--dest` 或 `--home`。每个目标独立提交事务；
多目标操作先检查已知冲突，但运行时故障可能只完成前几个目标。失败输出会列出
`completed` 和 `failed_agent`，先恢复失败目标，再重跑安装；已完成且无变化的目标不会重复替换。
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
npm run test:adapters
python3 tools/package.py build
```

发行包默认写入 `dist/`，包含完整插件、Python 安装器、逐文件指纹和
`SHA256SUMS`。版本发布流程见 [RELEASING.md](docs/RELEASING.md)，变更见
[CHANGELOG.md](CHANGELOG.md)，第三方组件见 [版权声明](THIRD_PARTY_NOTICES.md)。
