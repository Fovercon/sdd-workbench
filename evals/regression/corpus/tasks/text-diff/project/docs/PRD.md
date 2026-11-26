# PRD:词级文本比较工具

## 背景
审阅流程需要一个以"词"为粒度的两文件比较工具。

## 功能需求
- FR-001:`tokenize(text) -> list[str]`:按任意空白(空格/制表符)切分,连续空白视作一个分隔符。
- FR-002:`word_diff(old, new, ignore_case=False) -> list[tuple[str, str]]`:对两个文本的 token 序列做最长匹配对齐,输出操作序列,元素为 `('=', tok)`、`('-', tok)`、`('+', tok)`;同一替换块内先输出全部 `- 再输出全部 +(与 difflib.SequenceMatcher 的 opcode 顺序一致)。
- FR-003:`ignore_case=True` 时以小写化后的 token 参与对齐比较,但输出行保留原 token。
- FR-004:`render(ops) -> str`:每个 token 一行,行首为前缀字符加一个空格:`  tok`、`- tok`、`+ tok`;行间用 `\n` 分隔,末尾不包含换行符;空操作序列返回空字符串。
- FR-005:CLI `python3 diff.py [--ignore-case] OLD NEW`(OLD/NEW 为文件路径):向 stdout 输出 `render(word_diff(...))`,非空结果追加一个 `\n`,空结果不输出字符;两文件 token 序列(按上述比较规则)完全一致时退出码 0,否则 1;文件不可读时 stderr 输出 `ERROR unreadable` 并退出码 2。

## 交付物 API
- `diff.py` 位于仓库根目录,导出 `tokenize`、`word_diff`、`render`,并支持上述 CLI。
