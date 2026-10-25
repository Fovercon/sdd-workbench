# 安装维护与故障交接

面向维护套件安装的研发工程师。自 v0.3.0 提供 `install --dry-run`；v0.2.1 及更早发布的
安装器不支持该参数。以下预览命令在v0.3.0 及以后完整源码/发行包中执行；需要预览
旧版本时用 `--source /path/to/target-source` 指向目标完整源码。不要因此切换或清理有个人
修改的工作树。最新已发布版本与支持范围见 [README](../README.md)和[兼容说明](AGENT-COMPATIBILITY.md)。

## 先确定由谁管理这份安装

| 安装方式 | 更新/回退入口 | 可检查的证据 |
|---|---|---|
| Python 安装器 | 本文的 install/status/rollback/recover，使用原来的 agent/dest/state | 本安装器的 receipt、pending 与 transactions 备份 |
| Skills CLI / 公共目录链接 | 原来的 Skills 管理器及其固定版本来源 | doctor 可检查已知/显式目录；Python 不管理技能链接 |
| Codex/ZCode 插件、DSH/Pi 原生 package | 原来的宿主插件/package 管理方式，切换准确来源版本 | doctor 显式 --dest 可看文件，不能证明宿主已重新发现 |

不要把 Python 的 recover/rollback 用来修其他管理器的记录。`--adopt` 会开始管理当前源中的
同名目录；预览中必须看清接管范围。目录整体链接不能被 Python 接管，使用原管理器处理。
没有回执不等于没有安装，doctor 的版本/文件匹配也不能授予安装所有权。

## 一次更新的最短闭环

先准备可信的完整目标源码，固定版本并核对来源。保留原来的选择参数；下面以六目标为例，
单个目标可替换为 `--agent codex`，自定义路径同时携带原 `--dest`、`--state`。

```sh
python3 -B tools/doctor.py --agent all
python3 -B tools/install.py install --agent all --dry-run
```

doctor 的退出 1 可能是正常旧版本/目录观察项，按[问题码](DOCTOR.md)逐项核对。
预览输出 `operation=INSTALL_PREVIEW`，不创建目录、锁、字节码缓存、事务或备份。
源信息包含声明版本和完整包指纹；这不是远端标签认证。它只预览技能目录及回执的操作，
完整源包的文档/工具并不会因此复制进技能安装目录。

| 输出 | 怎么判断 |
|---|---|
| `eligible` | 全部/单目标当前通过预检；有一个 false 就先处理阻塞，不能把其他目标的 true 当成部分执行完成。 |
| `blocked_reason` | 当前阻塞原因，例如用户编辑、未恢复事务、未接管的同名内容或同版本不同技能字节。 |
| `current_version` / `target_version` | 回执版本与本次源声明版本；无有效回执不猜版本。 |
| `requires_transaction` | 真正执行时是否需要事务。仅版本变化、技能字节相同也会重新安装并记录备份。 |
| `skills[].files` | 相对于当前磁盘文件的 added/changed/removed 路径；不包含文件内容。不可读时为 null，并保留错误。 |
| `locally_modified` | 已管理目录与原回执不同；可能是用户编辑、缺失或损坏，不等于可自动覆盖。 |

操作名：INSTALL 新目录；REPLACE 替换内容；REINSTALL 字节相同但事务会重新写入；
REMOVE 移除曾管理而目标源已不包含的目录；ADOPT 接管不同内容；ADOPT_IDENTICAL 接管
相同内容；UNCHANGED 无需事务；UNREADABLE 不可读取，不能执行。无关未管理目录不扫描或接管。

预览退出 0 表示所选目标当前都可预检；1 表示阻塞/失败；参数错误由 argparse 返回 2。
有效源的目标问题保存在 JSON 中；参数/源检查本身失败可能只有 stderr。预览不持锁，
是当时的观察，不能当成审批令牌、写入完成证明或并发安全承诺。预览后发生编辑时，
正式执行仍必须重新预检、获取锁、备份和检查每次替换。

确认目标版本、差异与现有授权后，执行完全相同的源/目标参数，去掉 `--dry-run`：

```sh
python3 -B tools/install.py install --agent all
python3 -B tools/install.py status --agent all
python3 -B tools/doctor.py --agent all
```

需要覆盖已管理编辑或接管旧内容时，先保留个人工作并核对差异，再显式选择 `--force` /
`--adopt`。可以带着这些参数再做一次 dry-run，它只展示请求后的预检结果，不会提前执行。
备份以实际安装结果中的 `backup` 和 `transaction_id` 为准，预览不会提前产生备份号。
更新中不要启动读取这些目录的新 agent 会话。文件检查后重新加载宿主，在真实项目中
核对技能发现，再运行一项获准的小任务；这两步的客户端/模型结果要另行记录。

## 中断、回退与用户编辑

| 情形 | 实际下一步 | 完成后核对 |
|---|---|---|
| 多目标更新中途失败 | 从输出的 completed/failed_agent 开始；若进程直接退出而没有输出，先对全部原目标运行 status 和 dry-run。仅对 pending 目标用同一 dest/state 执行 recover，再重新预览/安装。 | 各目标版本、changed/pending；已完成目标不重复建立事务，其他目标随后完成。 |
| receipt 已提交但 pending 尚未删除 | 执行 recover，由记录及全部目标指纹判断是否完整提交。 | 完整提交保留新版本，不能一律当成回滚。 |
| 中断后又新增编辑 | recover 应停止。先把编辑复制到事务之外保全，人工核对并解决与记录的冲突，再恢复。 | 用户编辑保存位置、恢复后旧/新版本、备份与 pending；不要直接删除整个技能目录。 |
| 正常更新后需撤销 | 无新编辑时，执行 `python3 -B tools/install.py rollback --agent all`，或精确选择需要回退的目标。 | 恢复最近事务前的内容/回执；保留新生成的回退事务与原备份。 |
| 原更新用 force 保存过个人编辑 | rollback 会恢复事务前的编辑字节；原回执可能仍将其列为 changed，这是保全结果，不应假装变成干净官方版本。 | 实际编辑字节及备份一致；后续更新重新处理编辑。 |
| 回执/事务损坏、外来或链接失效 | 保留原文件、链接和所有备份，记录错误并交给安装维护者核对准确目录与来源。 | 安装应停止，不能把坏记录当作“没有安装”后重新接管。 |

rollback 撤销最近记录事务，不是任意选择历史版本。回退本身会生成新事务；连续 rollback
可能撤销刚才的回退、在两份内容间切换。需要指定版本时，准备那个版本完整源，再按预览
和安装流程处理。首次安装的 rollback 可能移除本安装器新建的技能，恢复原有同名内容。

## 交给维护者的最小记录

保存：安装管理方式；源码/包来源与指纹；agent/dest/state 的原始选择；宿主/OS/实际错误；
当前 status、dry-run 和 doctor 输出；哪些命令真正执行过；个人编辑的保全位置；实际
backup/transaction_id；预期下一步与尚未验证的客户端/模型行为。原始输出可能含本机路径，
提交到公司指定位置前由提供者审阅。本文不会自动采集业务代码、凭据或发送报告。

公司仍需指定安装维护者、升级批准范围、备份保管和支持入口。这些是待决定项，本文不为
公司指派负责人或新增强制政策。工程演练与证据限制见[第三步结果](https://github.com/Fovercon/sdd-workbench/blob/v0.4.0/docs/optimization/STEP-3-RESULTS.md)。
