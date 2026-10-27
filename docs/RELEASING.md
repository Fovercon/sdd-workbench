# 版本发布

`plugin.json` 是套件版本的唯一维护入口，使用语义化版本。12 个 skills 作为
一个兼容集合发布，不在同一发行包里混用不同套件版本。

## 版本选择

- Patch：修正文案、脚本缺陷或保持既有合同的实现问题。
- Minor：增加兼容能力、交互或方法支持。
- Major：改变已有工作流合同、安装布局或其他不兼容行为。

0.x 阶段仍应说明兼容性影响，不把试验版本描述为经过全面模型行为验证。

## 发布步骤

1. 在 `codex/*` 开发分支完成所需改动，选择本次发布范围。方法语义变化按相应 skill 的 forward 协议验证；结构与单测
   不替代真实模型行为演练。包装变化验证包身份、安装、升级、回退与恢复即可。
2. 执行 `python3 tools/package.py bump X.Y.Z`，同步通用清单、Codex/ZCode 清单与市场版本、Node package 和 lock 投影。
   更新 `CHANGELOG.md` 中对应版本的日期、行为变化、兼容性和已知限制。
3. 运行 README 中的检查，再运行相关浏览器检查：

   ```sh
   npm ci
   npm run test:adapters
   npx playwright install --with-deps chromium
   SDD_BROWSER_CHANNEL=chromium npm run test:browser
   SDD_BROWSER_CHANNEL=chromium npm run test:forward-browser
   ```

   本机也可用 `SDD_BROWSER_CHANNEL=chrome` 测试已安装的 Chrome。浏览器仅用于
   维护验证，Python 安装不要求 Node.js；通用 Skills CLI、Pi 和 DeepSeek 原生入口需要各自运行时。
4. 执行 `python3 tools/package.py build`。相同源文件产生相同 ZIP，包内
   `package-manifest.json` 绑定逐文件 SHA256 和套件版本；发行目录同时产生外部
   manifest 和 `SHA256SUMS`。`python3 tools/package.py verify dist/包名.zip`
   校验实际 ZIP 的内容。校验和证明文件一致性，不是签名。
5. 提交版本及变更说明，确认开发分支与合入检查通过。在用户授权范围内合入 `main`，
   核对最终提交与验证来源一致，再从该提交创建 `vX.Y.Z` 标签并推送。`Release` workflow 会再次调用完整 CI，然后按标签构建并创建 GitHub Release。
6. 核对远端标签、Release 资产和实际下载文件的哈希。不要移动发布过的标签，
   也不要给已经发布的版本替换内容；修正问题时发布新版本。

## 验证范围

CI 覆盖 Python 3.10/3.12/3.13 和 Windows 下的包与安装器测试、随包 router 测试、
浏览器图形/反馈回归、合成恢复输入的真实浏览器敏感性回归，以及固定版本的
共享安装和 DSH/Pi 原生发现任务。Release 只有在这些任务通过后才获得上传资产权限。
CI 不运行模型行为 actor，不构成所有工程场景有效的声明。

## 安装状态保护

Python 安装器对每次成功操作保存 suite version、skill 文件指纹、安装位置和
事务编号。备份包含操作前的真实目录与旧回执；不会把旧安装的本地改动默默认作
新版。恢复记录在替换前写入，回执在所有目录验证后提交。

`--adopt` 用于显式接管既有同名安装，`--force` 用于显式保留备份后替换已经
由套件管理的本地修改。它们不授权修改其他 skills。恢复发现未知的新编辑时会
停止，要求先保存编辑，不自动清除内容。

## 来源迁移

首版提取自 AI-Native-SDD，精确提交见 [UPSTREAM.json](UPSTREAM.json)。
后续通用套件优化以本仓库为发布来源。上游实验和业务案例按原链接留存；本包
不复制实际项目、历史 PPT、个人路径或用户反馈数据库。

## v0.4.0 起的构建证明

Release的发布任务在完整CI成功后，用固定提交的 `actions/attest` 为发行ZIP、外部manifest和SHA256SUMS生成Sigstore来源证明，并保留 `provenance.sigstore.json`。只有标签发布任务具有 `id-token: write` 和 `attestations: write`；普通CI保持只读。校验失败必须停止发布，不跳过证明步骤。

下载后按 [SECURITY.md](../SECURITY.md) 的仓库、工作流和标签约束验证。证明不代替逐文件校验、浏览器回归、模型评测或真人试用，也不授予软件许可。官方机制见 [GitHub构建证明说明](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations)。

ZIP与Node包不附带 `docs/optimization/`、`docs/releases/` 中的项目过程资料；这些文件保留在仓库，发行说明中的链接固定到对应版本。可复用的技能、工具、测试、维护指南与第三方声明仍随包提供。包内链接由 `python3 tools/docs.py check` 校验；Node清单另用 `npm run test:package` 验证。

## 开发候选与稳定安装入口

未发布候选可在 `plugin.json` 提前记目标版本，行为与限制写入 `Unreleased`。
安装命令仍固定到CHANGELOG中最新已有日期的稳定版本；不能把开发主线版本当成已存在的标签或Release。
正式发布前再补目标版本的日期/说明并同步安装示例。`notes` 命令拒绝无日期的草稿，
标签流程仍需实际CI及发布授权。原0.4.1候选未独立发布，其已验证改动纳入0.5.0。
未完成的评测框架与实验草稿继续保留在开发分支；实际发布状态以标签和Release资产为准。
