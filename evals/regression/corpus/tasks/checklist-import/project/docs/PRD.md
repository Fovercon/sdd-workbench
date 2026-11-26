# PRD:Markdown 清单解析器

## 背景
团队用 Markdown 复选框跟踪事项,需要可导出/导入的解析器。

## 功能需求
- FR-001:`parse(md_text) -> dict`:逐行识别清单项,合法行匹配 `^\s*-\s\[( |x|X)\]\s?(.*)$`(done 为组1属于 x/X;text 为组2 去首尾空白,允许为空串)。
- FR-002:去掉首尾空白后以 `- [` 开头、但不匹配 FR-001 模式的行(如 `- [x`、`- [y] 事项`)计入 `invalid_lines`;其余行(标题、空行、普通文本)一律忽略不计。
- FR-003:text 相同的项去重,保留首次出现(其 done 状态生效),后续重复项丢弃。
- FR-004:返回 `{"items": [{"text": str, "done": bool}, ...](按首次出现顺序), "invalid_lines": int}`。
- FR-005:`to_json(parsed) -> str`:`json.dumps(..., ensure_ascii=False, indent=2)`,字段即 FR-004 的两个键。
- FR-006:`from_json(s) -> dict`:`json.loads` 逆操作,坏输入的异常原样抛出(如 `json.JSONDecodeError`,其为 `ValueError` 子类)。
- FR-007:`stats(parsed) -> {"total": int, "done": int, "open": int}`。

## 交付物 API
- `checklist.py` 位于仓库根目录,导出 `parse`、`to_json`、`from_json`、`stats`。
