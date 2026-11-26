# PRD:日期递归展开器

## 背景
日历服务需要把人类可读的重复规则展开为具体日期列表。

## 规则语法(`parse_spec(text) -> dict`)
- `daily`:每天。→ `{"kind": "daily"}`
- `weekly:MON,WED`:每周指定星期;星期码 `MON TUE WED THU FRI SAT SUN`(大小写不敏感),星期一到日映射为 0..6;按出现顺序去重。→ `{"kind": "weekly", "days": [0, 2]}`
- `every:3d`:从起始日每 3 天;`3` 为正整数。→ `{"kind": "interval", "step": 3}`
- 允许整体首尾空白;其余任何形式(未知规则、step<=0、未知星期码、多余字段)抛 `ValueError`。

## 展开规则(`expand(spec_text, start, end, include_start=True, include_end=False) -> list[date]`)
- FR-001:先解析规则;`start > end` 直接返回 `[]`。
- FR-002:`daily` 自 start 起每日;`interval` 自 start 起每 step 天;`weekly` 取区间内所有命中星期的日期(首个命中可能早于 start?不会——仅从 start 起算)。
- FR-003:`include_start=False` 时,若 start 本身命中则从结果中剔除;`include_end=True` 时,若 end 命中则包含;默认区间为半开 `[start, end)`(start==end 时默认结果为空)。
- FR-004:结果升序、去重,元素为 `datetime.date`。

## 交付物 API
- `recurrence.py` 位于仓库根目录,导出 `parse_spec` 与 `expand`。
