# M1 WeChat JSON Static Generator Design

**目标**

构建一个 Python 静态生产服务，通过 GitHub Actions 定时抓取微信公众号日报文章，解析正文新闻列表并生成 `static/60s/YYYY-MM-DD.json`。M1 仅交付 JSON，不生成图片，不自动提交 git，不引入 LLM。

**范围**

M1 包含：

- 基于 GitHub Actions 的定时任务与手动回填入口
- 基于微信公众号后台接口的候选文章抓取
- 基于规则的文章正文解析
- JSON 文件落盘到 `static/news/`
- 可测试、分层、配置驱动的 Python 项目结构

M1 不包含：

- PNG 图片渲染
- git 自动提交与推送
- LLM 解析兜底
- 对外 HTTP API 服务
- 数据库存储

## 一、交付模型

该项目不是在线 API 服务，而是“离线静态内容生产器”。

执行结果是：

- GitHub Actions 在北京时间定时触发
- Python 任务抓取当天目标文章
- 解析后写入本地 JSON 文件
- 后续版本再决定是否提交仓库并通过 CDN 对外提供访问

M1 保持输出文件稳定，不引入额外发布机制。

## 二、数据契约

输出路径：

- `static/news/YYYY-MM-DD.json`

输出 JSON 契约：

```json
{
  "date": "2026-03-27",
  "news": [
    "新闻 1",
    "新闻 2"
  ],
  "cover": "https://mmbiz.qpic.cn/xxx",
  "image": "",
  "title": "2026年3月27日，星期五，农历二月初九，早安",
  "quote": "不要先说话后做事，要先做事后说话。想做的事做成了，还可以不说话。 --陈忠实",
  "link": "https://mp.weixin.qq.com/s/xxxxx",
  "publish_date": "2026-03-27 00:00:35",
  "create_date": "2026-03-27 06:30:00",
  "update_date": "2026-03-27 06:35:00"
}
```

字段规则：

- `date`：目标日期，格式 `YYYY-MM-DD`
- `news`：正文编号新闻列表，不能为空
- `cover`：文章封面图 URL，允许空字符串但优先提取
- `image`：M1 固定为空字符串
- `title`：公众号文章标题，不能为空
- `quote`：文末“心语 / 每日一句 / 微语 / 金句”，允许空字符串
- `link`：文章链接，不能为空
- `publish_date`：公众号文章发布日期时间，格式 `yyyy-MM-dd HH:mm:ss`，时区为北京时间
- `create_date`：微信接口中的文章创建时间，格式 `yyyy-MM-dd HH:mm:ss`，时区为北京时间
- `update_date`：微信接口中的文章更新时间，格式 `yyyy-MM-dd HH:mm:ss`，时区为北京时间

## 三、配置策略

公众号来源不写死在代码里，放在独立配置文件中。

配置文件路径：

- `config/accounts.yaml`

示例：

```yaml
accounts:
  - name: "绿健简报NEW"
    wechat_id: "ghnews"
    fake_id: "MzI0Njk2NzczOQ=="
    query: "绿健简报"
    parser_profile: "greenjian"
    enabled: true
    priority: 100
```

配置原则：

- 只读取 `enabled: true` 的账号
- 按 `priority` 从高到低尝试
- 单个账号配置变更不影响业务代码

## 四、架构设计

M1 采用单仓库、分层架构，避免脚本式堆叠逻辑。

建议目录：

```text
news-static/
  app/
    entrypoints/
      run_daily_job.py
      backfill.py
    application/
      daily_job.py
      article_selector.py
    domain/
      models.py
    ports/
      source_client.py
      article_parser.py
      repository.py
    infrastructure/
      config.py
      logging.py
      clock.py
      wechat/
        mp_client.py
        account_loader.py
      parser/
        wechat_article_parser.py
      storage/
        local_json_repository.py
  config/
    accounts.yaml
  static/
    60s/
  tests/
    unit/
    integration/
    fixtures/
  .github/workflows/
    daily-fetch.yml
  pyproject.toml
```

职责边界：

- `entrypoints`：CLI 参数、退出码、异常边界
- `application`：业务编排与文章选择
- `domain`：纯数据模型
- `ports`：抽象接口
- `infrastructure/wechat`：微信后台接口访问
- `infrastructure/parser`：HTML 规则解析
- `infrastructure/storage`：JSON 文件读写

## 五、核心流程

每日任务流程：

1. 计算目标日期，默认使用 `Asia/Shanghai` 的当天日期
2. 检查 `static/news/<date>.json` 是否存在
3. 若已存在，则任务成功退出
4. 读取账号配置并按优先级遍历
5. 调微信后台接口搜索候选文章
6. 依据标题关键词与日期规则选出目标文章
7. 下载目标文章 HTML
8. 解析 HTML，提取 `title`、`news`、`cover`、`quote`、`publish_date`
9. 结合微信接口元数据生成最终 JSON
10. 执行 schema 校验
11. 写入 `static/news/<date>.json`

## 六、文章选择规则

目标文章选择规则独立封装，不放进抓取客户端。

首版规则：

- 标题必须包含目标日期对应的“X月Y日”
- 标题必须包含账号配置中的 `query`
- 文章更新时间对应的年月必须与目标日期一致
- 候选文章按账号优先级顺序处理
- 同一账号只取第一个满足条件的候选文章

如果所有账号均未找到目标文章，则任务失败。

## 七、HTML 解析策略

M1 不使用 LLM，仅使用规则解析。

解析目标：

- `title`
- `cover`
- `news`
- `quote`
- `publish_date`

解析原则：

- 优先从文章主内容区域提取
- `news` 仅保留正文编号新闻项，不混入文末金句
- 去掉序号、无意义前后缀、空白噪声和广告尾巴
- `quote` 解析失败时写空字符串，不阻断任务
- `news` 解析为空时视为失败

为保证可维护性，规则解析器必须对固定 HTML fixture 做单测，而不是只在联调时验证。

## 八、失败策略

以下情况任务失败：

- 微信凭证失效
- 微信接口请求失败且超过重试次数
- 所有账号都未找到当天文章
- 找到文章但正文新闻列表为空
- 输出数据不满足 JSON 契约

以下情况不阻断产出：

- `quote` 缺失，写空字符串
- `cover` 缺失，写空字符串

## 九、时间规则

所有时间统一转换为北京时间字符串，格式：

- `yyyy-MM-dd HH:mm:ss`

适用字段：

- `publish_date`
- `create_date`
- `update_date`

日期字段 `date` 单独保持为：

- `YYYY-MM-DD`

## 十、测试策略

M1 最少覆盖以下测试：

- 账号配置加载测试
- 文章选择规则测试
- HTML fixture 解析测试
- 已存在 JSON 时的跳过测试
- 微信认证失败测试
- “所有账号均未命中”失败测试
- CLI 指定日期运行测试

测试分层：

- 单元测试：选择器、解析器、格式化工具
- 集成测试：日任务编排、文件产出

## 十一、GitHub Actions 设计

workflow 只负责运行，不承载业务逻辑。

M1 workflow 职责：

- checkout 仓库
- setup Python
- 安装依赖
- 设置时区和环境变量
- 运行每日任务

M1 暂不包含：

- git commit
- git push
- 图片相关缓存

支持两种触发方式：

- 定时触发
- `workflow_dispatch` 手动指定日期回填

## 十二、技术选型

推荐依赖：

- Python 3.12
- `httpx`
- `pydantic`
- `pydantic-settings`
- `PyYAML`
- `selectolax` 或 `beautifulsoup4 + lxml`
- `tenacity`
- `pytest`
- `respx`
- `ruff`
- `mypy`

M1 不引入 Playwright，因为还没有图片渲染需求。

## 十三、后续演进

M2 开始新增：

- HTML/CSS 模板或浏览器截图渲染
- `static/images/YYYY-MM-DD.png`
- `image` 字段真实回填

M3 再考虑：

- git 自动提交与推送
- 静态站点/CDN 发布
- LLM 兜底解析

## 自检结果

检查项结论：

- 规格覆盖了 M1 的输入、输出、目录、流程、失败规则和测试要求
- 无 `TODO`、`TBD`、占位性条目
- 时间格式、失败策略、`quote` 缺失行为与对话结论一致
- 范围控制在单一里程碑内，没有提前混入 M2/M3 能力
