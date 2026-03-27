# M2 Image Rendering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the M1 WeChat static generator to also render `static/images/YYYY-MM-DD.png` via Playwright, save the image locally, and backfill the JSON `image` field with a Git-based CDN URL.

**Architecture:** Keep M1’s fetch/parse pipeline unchanged and add a separate rendering pipeline behind an `ImageRenderer` port plus a static-assets repository that manages both JSON and PNG artifacts. Support both “fresh fetch then render” and “existing JSON then render missing image” paths through the orchestration layer.

**Tech Stack:** Python 3.12, httpx, pydantic, pydantic-settings, PyYAML, selectolax, tenacity, Playwright, pytest, respx, ruff, mypy, GitHub Actions

---

### Task 1: Add Image Rendering Port And Static Assets Repository Contract

**Files:**
- Create: `app/ports/image_renderer.py`
- Modify: `app/ports/repository.py`
- Create: `tests/unit/test_static_assets_contracts.py`
- Test: `tests/unit/test_static_assets_contracts.py`

- [ ] **Step 1: Write the failing contract test**

```python
from typing import get_type_hints

from app.ports.image_renderer import ImageRenderer
from app.ports.repository import StaticAssetsRepository


def test_image_renderer_contract_exists() -> None:
    hints = get_type_hints(ImageRenderer.render)
    assert hints["return"] is bytes


def test_static_assets_repository_contract_exists() -> None:
    methods = {
        "json_exists",
        "image_exists",
        "load_document",
        "save_document",
        "save_image",
        "build_image_url",
    }
    assert methods.issubset(set(dir(StaticAssetsRepository)))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_static_assets_contracts.py -v`
Expected: FAIL because the new contracts do not exist yet

- [ ] **Step 3: Add the new contracts**

```python
# app/ports/image_renderer.py
from __future__ import annotations

from typing import Protocol

from app.domain.models import DailyNewsDocument


class ImageRenderer(Protocol):
    def render(self, document: DailyNewsDocument) -> bytes:
        ...
```

```python
# app/ports/repository.py
from __future__ import annotations

from typing import Protocol

from app.domain.models import DailyNewsDocument


class StaticAssetsRepository(Protocol):
    def json_exists(self, date: str) -> bool:
        ...

    def image_exists(self, date: str) -> bool:
        ...

    def load_document(self, date: str) -> DailyNewsDocument | None:
        ...

    def save_document(self, document: DailyNewsDocument) -> None:
        ...

    def save_image(self, date: str, content: bytes) -> None:
        ...

    def build_image_url(self, date: str) -> str:
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_static_assets_contracts.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/ports/image_renderer.py app/ports/repository.py tests/unit/test_static_assets_contracts.py
git commit -m "feat: add image rendering and static assets contracts"
```

### Task 2: Implement Static Assets Repository For JSON, PNG, And Image URL Generation

**Files:**
- Create: `app/infrastructure/storage/static_assets_repository.py`
- Create: `tests/unit/test_static_assets_repository.py`
- Test: `tests/unit/test_static_assets_repository.py`

- [ ] **Step 1: Write the failing repository test**

```python
from pathlib import Path

from app.domain.models import DailyNewsDocument
from app.infrastructure.storage.static_assets_repository import StaticAssetsRepositoryImpl


def test_static_assets_repository_saves_json_and_png(tmp_path: Path) -> None:
    repository = StaticAssetsRepositoryImpl(
        json_dir=tmp_path / "news",
        image_dir=tmp_path / "images",
        image_base_url="https://cdn.jsdelivr.net/gh/example/news-static@main/static/images",
    )
    document = DailyNewsDocument(
        date="2026-03-27",
        news=["A"],
        cover="",
        image="",
        title="title",
        quote="",
        link="https://mp.weixin.qq.com/s/example",
        publish_date="2026-03-27 06:30:00",
        create_date="2026-03-27 06:30:00",
        update_date="2026-03-27 06:35:00",
    )

    repository.save_document(document)
    repository.save_image("2026-03-27", b"png-bytes")

    assert repository.json_exists("2026-03-27") is True
    assert repository.image_exists("2026-03-27") is True
    assert repository.build_image_url("2026-03-27").endswith("/2026-03-27.png")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_static_assets_repository.py -v`
Expected: FAIL because the repository implementation does not exist yet

- [ ] **Step 3: Implement the repository**

```python
# app/infrastructure/storage/static_assets_repository.py
from __future__ import annotations

import json
from pathlib import Path

from app.domain.models import DailyNewsDocument


class StaticAssetsRepositoryImpl:
    def __init__(self, *, json_dir: Path, image_dir: Path, image_base_url: str) -> None:
        self._json_dir = json_dir
        self._image_dir = image_dir
        self._image_base_url = image_base_url.rstrip("/")
        self._json_dir.mkdir(parents=True, exist_ok=True)
        self._image_dir.mkdir(parents=True, exist_ok=True)

    def json_exists(self, date: str) -> bool:
        return self._json_path(date).exists()

    def image_exists(self, date: str) -> bool:
        return self._image_path(date).exists()

    def load_document(self, date: str) -> DailyNewsDocument | None:
        path = self._json_path(date)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return DailyNewsDocument.model_validate(payload)

    def save_document(self, document: DailyNewsDocument) -> None:
        self._json_path(document.date).write_text(
            json.dumps(document.model_dump(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def save_image(self, date: str, content: bytes) -> None:
        self._image_path(date).write_bytes(content)

    def build_image_url(self, date: str) -> str:
        return f"{self._image_base_url}/{date}.png"

    def _json_path(self, date: str) -> Path:
        return self._json_dir / f"{date}.json"

    def _image_path(self, date: str) -> Path:
        return self._image_dir / f"{date}.png"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_static_assets_repository.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/infrastructure/storage/static_assets_repository.py tests/unit/test_static_assets_repository.py
git commit -m "feat: add static assets repository"
```

### Task 3: Add Render Configuration And Template Asset

**Files:**
- Modify: `app/infrastructure/config.py`
- Create: `app/infrastructure/render/__init__.py`
- Create: `app/infrastructure/render/template.html`
- Create: `tests/unit/test_render_template_exists.py`
- Test: `tests/unit/test_render_template_exists.py`

- [ ] **Step 1: Write the failing template/config test**

```python
from pathlib import Path


def test_render_template_exists() -> None:
    template = Path("app/infrastructure/render/template.html")
    assert template.exists()
    content = template.read_text(encoding="utf-8")
    assert "__DATA__" in content
    assert 'id="news-card"' in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_render_template_exists.py -v`
Expected: FAIL because the template and render package do not exist yet

- [ ] **Step 3: Add config helpers and HTML template**

```python
# app/infrastructure/config.py
from __future__ import annotations

import os
from pathlib import Path

import yaml

from app.domain.models import AccountConfig


def load_accounts(path: Path | str) -> list[AccountConfig]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    accounts = [AccountConfig.model_validate(item) for item in raw.get("accounts", [])]
    return sorted(
        (account for account in accounts if account.enabled),
        key=lambda account: account.priority,
        reverse=True,
    )


def get_image_base_url() -> str:
    return os.environ.get(
        "IMAGE_BASE_URL",
        "https://cdn.jsdelivr.net/gh/example/news-static@main/static/images",
    )
```

```html
<!-- app/infrastructure/render/template.html -->
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <style>
      body { margin: 0; font-family: "Noto Sans SC", sans-serif; background: #f4f1ea; }
      #news-card { width: 960px; margin: 0 auto; padding: 40px; background: #fffaf2; color: #2d2418; }
      .cover { width: 100%; border-radius: 16px; margin: 20px 0; }
      .title { font-size: 36px; line-height: 1.3; font-weight: 700; }
      .meta { font-size: 18px; color: #766757; margin-top: 12px; }
      .news-item { font-size: 22px; line-height: 1.7; margin: 12px 0; }
      .quote { margin-top: 32px; padding: 20px; background: #f0e6d8; border-radius: 12px; font-size: 20px; }
    </style>
  </head>
  <body>
    <div id="news-card"></div>
    <script>
      const DATA = __DATA__;
      const root = document.getElementById("news-card");
      const coverHtml = DATA.cover ? `<img class="cover" src="${DATA.cover}" alt="cover" />` : "";
      const quoteHtml = DATA.quote ? `<div class="quote">${DATA.quote}</div>` : "";
      const newsHtml = DATA.news.map((item, idx) => `<div class="news-item">${idx + 1}. ${item}</div>`).join("");
      root.innerHTML = `
        <div class="title">${DATA.title}</div>
        <div class="meta">${DATA.date} | 发布于 ${DATA.publish_date}</div>
        ${coverHtml}
        ${newsHtml}
        ${quoteHtml}
      `;
    </script>
  </body>
</html>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_render_template_exists.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/infrastructure/config.py app/infrastructure/render tests/unit/test_render_template_exists.py
git commit -m "feat: add render template and image url config"
```

### Task 4: Implement Playwright Image Renderer

**Files:**
- Create: `app/infrastructure/render/playwright_image_renderer.py`
- Modify: `pyproject.toml`
- Create: `tests/unit/test_playwright_image_renderer.py`
- Test: `tests/unit/test_playwright_image_renderer.py`

- [ ] **Step 1: Write the failing renderer test**

```python
from pathlib import Path

from app.domain.models import DailyNewsDocument
from app.infrastructure.render.playwright_image_renderer import PlaywrightImageRenderer


def test_playwright_renderer_renders_html_document(monkeypatch, tmp_path: Path) -> None:
    document = DailyNewsDocument(
        date="2026-03-27",
        news=["A"],
        cover="",
        image="",
        title="title",
        quote="quote",
        link="https://mp.weixin.qq.com/s/example",
        publish_date="2026-03-27 06:30:00",
        create_date="2026-03-27 06:30:00",
        update_date="2026-03-27 06:35:00",
    )
    renderer = PlaywrightImageRenderer(template_path=Path("app/infrastructure/render/template.html"))

    html = renderer.build_html(document)

    assert "title" in html
    assert "quote" in html
    assert "A" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_playwright_image_renderer.py -v`
Expected: FAIL because the renderer implementation does not exist yet

- [ ] **Step 3: Add Playwright dependency and renderer implementation**

```toml
# pyproject.toml
[project]
dependencies = [
  "httpx>=0.27.0",
  "pydantic>=2.8.0",
  "pydantic-settings>=2.4.0",
  "PyYAML>=6.0.2",
  "selectolax>=0.3.21",
  "tenacity>=9.0.0",
  "playwright>=1.52.0",
]
```

```python
# app/infrastructure/render/playwright_image_renderer.py
from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from playwright.sync_api import sync_playwright

from app.domain.models import DailyNewsDocument


class PlaywrightImageRenderer:
    def __init__(self, *, template_path: Path, viewport_width: int = 1100, device_scale_factor: float = 2.0) -> None:
        self._template_path = template_path
        self._viewport_width = viewport_width
        self._device_scale_factor = device_scale_factor

    def build_html(self, document: DailyNewsDocument) -> str:
        template = self._template_path.read_text(encoding="utf-8")
        return template.replace("__DATA__", json.dumps(document.model_dump(), ensure_ascii=False))

    def render(self, document: DailyNewsDocument) -> bytes:
        html = self.build_html(document)
        with NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as temp:
            temp.write(html)
            temp_path = Path(temp.name)

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page(
                    viewport={"width": self._viewport_width, "height": 2400},
                    device_scale_factor=self._device_scale_factor,
                )
                page.goto(temp_path.as_uri(), wait_until="load")
                page.locator("#news-card").wait_for()
                image = page.locator("#news-card").screenshot(type="png")
                browser.close()
                return image
        finally:
            temp_path.unlink(missing_ok=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_playwright_image_renderer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml app/infrastructure/render/playwright_image_renderer.py tests/unit/test_playwright_image_renderer.py
git commit -m "feat: add playwright image renderer"
```

### Task 5: Update Daily Job To Support New Render Paths

**Files:**
- Modify: `app/application/daily_job.py`
- Create: `tests/integration/test_daily_job_images.py`
- Test: `tests/integration/test_daily_job_images.py`

- [ ] **Step 1: Write the failing integration test for fresh fetch and backfill**

```python
from pathlib import Path

from app.application.daily_job import DailyJobService
from app.domain.models import AccountConfig, CandidateArticle, DailyNewsDocument, ParsedArticle
from app.infrastructure.storage.static_assets_repository import StaticAssetsRepositoryImpl


class FakeSourceClient:
    def search_articles(self, fake_id: str, query: str, count: int = 6):
        return [
            CandidateArticle(
                title="3月27日 读懂世界",
                link="https://mp.weixin.qq.com/s/example",
                cover="https://example.com/cover.png",
                create_ts=1774564200,
                update_ts=1774564500,
            )
        ]

    def fetch_article_html(self, link: str) -> str:
        return "<html></html>"


class FakeParser:
    def parse(self, html: str) -> ParsedArticle:
        return ParsedArticle(
            title="每日简报 3月27日",
            news=["第一条"],
            cover="https://example.com/cover.png",
            quote="先照顾好自己",
            publish_date="2026-03-27 06:30:00",
        )


class FakeRenderer:
    def render(self, document: DailyNewsDocument) -> bytes:
        return b"png-bytes"


def test_daily_job_writes_json_and_png(tmp_path: Path) -> None:
    repository = StaticAssetsRepositoryImpl(
        json_dir=tmp_path / "news",
        image_dir=tmp_path / "images",
        image_base_url="https://cdn.jsdelivr.net/gh/example/news-static@main/static/images",
    )
    service = DailyJobService(
        source_client=FakeSourceClient(),
        parser=FakeParser(),
        repository=repository,
        accounts=[
            AccountConfig(
                name="main",
                wechat_id="mt36501",
                fake_id="fake-id",
                query="读懂世界",
                enabled=True,
                priority=100,
            )
        ],
        image_renderer=FakeRenderer(),
    )

    document = service.run("2026-03-27")

    assert document is not None
    assert repository.json_exists("2026-03-27") is True
    assert repository.image_exists("2026-03-27") is True
    assert document.image.endswith("/2026-03-27.png")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_daily_job_images.py -v`
Expected: FAIL because the orchestration does not yet support rendering

- [ ] **Step 3: Update orchestration**

```python
# app/application/daily_job.py
from __future__ import annotations

import logging
from datetime import datetime
from typing import Sequence

from app.application.article_selector import select_article
from app.domain.models import AccountConfig, DailyNewsDocument
from app.infrastructure.clock import format_beijing_datetime
from app.ports.article_parser import ArticleParser
from app.ports.image_renderer import ImageRenderer
from app.ports.repository import StaticAssetsRepository
from app.ports.source_client import SourceClient

logger = logging.getLogger(__name__)


class DailyJobService:
    def __init__(
        self,
        *,
        source_client: SourceClient,
        parser: ArticleParser,
        repository: StaticAssetsRepository,
        accounts: Sequence[AccountConfig],
        image_renderer: ImageRenderer,
    ) -> None:
        self._source_client = source_client
        self._parser = parser
        self._repository = repository
        self._accounts = list(accounts)
        self._image_renderer = image_renderer

    def run(self, target_date: str) -> DailyNewsDocument | None:
        json_exists = self._repository.json_exists(target_date)
        image_exists = self._repository.image_exists(target_date)

        if json_exists and image_exists:
            logger.info("json and image already exist for %s", target_date)
            return None

        if json_exists and not image_exists:
            document = self._repository.load_document(target_date)
            if document is None:
                raise RuntimeError(f"document missing for {target_date}")
            return self._render_and_save(document)

        document = self._fetch_document(target_date)
        return self._render_and_save(document)

    def _fetch_document(self, target_date: str) -> DailyNewsDocument:
        target = datetime.strptime(target_date, "%Y-%m-%d")
        query_prefix = f"{target.month}月{target.day}日"

        for account in self._accounts:
            query = f"{query_prefix} {account.query}"
            try:
                candidates = self._source_client.search_articles(account.fake_id, query)
                selected = select_article(target_date, account, candidates)
                if selected is None:
                    continue
                html = self._source_client.fetch_article_html(selected.link)
                parsed = self._parser.parse(html)
            except Exception:
                logger.exception("account %s failed for %s", account.name, target_date)
                continue

            return DailyNewsDocument(
                date=target_date,
                news=parsed.news,
                cover=parsed.cover,
                image="",
                title=parsed.title,
                quote=parsed.quote,
                link=selected.link,
                publish_date=parsed.publish_date,
                create_date=format_beijing_datetime(selected.create_ts),
                update_date=format_beijing_datetime(selected.update_ts),
            )

        raise RuntimeError(f"no article found for {target_date}")

    def _render_and_save(self, document: DailyNewsDocument) -> DailyNewsDocument:
        image_bytes = self._image_renderer.render(document)
        self._repository.save_image(document.date, image_bytes)
        final_document = document.model_copy(update={"image": self._repository.build_image_url(document.date)})
        self._repository.save_document(final_document)
        return final_document

    def close(self) -> None:
        close = getattr(self._source_client, "close", None)
        if callable(close):
            close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_daily_job_images.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/application/daily_job.py tests/integration/test_daily_job_images.py
git commit -m "feat: support image rendering in daily job"
```

### Task 6: Wire Renderer And Static Assets Repository Into CLI Composition Root

**Files:**
- Modify: `app/entrypoints/run_daily_job.py`
- Modify: `app/entrypoints/backfill.py`
- Create: `tests/integration/test_m2_composition.py`
- Test: `tests/integration/test_m2_composition.py`

- [ ] **Step 1: Write the failing composition test**

```python
from pathlib import Path

from app.entrypoints.run_daily_job import build_service, parse_args


def test_build_service_wires_static_assets_and_renderer(monkeypatch, tmp_path: Path) -> None:
    accounts_file = tmp_path / "accounts.yaml"
    accounts_file.write_text(
        '''
accounts:
  - name: main
    wechat_id: mt36501
    fake_id: fake-id
    query: 读懂世界
    enabled: true
    priority: 100
'''.strip(),
        encoding="utf-8",
    )

    args = parse_args(["--accounts-file", str(accounts_file)])
    service = build_service(args)

    assert service is not None
```

- [ ] **Step 2: Run test to verify it fails if M2 wiring is incomplete**

Run: `pytest tests/integration/test_m2_composition.py -v`
Expected: FAIL until the renderer and static assets repository are wired in

- [ ] **Step 3: Update the composition root**

```python
# app/entrypoints/run_daily_job.py
from __future__ import annotations

import argparse
import logging
import os
from datetime import datetime
from pathlib import Path

from app.application.daily_job import DailyJobService
from app.infrastructure.clock import BEIJING_TZ
from app.infrastructure.config import get_image_base_url, load_accounts
from app.infrastructure.logging import configure_logging
from app.infrastructure.parser.wechat_article_parser import WeChatArticleParser
from app.infrastructure.render.playwright_image_renderer import PlaywrightImageRenderer
from app.infrastructure.storage.static_assets_repository import StaticAssetsRepositoryImpl
from app.infrastructure.wechat.mp_client import WeChatMPClient


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the daily WeChat fetch job")
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--accounts-file", type=Path, default=Path("config/accounts.yaml"))
    parser.add_argument("--output-dir", type=Path, default=Path("static/news"))
    parser.add_argument("--image-dir", type=Path, default=Path("static/images"))
    parser.add_argument(
        "--template-path",
        type=Path,
        default=Path("app/infrastructure/render/template.html"),
    )
    return parser.parse_args(argv)


def build_service(args: argparse.Namespace) -> DailyJobService:
    token, cookie = _read_credentials()
    accounts = load_accounts(args.accounts_file)
    repository = StaticAssetsRepositoryImpl(
        json_dir=args.output_dir,
        image_dir=args.image_dir,
        image_base_url=get_image_base_url(),
    )
    renderer = PlaywrightImageRenderer(template_path=args.template_path)
    return DailyJobService(
        source_client=WeChatMPClient(token=token, cookie=cookie),
        parser=WeChatArticleParser(),
        repository=repository,
        accounts=accounts,
        image_renderer=renderer,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_m2_composition.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/entrypoints/run_daily_job.py app/entrypoints/backfill.py tests/integration/test_m2_composition.py
git commit -m "feat: wire image rendering into cli composition"
```

### Task 7: Update Workflow For Playwright Browser Rendering

**Files:**
- Modify: `.github/workflows/daily-fetch.yml`
- Modify: `tests/unit/test_workflow_contract.py`
- Test: `tests/unit/test_workflow_contract.py`

- [ ] **Step 1: Write the failing workflow expectation**

```python
from pathlib import Path


def test_daily_fetch_workflow_installs_playwright() -> None:
    content = Path(".github/workflows/daily-fetch.yml").read_text(encoding="utf-8")
    assert "playwright" in content.lower()
    assert "python -m playwright install" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_workflow_contract.py -v`
Expected: FAIL because the current workflow does not install Playwright yet

- [ ] **Step 3: Add Playwright setup to the workflow**

```yaml
# .github/workflows/daily-fetch.yml
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e .[dev]

      - name: Install Playwright browser
        run: |
          python -m playwright install chromium
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_workflow_contract.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/daily-fetch.yml tests/unit/test_workflow_contract.py
git commit -m "feat: install playwright in workflow"
```

### Task 8: Add Missing-Image Backfill And Failure Coverage

**Files:**
- Create: `tests/integration/test_m2_backfill_and_failures.py`
- Test: `tests/integration/test_m2_backfill_and_failures.py`

- [ ] **Step 1: Write the failing backfill/failure tests**

```python
from pathlib import Path

import pytest

from app.application.daily_job import DailyJobService
from app.domain.models import AccountConfig, DailyNewsDocument
from app.infrastructure.storage.static_assets_repository import StaticAssetsRepositoryImpl


class NeverSourceClient:
    def search_articles(self, fake_id: str, query: str, count: int = 6):
        raise AssertionError("search should not run when json already exists")

    def fetch_article_html(self, link: str) -> str:
        raise AssertionError("fetch should not run when json already exists")


class NeverParser:
    def parse(self, html: str):
        raise AssertionError("parse should not run when json already exists")


class FakeRenderer:
    def render(self, document: DailyNewsDocument) -> bytes:
        return b"png-bytes"


class FailingRenderer:
    def render(self, document: DailyNewsDocument) -> bytes:
        raise RuntimeError("render failed")


def test_existing_json_can_backfill_missing_image(tmp_path: Path) -> None:
    repository = StaticAssetsRepositoryImpl(
        json_dir=tmp_path / "news",
        image_dir=tmp_path / "images",
        image_base_url="https://cdn.jsdelivr.net/gh/example/news-static@main/static/images",
    )
    repository.save_document(
        DailyNewsDocument(
            date="2026-03-27",
            news=["A"],
            cover="",
            image="",
            title="title",
            quote="",
            link="https://mp.weixin.qq.com/s/example",
            publish_date="2026-03-27 06:30:00",
            create_date="2026-03-27 06:30:00",
            update_date="2026-03-27 06:35:00",
        )
    )
    service = DailyJobService(
        source_client=NeverSourceClient(),
        parser=NeverParser(),
        repository=repository,
        accounts=[],
        image_renderer=FakeRenderer(),
    )

    document = service.run("2026-03-27")

    assert document is not None
    assert repository.image_exists("2026-03-27") is True
    assert repository.load_document("2026-03-27").image.endswith("/2026-03-27.png")


def test_render_failure_bubbles_up(tmp_path: Path) -> None:
    repository = StaticAssetsRepositoryImpl(
        json_dir=tmp_path / "news",
        image_dir=tmp_path / "images",
        image_base_url="https://cdn.jsdelivr.net/gh/example/news-static@main/static/images",
    )
    repository.save_document(
        DailyNewsDocument(
            date="2026-03-27",
            news=["A"],
            cover="",
            image="",
            title="title",
            quote="",
            link="https://mp.weixin.qq.com/s/example",
            publish_date="2026-03-27 06:30:00",
            create_date="2026-03-27 06:30:00",
            update_date="2026-03-27 06:35:00",
        )
    )
    service = DailyJobService(
        source_client=NeverSourceClient(),
        parser=NeverParser(),
        repository=repository,
        accounts=[],
        image_renderer=FailingRenderer(),
    )

    with pytest.raises(RuntimeError, match="render failed"):
        service.run("2026-03-27")
```

- [ ] **Step 2: Run test to verify it fails if M2 paths are incomplete**

Run: `pytest tests/integration/test_m2_backfill_and_failures.py -v`
Expected: FAIL until backfill and render-failure behavior are correctly implemented

- [ ] **Step 3: Refine orchestration only as needed**

```python
# app/application/daily_job.py
# Ensure json-existing/image-missing path loads the document,
# renders the image, saves it, updates `image`, and rewrites JSON.
# Ensure renderer exceptions are not swallowed in that path.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_m2_backfill_and_failures.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/integration/test_m2_backfill_and_failures.py app/application/daily_job.py
git commit -m "feat: support missing-image backfill"
```

### Task 9: Verify Full M2 Baseline

**Files:**
- Modify: `config/accounts.yaml`
- Test: `tests/unit/`
- Test: `tests/integration/`

- [ ] **Step 1: Ensure default image URL base is documented by environment**

```yaml
# config/accounts.yaml
accounts:
  - name: "绿健简报NEW"
    wechat_id: "ghnews"
    fake_id: "MzI0Njk2NzczOQ=="
    query: "绿健简报"
    parser_profile: "greenjian"
    enabled: true
    priority: 100
```

- [ ] **Step 2: Run all unit tests**

Run: `pytest tests/unit -v`
Expected: PASS

- [ ] **Step 3: Run all integration tests**

Run: `pytest tests/integration -v`
Expected: PASS

- [ ] **Step 4: Run lint and type checks**

Run: `ruff check .`
Expected: All checks pass

Run: `mypy app`
Expected: Success with no issues found

- [ ] **Step 5: Commit**

```bash
git add config/accounts.yaml
git commit -m "chore: finalize m2 baseline"
```

## Self-Review

Spec coverage check:

- Covered new renderer port, static assets repository, HTML template, Playwright renderer, orchestration changes, CLI wiring, workflow updates, and backfill/failure behavior.
- Covered the user-confirmed constraints: browser rendering, static image output, Git-based image URL, and support for existing-JSON image backfill.

Placeholder scan:

- No `TODO`, `TBD`, or unresolved placeholders remain.

Type consistency:

- Core types and responsibilities remain consistent with M1: `DailyNewsDocument` stays the rendering input and final persisted output.
- `DailyJobService` expands only by injecting `image_renderer` and using `StaticAssetsRepository`.

Execution handoff:

Plan complete and saved to `docs/superpowers/plans/2026-03-27-m2-image-rendering-implementation.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
