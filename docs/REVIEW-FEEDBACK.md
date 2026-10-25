# 多人审查反馈：固定版本、证据与复验

本工具服务于多人、跨会话或跨版本的正式审查记录。普通小改动仍可直接反馈，不要求所有
研发任务填写 JSON。自 v0.3.0 提供，v0.2.1 及更早版本不包含；使用 v0.3.0 及以后完整源码/发行 ZIP，
原生 skill/package 安装不一定包含 tools。先按[审查包](https://github.com/Fovercon/sdd-workbench/blob/v0.4.0/docs/optimization/REVIEW-KIT.md)独立使用，
再汇总；没有新的公司审批规则、身份认证、在线收集或自动发布功能。
方法前向评测的 actor 仍只拿 runtime skills 和原始任务输入；由维护者在 actor 之外固定
候选和整理报告，不为了填表把 rubric、准备器或作者的旧结论发给 actor。

## 一份反馈怎么准备

先固定一份不再同时编辑的候选源码，并准备包输入之外的审查目录，例如
`.eval-artifacts/reviews/` 和其中的 `evidence/`。所有命令只读，输出到 stdout；下面的保存
行为来自你显式使用的终端重定向，工具不会创建数据库、目录或自动覆盖原报告。

```sh
python3 -B tools/review.py snapshot > .eval-artifacts/reviews/candidate.json
python3 -B tools/review.py new --id agent01 --reviewer agent01 --kind agent > .eval-artifacts/reviews/agent01.sdd-review.json
```

`--source /path/to/candidate` 可检查另一份完整源码。snapshot 的指纹包括全部发行输入，
包括 tools/docs/tests 下未被 Git 跟踪但会进入发行包的文件；复制到其他绝对路径后指纹相同。
范围明确为 RELEASE_INPUTS：不是完整工作树审查，CI、忽略文件和实际反馈不在指纹内。
这里按 tools/package.py 的正向清单计算，不是原生宿主安装回执或其他包格式的产物指纹。
完整工作树还需按审查包记录 Git diff 和所有未跟踪文件。快照不持锁，准备者应冻结副本，
不把并发编辑中的目录当成可重现基线。声明版本号不能代替实际指纹，也不能证明发布标签。

new 输出 DRAFT。填写 task（实际任务）、notes（结果/未做项）、environment，以及观察事实。
如有任务输入，在 inputs 中记录它们的证据描述；没有提供时保留空数组并说明限制，不能
把工具的候选身份核对当成业务任务输入已经齐全。
没有证据的环境信息保留 null，不猜模型版本。reviewer 字段如下：

| 字段 | 取值与含义 |
|---|---|
| id | 稳定 ASCII 别名：字母开头，字母/数字/下划线/连字符，最长 64；不要冒用身份。 |
| kind | human / agent / unknown，自述人工或 agent；agent 扮演专家不能标成人工专家使用。 |
| relation | author / other / unknown，相对于**被审实现作者**的关系，不是是否提出了这个问题。 |
| context | fresh / shared / unknown，是上下文声明，不能证明独立。 |
| informed | 是否已读作者结论：true / false / null；无法确认保留 null。 |

一项 finding 需要：id、title、severity（P0–P3）、scope（候选内文件路径数组）、expectation、
expectation_source、observation、consequence、steps（步骤字符串数组）、evidence（证据描述数组）。
预期行为写出依据，事实与原因推测分开；scope 是提交者声明的范围，工具不会推断全部影响。
没有发现也可保留空数组，但 notes 应写出实际检查和未覆盖范围，不能只填“通过”。

先把真实检查输出/观察记录保存在报告旁的 evidence/，再取得描述：

```sh
python3 -B tools/review.py evidence --root .eval-artifacts/reviews --path evidence/repro.txt
```

返回 `{"path":"evidence/repro.txt","sha256":"…"}`，填入 evidence 数组。工具只读普通文件，
不执行 steps，不根据日志内容判断测试是否真的通过。证据必须在该报告旁的 evidence/ 中，
拒绝绝对路径、越界、路径中的链接和非普通文件。单份报告最多 1 MiB，每个证据最多 16 MiB；
大日志提供保留原文来源的适当节选。普通二进制文件也可核对字节，不会被自动打开或执行。

完成实际检查后显式改为 SUBMITTED，保留原报告和证据，再运行：

```sh
python3 -B tools/review.py check --report .eval-artifacts/reviews/agent01.sdd-review.json
```

多个报告用 `--report 路径A 路径B`；不会递归搜索或读取未列出的报告。报告 ID 和报告内
finding/followup ID 必须唯一，JSON 重复 key、未知字段、错误引用和不匹配证据都会失败。
目录移位需把报告及相邻 evidence/ 一起复制；原文件原样保留，后续动作使用新报告 ID。

## 修复与复验怎样关联

后续动作使用新报告。candidate 绑定这次实际审查的候选，followups 数组每项使用：

```json
{
  "id": "E1",
  "target": "agent01/F1",
  "action": "RECHECK_PASS",
  "reason": "说明实际复验、范围及限制",
  "evidence": [{"path": "evidence/recheck.txt", "sha256": "填写 evidence 命令给出的真实值"}]
}
```

示例仅展示字段，不是真实评审意见；替换占位符。target 为原报告 ID/发现 ID，check 时须
同时列出原报告与跟进报告。支持 REPRODUCED、FIX_REPORTED、RECHECK_PASS、RECHECK_FAIL、
REJECT_PROPOSED、DUPLICATE_PROPOSED；前四类必须有证据。重复建议还需 duplicate_of 指向
另一个发现；仅保留关联建议，不删除/合并原文，不按多数意见裁决。

| 汇总状态 | 含义 |
|---|---|
| OPEN | 发现仍保留；拒绝/重复建议不自动关闭。 |
| REPRODUCTION_REPORTED / FIX_REPORTED | 当前候选有复现/修复声明及匹配证据；语义结论仍需审查。 |
| RECHECK_REPORTED | 当前候选有通过声明和匹配证据，不表示问题被自动关闭。 |
| RECHECK_FAILED | 当前候选有失败声明；旧通过不能覆盖它。 |
| DISPUTED | 当前候选同时有通过和失败声明；不按人头、时间或模型名选择胜者。 |
| STALE_RECHECK | 只有其他候选上的复验；源文件即使保持同一版本号，字节变化也不会续期旧结论。 |

每个 followup 保留自述 reviewer、候选身份、原始证据及报告文件 SHA；same_reporter_id
只比较提交者别名，self_recheck_declared 只反映其与实现作者的自述关系，未知为 null。
两轮检查、不同 ID、human 标记或 fresh 字样都不能由本工具认证为独立审查。

## 校验结果的边界

退出 0 / validation=VALID 只表示格式、关联和本次证据字节匹配；即使存在 P0 或争议发现，
输入仍可能 VALID。退出 2 表示输入/来源/证据失败。check 输出始终标记 identity_authenticated=false、
commands_executed=false、automatic_closure=false、release_readiness=NOT_ASSESSED。
需要按事实复现、判定责任与影响、实施修复并选择有资格的人复验；公司 owner 决定问题处置。
不要把这个退出码接成发布门禁，也不要把自述数据当成真实命令执行或身份认证的证明。

工具不修改源、原报告、回执或模型设置，不上传材料。实际报告可能含本机路径或业务细节，
由提供者审阅后保存在公司指定位置。实际报告和 candidate 清单不是包输入，放进 docs/tools
等包目录会被 package check 拒绝；改文件名也不会绕过已知 kind 标记的隔离检查。
合成回归及工具可以发行，不代表已经收到其他 agents/专家的真实审查意见。
