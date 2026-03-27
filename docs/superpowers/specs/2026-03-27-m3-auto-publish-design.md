# M3 Auto Publish Design

**目标**

在 M2 的基础上，为每日新闻静态生成器增加 GitHub Actions 自动发布能力。任务成功并产生静态产物变更后，workflow 自动提交并 push 到当前仓库主分支。

**范围**

M3 包含：

- Python 任务输出结构化运行结果
- workflow 基于运行结果决定是否提交与推送
- 自动 commit message 固定化
- GitHub Actions 并发控制与发布摘要

M3 不包含：

- PR 模式
- 发布分支
- 自动回滚
- 多仓库同步
- tag / release
- 人工审批流

## 一、交付模型

M3 仍然是单仓库静态生产器。

新的闭环为：

1. workflow 定时运行抓取任务
2. Python 任务生成或补齐静态产物
3. Python 任务输出结构化状态
4. workflow 根据状态判断是否发布
5. 若有变更则 commit 并 push 回当前仓库主分支

## 二、发布边界

M3 只做当前仓库主分支自动推送。

提交范围只包含静态产物：

- `static/news/*.json`
- `static/images/*.png`

M3 不发布：

- `docs/`
- `tests/`
- `app/`
- 其他配置文件

## 三、提交信息

M3 的 commit message 固定为：

```text
actions:news:update YYYY-MM-DD assets
```

示例：

```text
actions:news:update 2026-03-27 assets
```

## 四、结果模型

M3 不让 workflow 从业务行为反推状态，而是由 Python 任务显式输出运行结果。

建议结果字段：

- `status`
- `target_date`

`status` 允许值：

- `skipped`
- `updated`
- `backfilled_image`

含义：

- `skipped`：JSON 和 PNG 已存在，无需修改
- `updated`：新抓取并产出 JSON 与 PNG
- `backfilled_image`：JSON 已存在，仅补 PNG 并回填 `image`

Python 层不需要输出 `failed` 状态；失败直接通过非零退出码交给 workflow 处理。

## 五、职责分离

M3 的核心原则是：

- Python 决定“这次运行产生了什么业务结果”
- workflow 决定“是否执行 git commit / push”

这意味着：

- 业务层不执行 git 命令
- workflow 不判断文章抓取逻辑
- workflow 只根据运行结果与工作区 diff 做发布决策

## 六、Python 侧改动

M3 需要在应用层和入口层新增一个轻量结果对象。

建议：

- `DailyJobService.run()` 返回 `JobRunResult`
- `JobRunResult` 至少包含：
  - `status`
  - `target_date`
  - `document` 可选

入口层负责：

- 调用 `DailyJobService`
- 捕获结果
- 在 GitHub Actions 环境中写入 `$GITHUB_OUTPUT`

写出内容示例：

```text
status=updated
target_date=2026-03-27
```

## 七、workflow 发布流程

M3 workflow 流程：

1. checkout 仓库
2. setup Python
3. 安装依赖
4. 安装 Playwright
5. 运行每日任务，并输出 `status` 与 `target_date`
6. 若 `status != skipped`：
   - 配置 git 用户
   - `git add static/news static/images`
   - 用固定格式生成 commit message
   - 若工作区确实有 diff，则 commit 并 push
7. 生成 step summary

workflow 保留 `git status --porcelain` 作为双保险，但不替代 Python 的业务结果。

## 八、并发控制

为避免同一分支上多个 workflow 同时 push，M3 workflow 必须启用并发控制。

建议：

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: false
```

## 九、失败策略

以下情况不进入发布：

- Python 任务非零退出
- `status=skipped`
- Python 声称有更新，但 `git status --porcelain` 为空

以下情况视为 workflow 失败：

- `git commit` 失败
- `git push` 失败

## 十、测试策略

M3 最少覆盖：

- `DailyJobService.run()` 不同状态的结果测试
- CLI 入口写出结果的测试
- workflow 文件包含 concurrency、git 用户设置、发布步骤
- `skipped` 状态下 workflow 不应进入发布分支的契约测试

## 十一、实现约束

M3 不重构 M1/M2 的抓取、解析、渲染逻辑，只在其外增加结果表达与 workflow 发布步骤。

Git 相关逻辑优先放在 workflow，不新增复杂的 Python git 封装。

## 十二、自检结果

检查项结论：

- 已明确 Python 与 workflow 的职责边界
- 已明确 commit message 格式
- 已明确跳过发布与失败发布的规则
- 范围保持在“自动 commit 并 push 当前主分支”，未提前引入 PR / release 等额外机制
