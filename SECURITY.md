# 安全与发布验证

## 报告安全问题

请使用 GitHub 的 [私密漏洞报告入口](https://github.com/Fovercon/sdd-workbench/security/advisories/new)。
不要在公开 Issue 中发布密钥、生产数据或可用于攻击他人的详细资料。
报告请包含套件版本、宿主、最小复现输入、实际影响及保护范围；响应时间以维护者实际处理为准。
普通功能或文案问题使用 [Issues](https://github.com/Fovercon/sdd-workbench/issues)。

## 适用范围

请优先使用最新 Release。旧版记录保留，但没有承诺所有历史版本持续获得安全回补。
Skills 是代理的指令与辅助工具，不能代替宿主权限控制或操作系统沙箱。
本机反馈服务只绑定回环地址；不要直接暴露到公网。共享前请清理项目来源及反馈中的敏感内容。

## 核对下载来源

v0.4.0 起，标签发布流程为发行 ZIP、逐文件 manifest 和 SHA256SUMS 生成 Sigstore 构建来源证明。
它把产物摘要与仓库、提交、工作流绑定；校验和用于核对内容，构建证明用于核对构建身份。
这不表示产品获得安全审计、业务认证或公司推广批准。

```sh
gh release download v0.5.0 --repo Fovercon/sdd-workbench --pattern 'sdd-workbench-*.zip'
gh attestation verify sdd-workbench-v0.5.0.zip --repo Fovercon/sdd-workbench --signer-workflow Fovercon/sdd-workbench/.github/workflows/release.yml --source-ref refs/tags/v0.5.0
python3 tools/package.py verify sdd-workbench-v0.5.0.zip
```

最后一条命令需要本仓库的工具；验证成功只说明包的身份及逐文件内容匹配。
更换版本时同时更换标签、文件名及 `--source-ref`，不要省略目标仓库约束。
具体步骤见 [发布流程](docs/RELEASING.md) 及 [GitHub 验证文档](https://cli.github.com/manual/gh_attestation_verify)。

## 许可证状态

项目级许可证待定。构建证明不授予使用、修改或再分发许可。
Mermaid 的独立 MIT 许可及依赖声明见 [第三方声明](THIRD_PARTY_NOTICES.md)。
