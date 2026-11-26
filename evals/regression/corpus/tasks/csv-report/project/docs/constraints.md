# 技术与过程约束
- Python 3.10+,仅标准库;单文件实现放 `report.py`,不引入第三方依赖。
- 不要修改 `docs/` 目录下任何文件;不要执行 git 提交或推送。
- 需要自带测试时放在 `tests/` 目录,命令 `python3 -B -m unittest discover -s tests`。
- CLI 行为(stdout/stderr/退出码)按 PRD 逐条实现,不留 TODO。
