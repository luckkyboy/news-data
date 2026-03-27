from __future__ import annotations

from datetime import datetime

from app.domain.models import AccountConfig, CandidateArticle
from app.infrastructure.clock import to_beijing_datetime


def select_article(
    target_date: str,
    account: AccountConfig,
    candidates: list[CandidateArticle],
) -> CandidateArticle | None:
    target = datetime.strptime(target_date, "%Y-%m-%d")
    date_token = f"{target.month}月{target.day}日"

    for candidate in candidates:
        if date_token not in candidate.title:
            continue
        if account.query not in candidate.title:
            continue

        update_dt = to_beijing_datetime(candidate.update_ts)
        if update_dt.year != target.year or update_dt.month != target.month:
            continue

        return candidate

    return None
