# 安装诊断

自 v0.3.0 提供，v0.2.1 及更早版本不包含。使用 v0.3.0 及以后完整源码/Release ZIP，
在其 `sdd-workbench` 目录运行：

```sh
python3 -B tools/doctor.py --agent all
```

它只读检查六平台代理的已知技能入口，列出缺失、重复副本、不同内容、失效链接、Python
安装回执和未恢复事务。不会启动客户端、执行 PATH 中的命令、安装、恢复或覆盖个人修改。
只检查 Codex 可省略 `--agent`，其他名称是 `hermes zcode deepseek opencode pi shared`。
Python 版本要求与[安装器](../README.md#python-整套安装)一致。

## 输出怎么读

输出包含本次源目录的声明版本和技能指纹；声明版本不是发布标签认证，也不查询网上最新版。
`NO_FILE_ISSUES_OBSERVED` 表示所检查文件未发现问题；宿主实际发现、工具执行和模型任务仍需
在客户端中验证。桌面客户端不在 PATH 上不等于没有安装；命令在 PATH 上也不等于可用。

| 观察项 | 含义与下一步 |
|---|---|
| `NO_VISIBLE_DEFAULT_SKILLS` | 所检查目录未发现完整套件；先核对真实入口，不能据此认定没有安装。 |
| `DUPLICATE_PHYSICAL_COPIES` / `CONFLICTING_COPIES` | 同名技能有多个物理副本；后者字节不同。核对宿主优先级和安装方式，先保留个人修改。多个链接指向同一真实目录不会算成独立副本。 |
| `MANAGED_CONTENT_CHANGED` | 文件与 Python 安装回执不同，可能是编辑、缺失或损坏；先看差异和备份，不直接强制覆盖。 |
| `CONTENT_DIFFERS_FROM_SOURCE` / `VERSION_DIFFERS_FROM_SOURCE` | 与这次检查源不同；正常旧版本或个人修改也会出现。核对准确来源再决定更新。没有回执不会猜测版本或安装所有权。 |
| `PENDING_RECOVERY` | 存在未恢复事务。保留新编辑后，按[恢复说明](../README.md#更新与故障处理)使用同一 destination/state 恢复；诊断不会代为恢复。 |
| `INVALID_OR_UNREADABLE_RECEIPT` / `EXTRA_RECORDED_SKILL` | 回执不可读、归属不符或记录了当前源未包含的技能；保留原记录、目录与备份，核对迁移来源。 |
| `BROKEN_SKILL_LINK` / `UNREADABLE_OR_INVALID_SKILL` / `INVALID_SKILL_ROOT` | 链接、文件、元数据或根目录不可用。核对路径、权限、来源；只支持技能目录整体链接，资源内部链接不在支持布局内。 |

## 自定义入口与机器输出

插件缓存、项目内安装和自定义目录不会被默认扫描穷举。已知真实技能根时显式给出：

```sh
python3 -B tools/doctor.py --agent codex --dest /path/to/skills --json
python3 -B tools/doctor.py --agent codex --dest /path/to/skills --state /path/to/installer-state
```

`--dest` 只允许一个目标，关闭其他根目录扫描；`--state` 必须与 `--dest` 一起使用。
`--home /temporary/profile` 使用安装器相同的隔离 home 规则，忽略目标环境路径覆盖，适合测试。
`--source /path/to/source` 指定完整检查源，不改变宿主选择，也不会下载源。
默认共享搜索只用于 Codex、DeepSeek Harness、OpenCode、Pi；Hermes/ZCode 的原生目录可以
包含整体技能链接，但公共目录存在本身不能证明它们会自动发现。

退出码：`0` 所检查文件未发现问题；`1` 存在观察项（包括需核对的警告）；`2` 参数、来源或
诊断无法完成。JSON 中保留稳定问题码、实际路径、后续动作与 `NOT_TESTED` 客户端状态。
自动化不得把退出码 0 转换为“模型任务通过”或“公司推广就绪”。
实际更新前可用 `install --dry-run` 核对影响；执行、回退和恢复见[安装维护指南](OPERATIONS.md)。

完整工具在 Git/Release ZIP 中；原生 skill/package 安装只负责向宿主提供技能，不一定包含
仓库 `tools/`。需要诊断时使用可信的完整源码副本，按真实入口传 `--dest`。
