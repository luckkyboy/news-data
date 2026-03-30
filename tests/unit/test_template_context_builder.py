from __future__ import annotations

from app.domain.models import DailyNewsDocument
from app.infrastructure.render.template_context_builder import DailyNewsTemplateContextBuilder


def test_context_builder_builds_expected_render_context() -> None:
    document = DailyNewsDocument(
        date="2026-03-27",
        news=["第一条", "第二条"],
        sources=["新华社", "央视新闻"],
        cover="https://example.com/cover.png",
        image="",
        title="2026年3月27日#绿健简报，星期五，农历二月初九，早安！",
        quote=" 一句话总结 ",
        link="https://mp.weixin.qq.com/s/example",
        publish_date="2026-03-27 06:30:00",
        create_date="2026-03-27 06:30:00",
        update_date="2026-03-27 06:35:00",
    )
    builder = DailyNewsTemplateContextBuilder()

    context = builder.build(document, font_face_css="font-face")

    assert context["font_face_css"] == "font-face"
    assert context["theme_name"] == "rose"
    assert context["hero_meta_text"] == "2026年3月27日 / 星期五 / 丙午年二月初九"
    assert context["news_items"] == ["第一条", "第二条"]
    assert context["quote_text"] == "一句话总结"
    assert context["source_text"] == "新华社/央视新闻"
    assert context["news_count_text"] == "共 2 条国内外精选新闻 "
    assert context["updated_text"] == "   更新于 2026-03-27 06:30"


def test_context_builder_handles_missing_optional_fields() -> None:
    document = DailyNewsDocument(
        date="2026-03-27",
        news=["第一条"],
        sources=[],
        cover="",
        image="",
        title="每日简报",
        quote="",
        link="https://mp.weixin.qq.com/s/example",
        publish_date="2026-03-27 00:00:00",
        create_date="2026-03-27 00:00:00",
        update_date="",
    )
    builder = DailyNewsTemplateContextBuilder()

    context = builder.build(document, font_face_css="")

    assert context["theme_name"] == "rose"
    assert context["hero_meta_text"] == "2026年3月27日 / 星期五"
    assert context["quote_text"] == ""
    assert context["source_text"] == ""
    assert context["updated_text"] == "   更新于 2026-03-27 00:00"


def test_context_builder_maps_all_weekdays_to_expected_themes() -> None:
    builder = DailyNewsTemplateContextBuilder()
    expected = {
        "2026-03-30": "cool",
        "2026-03-31": "forest",
        "2026-04-01": "navy",
        "2026-04-02": "terracotta",
        "2026-04-03": "rose",
        "2026-04-04": "warm",
        "2026-04-05": "citrus",
    }

    for date_value, theme_name in expected.items():
        document = DailyNewsDocument(
            date=date_value,
            news=["第一条"],
            cover="https://example.com/cover.png",
            image="",
            title=f"每日简报｜{date_value[5:7].lstrip('0')}月{date_value[8:10].lstrip('0')}日",
            quote="一句话总结",
            link="https://mp.weixin.qq.com/s/example",
            publish_date=f"{date_value} 00:00:00",
            create_date=f"{date_value} 00:00:00",
            update_date="",
        )

        context = builder.build(document, font_face_css="")

        assert context["theme_name"] == theme_name
