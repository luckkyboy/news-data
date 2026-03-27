from __future__ import annotations

import json
from pathlib import Path

from app.application.daily_job import DailyJobService
from app.domain.models import AccountConfig, CandidateArticle, DailyNewsDocument, ParsedArticle
from app.infrastructure.storage.static_assets_repository import StaticAssetsRepositoryImpl


class _FakeSourceClient:
    def __init__(self) -> None:
        self.search_calls: list[tuple[str, str, int]] = []
        self.fetch_calls: list[str] = []

    def search_articles(self, fake_id: str, query: str, count: int = 6) -> list[CandidateArticle]:
        self.search_calls.append((fake_id, query, count))
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
        return "<html></html>"


class _FakeParser:
    def __init__(self) -> None:
        self.calls = 0

    def parse(self, html: str) -> ParsedArticle:
        self.calls += 1
        return ParsedArticle(
            title="每天60秒读懂世界｜3月27日",
            news=["第一条", "第二条"],
            sources=["人民日报"],
            cover="https://example.com/cover.png",
            quote="一句话总结",
            publish_date="2026-03-27 06:30:00",
        )


class _FakeRenderer:
    def __init__(self, content: bytes = b"png-bytes") -> None:
        self.content = content
        self.calls: list[str] = []

    def render(self, document: DailyNewsDocument) -> bytes:
        self.calls.append(document.date)
        return self.content


def test_daily_job_fresh_fetch_writes_json_and_png_and_backfills_image(tmp_path: Path) -> None:
    repository = StaticAssetsRepositoryImpl(
        json_dir=tmp_path / "60s",
        image_dir=tmp_path / "images",
        image_base_url="https://cdn.example.com/static/images/",
    )
    source_client = _FakeSourceClient()
    parser = _FakeParser()
    renderer = _FakeRenderer()
    service = DailyJobService(
        source_client=source_client,
        parser=parser,
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
        image_renderer=renderer,
    )

    result = service.run("2026-03-27")
    document = result.document

    assert result.status == "updated"
    assert document is not None
    assert repository.json_exists("2026-03-27") is True
    assert repository.image_exists("2026-03-27") is True
    assert document.image == "https://cdn.example.com/static/images/2026-03-27.png"
    assert json.loads((tmp_path / "60s" / "2026-03-27.json").read_text(encoding="utf-8"))[
        "image"
    ] == "https://cdn.example.com/static/images/2026-03-27.png"
    assert parser.calls == 1
    assert renderer.calls == ["2026-03-27"]
    assert source_client.search_calls == [("fake-id", "3月27日 读懂世界", 6)]
    assert source_client.fetch_calls == ["https://mp.weixin.qq.com/s/example"]


def test_daily_job_backfills_missing_png_without_refetching(tmp_path: Path) -> None:
    repository = StaticAssetsRepositoryImpl(
        json_dir=tmp_path / "60s",
        image_dir=tmp_path / "images",
        image_base_url="https://cdn.example.com/static/images/",
    )
    existing = DailyNewsDocument(
        date="2026-03-27",
        news=["第一条"],
        sources=["人民日报"],
        cover="https://example.com/cover.png",
        image="",
        title="每天60秒读懂世界｜3月27日",
        quote="一句话总结",
        link="https://mp.weixin.qq.com/s/example",
        publish_date="2026-03-27 06:30:00",
        create_date="2026-03-27 06:30:00",
        update_date="2026-03-27 06:35:00",
    )
    repository.save_document(existing)

    class _FailingSourceClient:
        def search_articles(
            self,
            fake_id: str,
            query: str,
            count: int = 6,
        ) -> list[CandidateArticle]:
            raise AssertionError("search should not run during backfill")

        def fetch_article_html(self, link: str) -> str:
            raise AssertionError("fetch should not run during backfill")

    parser = _FakeParser()
    renderer = _FakeRenderer(content=b"backfill-png")
    service = DailyJobService(
        source_client=_FailingSourceClient(),
        parser=parser,
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
        image_renderer=renderer,
    )

    result = service.run("2026-03-27")
    document = result.document

    assert result.status == "backfilled_image"
    assert document is not None
    assert parser.calls == 0
    assert renderer.calls == ["2026-03-27"]
    assert repository.image_exists("2026-03-27") is True
    assert document.image == "https://cdn.example.com/static/images/2026-03-27.png"


def test_daily_job_raises_if_renderer_fails(tmp_path: Path) -> None:
    repository = StaticAssetsRepositoryImpl(
        json_dir=tmp_path / "60s",
        image_dir=tmp_path / "images",
        image_base_url="https://cdn.example.com/static/images/",
    )

    class _RendererError(RuntimeError):
        pass

    class _FailingRenderer:
        def render(self, document: DailyNewsDocument) -> bytes:
            raise _RendererError("boom")

    service = DailyJobService(
        source_client=_FakeSourceClient(),
        parser=_FakeParser(),
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
        image_renderer=_FailingRenderer(),
    )

    try:
        service.run("2026-03-27")
    except _RendererError:
        pass
    else:
        raise AssertionError("renderer failures must be raised")
