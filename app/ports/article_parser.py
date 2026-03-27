from __future__ import annotations

from typing import Protocol

from app.domain.models import ParsedArticle


class ArticleParser(Protocol):
    def parse(self, html: str) -> ParsedArticle:
        ...
