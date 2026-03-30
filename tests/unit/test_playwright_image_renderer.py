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
    assert '<div id="quote" class="quote-shell">' in html
    assert '<span class="quote-mark quote-mark-left" aria-hidden="true">『</span>' in html
    assert '<p class="quote-text">一句话总结</p>' in html
    assert '<span class="quote-mark quote-mark-right" aria-hidden="true">』</span>' in html
    assert "window.__DATA__ =" not in html
    assert "__NEWS_DATA__" not in html
    assert "2026年3月27日" in html
    assert "更新于 2026-03-27 06:35" in html
    assert 'data-theme="cool"' in html


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
    assert 'data-theme="cool"' in html


def test_build_html_uses_adaptive_card_height_layout() -> None:
    document = DailyNewsDocument(
        date="2026-03-29",
        news=["第一条", "第二条", "第三条"],
        cover="https://example.com/cover.png",
        image="",
        title="每天60秒读懂世界｜3月29日",
        quote="一句话总结",
        link="https://mp.weixin.qq.com/s/example",
        publish_date="2026-03-29 06:30:00",
        create_date="2026-03-29 06:30:00",
        update_date="2026-03-29 06:35:00",
    )
    renderer = PlaywrightImageRenderer(template_path=TEMPLATE_PATH)

    html = renderer.build_html(document)

    assert "#news-card {" in html
    assert "display: flex;" in html
    assert "flex-direction: column;" in html
    assert "height: 1800px;" not in html
    assert "grid-template-rows:" not in html
    assert ".quote-zone {" in html
    assert "margin-bottom: 8px;" in html
    assert ".quote-shell {" in html
    assert "position: relative;" in html
    assert "font-style: italic;" in html
    assert "transform: translateY(-50%) skewX(-12deg);" in html


def test_build_html_uses_warm_theme_for_weekend() -> None:
    document = DailyNewsDocument(
        date="2026-03-29",
        news=["第一条"],
        cover="https://example.com/cover.png",
        image="",
        title="每天60秒读懂世界｜3月29日",
        quote="一句话总结",
        link="https://mp.weixin.qq.com/s/example",
        publish_date="2026-03-29 06:30:00",
        create_date="2026-03-29 06:30:00",
        update_date="2026-03-29 06:35:00",
    )
    renderer = PlaywrightImageRenderer(template_path=TEMPLATE_PATH)

    html = renderer.build_html(document)

    assert 'data-theme="warm"' in html
    assert 'body[data-theme="warm"] {' in html
