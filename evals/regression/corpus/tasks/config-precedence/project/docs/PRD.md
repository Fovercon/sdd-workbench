# PRD:配置优先级合并

## 背景
服务需要"默认值 < 配置文件 < 环境变量"的三层配置合并。

## 功能需求
- FR-001:`coerce(value: str)`:字符串转基础类型——`true`/`false`(大小写不敏感)转 bool;匹配 `^[+-]?\d+$` 转 int;匹配 `^[+-]?\d+\.\d+$` 转 float;其余保持 str。
- FR-002:`merge(defaults, file_path=None, env=None) -> dict`,返回全新字典,不得修改入参。
- FR-003:`file_path` 提供时读取 JSON 对象并深合并(dict 递归,list 与标量直接覆盖);文件不存在则忽略;内容不是合法 JSON 对象时抛 `ConfigError`。
- FR-004:`env` 为 `None` 时取 `os.environ`(测试时显式传 dict);仅处理以 `APP_` 开头的键,其余忽略。
- FR-005:环境键规则——去掉 `APP_` 前缀后按 `__` 切分路径:`APP_DB__HOST` 指向 `db.host`;路径段大小写不敏感(比较与写入时按小写);路径在 `defaults` 中不存在时该键整体忽略(不新建键);值经 `coerce`。
- FR-006:优先级 env > file > defaults;嵌套 dict 逐层合并。
- FR-007:模块内定义异常类 `ConfigError(Exception)`。

## 交付物 API
- `config.py` 位于仓库根目录,导出 `coerce`、`merge`、`ConfigError`。
