# PRD:销售报表生成器

## 背景
运营每天导出各地区销售 CSV,需要一个生成地区汇总报表的命令行工具。

## 输入格式
CSV 文件,每行四个字段,以英文逗号分隔,不含引号转义:
`date,region,product,amount`

示例:
```
2026-10-01,east,apple,120.5
2026-10-01,west,pear,80
```

## 功能需求
- FR-001:逐行解析;空行或纯空白行、字段数不等于 4、amount 不能解析为 float 的行视为无效行。
- FR-002:无效行跳过,不进入统计;当跳过行数大于 0 时,向 stderr 输出一行 `SKIPPED\t<n>`(n 为跳过行数)。
- FR-003:按地区汇总 amount 总和,输出按地区名升序排序。
- FR-004:CLI 用法 `python3 report.py INPUT.csv`,输出到 stdout:每个地区一行 `<region>\t<总额两位小数>`,最后输出一行 `REGIONS\t<地区数>`。
- FR-005:读取文件使用 utf-8-sig 编码(兼容 BOM);输入文件不存在时 stderr 输出 `ERROR missing file`,退出码 2。
- FR-006:正常结束退出码 0(即使存在跳过行);金额可为负数。

## 交付物 API(必须同名同签名)
- `report.py` 位于仓库根目录。
- `parse_line(line: str) -> tuple[str, str, str, float] | None`:解析单行,无效返回 None;前三个字段去除首尾空白。
- `summarize(rows: list) -> list[tuple[str, float]]`:输入 parse_line 结果列表,返回按地区名升序的 `(region, total)` 列表;空输入返回 `[]`。
