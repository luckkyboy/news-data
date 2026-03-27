from __future__ import annotations

import json
from pathlib import Path

from app.application.daily_job import DailyJobService
from app.domain.models import AccountConfig, CandidateArticle, DailyNewsDocument
from app.infrastructure.clock import format_beijing_datetime
from app.infrastructure.parser.wechat_article_parser import WeChatArticleParser
from app.infrastructure.storage.local_json_repository import LocalJsonRepository


class _FakeSourceClient:
    def __init__(self, html: str) -> None:
        self._html = html
        self.search_calls: list[tuple[str, str, int]] = []
        self.fetch_calls: list[str] = []

    def search_articles(self, fake_id: str, query: str, count: int = 6) -> list[CandidateArticle]:
        self.search_calls.append((fake_id, query, count))
        if fake_id == "fake-1":
            return [
                CandidateArticle(
                    title="3月27日 无关内容",
                    link="https://mp.weixin.qq.com/s/miss",
                    cover="",
                    create_ts=1774564200,
                    update_ts=1774564500,
                )
            ]
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
        self.fetch_calls.append(link)
        return self._html


class _FailingSourceClient:
    def search_articles(self, fake_id: str, query: str, count: int = 6) -> list[CandidateArticle]:
        raise AssertionError("source client should not be called when document already exists")

    def fetch_article_html(self, link: str) -> str:
        raise AssertionError("source client should not be called when document already exists")


def test_daily_job_success_writes_json(tmp_path: Path) -> None:
    html = Path("tests/fixtures/wechat_article_sample.html").read_text(encoding="utf-8")
    source_client = _FakeSourceClient(html)
    parser = WeChatArticleParser()
    repository = LocalJsonRepository(tmp_path)
    accounts = [
        AccountConfig(
            name="first",
            wechat_id="wechat-1",
            fake_id="fake-1",
            query="读懂世界",
            enabled=True,
            priority=20,
        ),
        AccountConfig(
            name="second",
            wechat_id="wechat-2",
            fake_id="fake-2",
            query="读懂世界",
            enabled=True,
            priority=10,
        ),
    ]
    service = DailyJobService(
        source_client=source_client,
        parser=parser,
        repository=repository,
        accounts=accounts,
    )

    result = service.run("2026-03-27")

    saved_path = tmp_path / "2026-03-27.json"
    payload = json.loads(saved_path.read_text(encoding="utf-8"))
    parsed = parser.parse(html)

    assert result.status == "updated"
    assert result.document is not None
    assert result.document == DailyNewsDocument(
        date="2026-03-27",
        news=parsed.news,
        sources=parsed.sources,
        cover=parsed.cover,
        image="",
        title=parsed.title,
        quote=parsed.quote,
        link="https://mp.weixin.qq.com/s/example",
        publish_date=parsed.publish_date,
        create_date=format_beijing_datetime(1774564200),
        update_date=format_beijing_datetime(1774564500),
    )
    assert payload == {
        "date": "2026-03-27",
        "news": parsed.news,
        "sources": parsed.sources,
        "cover": parsed.cover,
        "image": "",
        "title": parsed.title,
        "quote": parsed.quote,
        "link": "https://mp.weixin.qq.com/s/example",
        "publish_date": parsed.publish_date,
        "create_date": format_beijing_datetime(1774564200),
        "update_date": format_beijing_datetime(1774564500),
    }
    assert source_client.search_calls == [
        ("fake-1", "3月27日 读懂世界", 6),
        ("fake-2", "3月27日 读懂世界", 6),
    ]
    assert source_client.fetch_calls == ["https://mp.weixin.qq.com/s/example"]


def test_daily_job_returns_without_writing_when_document_exists(tmp_path: Path) -> None:
    repository = LocalJsonRepository(tmp_path)
    existing = DailyNewsDocument(
        date="2026-03-27",
        news=["A"],
        sources=[],
        cover="",
        title="existing",
        link="https://example.com",
        publish_date="2026-03-27 06:30:00",
        create_date="2026-03-27 06:30:00",
        update_date="2026-03-27 06:35:00",
    )
    repository.save(existing)
    original_content = (tmp_path / "2026-03-27.json").read_text(encoding="utf-8")

    service = DailyJobService(
        source_client=_FailingSourceClient(),
        parser=WeChatArticleParser(),
        repository=repository,
        accounts=[
            AccountConfig(
                name="first",
                wechat_id="wechat-1",
                fake_id="fake-1",
                query="读懂世界",
                enabled=True,
                priority=20,
            )
        ],
    )

    result = service.run("2026-03-27")

    assert result.status == "skipped"
    assert result.document is None
    assert (tmp_path / "2026-03-27.json").read_text(encoding="utf-8") == original_content
