from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import Protocol

from app.domain.models import ParsedArticle

_NEWS_PATTERN = re.compile(r"^\s*\d+\s*[、\.．]\s*(.+?)\s*$")
_QUOTE_PATTERN = re.compile(
    r"^\s*[【\[]?\s*(?:微语|每日一句|每日金句|金句|心语|早安心语)\s*[】\]]?\s*[:：]?\s*(.+?)\s*$"
)
_SOURCE_PATTERN = re.compile(
    r"^\s*[【\[]?\s*(?:新闻来源|来源)\s*[】\]]?\s*[:：|丨]?\s*(.+?)\s*$"
)
_AD_BLACKLIST = frozenset(
    {
        "设置为星标",
        "点击文末右下角",
        "公众号ID",
    }
)
_SOURCE_SPLIT_PATTERN = re.compile(r"\s*[、，,/｜|]\s*")


@dataclass(slots=True)
class _ExtractedContent:
    title: str
    publish_date: str
    cover: str
    paragraphs: list[str]
    blocks: list[str]


class _WeChatArticleHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.cover = ""
        self._in_page_content = False
        self._page_content_depth = 0
        self._in_paragraph = False
        self._paragraph_buffer: list[str] = []
        self.paragraphs: list[str] = []
        self._capture_depth = 0
        self._capture_buffer: list[str] = []
        self.blocks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = {key: value or "" for key, value in attrs}
        if tag == "meta" and attrs_map.get("property") == "og:image":
            self.cover = attrs_map.get("content", "")
        elif tag == "div" and attrs_map.get("id") == "page-content":
            self._in_page_content = True
            self._page_content_depth = 1
        elif self._in_page_content:
            self._page_content_depth += 1
            if tag == "p":
                self._in_paragraph = True
                self._paragraph_buffer = []
            if tag in {"p", "section"}:
                if self._capture_depth == 0:
                    self._capture_buffer = []
                self._capture_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if not self._in_page_content:
            return
        if tag == "p" and self._in_paragraph:
            text = unescape("".join(self._paragraph_buffer)).strip()
            if text:
                self.paragraphs.append(text)
            self._in_paragraph = False
            self._paragraph_buffer = []
        if self._capture_depth > 0 and tag in {"p", "section"}:
            self._capture_depth -= 1
            if self._capture_depth == 0:
                text = unescape("".join(self._capture_buffer)).strip()
                if text:
                    self.blocks.append(text)
                self._capture_buffer = []
        self._page_content_depth -= 1
        if self._page_content_depth <= 0:
            self._in_page_content = False

    def handle_data(self, data: str) -> None:
        if self._in_page_content and self._in_paragraph:
            self._paragraph_buffer.append(data)
        if self._in_page_content and self._capture_depth > 0:
            self._capture_buffer.append(data)


class _ParseStrategy(Protocol):
    def extract_news_and_quote(self, paragraphs: list[str]) -> tuple[list[str], str]:
        ...

    def extract_sources(self, blocks: list[str], paragraphs: list[str]) -> list[str]:
        ...


class _BaseStrategy:
    def extract_news_and_quote(self, paragraphs: list[str]) -> tuple[list[str], str]:
        news: list[str] = []
        quote = ""
        for paragraph in paragraphs:
            normalized = _normalize(paragraph)
            if not normalized or _is_blacklisted(normalized):
                continue
            if not quote:
                match = _QUOTE_PATTERN.match(normalized)
                if match:
                    quote = _trim_noise(match.group(1))
                    continue
            match = _NEWS_PATTERN.match(normalized)
            if not match:
                continue
            item = _trim_noise(match.group(1))
            if _is_blacklisted(item):
                continue
            news.append(item)
        return news, quote

    def extract_sources(self, blocks: list[str], paragraphs: list[str]) -> list[str]:
        for text in [*blocks, *paragraphs]:
            normalized = _normalize(text)
            if not normalized:
                continue
            match = _SOURCE_PATTERN.match(normalized)
            if match:
                return self._split_sources(match.group(1))
        return []

    def _cleanup_source_text(self, text: str) -> str:
        cleaned = _trim_noise(text)
        cleaned = re.sub(r"[（(]综合[）)]", "", cleaned).strip()
        cleaned = re.sub(r"等$", "", cleaned).strip()
        return cleaned

    def _split_sources(self, text: str) -> list[str]:
        cleaned = self._cleanup_source_text(text)
        parts = _SOURCE_SPLIT_PATTERN.split(cleaned)
        result: list[str] = []
        for part in parts:
            item = part.strip()
            if not item:
                continue
            item = re.sub(r"等$", "", item).strip()
            if item:
                result.append(item)
        return result


class _GreenJianStrategy(_BaseStrategy):
    def _cleanup_source_text(self, text: str) -> str:
        cleaned = super()._cleanup_source_text(text)
        cleaned = re.split(
            r"(?:绿健君微信二维码|微信二维码|欢迎添加|交个朋友)",
            cleaned,
            maxsplit=1,
        )[0]
        return cleaned.strip()


class WeChatArticleParser:
    def __init__(self, default_profile: str = "generic") -> None:
        self._default_profile = default_profile
        self._strategies: dict[str, _ParseStrategy] = {
            "generic": _BaseStrategy(),
            "greenjian": _GreenJianStrategy(),
        }

    def parse(self, html: str, parser_profile: str | None = None) -> ParsedArticle:
        extracted = self._extract_content(html)
        strategy = self._resolve_strategy(parser_profile)
        news, quote = strategy.extract_news_and_quote(extracted.paragraphs)
        if not news:
            raise ValueError("news is empty")
        sources = strategy.extract_sources(extracted.blocks, extracted.paragraphs)
        return ParsedArticle(
            title=extracted.title,
            news=news,
            sources=sources,
            cover=extracted.cover,
            quote=quote,
            publish_date=extracted.publish_date,
        )

    def _resolve_strategy(self, parser_profile: str | None) -> _ParseStrategy:
        key = (parser_profile or self._default_profile).strip().lower()
        return self._strategies.get(key, self._strategies["generic"])

    def _extract_content(self, html: str) -> _ExtractedContent:
        parser = _WeChatArticleHTMLParser()
        parser.feed(html)
        title = _extract_by_regex(html, r'<h1[^>]*id=["\']activity-name["\'][^>]*>(.*?)</h1>')
        if not title:
            title = _extract_by_regex(html, r"<title>(.*?)</title>")
        publish_date = _extract_by_regex(
            html,
            r'<em[^>]*id=["\']publish_time["\'][^>]*>(.*?)</em>',
        )
        if not publish_date:
            publish_date = _extract_by_regex(
                html,
                r"create_time\s*:\s*JsDecode\('([^']+)'\)",
            )
            publish_date = _normalize_publish_date(publish_date)
        cover = parser.cover or _extract_by_regex(
            html,
            r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\'](.*?)["\']',
        )
        return _ExtractedContent(
            title=title,
            publish_date=publish_date,
            cover=cover,
            paragraphs=parser.paragraphs,
            blocks=parser.blocks,
        )


def _extract_by_regex(html: str, pattern: str) -> str:
    match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return _normalize(match.group(1))


def _normalize(text: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "", text)).strip()


def _trim_noise(text: str) -> str:
    return text.rstrip("。.;；")


def _is_blacklisted(text: str) -> bool:
    return any(phrase in text for phrase in _AD_BLACKLIST)


def _normalize_publish_date(text: str) -> str:
    normalized = text.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", normalized):
        return f"{normalized}:00"
    return normalized
