from __future__ import annotations

import logging
from datetime import datetime
from typing import Sequence

from app.application.article_selector import select_article
from app.domain.models import AccountConfig, DailyNewsDocument, JobRunResult, ParsedArticle
from app.infrastructure.clock import format_beijing_datetime
from app.ports.article_parser import ArticleParser
from app.ports.image_renderer import ImageRenderer
from app.ports.repository import DailyNewsRepository, StaticAssetsRepository
from app.ports.source_client import SourceClient

logger = logging.getLogger(__name__)


class DailyJobService:
    def __init__(
        self,
        *,
        source_client: SourceClient,
        parser: ArticleParser,
        repository: StaticAssetsRepository | DailyNewsRepository,
        accounts: Sequence[AccountConfig],
        image_renderer: ImageRenderer | None = None,
    ) -> None:
        self._source_client = source_client
        self._parser = parser
        self._repository = repository
        self._accounts = list(accounts)
        self._image_renderer = image_renderer

    def run(self, target_date: str) -> JobRunResult:
        if self._supports_static_assets():
            return self._run_with_static_assets(target_date)

        if self._repository.exists(target_date):
            logger.info("daily news already exists for %s", target_date)
            return JobRunResult(status="skipped", target_date=target_date)

        document = self._fetch_document(target_date)
        self._repository.save(document)
        logger.info("saved daily news for %s", target_date)
        return JobRunResult(status="updated", target_date=target_date, document=document)

    def _run_with_static_assets(self, target_date: str) -> JobRunResult:
        repository = self._static_repository()
        json_exists = repository.json_exists(target_date)
        image_exists = repository.image_exists(target_date)

        if json_exists and image_exists:
            logger.info("json and image already exist for %s", target_date)
            return JobRunResult(status="skipped", target_date=target_date)

        if json_exists:
            document = repository.load_document(target_date)
            if document is None:
                raise RuntimeError(f"document missing for {target_date}")
            final_document = self._render_and_save(repository, document)
            return JobRunResult(
                status="backfilled_image",
                target_date=target_date,
                document=final_document,
            )

        document = self._fetch_document(target_date)
        final_document = self._render_and_save(repository, document)
        return JobRunResult(status="updated", target_date=target_date, document=final_document)

    def _fetch_document(self, target_date: str) -> DailyNewsDocument:
        target = datetime.strptime(target_date, "%Y-%m-%d")
        query_prefix = f"{target.month}月{target.day}日"

        for account in self._accounts:
            query = f"{query_prefix} {account.query}"
            try:
                candidates = self._source_client.search_articles(account.fake_id, query)
                selected = select_article(target_date, account, candidates)
                if selected is None:
                    continue

                html = self._source_client.fetch_article_html(selected.link)
                parsed = self._parse_article(html, account.parser_profile)
            except Exception:
                logger.exception("account %s failed for %s", account.name, target_date)
                continue

            return DailyNewsDocument(
                date=target_date,
                news=parsed.news,
                sources=parsed.sources,
                cover=parsed.cover,
                image="",
                title=parsed.title,
                quote=parsed.quote,
                link=selected.link,
                publish_date=parsed.publish_date,
                create_date=format_beijing_datetime(selected.create_ts),
                update_date=format_beijing_datetime(selected.update_ts),
            )

        raise RuntimeError(f"no article found for {target_date}")

    def _render_and_save(
        self,
        repository: StaticAssetsRepository,
        document: DailyNewsDocument,
    ) -> DailyNewsDocument:
        if self._image_renderer is None:
            raise RuntimeError("image_renderer is required for static asset rendering")

        image_bytes = self._image_renderer.render(document)
        repository.save_image(document.date, image_bytes)
        final_document = document.model_copy(
            update={"image": repository.build_image_url(document.date)}
        )
        repository.save_document(final_document)
        logger.info("saved daily news assets for %s", document.date)
        return final_document

    def _supports_static_assets(self) -> bool:
        required = (
            "json_exists",
            "image_exists",
            "load_document",
            "save_document",
            "save_image",
            "build_image_url",
        )
        return all(hasattr(self._repository, name) for name in required)

    def _static_repository(self) -> StaticAssetsRepository:
        if not isinstance(self._repository, StaticAssetsRepository):
            raise RuntimeError("static assets repository is required")
        return self._repository

    def close(self) -> None:
        close = getattr(self._source_client, "close", None)
        if callable(close):
            close()

    def _parse_article(self, html: str, parser_profile: str) -> ParsedArticle:
        try:
            return self._parser.parse(html, parser_profile)  # type: ignore[misc]
        except TypeError:
            # Compatibility for tests/fake parsers that only accept `html`.
            return self._parser.parse(html)  # type: ignore[misc]
