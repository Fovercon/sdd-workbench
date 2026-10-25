# 参与维护

先阅读 [项目入口](README.md)、[开发规则](AGENTS.md) 和 [能力目录](skills/CATALOG.md)。
复现问题不需要先学习全部技能；请给出期望行为、实际结果、所用版本及最小输入。

## 报告问题与提出改进

普通问题通过 [Issues](https://github.com/Fovercon/sdd-workbench/issues) 提交。
标明宿主及版本、模型实际报告的名称、操作系统、安装方式和套件版本。删除密钥、公司代码和个人资料后再附命令、日志、截图；不要提交实际反馈数据库。
涉及安全漏洞时按 [SECURITY.md](SECURITY.md) 处理。

提出方法变化时说明它解决的实际失败、影响的阶段和保留的边界。
仅用单元测试或模型自评不能证明方法有效；准备可独立复现的输入，并保留失败及重试。
外部评审的记录格式见 [审查工具](docs/REVIEW-FEEDBACK.md)。

## 开发与验证

需要 Python 3.10+；浏览器维护还需要 Node.js 20+。

```sh
python3 tools/package.py check
python3 -B -m unittest discover -s tests
python3 -B -m unittest discover -s skills/sdd-workflow-router/tests
python3 tools/docs.py check
npm ci
npm run test:adapters
npx playwright install --with-deps chromium
SDD_BROWSER_CHANNEL=chromium npm run test:browser
SDD_BROWSER_CHANNEL=chromium npm run test:forward-browser
```

安装测试只使用临时目录，不能修改开发者正在使用的 skills。
涉及技能方法时，另跑受影响技能的 forward 评测；记录实际宿主、模型、输入、交互和用量。
更改看板或本机反馈时需要真实浏览器检查。

提交或 Pull Request 应说明具体问题、改后行为、验证结果及实际限制。
保留原有历史、来源指纹和第三方声明，不把计划、文件存在、测试通过或反馈提交当成批准。
发行包不包含项目试点及优化过程资料；其固定版本链接仍可在仓库阅读。

项目级许可证尚未确定；不要在贡献中引入无法授权的内容，也不要将当前仓库描述为 MIT 或 Apache 项目。
发布由维护者按 [发布流程](docs/RELEASING.md) 执行，不移动已发布标签或替换同版本资产。
