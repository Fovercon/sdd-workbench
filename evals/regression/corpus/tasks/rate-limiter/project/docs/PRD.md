# PRD:接口限流器库

## 背景
网关需要对第三方调用做两类限流:令牌桶与滑动窗口。

## 功能需求
- FR-001:`TokenBucketLimiter(rate, capacity)` 构造;`rate<=0` 或 `capacity<=0` 抛 `ValueError`。
- FR-002:`allow(now, tokens=1.0)`:令牌按 `rate` 个/秒 从上次调用时刻补充到 `now`,上限 `capacity`;当前可用令牌不足 `tokens` 时返回 `False` 且不消耗;足够则消耗并返回 `True`;`tokens<0` 抛 `ValueError`。
- FR-003:`available(now)` 返回当前可用令牌数(float),不产生消耗。
- FR-004:新构造的桶从满桶开始。
- FR-005:`SlidingWindowLimiter(window, max_events)` 构造;`window<=0` 或 `max_events<=0` 抛 `ValueError`。
- FR-006:`allow(now)`:统计时间戳严格大于 `now-window` 且不大于 `now` 的已记录事件,加本次若超过 `max_events` 则拒绝且不记录;否则记录并返回 `True`;相同时间戳按独立事件计。
- FR-007:拒绝的事件不占用窗口名额;窗口外旧事件自然失效。

## 交付物 API
- `limiter.py` 位于仓库根目录,导出 `TokenBucketLimiter` 与 `SlidingWindowLimiter`。
- 时间参数 `now` 一律为 float 秒;库不做真实时间调用(纯函数式,便于测试)。
