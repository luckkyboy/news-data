from __future__ import annotations

from app.domain.models import DailyNewsDocument
from app.infrastructure.render import TEMPLATE_PATH
from app.infrastructure.render.playwright_image_renderer import PlaywrightImageRenderer


def test_build_html_injects_document_fields() -> None:
    document = DailyNewsDocument(
        date="2026-03-27",
        news=["第一条", "第二条"],
        cover="https://example.com/cover.png",
        image="",
        title="每天60秒读懂世界｜3月27日",
        quote="一句话总结",
        link="https://mp.weixin.qq.com/s/example",
        publish_date="2026-03-27 06:30:00",
        create_date="2026-03-27 06:30:00",
        update_date="2026-03-27 06:35:00",
    )
    renderer = PlaywrightImageRenderer(
        template_path=TEMPLATE_PATH,
    )

    html = renderer.build_html(document)

    assert "<li>第一条</li>" in html
    assert "『一句话总结』" in html
    assert "window.__DATA__ =" not in html
    assert "__NEWS_DATA__" not in html
    assert "2026年3月27日" in html
    assert "更新于 2026-03-27 06:35" in html


def test_build_html_uses_fixed_brand_header_and_omits_cover_rendering() -> None:
    document = DailyNewsDocument(
        date="2026-03-27",
        news=["第一条"],
        cover="https://example.com/cover.png",
        image="",
        title="2026年3月27日#绿健简报，星期五，农历二月初九，早安！",
        quote="",
        link="https://mp.weixin.qq.com/s/example",
        publish_date="2026-03-27 00:00:00",
        create_date="2026-03-27 00:00:00",
        update_date="2026-03-27 00:00:00",
    )
    renderer = PlaywrightImageRenderer(
        template_path=TEMPLATE_PATH,
    )

    html = renderer.build_html(document)

    assert "每日简报" in html
    assert "每天60秒读懂世界" not in html
    assert 'id="cover"' not in html
    assert "共 1 条国内外精选新闻" in html
    assert "更新于 2026-03-27 00:00" in html
    assert "丙午年二月初九" in html
