# Contributing

感谢你为 `news-data` 做贡献。

## 开发环境

- Python `3.12`
- Playwright Chromium

安装：

```bash
python -m pip install -e .[dev]
python -m playwright install --with-deps chromium
```

如果要执行真实抓取，还需要：

- `WECHAT_TOKEN`
- `WECHAT_COOKIE`

## 贡献流程

建议按这个顺序：

1. Fork 仓库并创建分支
2. 只针对一个明确问题做改动
3. 本地跑测试
4. 提交 PR，写清楚改了什么、为什么改、怎么验证

## 测试

常用命令：

```bash
pytest -q
```

如果只改了模板、Pages 或 workflow，可以只跑相关测试。

## 提交约束

请尽量保持提交聚焦，不要把无关改动混在一起。

不要提交这些内容：

- `.idea/`
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `.ruff_cache/`
- 本地临时预览图
- 与当前问题无关的批量格式化结果

如果你的改动会影响 `README.md`、workflow、`pages/`、`static/news` 或 `static/images`，请在 PR 描述里说明原因。

## 许可证

提交到本仓库的代码默认按当前仓库许可证发布，即 [MIT License](./LICENSE)。
