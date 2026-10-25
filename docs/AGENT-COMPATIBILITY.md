# 多平台安装兼容

自 v0.2.0 起维护一份 `skills/`，包含 12 个 skills 及所有相对引用、模板、脚本和离线 Mermaid。
v0.2.0 的适配只改变发现、安装和包元数据。v0.2.1 另澄清 Code Review 的授权交接并补充独立评测输入，阶段职责保持不变。
v0.3.0 增加任务入口分流、产物约定与异常合同审查修正，以及诊断/安装预览/审查反馈工具；
安装布局和 12 个技能名称保持兼容。新增工具见[维护指南](OPERATIONS.md)，当前验证范围见
[0.3.0 发布准备记录](releases/0.3.0.md)。
这里的多平台支持不提供跨客户端会话同步或调度：每个 agent 仍使用自己的工具、权限和模型。

## 共享安装

```sh
npx skills@1.7.4 add https://github.com/Fovercon/sdd-workbench/tree/v0.3.0 -g -a codex hermes-agent zcode opencode pi -y
```

Vercel CLI 将 `~/.agents/skills` 作为公共存储。Codex、OpenCode、Pi 使用公共入口，
Hermes 和 ZCode 的原生目录链接到公共存储。DeepSeek Harness 0.2.1-rc.2 的
默认文件系统 provider 同时扫描 `~/.agents/skills`；不需要额外复制。
自定义 DSH profile 若移除了 `skill-filesystem` 或关闭默认 roots，应保留该 provider、
配置 `customSkillDirs`，或使用原生 bundle。

Vercel CLI 的更新/删除行为由上游工具管理，不具备本仓库 Python 安装器的编辑保护和事务备份。
有旧副本或个人修改时，先保存这些内容，选择一种安装方式；避免在多个搜索根保留同名的不同版本。
Windows 无链接权限时上游会回退为复制，因此不承诺所有系统上只有一份物理文件。

## Python 目标映射

`python3 tools/install.py install --agent all` 复制到六个平台原生目录，
使用原有保护、指纹、备份、回退和恢复机制。`all` 不额外安装 shared。

| `--agent` | 默认目录 | 环境变量覆盖 | 别名 |
|---|---|---|---|
| `codex` | `~/.codex/skills` | `$CODEX_HOME/skills` | — |
| `hermes` | `~/.hermes/skills` | `$HERMES_HOME/skills` | `hermes-agent` |
| `zcode` | `~/.zcode/skills` | — | — |
| `deepseek` | `~/.dsh/skills` | `$DSH_HOME/skills` | `deepseek-harness`, `dsh` |
| `opencode` | `~/.config/opencode/skills` | `$XDG_CONFIG_HOME/opencode/skills` | `open-code` |
| `pi` | `~/.pi/agent/skills` | `$PI_CODING_AGENT_DIR/skills` | `pi-agent` |
| `shared` | `~/.agents/skills` | — | — |

不带参数的 Codex 默认路径保持 0.1.x 行为。显式 `--home BASE` 会忽略环境覆盖，
所有目标都相对于 BASE 解析。每个目录有独立回执；多目标调用不是一个全局原子事务。
已知冲突和未恢复事务在首次写入前拦截，运行时故障输出已完成目标和失败目标。
先对失败目标 `recover`，再重跑原命令。原有用户编辑和未知恢复内容仍会阻止覆盖。

只安装 shared 时，Hermes 可通过 `skills.external_dirs` 指向该目录；ZCode 支持导入链接。
需要自动创建两者入口时使用共享安装命令。

## 原生包

- Codex：`.codex-plugin/plugin.json` 和 `.agents/plugins/marketplace.json`。
- ZCode：`.zcode-plugin/plugin.json`，根与 `.zcode-plugin/` 下的 marketplace 投影。
- Pi：`package.json` 的 `pi.skills` 直接指向 `./skills`。
- DeepSeek：`dsh.bundle.patch` 注册 `sdd-workbench` provider，延迟读取同一目录，
  将完整目录作为 `resourceBase`，无需构建或运行时第三方依赖。

`plugin.json` 是版本真源；`tools/package.py bump VERSION` 同步这些投影及 Node lock。
包检查拒绝版本漂移、指向独立副本的入口、危险目标路径和重复别名。
DeepSeek 原生 provider 针对 0.2.1-rc.2 的公开 skills API，声明支持范围为
`>=0.2.1-rc.2 <0.3.0`；后续版本需重新验证。Pi 原生入口验证版本为 0.86.1。

## v0.2.0 安装证据（2026-10-25）

| 平台/入口 | 实际验证 | 边界 |
|---|---|---|
| 通用 Skills CLI 1.7.4 | 隔离 home 执行五 agent 命令；12 个目录和所有资源字节一致；Hermes/ZCode 链接解析为公共目录 | 未写开发者安装目录 |
| Codex | 通用安装布局、原生清单与市场投影检查 | 本次未运行完整 Codex 客户端安装；0.1.0 的 CLI 解析结果见 VALIDATION |
| Hermes | 官方源码扫描器发现 12 个链接 skills | 扫描器提交 `51edc3cf2412c700880ab33e97e1639685fe8459`；未跑模型会话 |
| Z.ai ZCode | 通用 CLI 的 ZCode 安装入口、链接、官方清单/市场布局检查 | 未运行 ZCode 桌面插件商店 |
| DeepSeek Harness 0.2.1-rc.2 | 原生 `dsh plugin` 安装、`--dump-config` 合并；真实 Cordis/SkillRegistry 加载 12 个 bundle skills；真实文件系统 provider 发现共享目录并加载正文 | 不调用模型 API；上游源码参考提交 `22ddee3792402c3e70ec5f86a63c3e3e895a2f60` |
| OpenCode 1.19.4 | 隔离 XDG 目录运行 `opencode debug skill`，12 个 skills 来自安装目录并带正文 | 未跑模型会话 |
| Pi 0.86.1 | 原生 package 安装、真实资源加载器加载 12 个 skills；隔离 home 自动发现公共目录，零 diagnostics | 未跑模型会话 |
| Python 安装器 | 六目标安装、升级、备份回退、编辑/冲突保护、未完成事务拦截、部分失败报告、旧 CLI 兼容 | 平台矩阵以实际 CI 结果为准 |

这建立的是安装和发现兼容性，不是各平台模型执行 SDD 工作流的可靠性结论。
v0.2.0 的 `skills/` 相对 v0.1.1 没有修改；v0.2.1 的内容修正与实际 forward 演练另见 [VALIDATION.md](VALIDATION.md)。后续方法语义变化仍需 forward 评测。
脚本执行仍需本机 Python、浏览器或项目工具等相应能力，安装本身不会为客户端补充工具权限。

## 可复跑原生发现回归

在临时 npm 前缀安装测试依赖，不安装到开发者环境：

```sh
npm install --prefix /temporary/sdd-native --ignore-scripts skills@1.7.4 @deepseek-ai/cordis@4.0.5 @deepseek-ai/dsh-skill@0.2.1-rc.2 @deepseek-ai/dsh-skill-filesystem@0.2.1-rc.2 @earendil-works/pi-coding-agent@0.86.1
node tests/native_agents.mjs /temporary/sdd-native /temporary/sdd-native/node_modules/@earendil-works/pi-coding-agent
```

CI 固定这些版本，自动覆盖共享安装、所有资源保留、DSH 两种 provider 和 Pi 两种入口。
Hermes 源码扫描、OpenCode CLI、DeepSeek 配置合并是本次补充验证，未宣称纳入全部 CI。

## 官方接口依据

- [Codex skills](https://developers.openai.com/codex/skills/)、[Codex plugins](https://developers.openai.com/plugins/build/plugins)
- [Hermes skills 和 external_dirs](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)
- [ZCode skills](https://www.zcode.network/en/docs/skill/)、[ZCode plugins](https://www.zcode.network/en/docs/plugin/)
- [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)、[文件系统 provider](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/packages/skill/skill-filesystem/README.md)
- [OpenCode skills](https://opencode.ai/docs/skills/)
- [Pi skills](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md)、[Pi packages](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md)
- [Vercel Skills CLI](https://github.com/vercel-labs/skills)
