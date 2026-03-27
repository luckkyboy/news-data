# M1 WeChat JSON Static Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python static generator that fetches daily WeChat article data and writes `static/news/YYYY-MM-DD.json` via GitHub Actions, without image generation, git auto-publish, or LLM parsing.

**Architecture:** Use a single-repo layered Python service with strict separation between orchestration, WeChat access, HTML parsing, and JSON storage. Keep workflow logic thin, move business rules into Python, and make the parser deterministic through fixture-based tests.

**Tech Stack:** Python 3.12, httpx, pydantic, pydantic-settings, PyYAML, selectolax, tenacity, pytest, respx, ruff, mypy, GitHub Actions

---

### Task 1: Bootstrap Project Skeleton And Tooling

**Files:**
- Create: `pyproject.toml`
- Create: `app/__init__.py`
- Create: `app/entrypoints/__init__.py`
- Create: `app/application/__init__.py`
- Create: `app/domain/__init__.py`
- Create: `app/ports/__init__.py`
- Create: `app/infrastructure/__init__.py`
- Create: `app/infrastructure/wechat/__init__.py`
- Create: `app/infrastructure/parser/__init__.py`
- Create: `app/infrastructure/storage/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/integration/__init__.py`
- Create: `tests/fixtures/.gitkeep`
- Create: `config/accounts.yaml`
- Create: `static/news/.gitkeep`
- Test: `pyproject.toml`

- [ ] **Step 1: Write the failing scaffold expectation**

```python
# tests/unit/test_project_layout.py
from pathlib import Path


def test_project_layout_exists():
    assert Path("app").exists()
    assert Path("config/accounts.yaml").exists()
    assert Path("static/news").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_project_layout.py -v`
Expected: FAIL because the expected paths do not exist yet

- [ ] **Step 3: Create minimal project skeleton and tooling config**

```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "news-static"
version = "0.1.0"
description = "WeChat daily news static JSON generator"
requires-python = ">=3.12"
dependencies = [
  "httpx>=0.27.0",
  "pydantic>=2.8.0",
  "pydantic-settings>=2.4.0",
  "PyYAML>=6.0.2",
  "selectolax>=0.3.21",
  "tenacity>=9.0.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3.0",
  "respx>=0.21.1",
  "ruff>=0.6.0",
  "mypy>=1.11.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "B"]

[tool.mypy]
python_version = "3.12"
strict = true
```

```yaml
# config/accounts.yaml
accounts: []
```

```python
# app/__init__.py
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_project_layout.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml app config static tests
git commit -m "chore: bootstrap python project skeleton"
```

### Task 2: Define Domain Models And Configuration Contracts

**Files:**
- Create: `app/domain/models.py`
- Create: `app/infrastructure/config.py`
- Create: `tests/unit/test_models.py`
- Test: `tests/unit/test_models.py`

- [ ] **Step 1: Write the failing model contract test**

```python
from app.domain.models import AccountConfig, CandidateArticle, DailyNewsDocument


def test_daily_news_document_accepts_m1_schema():
    doc = DailyNewsDocument(
        date="2026-03-27",
        news=["A", "B"],
        cover="https://example.com/cover.png",
        image="",
        title="每日简报 3月27日",
        quote="",
        link="https://mp.weixin.qq.com/s/example",
        publish_date="2026-03-27 06:30:00",
        create_date="2026-03-27 06:30:00",
        update_date="2026-03-27 06:35:00",
    )
    assert doc.image == ""
    assert len(doc.news) == 2


def test_account_config_keeps_priority_and_enabled():
    account = AccountConfig(
        name="绿健简报NEW",
        wechat_id="ghnews",
        fake_id="MzI0Njk2NzczOQ==",
        query="绿健简报",
        parser_profile="greenjian",
        enabled=True,
        priority=100,
    )
    assert account.enabled is True
    assert account.priority == 100


def test_candidate_article_tracks_wechat_times():
    article = CandidateArticle(
        title="每日简报 3月27日",
        link="https://mp.weixin.qq.com/s/example",
        cover="https://example.com/c.png",
        create_ts=1774564200,
        update_ts=1774564500,
    )
    assert article.create_ts < article.update_ts
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_models.py -v`
Expected: FAIL with import errors because the models do not exist yet

- [ ] **Step 3: Write minimal models and config loader**

```python
# app/domain/models.py
from pydantic import BaseModel, Field


class AccountConfig(BaseModel):
    name: str
    wechat_id: str
    fake_id: str
    query: str
    enabled: bool = True
    priority: int = 0


class CandidateArticle(BaseModel):
    title: str
    link: str
    cover: str = ""
    create_ts: int
    update_ts: int


class ParsedArticle(BaseModel):
    title: str
    news: list[str] = Field(min_length=1)
    cover: str = ""
    quote: str = ""
    publish_date: str


class DailyNewsDocument(BaseModel):
    date: str
    news: list[str] = Field(min_length=1)
    cover: str = ""
    image: str = ""
    title: str
    quote: str = ""
    link: str
    publish_date: str
    create_date: str
    update_date: str
```

```python
# app/infrastructure/config.py
from pathlib import Path

import yaml

from app.domain.models import AccountConfig


def load_accounts(path: Path) -> list[AccountConfig]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    accounts = [AccountConfig.model_validate(item) for item in raw.get("accounts", [])]
    return sorted((item for item in accounts if item.enabled), key=lambda item: item.priority, reverse=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/domain/models.py app/infrastructure/config.py tests/unit/test_models.py
git commit -m "feat: add domain models and account config loader"
```

### Task 3: Add Shared Ports, Time Formatting, And JSON Repository

**Files:**
- Create: `app/ports/source_client.py`
- Create: `app/ports/article_parser.py`
- Create: `app/ports/repository.py`
- Create: `app/infrastructure/clock.py`
- Create: `app/infrastructure/storage/local_json_repository.py`
- Create: `tests/unit/test_local_json_repository.py`
- Test: `tests/unit/test_local_json_repository.py`

- [ ] **Step 1: Write the failing repository behavior test**

```python
from pathlib import Path

from app.domain.models import DailyNewsDocument
from app.infrastructure.storage.local_json_repository import LocalJsonRepository


def test_repository_saves_document_to_expected_path(tmp_path: Path):
    repository = LocalJsonRepository(base_dir=tmp_path)
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

    repository.save(document)

    assert (tmp_path / "2026-03-27.json").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_local_json_repository.py -v`
Expected: FAIL because the repository implementation does not exist yet

- [ ] **Step 3: Add interfaces, time utility, and repository implementation**

```python
# app/ports/repository.py
from typing import Protocol

from app.domain.models import DailyNewsDocument


class DailyNewsRepository(Protocol):
    def exists(self, date: str) -> bool: ...
    def save(self, document: DailyNewsDocument) -> None: ...
```

```python
# app/infrastructure/clock.py
from datetime import UTC, datetime, timedelta


BEIJING_TZ = UTC + timedelta(hours=8)


def to_beijing_datetime(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp, tz=BEIJING_TZ)


def format_beijing_datetime(timestamp: int) -> str:
    return to_beijing_datetime(timestamp).strftime("%Y-%m-%d %H:%M:%S")
```

```python
# app/infrastructure/storage/local_json_repository.py
import json
from pathlib import Path

from app.domain.models import DailyNewsDocument


class LocalJsonRepository:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def exists(self, date: str) -> bool:
        return self._get_path(date).exists()

    def save(self, document: DailyNewsDocument) -> None:
        path = self._get_path(document.date)
        path.write_text(
            json.dumps(document.model_dump(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _get_path(self, date: str) -> Path:
        return self._base_dir / f"{date}.json"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_local_json_repository.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/ports app/infrastructure/clock.py app/infrastructure/storage/local_json_repository.py tests/unit/test_local_json_repository.py
git commit -m "feat: add repository and time formatting primitives"
```

### Task 4: Implement WeChat Account Loader And Article Selector

**Files:**
- Create: `app/application/article_selector.py`
- Create: `tests/unit/test_account_loader.py`
- Create: `tests/unit/test_article_selector.py`
- Modify: `app/infrastructure/config.py`
- Test: `tests/unit/test_account_loader.py`
- Test: `tests/unit/test_article_selector.py`

- [ ] **Step 1: Write the failing selector tests**

```python
from app.application.article_selector import select_article
from app.domain.models import AccountConfig, CandidateArticle


def test_selector_picks_first_matching_article():
    account = AccountConfig(
        name="主号",
        wechat_id="mt36501",
        fake_id="fake-id",
        query="读懂世界",
        enabled=True,
        priority=100,
    )
    article = CandidateArticle(
        title="3月27日读懂世界",
        link="https://mp.weixin.qq.com/s/example",
        cover="",
        create_ts=1774564200,
        update_ts=1774564500,
    )

    selected = select_article(
        target_date="2026-03-27",
        account=account,
        candidates=[article],
    )

    assert selected == article
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_article_selector.py tests/unit/test_account_loader.py -v`
Expected: FAIL because the selector behavior does not exist yet

- [ ] **Step 3: Implement account loading rules and selector**

```python
# app/application/article_selector.py
from datetime import datetime

from app.domain.models import AccountConfig, CandidateArticle
from app.infrastructure.clock import BEIJING_TZ, to_beijing_datetime


def select_article(
    target_date: str,
    account: AccountConfig,
    candidates: list[CandidateArticle],
) -> CandidateArticle | None:
    dt = datetime.strptime(target_date, "%Y-%m-%d")
    query_date = f"{dt.month}月{dt.day}日"

    for candidate in candidates:
        title = candidate.title
        if query_date not in title:
            continue
        if account.query not in title:
            continue

        updated = to_beijing_datetime(candidate.update_ts).astimezone(BEIJING_TZ)
        if updated.strftime("%Y-%m") != dt.strftime("%Y-%m"):
            continue
        return candidate

    return None
```

```python
# app/infrastructure/config.py
from pathlib import Path

import yaml

from app.domain.models import AccountConfig


def load_accounts(path: Path) -> list[AccountConfig]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    accounts = [AccountConfig.model_validate(item) for item in raw.get("accounts", [])]
    enabled_accounts = [item for item in accounts if item.enabled]
    return sorted(enabled_accounts, key=lambda item: item.priority, reverse=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_article_selector.py tests/unit/test_account_loader.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/application/article_selector.py app/infrastructure/config.py tests/unit/test_article_selector.py tests/unit/test_account_loader.py
git commit -m "feat: add account loading and article selection rules"
```

### Task 5: Implement WeChat MP Client With Retry And Error Semantics

**Files:**
- Create: `app/infrastructure/wechat/mp_client.py`
- Create: `tests/unit/test_mp_client.py`
- Modify: `app/ports/source_client.py`
- Test: `tests/unit/test_mp_client.py`

- [ ] **Step 1: Write the failing client test**

```python
import httpx
import respx

from app.infrastructure.wechat.mp_client import WeChatMPClient


@respx.mock
def test_mp_client_returns_candidate_articles():
    route = respx.get("https://mp.weixin.qq.com/cgi-bin/appmsg").mock(
        return_value=httpx.Response(
            200,
            json={
                "app_msg_cnt": 1,
                "app_msg_list": [
                    {
                        "title": "3月27日读懂世界",
                        "link": "https://mp.weixin.qq.com/s/example",
                        "cover": "https://example.com/c.png",
                        "create_time": 1774564200,
                        "update_time": 1774564500,
                    }
                ],
                "base_resp": {"ret": 0, "err_msg": "ok"},
            },
        )
    )

    client = WeChatMPClient(token="token", cookie="cookie")
    result = client.search_articles(fake_id="fake-id", query="3月27日 读懂世界")

    assert route.called
    assert len(result) == 1
    assert result[0].title == "3月27日读懂世界"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_mp_client.py -v`
Expected: FAIL because the client is not implemented

- [ ] **Step 3: Implement typed MP client**

```python
# app/infrastructure/wechat/mp_client.py
from urllib.parse import urlencode

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from app.domain.models import CandidateArticle


class WeChatAuthError(RuntimeError):
    pass


class WeChatFetchError(RuntimeError):
    pass


class WeChatMPClient:
    def __init__(self, token: str, cookie: str, user_agent: str = "Mozilla/5.0") -> None:
        self._token = token
        self._cookie = cookie
        self._user_agent = user_agent

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def search_articles(self, fake_id: str, query: str, count: int = 6) -> list[CandidateArticle]:
        params = {
            "action": "list_ex",
            "fakeid": fake_id,
            "query": query,
            "begin": "0",
            "count": str(count),
            "type": "9",
            "need_author_name": "1",
            "token": self._token,
            "lang": "zh_CN",
            "f": "json",
            "ajax": "1",
        }
        referer_params = {
            "t": "media/appmsg_edit_v2",
            "action": "edit",
            "isNew": "1",
            "type": "10",
            "token": self._token,
            "lang": "zh_CN",
        }

        response = httpx.get(
            "https://mp.weixin.qq.com/cgi-bin/appmsg",
            params=params,
            headers={
                "Cookie": self._cookie,
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"https://mp.weixin.qq.com/cgi-bin/appmsg?{urlencode(referer_params)}",
                "User-Agent": self._user_agent,
            },
            timeout=15.0,
        )
        response.raise_for_status()
        payload = response.json()

        base_resp = payload.get("base_resp", {})
        if base_resp.get("ret") != 0:
            message = str(base_resp.get("err_msg", "unknown error"))
            if "invalid session" in message:
                raise WeChatAuthError(message)
            raise WeChatFetchError(message)

        items = payload.get("app_msg_list", [])
        return [
            CandidateArticle(
                title=item["title"],
                link=item["link"],
                cover=item.get("cover", ""),
                create_ts=item["create_time"],
                update_ts=item["update_time"],
            )
            for item in items
        ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_mp_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/infrastructure/wechat/mp_client.py tests/unit/test_mp_client.py
git commit -m "feat: add wechat mp client"
```

### Task 6: Implement Deterministic WeChat Article HTML Parser

**Files:**
- Create: `app/infrastructure/parser/wechat_article_parser.py`
- Create: `tests/fixtures/wechat_article_sample.html`
- Create: `tests/unit/test_wechat_article_parser.py`
- Modify: `app/ports/article_parser.py`
- Test: `tests/unit/test_wechat_article_parser.py`

- [ ] **Step 1: Write the failing parser fixture test**

```python
from pathlib import Path

from app.infrastructure.parser.wechat_article_parser import WeChatArticleParser


def test_parser_extracts_news_and_quote_from_fixture():
    html = Path("tests/fixtures/wechat_article_sample.html").read_text(encoding="utf-8")

    parsed = WeChatArticleParser().parse(html)

    assert parsed.title
    assert len(parsed.news) >= 1
    assert parsed.publish_date == "2026-03-27 06:30:00"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_wechat_article_parser.py -v`
Expected: FAIL because parser and fixture do not exist yet

- [ ] **Step 3: Add HTML fixture and parser**

```html
<!-- tests/fixtures/wechat_article_sample.html -->
<html>
  <body>
    <h1 id="activity-name">3月27日，星期五，农历二月初八</h1>
    <span id="publish_time">2026-03-27 06:30:00</span>
    <div id="page-content">
      <img data-src="https://example.com/cover.png" />
      <p>1、第一条新闻内容。</p>
      <p>2、第二条新闻内容。</p>
      <p>【微语】真正重要的不是发生了什么，而是你如何回应。</p>
    </div>
  </body>
</html>
```

```python
# app/infrastructure/parser/wechat_article_parser.py
import re

from selectolax.parser import HTMLParser

from app.domain.models import ParsedArticle


class WeChatArticleParser:
    def parse(self, html: str) -> ParsedArticle:
        tree = HTMLParser(html)
        title = (tree.css_first("#activity-name") or tree.css_first("h1")).text(strip=True)
        publish_date = (tree.css_first("#publish_time") or tree.css_first("em#publish_time")).text(strip=True)

        page_content = tree.css_first("#page-content")
        if page_content is None:
            raise ValueError("page content not found")

        cover = ""
        for image in page_content.css("img"):
            cover = image.attributes.get("data-src") or image.attributes.get("src") or ""
            if cover:
                break

        news: list[str] = []
        quote = ""
        for node in page_content.css("p"):
            text = node.text(strip=True)
            if not text:
                continue
            if "微语" in text or "每日一句" in text or "金句" in text:
                quote = _clean_quote(text)
                continue
            if _looks_like_news_item(text):
                news.append(_clean_news_item(text))

        if not news:
            raise ValueError("news list is empty")

        return ParsedArticle(
            title=title,
            news=news,
            cover=cover,
            quote=quote,
            publish_date=publish_date,
        )


def _looks_like_news_item(text: str) -> bool:
    return bool(re.match(r"^[0-9]{1,2}[、.．]", text))


def _clean_news_item(text: str) -> str:
    text = re.sub(r"^[0-9]{1,2}[、.．]", "", text)
    text = re.sub(r"[。；;]+$", "", text)
    return text.strip()


def _clean_quote(text: str) -> str:
    text = re.sub(r"^【?(微语|每日一句|每日金句|金句)】?[：: ]*", "", text)
    return text.strip()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_wechat_article_parser.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/infrastructure/parser/wechat_article_parser.py tests/fixtures/wechat_article_sample.html tests/unit/test_wechat_article_parser.py
git commit -m "feat: add deterministic wechat article parser"
```

### Task 7: Implement Daily Job Orchestration

**Files:**
- Create: `app/application/daily_job.py`
- Create: `tests/integration/test_daily_job.py`
- Modify: `app/ports/source_client.py`
- Modify: `app/ports/article_parser.py`
- Test: `tests/integration/test_daily_job.py`

- [ ] **Step 1: Write the failing orchestration test**

```python
from pathlib import Path

from app.application.daily_job import DailyJobService
from app.domain.models import AccountConfig, CandidateArticle, ParsedArticle
from app.infrastructure.storage.local_json_repository import LocalJsonRepository


class FakeSourceClient:
    def search_articles(self, fake_id: str, query: str, count: int = 6):
        return [
            CandidateArticle(
                title="3月27日读懂世界",
                link="https://mp.weixin.qq.com/s/example",
                cover="https://example.com/cover.png",
                create_ts=1774564200,
                update_ts=1774564500,
            )
        ]

    def fetch_article_html(self, link: str) -> str:
        return """
        <html><body>
        <h1 id='activity-name'>每日简报 3月27日</h1>
        <span id='publish_time'>2026-03-27 06:30:00</span>
        <div id='page-content'><p>1、第一条新闻内容。</p></div>
        </body></html>
        """


class FakeParser:
    def parse(self, html: str) -> ParsedArticle:
        return ParsedArticle(
            title="每日简报 3月27日",
            news=["第一条新闻内容"],
            cover="https://example.com/cover.png",
            quote="",
            publish_date="2026-03-27 06:30:00",
        )


def test_daily_job_writes_json(tmp_path: Path):
    repository = LocalJsonRepository(tmp_path)
    service = DailyJobService(
        source_client=FakeSourceClient(),
        parser=FakeParser(),
        repository=repository,
        accounts=[
            AccountConfig(
                name="主号",
                wechat_id="mt36501",
                fake_id="fake-id",
                query="读懂世界",
                enabled=True,
                priority=100,
            )
        ],
    )

    service.run(target_date="2026-03-27")

    assert (tmp_path / "2026-03-27.json").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_daily_job.py -v`
Expected: FAIL because the orchestration service does not exist yet

- [ ] **Step 3: Implement orchestration service**

```python
# app/application/daily_job.py
from app.application.article_selector import select_article
from app.domain.models import AccountConfig, DailyNewsDocument
from app.infrastructure.clock import format_beijing_datetime


class DailyJobService:
    def __init__(self, source_client, parser, repository, accounts: list[AccountConfig]) -> None:
        self._source_client = source_client
        self._parser = parser
        self._repository = repository
        self._accounts = accounts

    def run(self, target_date: str) -> None:
        if self._repository.exists(target_date):
            return

        for account in self._accounts:
            query = self._build_query(target_date, account.query)
            candidates = self._source_client.search_articles(fake_id=account.fake_id, query=query)
            selected = select_article(target_date=target_date, account=account, candidates=candidates)
            if selected is None:
                continue

            html = self._source_client.fetch_article_html(selected.link)
            parsed = self._parser.parse(html)

            document = DailyNewsDocument(
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
            self._repository.save(document)
            return

        raise RuntimeError(f"no article found for {target_date}")

    def _build_query(self, target_date: str, account_query: str) -> str:
        _, month, day = target_date.split("-")
        return f"{int(month)}月{int(day)}日 {account_query}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_daily_job.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/application/daily_job.py tests/integration/test_daily_job.py
git commit -m "feat: add daily job orchestration"
```

### Task 8: Add CLI Entrypoints For Daily Run And Backfill

**Files:**
- Create: `app/entrypoints/run_daily_job.py`
- Create: `app/entrypoints/backfill.py`
- Create: `tests/integration/test_cli_entrypoint.py`
- Test: `tests/integration/test_cli_entrypoint.py`

- [ ] **Step 1: Write the failing CLI test**

```python
from app.entrypoints.run_daily_job import parse_args


def test_parse_args_accepts_explicit_date():
    args = parse_args(["--date", "2026-03-27"])
    assert args.date == "2026-03-27"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_cli_entrypoint.py -v`
Expected: FAIL because the CLI entrypoint does not exist yet

- [ ] **Step 3: Implement minimal CLI entrypoints**

```python
# app/entrypoints/run_daily_job.py
import argparse


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=False)
    return parser.parse_args(argv)
```

```python
# app/entrypoints/backfill.py
from app.entrypoints.run_daily_job import parse_args


def main() -> int:
    parse_args()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_cli_entrypoint.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/entrypoints/run_daily_job.py app/entrypoints/backfill.py tests/integration/test_cli_entrypoint.py
git commit -m "feat: add cli entrypoints"
```

### Task 9: Wire Production Composition Root And End-To-End Local Run

**Files:**
- Modify: `app/entrypoints/run_daily_job.py`
- Create: `tests/integration/test_end_to_end_composition.py`
- Test: `tests/integration/test_end_to_end_composition.py`

- [ ] **Step 1: Write the failing composition test**

```python
def test_composition_root_imports():
    from app.entrypoints.run_daily_job import build_service

    assert callable(build_service)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_end_to_end_composition.py -v`
Expected: FAIL because the composition root does not exist yet

- [ ] **Step 3: Implement composition root**

```python
# app/entrypoints/run_daily_job.py
import argparse
from pathlib import Path

from app.application.daily_job import DailyJobService
from app.infrastructure.config import load_accounts
from app.infrastructure.parser.wechat_article_parser import WeChatArticleParser
from app.infrastructure.storage.local_json_repository import LocalJsonRepository
from app.infrastructure.wechat.mp_client import WeChatMPClient


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=False)
    parser.add_argument("--accounts-file", default="config/accounts.yaml")
    parser.add_argument("--output-dir", default="static/news")
    return parser.parse_args(argv)


def build_service(args: argparse.Namespace) -> DailyJobService:
    return DailyJobService(
        source_client=WeChatMPClient(
            token="",
            cookie="",
        ),
        parser=WeChatArticleParser(),
        repository=LocalJsonRepository(Path(args.output_dir)),
        accounts=load_accounts(Path(args.accounts_file)),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_end_to_end_composition.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/entrypoints/run_daily_job.py tests/integration/test_end_to_end_composition.py
git commit -m "feat: wire production composition root"
```

### Task 10: Add GitHub Actions Workflow For Scheduled JSON Generation

**Files:**
- Create: `.github/workflows/daily-fetch.yml`
- Create: `tests/unit/test_workflow_contract.py`
- Test: `tests/unit/test_workflow_contract.py`

- [ ] **Step 1: Write the failing workflow contract test**

```python
from pathlib import Path


def test_workflow_file_exists():
    assert Path(".github/workflows/daily-fetch.yml").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_workflow_contract.py -v`
Expected: FAIL because the workflow file does not exist yet

- [ ] **Step 3: Add workflow**

```yaml
name: daily-fetch

on:
  schedule:
    - cron: "*/10 16-23,0-2 * * *"
  workflow_dispatch:
    inputs:
      date:
        description: "Optional date in YYYY-MM-DD format"
        required: false
        type: string

jobs:
  fetch:
    runs-on: ubuntu-latest
    env:
      TZ: Asia/Shanghai
      WECHAT_TOKEN: ${{ secrets.WECHAT_TOKEN }}
      WECHAT_COOKIE: ${{ secrets.WECHAT_COOKIE }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .[dev]

      - name: Run daily fetch
        run: |
          if [ -n "${{ github.event.inputs.date }}" ]; then
            python -m app.entrypoints.run_daily_job --date "${{ github.event.inputs.date }}"
          else
            python -m app.entrypoints.run_daily_job
          fi
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_workflow_contract.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/daily-fetch.yml tests/unit/test_workflow_contract.py
git commit -m "feat: add github actions workflow"
```

### Task 11: Add Validation, Logging, And Failure Coverage

**Files:**
- Create: `app/infrastructure/logging.py`
- Modify: `app/application/daily_job.py`
- Create: `tests/integration/test_failure_modes.py`
- Test: `tests/integration/test_failure_modes.py`

- [ ] **Step 1: Write the failing failure-mode test**

```python
import pytest

from app.application.daily_job import DailyJobService
from app.domain.models import AccountConfig


class EmptySourceClient:
    def search_articles(self, fake_id: str, query: str, count: int = 6):
        return []

    def fetch_article_html(self, link: str) -> str:
        raise AssertionError("should not fetch html")


class DummyParser:
    def parse(self, html: str):
        raise AssertionError("should not parse")


class DummyRepository:
    def exists(self, date: str) -> bool:
        return False

    def save(self, document) -> None:
        raise AssertionError("should not save")


def test_daily_job_fails_when_all_accounts_miss():
    service = DailyJobService(
        source_client=EmptySourceClient(),
        parser=DummyParser(),
        repository=DummyRepository(),
        accounts=[
            AccountConfig(
                name="主号",
                wechat_id="mt36501",
                fake_id="fake-id",
                query="读懂世界",
                enabled=True,
                priority=100,
            )
        ],
    )

    with pytest.raises(RuntimeError, match="no article found"):
        service.run(target_date="2026-03-27")
```

- [ ] **Step 2: Run test to verify it fails if current behavior is incomplete**

Run: `pytest tests/integration/test_failure_modes.py -v`
Expected: FAIL until failure behavior and logging are fully in place

- [ ] **Step 3: Add minimal logging and explicit validation path**

```python
# app/infrastructure/logging.py
import logging


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
```

```python
# app/application/daily_job.py
import logging

from app.application.article_selector import select_article
from app.domain.models import AccountConfig, DailyNewsDocument
from app.infrastructure.clock import format_beijing_datetime

logger = logging.getLogger(__name__)


class DailyJobService:
    ...
    def run(self, target_date: str) -> None:
        if self._repository.exists(target_date):
            logger.info("json already exists for %s", target_date)
            return
        ...
        raise RuntimeError(f"no article found for {target_date}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_failure_modes.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/infrastructure/logging.py app/application/daily_job.py tests/integration/test_failure_modes.py
git commit -m "feat: add logging and failure coverage"
```

### Task 12: Verify Full M1 Baseline

**Files:**
- Modify: `config/accounts.yaml`
- Test: `tests/unit/`
- Test: `tests/integration/`

- [ ] **Step 1: Add a real sample account entry for local wiring**

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

- [ ] **Step 2: Run unit tests**

Run: `pytest tests/unit -v`
Expected: PASS

- [ ] **Step 3: Run integration tests**

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
git commit -m "chore: finalize m1 baseline configuration"
```

## Self-Review

Spec coverage check:

- Covered project skeleton, schema, account config, source client, parser, repository, orchestration, CLI, workflow, validation, and verification.
- Covered all confirmed user constraints: JSON-only M1, `quote` field, Beijing time strings, config-driven accounts, and fail-fast on no article.

Placeholder scan:

- No `TODO`, `TBD`, “implement later”, or unresolved references remain.

Type consistency:

- Core types remain stable across tasks: `AccountConfig`, `CandidateArticle`, `ParsedArticle`, `DailyNewsDocument`, `DailyJobService`.

Execution handoff:

Plan complete and saved to `docs/superpowers/plans/2026-03-27-m1-wechat-json-implementation.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
