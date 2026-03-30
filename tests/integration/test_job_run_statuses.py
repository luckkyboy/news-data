from __future__ import annotations

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
            title="每日简报｜3月27日",
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


def _service(
    tmp_path: Path,
    renderer: _FakeRenderer,
) -> tuple[
    DailyJobService,
    StaticAssetsRepositoryImpl,
    _FakeSourceClient,
    _FakeParser,
]:
    repository = StaticAssetsRepositoryImpl(
        json_dir=tmp_path / "60s",
        image_dir=tmp_path / "images",
        image_base_url="https://cdn.example.com/static/images/",
    )
    source_client = _FakeSourceClient()
    parser = _FakeParser()
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
    return service, repository, source_client, parser


def test_job_run_status_updated_for_fresh_fetch(tmp_path: Path) -> None:
    service, repository, source_client, parser = _service(tmp_path, _FakeRenderer())

    result = service.run("2026-03-27")

    assert result.status == "updated"
    assert result.document is not None
    assert result.document.date == "2026-03-27"
    assert repository.json_exists("2026-03-27") is True
    assert repository.image_exists("2026-03-27") is True
    assert parser.calls == 1
    assert source_client.fetch_calls == ["https://mp.weixin.qq.com/s/example"]


def test_job_run_status_backfilled_image_for_existing_json(tmp_path: Path) -> None:
    service, repository, source_client, parser = _service(
        tmp_path,
        _FakeRenderer(content=b"backfill"),
    )
    repository.save_document(
        DailyNewsDocument(
            date="2026-03-27",
            news=["第一条"],
            sources=["人民日报"],
            cover="https://example.com/cover.png",
            image="",
            title="每日简报｜3月27日",
            quote="一句话总结",
            link="https://mp.weixin.qq.com/s/example",
            publish_date="2026-03-27 06:30:00",
            create_date="2026-03-27 06:30:00",
            update_date="2026-03-27 06:35:00",
        )
    )

    result = service.run("2026-03-27")

    assert result.status == "backfilled_image"
    assert result.document is not None
    assert result.document.image == "https://cdn.example.com/static/images/2026-03-27.png"
    assert parser.calls == 0
    assert source_client.search_calls == []


def test_job_run_status_skipped_for_existing_json_and_png(tmp_path: Path) -> None:
    service, repository, source_client, parser = _service(tmp_path, _FakeRenderer())
    repository.save_document(
        DailyNewsDocument(
            date="2026-03-27",
            news=["第一条"],
            sources=["人民日报"],
            cover="https://example.com/cover.png",
            image="https://cdn.example.com/static/images/2026-03-27.png",
            title="每日简报｜3月27日",
            quote="一句话总结",
            link="https://mp.weixin.qq.com/s/example",
            publish_date="2026-03-27 06:30:00",
            create_date="2026-03-27 06:30:00",
            update_date="2026-03-27 06:35:00",
        )
    )
    repository.save_image("2026-03-27", b"png")

    result = service.run("2026-03-27")

    assert result.status == "skipped"
    assert result.document is None
    assert parser.calls == 0
    assert source_client.search_calls == []
