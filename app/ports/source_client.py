from __future__ import annotations

from typing import Protocol

from app.domain.models import CandidateArticle


class SourceClient(Protocol):
    def search_articles(self, fake_id: str, query: str, count: int = 6) -> list[CandidateArticle]:
        ...

    def fetch_article_html(self, link: str) -> str:
        ...
