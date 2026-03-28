from __future__ import annotations

import re
from datetime import date as datetime_date
from typing import TypedDict

from app.domain.models import DailyNewsDocument


class NewsTemplateContext(TypedDict):
    font_face_css: str
    hero_meta_text: str
    news_items: list[str]
    quote_text: str
    source_text: str
    news_count_text: str
    updated_text: str
    document: dict[str, object]


class DailyNewsTemplateContextBuilder:
    _DATE_REGEX = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
    _LUNAR_TEXT_REGEX = re.compile(r"农历[^，,！!]+")
    _GANZHI_YEAR_REGEX = re.compile(r"^[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]年")
    _GANZHI_STEMS = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")
    _GANZHI_BRANCHES = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")
    _WEEKDAY_LABELS = ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")

    def build(self, document: DailyNewsDocument, *, font_face_css: str) -> NewsTemplateContext:
        return {
            "font_face_css": font_face_css,
            "hero_meta_text": self._build_hero_meta_text(document),
            "news_items": document.news,
            "quote_text": document.quote.strip(),
            "source_text": "/".join(document.sources),
            "news_count_text": f"共 {len(document.news)} 条国内外精选新闻 ",
            "updated_text": self._build_updated_text(document.update_date),
            "document": document.model_dump(),
        }

    def _build_hero_meta_text(self, document: DailyNewsDocument) -> str:
        date_parts = self._parse_date_parts(document.date)
        date_text = (
            f"{date_parts[0]}年{date_parts[1]}月{date_parts[2]}日"
            if date_parts is not None
            else ""
        )
        weekday_text = self._format_chinese_weekday(date_parts)
        lunar_text = self._build_lunar_display(document.date, document.title)
        return " / ".join(part for part in (date_text, weekday_text, lunar_text) if part)

    def _build_updated_text(self, value: str) -> str:
        if not value:
            return ""
        return f"   更新于 {self._trim_seconds(value)}"

    @classmethod
    def _parse_date_parts(cls, value: str) -> tuple[int, int, int] | None:
        match = cls._DATE_REGEX.fullmatch(value)
        if match is None:
            return None
        year, month, day = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        return year, month, day

    @classmethod
    def _format_chinese_weekday(cls, date_parts: tuple[int, int, int] | None) -> str:
        if date_parts is None:
            return ""
        year, month, day = date_parts
        try:
            weekday = datetime_date(year, month, day).weekday()
        except ValueError:
            return ""
        return cls._WEEKDAY_LABELS[weekday]

    @classmethod
    def _extract_lunar_text(cls, title: str) -> str:
        if not title:
            return ""
        match = cls._LUNAR_TEXT_REGEX.search(title)
        return match.group(0).replace("农历", "", 1).strip() if match else ""

    @classmethod
    def _ganzhi_year(cls, year: int) -> str:
        offset = year - 1984  # 1984 = 甲子
        stem = cls._GANZHI_STEMS[offset % 10]
        branch = cls._GANZHI_BRANCHES[offset % 12]
        return f"{stem}{branch}"

    @classmethod
    def _build_lunar_display(cls, date_value: str, title: str) -> str:
        from_title = cls._extract_lunar_text(title)
        if not from_title:
            return ""
        if cls._GANZHI_YEAR_REGEX.match(from_title):
            return from_title
        date_parts = cls._parse_date_parts(date_value)
        if date_parts is None:
            return from_title
        return f"{cls._ganzhi_year(date_parts[0])}年{from_title}"

    @staticmethod
    def _trim_seconds(value: str) -> str:
        return value[:16] if len(value) >= 16 else value

