Status: APPROVED
Planning mode: STANDARD

# 技术计划
- 通知网关 NotificationGateway:send(channel, payload)。
- 重试策略 RetryPolicy:interval=[1s,4s],max=2。

## 切片
- S01:站内信发送基础链路(链接 FR-001/AC-001.1)。
- S02:失败重试与失败事件(链接 FR-002/AC-002.1)。
- S03:营销通知开关(链接 FR-003/AC-003.1)。
