from __future__ import annotations

import pytest

from app.application.daily_job import DailyJobService
from app.domain.models import AccountConfig


class _MissClient:
    def search_articles(self, fake_id: str, query: str, count: int = 6) -> list[object]:
        return []

    def fetch_article_html(self, link: str) -> str:
        raise AssertionError("fetch should not be called when there are no candidates")


class _NeverParser:
    def parse(self, html: str) -> object:
        raise AssertionError("parse should not be called when there are no candidates")


class _MemoryRepository:
    def exists(self, date: str) -> bool:
        return False

    def save(self, document: object) -> None:
        raise AssertionError("save should not be called when there is no article")


def test_daily_job_raises_when_all_accounts_miss() -> None:
    service = DailyJobService(
        source_client=_MissClient(),
        parser=_NeverParser(),
        repository=_MemoryRepository(),
        accounts=[
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
        ],
    )

    with pytest.raises(RuntimeError, match="no article found for 2026-03-27"):
        service.run("2026-03-27")
