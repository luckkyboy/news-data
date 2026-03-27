# M2 Image Rendering Design

**目标**

在 M1 的基础上，为每日新闻静态生成器增加 PNG 图片产出能力。每日任务除了写入 `static/news/YYYY-MM-DD.json` 外，还要生成 `static/images/YYYY-MM-DD.png`，并将 JSON 中的 `image` 字段回填为基于 GitHub 仓库产物的稳定访问地址。

**范围**

M2 包含：

- 浏览器渲染生成每日新闻 PNG
- `static/images/YYYY-MM-DD.png` 落盘
- JSON 中 `image` 字段真实回填
- 支持“已有 JSON 补图”的路径
- GitHub Actions 安装并运行浏览器渲染依赖

M2 不包含：

- git 自动提交与推送
- 复杂前端工程拆分
- 多主题皮肤系统
- 图片压缩优化策略细分
- LLM 参与图片文案处理

## 一、交付模型

M2 仍然是离线静态生产器。

每日任务产物变为两类：

- `static/news/YYYY-MM-DD.json`
- `static/images/YYYY-MM-DD.png`

JSON 和图片是同一份每日内容的双格式静态产物。

## 二、数据契约变化

M2 不新增 JSON 字段，但修改 `image` 字段语义。

M1：

- `image = ""`

M2：

- `image = 图片静态访问 URL`

示例：

```json
{
  "date": "2026-03-27",
  "news": ["新闻 1", "新闻 2"],
  "cover": "https://mmbiz.qpic.cn/xxx",
  "image": "https://cdn.jsdelivr.net/gh/<owner>/<repo>@main/static/images/2026-03-27.png",
  "title": "每日简报 3月27日",
  "quote": "先照顾好自己，再去照顾世界",
  "link": "https://mp.weixin.qq.com/s/xxxxx",
  "publish_date": "2026-03-27 06:30:00",
  "create_date": "2026-03-27 06:30:00",
  "update_date": "2026-03-27 06:35:00"
}
```

## 三、图片 URL 策略

M2 使用基于 GitHub 仓库静态产物的地址。

默认策略：

- `https://cdn.jsdelivr.net/gh/<owner>/<repo>@<ref>/static/images/YYYY-MM-DD.png`

理由：

- 保持“先使用 git 的地址”这一要求
- 比 `raw.githubusercontent.com` 更适合静态分发
- 后续若切换自定义域名，仅需调整配置，不改业务逻辑

该 URL 基础前缀通过配置提供，不写死在应用层。

## 四、架构设计

M2 在现有 M1 基础上增加渲染职责，但保持现有分层。

建议新增目录与文件：

```text
app/
  ports/
    image_renderer.py
  infrastructure/
    render/
      __init__.py
      playwright_image_renderer.py
      template.html
    storage/
      static_assets_repository.py
```

职责边界：

- `ImageRenderer`：输入文档，输出 PNG 字节
- `PlaywrightImageRenderer`：负责浏览器渲染与截图
- `StaticAssetsRepository`：统一处理 JSON 路径、图片路径、保存、读取、存在性检查和图片 URL 生成
- `DailyJobService`：只做编排，不直接处理模板、截图或 URL 拼接

## 五、核心数据流

M2 支持两条主路径。

### 路径 A：当天 JSON 和 PNG 都不存在

1. 按 M1 既有逻辑抓取公众号文章
2. 生成结构化 `DailyNewsDocument`
3. 调用渲染器生成 PNG 字节
4. 保存 PNG 到 `static/images/YYYY-MM-DD.png`
5. 生成图片 URL，写入 `document.image`
6. 保存最终 JSON 到 `static/news/YYYY-MM-DD.json`

### 路径 B：当天 JSON 已存在，但 PNG 不存在

1. 从本地读取 `static/60s/YYYY-MM-DD.json`
2. 反序列化为 `DailyNewsDocument`
3. 调用渲染器生成 PNG
4. 保存 PNG
5. 回填 `image`
6. 重写 JSON

### 跳过路径

如果 JSON 与 PNG 都存在，则直接跳过。

## 六、模板与渲染策略

M2 继续走浏览器渲染，不使用 Pillow。

渲染方式：

- Python 将 `DailyNewsDocument` 注入本地 HTML 模板
- Playwright 打开本地 HTML
- 等待页面稳定后截图目标容器
- 输出 PNG

M2 模板要求：

- 单文件 HTML 模板
- 内嵌 CSS
- 不引入前端打包工具
- 页面结构清晰，便于后续迭代

M2 页面内容至少包含：

- 标题
- 日期
- 新闻列表
- quote
- 封面图（有则展示，无则隐藏）

M2 页面目标是“稳定产图”，不是视觉高度还原。

## 七、配置策略

除现有账号配置外，M2 增加渲染和发布相关配置。

建议配置项：

- `image_base_url`
- `playwright_browser_channel` 或浏览器执行配置
- `render_viewport_width`
- `render_device_scale_factor`

这些配置可以先放入 `config.py` 或环境变量读取逻辑中，但必须集中管理。

## 八、存储策略

当前 M1 的 `LocalJsonRepository` 只负责 JSON。

M2 建议新增 `StaticAssetsRepository`，统一管理静态产物：

- `json_exists(date)`
- `image_exists(date)`
- `load_document(date)`
- `save_document(document)`
- `save_image(date, content)`
- `build_image_url(date)`

这样可以避免把图片路径逻辑分散在编排层和入口层。

## 九、失败策略

以下情况任务失败：

- 新抓取路径下，文章抓取成功但图片渲染失败
- 已有 JSON 补图路径下，图片渲染失败
- 图片保存失败
- 模板渲染后输出为空

以下情况允许继续：

- `cover` 缺失，页面隐藏封面区块
- `quote` 缺失，页面隐藏 quote 区块

## 十、GitHub Actions 设计

M2 workflow 在 M1 基础上新增浏览器依赖准备。

职责：

- 安装 Python 依赖
- 安装 Playwright 与浏览器
- 运行日任务

仍然不包含：

- git commit
- git push

## 十一、测试策略

M2 最少测试：

- 新抓取路径同时产出 JSON 与 PNG
- 已有 JSON 且缺 PNG 时仅补图
- `image` 字段被正确回填
- 产图失败时任务失败
- workflow 文件包含 Playwright 安装步骤

测试分层：

- 单元测试：URL 生成、仓储逻辑、模板数据注入
- 集成测试：DailyJobService 产出 JSON 和 PNG

如果环境允许，可增加真实 Playwright 渲染测试；否则先以假渲染器做编排验证。

## 十二、技术选型

M2 推荐新增依赖：

- `playwright`

不新增模板引擎，优先使用标准库字符串替换或最轻量模板拼装方式。

## 十三、演进约束

M2 不重构 M1 的抓取和解析边界，只在其后增加渲染与静态产物管理能力。

如果后续进入 M3，再考虑：

- git 自动提交发布
- 图片优化与压缩
- 更复杂的视觉模板
- 自定义域名或多 CDN 回填

## 自检结果

检查项结论：

- 范围明确限定在图片生成和 `image` 回填
- 已明确 JSON 补图路径，避免将来回填必须重抓文章
- 已明确静态资源仓储职责，避免编排层承担路径和 URL 逻辑
- 未提前引入 M3 的自动发布能力
