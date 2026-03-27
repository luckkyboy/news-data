from app.application.article_selector import select_article
from app.domain.models import AccountConfig, CandidateArticle


def test_select_article_returns_first_matching_candidate() -> None:
    account = AccountConfig(
        name="主号",
        wechat_id="mt36501",
        fake_id="fake-id",
        query="读懂世界",
        enabled=True,
        priority=100,
    )
    first = CandidateArticle(
        title="3月27日 读懂世界",
        link="https://mp.weixin.qq.com/s/first",
        cover="",
        create_ts=1774564200,
        update_ts=1774564500,
    )
    second = CandidateArticle(
        title="3月27日 读懂世界",
        link="https://mp.weixin.qq.com/s/second",
        cover="",
        create_ts=1774564200,
        update_ts=1774564500,
    )

    selected = select_article(
        target_date="2026-03-27",
        account=account,
        candidates=[first, second],
    )

    assert selected == first


def test_select_article_returns_none_when_month_or_query_does_not_match() -> None:
    account = AccountConfig(
        name="主号",
        wechat_id="mt36501",
        fake_id="fake-id",
        query="读懂世界",
        enabled=True,
        priority=100,
    )
    candidate = CandidateArticle(
        title="3月27日 其他内容",
        link="https://mp.weixin.qq.com/s/example",
        cover="",
        create_ts=1774564200,
        update_ts=1774564500,
    )

    selected = select_article(
        target_date="2026-04-27",
        account=account,
        candidates=[candidate],
    )

    assert selected is None
