# GitHub Pages 预览站设计

## 目标

为当前新闻静态产物增加一个可公开访问的预览页面，部署在 GitHub Pages。

该页面用于：

- 浏览已有日期的新闻图片
- 查看同一天对应的 JSON 内容
- 验证正式产物与数据是否一致

同时补充一个仅供本地开发使用的预览命令，方便在修改模板后快速查看渲染效果。

## 设计结论

线上预览站只展示正式产物，不在浏览器端实时重做模板渲染。

具体来说：

- GitHub Pages 页面默认展示 `static/images/YYYY-MM-DD.png`
- 页面同时读取并展示 `static/news/YYYY-MM-DD.json`
- 页面不在前端复刻 Python + Jinja2 + Playwright 的模板渲染逻辑

本地开发时，另提供一个本地预览命令，直接调用现有渲染链路生成预览图。

## 不采用浏览器端实时渲染的原因

当前正式图片的生成依赖：

- Python
- Jinja2
- Playwright
- 本地字体文件
- 现有模板上下文构建逻辑

如果在 GitHub Pages 前端再实现一套浏览器端模板渲染：

- 会复制第二套模板逻辑
- 会与正式产物逐步偏离
- 后续每次模板调整都要同步两份实现

这不符合当前项目已经建立起来的“单一模板来源”原则。

## 范围

本次只做以下内容：

1. GitHub Pages 静态预览站
2. Pages 所需的数据索引生成
3. GitHub Actions Pages 部署流程
4. 本地预览命令
5. 对应测试

本次不做：

1. 浏览器端实时模板渲染
2. 在线修改 JSON 后即时重绘图片
3. 在线编辑模板
4. 独立服务端预览站

## 架构

### 产物来源

正式数据仍然由现有流程生成：

- `static/news/YYYY-MM-DD.json`
- `static/images/YYYY-MM-DD.png`

### Pages 站点目录

新增静态站点目录，例如：

- `pages/index.html`
- `pages/app.js`
- `pages/styles.css`
- `pages/data/index.json`

其中：

- `pages/data/index.json` 作为预览页索引
- 页面通过索引定位可用日期，再加载对应 JSON 和 PNG

### 部署方式

新增 GitHub Actions workflow，在 `main` 更新后构建并部署 `pages/` 到 GitHub Pages。

该 workflow 不负责生成新闻数据本身，只负责：

1. 读取仓库现有 `static/news` 与 `static/images`
2. 生成 Pages 索引文件
3. 部署静态站点

## 页面结构

页面采用三栏或双栏响应式布局。

桌面端：

1. 左侧：日期列表
2. 中间：正式图片预览
3. 右侧：JSON 数据查看

移动端：

1. 顶部：日期切换
2. 中间：图片预览
3. 下方：JSON 查看

## 页面功能

### 日期浏览

- 显示所有可预览日期
- 默认打开最新日期
- 支持点击切换
- 支持上一天 / 下一天

### 图片预览

- 展示正式 PNG
- 图片链接来自仓库当前分支上的 `static/images`
- 页面不自行重绘模板

### JSON 查看

- 展示原始 JSON 结构
- 至少展示以下关键字段：
  - `date`
  - `title`
  - `publish_date`
  - `create_date`
  - `update_date`
  - `news`
  - `sources`
  - `quote`
  - `image`

### URL 状态

支持以 query 参数打开指定日期：

- `?date=2026-03-30`

这样可以直接分享某一天的预览链接。

## Pages 数据索引

新增一个索引生成步骤，输出例如：

```json
{
  "latest": "2026-03-30",
  "items": [
    {
      "date": "2026-03-26",
      "json_path": "../static/news/2026-03-26.json",
      "image_path": "../static/images/2026-03-26.png"
    }
  ]
}
```

索引只负责让前端知道有哪些日期、各自对应哪些静态文件。

前端不自行扫描目录。

## 本地预览工具

新增一个本地命令，用于开发时快速验证模板效果。

建议能力：

1. 指定某一天 JSON 文件
2. 使用现有渲染器重生成图片
3. 输出到临时路径或指定路径
4. 可选择保留 PNG 或生成临时 HTML 便于排查

这个工具只服务开发，不部署到 GitHub Pages。

## 文件规划

建议新增或修改如下文件：

- `pages/index.html`
- `pages/app.js`
- `pages/styles.css`
- `pages/data/index.json`（构建产物）
- `.github/workflows/pages-preview.yml`
- `app/entrypoints/preview_page_index.py` 或等价脚本
- `app/entrypoints/preview_render.py` 或等价脚本

是否采用上述具体文件名，可在实施阶段根据现有目录风格微调。

## 数据流

### Pages

1. 用户打开 GitHub Pages 站点
2. 前端加载 `pages/data/index.json`
3. 确定当前日期
4. 展示对应 PNG
5. 请求对应 JSON
6. 渲染 JSON 详情面板

### 本地预览

1. 开发者指定日期或 JSON 路径
2. 工具读取 JSON
3. 工具调用当前 `PlaywrightImageRenderer`
4. 输出预览图片

## 错误处理

### Pages

- 索引缺失：显示“预览数据不可用”
- JSON 缺失：保留图片区，JSON 区显示错误提示
- 图片缺失：显示占位提示，不阻断页面其余部分
- query 参数日期不存在：回退到最新日期

### 本地预览

- JSON 解析失败：直接报错退出
- 模板渲染失败：直接报错退出
- Playwright 启动失败：保留现有报错，不吞异常

## 测试策略

### 单元测试

- 索引生成器输出正确的最新日期和条目列表
- Pages 页面模板存在关键挂载点
- query 参数解析逻辑正确

### Workflow 契约测试

- 校验新增 Pages workflow 存在
- 校验 workflow 包含 Pages 部署关键步骤

### 本地预览测试

- 给定有效 JSON，能生成目标输出路径
- 路径参数错误时会失败

## 兼容性要求

- 不改变现有 `daily-fetch.yml` 的主流程职责
- 不改变现有正式 JSON / PNG 的生成方式
- 不影响现有 jsDelivr 访问地址
- Pages 只是新增预览入口，不替换当前 CDN 使用方式

## 实施顺序

1. 实现预览索引生成器
2. 实现 Pages 静态前端
3. 实现本地预览命令
4. 新增 Pages workflow
5. 补测试
6. 联调 GitHub Pages 部署

## 最终建议

采用“双层方案”：

- 线上：GitHub Pages 静态预览站，展示正式 PNG + JSON
- 本地：实时调用现有渲染链路的预览命令

这条路线最符合当前仓库结构，也最能避免模板逻辑分叉。
