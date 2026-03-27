from __future__ import annotations

from pathlib import Path

import pytest

from app.application.daily_job import DailyJobService
from app.domain.models import AccountConfig, DailyNewsDocument
from app.infrastructure.storage.static_assets_repository import StaticAssetsRepositoryImpl


class _NeverSourceClient:
    def search_articles(self, fake_id: str, query: str, count: int = 6) -> list[object]:
        raise AssertionError("search should not run when json already exists")

    def fetch_article_html(self, link: str) -> str:
        raise AssertionError("fetch should not run when json already exists")


class _NeverParser:
    def parse(self, html: str) -> object:
        raise AssertionError("parse should not run when json already exists")


class _FailingRenderer:
    def render(self, document: DailyNewsDocument) -> bytes:
        raise RuntimeError("render failed")


def test_daily_job_skips_when_json_and_png_exist(tmp_path: Path) -> None:
    repository = StaticAssetsRepositoryImpl(
        json_dir=tmp_path / "60s",
        image_dir=tmp_path / "images",
        image_base_url="https://cdn.example.com/static/images/",
    )
    document = DailyNewsDocument(
        date="2026-03-27",
        news=["第一条"],
        cover="",
        image="https://cdn.example.com/static/images/2026-03-27.png",
        title="每天60秒读懂世界｜3月27日",
        quote="一句话总结",
        link="https://mp.weixin.qq.com/s/example",
        publish_date="2026-03-27 06:30:00",
        create_date="2026-03-27 06:30:00",
        update_date="2026-03-27 06:35:00",
    )
    repository.save_document(document)
    repository.save_image("2026-03-27", b"png")

    service = DailyJobService(
        source_client=_NeverSourceClient(),
        parser=_NeverParser(),
        repository=repository,
        accounts=[
            AccountConfig(
                name="main",
                wechat_id="wechat-1",
                fake_id="fake-1",
                query="读懂世界",
                enabled=True,
                priority=10,
            )
        ],
        image_renderer=_FailingRenderer(),
    )

    result = service.run("2026-03-27")

    assert result.status == "skipped"
    assert result.document is None


def test_daily_job_raises_when_renderer_fails_on_backfill(tmp_path: Path) -> None:
    repository = StaticAssetsRepositoryImpl(
        json_dir=tmp_path / "60s",
        image_dir=tmp_path / "images",
        image_base_url="https://cdn.example.com/static/images/",
    )
    repository.save_document(
        DailyNewsDocument(
            date="2026-03-27",
            news=["第一条"],
            cover="",
            image="",
            title="每天60秒读懂世界｜3月27日",
            quote="一句话总结",
            link="https://mp.weixin.qq.com/s/example",
            publish_date="2026-03-27 06:30:00",
            create_date="2026-03-27 06:30:00",
            update_date="2026-03-27 06:35:00",
        )
    )

    service = DailyJobService(
        source_client=_NeverSourceClient(),
        parser=_NeverParser(),
        repository=repository,
        accounts=[
            AccountConfig(
                name="main",
                wechat_id="wechat-1",
                fake_id="fake-1",
                query="读懂世界",
                enabled=True,
                priority=10,
            )
        ],
        image_renderer=_FailingRenderer(),
    )

    with pytest.raises(RuntimeError, match="render failed"):
        service.run("2026-03-27")
