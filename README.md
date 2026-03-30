# news-data

一个用于每日定时抓取新闻资讯并生成静态内容的仓库。

GitHub Pages 预览：

[https://luckkyboy.github.io/news-data](https://luckkyboy.github.io/news-data)

本项目代码完全是由 AI 生成，采用 [MIT License](./LICENSE)，可自由使用、修改和分发。

项目会产出两类文件：

- `static/news/YYYY-MM-DD.json`
- `static/images/YYYY-MM-DD.png`

## 数据访问地址

CDN 访问：

- JSON：`https://cdn.jsdelivr.net/gh/luckkyboy/news-data@main/static/news/YYYY-MM-DD.json`
- 图片：`https://cdn.jsdelivr.net/gh/luckkyboy/news-data@main/static/images/YYYY-MM-DD.png`

原始访问：

- JSON：`https://luckkyboy.github.io/news-data/static/news/YYYY-MM-DD.json`
- 图片：`https://luckkyboy.github.io/news-data/static/images/YYYY-MM-DD.png`

示例（2026-03-27）：

- CDN JSON：`https://cdn.jsdelivr.net/gh/luckkyboy/news-data@main/static/news/2026-03-27.json`
- CDN 图片：`https://cdn.jsdelivr.net/gh/luckkyboy/news-data@main/static/images/2026-03-27.png`
- 原始 JSON：`https://luckkyboy.github.io/news-data/static/news/2026-03-27.json`
- 原始图片：`https://luckkyboy.github.io/news-data/static/images/2026-03-27.png`

## 项目结构

核心目录如下：

- `app/domain`：领域模型定义（账号配置、解析结果、每日文档等）
- `app/ports`：端口协议（数据源、解析器、仓储、渲染器）
- `app/application`：应用服务编排（按日期抓取、选择文章、生成 JSON/图片）
- `app/infrastructure/wechat`：微信公众号素材接口访问
- `app/infrastructure/parser`：文章 HTML 解析
- `app/infrastructure/render`：基于模板 + Playwright 渲染图片
- `app/infrastructure/storage`：静态资产读写（`static/news`、`static/images`）
- `app/entrypoints`：运行入口（如 `run_daily_job.py`、`preview_render.py`）
- `config/accounts.yaml`：公众号账号配置
- `.github/workflows/daily-fetch.yml`：定时任务与自动提交流程
- `.github/workflows/pages-preview.yml`：GitHub Pages 预览站部署
- `pages/`：GitHub Pages 静态预览页面

## 运行逻辑

主流程由 `python -m app.entrypoints.run_daily_job` 驱动：

1. 读取环境变量 `WECHAT_TOKEN`、`WECHAT_COOKIE`
2. 加载 `config/accounts.yaml` 中启用的账号并按优先级排序
3. 根据目标日期拼接检索词（如 `3月27日 ...`）查询候选文章
4. 选择目标文章并抓取 HTML，解析出新闻条目、来源、金句等
5. 生成 `DailyNewsDocument`，渲染图片并写入 `static/images/YYYY-MM-DD.png`
6. 回写文档到 `static/news/YYYY-MM-DD.json`，并填充 `image` CDN 地址

幂等策略：

- 同一天若 JSON 和图片都已存在：跳过
- JSON 存在但图片缺失：仅补图并更新 JSON 中的 `image` 字段

## GitHub Action 每日更新

工作流文件：`.github/workflows/daily-fetch.yml`

- 触发方式：
  - 定时触发：`cron: "*/10 16-23,0-2 * * *"`（UTC）
  - 手动触发：`workflow_dispatch`
- 运行后会自动提交并推送 `static/news` 与 `static/images` 的更新

对应北京时间为：每天 `00:00-10:59` 每 10 分钟执行一次。

## GitHub Pages 预览

- 预览站展示正式 PNG 和对应 JSON
- 部署工作流：`.github/workflows/pages-preview.yml`

本地按某个 JSON 渲染预览图：

`python -m app.entrypoints.preview_render --json-path static/news/2026-03-30.json --output /tmp/preview.png`

`uv run --project . python -m app.entrypoints.preview_render --json-path static/news/2026-03-30.json --output static/images/preview.png`

## 本地快速运行

1. 安装依赖（Python 3.12）：

`python -m pip install -e .[dev]`

2. 安装 Playwright Chromium：

`python -m playwright install --with-deps chromium`

3. 配置环境变量（必须）：

- `WECHAT_TOKEN`
- `WECHAT_COOKIE`

4. 执行当天任务：

`python -m app.entrypoints.run_daily_job`

5. 指定日期执行：

`python -m app.entrypoints.run_daily_job --date 2026-03-27`

产物目录：

- JSON：`static/news`
- 图片：`static/images`

## 致谢

- 感谢霞鹜文楷字体支持
- 感谢项目：<https://github.com/wnma3mz/wechat_articles_spider>
- 感谢项目：<https://github.com/vikiboss/60s-static-host>
