from pathlib import Path

import pytest
from pydantic import ValidationError

from app.domain.models import AccountConfig, CandidateArticle, DailyNewsDocument, ParsedArticle
from app.infrastructure.config import load_accounts


def test_account_config_keeps_priority_and_enabled() -> None:
    account = AccountConfig(
        name="主号",
        wechat_id="mt36501",
        fake_id="MzkwNDc5NTA0Mw==",
        query="读懂世界",
        enabled=True,
        priority=100,
    )

    assert account.enabled is True
    assert account.priority == 100
    assert account.parser_profile == "generic"


def test_candidate_article_tracks_wechat_times() -> None:
    article = CandidateArticle(
        title="3月27日 读懂世界",
        link="https://mp.weixin.qq.com/s/example",
        cover="https://example.com/c.png",
        create_ts=1774564200,
        update_ts=1774564500,
    )

    assert article.create_ts < article.update_ts


def test_parsed_article_requires_at_least_one_news_item() -> None:
    article = ParsedArticle(
        title="3月27日 读懂世界",
        news=["A"],
        publish_date="2026-03-27",
    )

    assert article.news == ["A"]
    assert article.sources == []
    assert article.quote == ""

    with pytest.raises(ValidationError):
        ParsedArticle(title="3月27日 读懂世界", news=[], publish_date="2026-03-27")


def test_daily_news_document_accepts_m1_schema() -> None:
    doc = DailyNewsDocument(
        date="2026-03-27",
        news=["A", "B"],
        cover="https://example.com/cover.png",
        title="每天60秒读懂世界｜3月27日",
        link="https://mp.weixin.qq.com/s/example",
        publish_date="2026-03-27 06:30:00",
        create_date="2026-03-27 06:30:00",
        update_date="2026-03-27 06:35:00",
    )

    assert doc.image == ""
    assert doc.sources == []
    assert len(doc.news) == 2

    with pytest.raises(ValidationError):
        DailyNewsDocument(
            date="2026-03-27",
            news=[],
            title="每天60秒读懂世界｜3月27日",
            link="https://mp.weixin.qq.com/s/example",
            publish_date="2026-03-27 06:30:00",
            create_date="2026-03-27 06:30:00",
            update_date="2026-03-27 06:35:00",
        )


def test_load_accounts_filters_disabled_and_sorts_by_priority(tmp_path: Path) -> None:
    accounts_file = tmp_path / "accounts.yaml"
    accounts_file.write_text(
        """
accounts:
  - name: low
    wechat_id: low_id
    fake_id: low_fake
    query: low query
    enabled: true
    priority: 10
  - name: disabled
    wechat_id: disabled_id
    fake_id: disabled_fake
    query: disabled query
    enabled: false
    priority: 999
  - name: high
    wechat_id: high_id
    fake_id: high_fake
    query: high query
    enabled: true
    priority: 20
""".strip(),
        encoding="utf-8",
    )

    accounts = load_accounts(accounts_file)

    assert [account.name for account in accounts] == ["high", "low"]
    assert all(account.enabled for account in accounts)
