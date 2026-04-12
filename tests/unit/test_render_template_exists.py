from pathlib import Path

from app.infrastructure.render import TEMPLATE_PATH


def test_render_template_exists_and_uses_structured_layout() -> None:
    template_path = Path(TEMPLATE_PATH)
    content = template_path.read_text(encoding="utf-8")

    assert template_path.exists()
    assert '{% extends "base.html" %}' in content
    assert '{% include "partials/hero.html" %}' in content
    assert '{% include "partials/content.html" %}' in content
    assert '{% include "partials/quote.html" %}' in content
    assert '{% include "partials/footer.html" %}' in content


def test_render_template_partials_exist() -> None:
    root = Path(TEMPLATE_PATH).parent
    assert (root / "base.html").exists()
    assert (root / "partials/hero.html").exists()
    assert (root / "partials/content.html").exists()
    assert (root / "partials/quote.html").exists()
    assert (root / "partials/footer.html").exists()
    hero_partial = (root / "partials/hero.html").read_text(encoding="utf-8")
    assert 'class="hero-meta-separator"' in hero_partial


def test_base_template_uses_adaptive_height_layout_contract() -> None:
    base_template = Path(TEMPLATE_PATH).parent / "base.html"
    content = base_template.read_text(encoding="utf-8")
    content_section = content.split(".content {", maxsplit=1)[1].split("}", maxsplit=1)[0]
    quote_zone_section = content.split(".quote-zone {", maxsplit=1)[1].split("}", maxsplit=1)[0]
    quote_shell_section = content.split(".quote-shell {", maxsplit=1)[1].split("}", maxsplit=1)[0]
    quote_mark_section = content.split(".quote-mark {", maxsplit=1)[1].split("}", maxsplit=1)[0]
    quote_text_section = content.split(".quote-text {", maxsplit=1)[1].split("}", maxsplit=1)[0]

    assert "#news-card {" in content
    assert "display: flex;" in content
    assert "flex-direction: column;" in content
    assert "height: 1800px;" not in content
    assert "grid-template-rows:" not in content
    assert ".content {" in content
    assert "overflow: hidden;" not in content_section
    assert ".quote-zone {" in content
    assert "margin-bottom: 0;" in content
    assert "padding: 14px 42px 16px;" in quote_zone_section
    assert "min-height: 104px;" in quote_zone_section
    assert "\n        height: 104px;" not in quote_zone_section
    assert "position: relative;" in quote_shell_section
    assert "display: flex;" in quote_shell_section
    assert "transform: translateY(-50%) skewX(-12deg);" in quote_mark_section
    assert "max-width: 84%;" in quote_text_section
    assert "font-style: italic;" in quote_text_section
    assert "color: var(--muted-strong);" in content.split(".hero-meta {", maxsplit=1)[1].split("}", maxsplit=1)[0]
    assert "color: var(--accent);" in content.split(".hero-meta-separator {", maxsplit=1)[1].split("}", maxsplit=1)[0]
    assert '<body data-theme="{{ theme_name }}">' in content
    assert 'body[data-theme="warm"] {' in content
    assert 'body[data-theme="forest"] {' in content
    assert 'body[data-theme="navy"] {' in content
    assert 'body[data-theme="terracotta"] {' in content
    assert 'body[data-theme="rose"] {' in content
    assert 'body[data-theme="citrus"] {' in content
    assert "--accent: #ef7d00;" in content
    assert "--hero-meta-size: 34px;" in content
    assert "--news-font-size: 38px;" in content
    assert "font-size: 34px;" in quote_text_section


def test_pages_preview_shell_exists() -> None:
    html = Path("pages/index.html").read_text(encoding="utf-8")
    js = Path("pages/app.js").read_text(encoding="utf-8")
    css = Path("pages/styles.css").read_text(encoding="utf-8")

    assert 'data-theme="cool"' in html
    assert 'class="split-shell"' in html
    assert 'class="preview-pane"' in html
    assert 'class="inspector-pane"' in html
    assert 'class="preview-topbar"' in html
    assert 'id="preview-image"' in html
    assert 'id="json-panel"' in html
    assert 'class="raw-json-panel"' in html
    assert 'id="current-date-label"' not in html
    assert 'id="date-list"' not in html
    assert 'id="summary-panel"' not in html
    assert "new URLSearchParams" in js
    assert 'const EARLIEST_DATE = "2026-03-26";' in js
    assert "themeByWeekday" in js
    assert "document.body.dataset.theme" in js
    assert "findAvailableDate" in js
    assert "syncNavigationButtons" in js
    assert 'fetch("./data/index.json")' not in js
    assert "width: min(calc(100vw - 36px), 1620px);" in css
    assert "grid-template-columns: minmax(0, 1200px) 384px;" in css
    assert "justify-content: center;" in css
    assert 'grid-template-areas: "badge actions";' in css
    assert "grid-template-columns: repeat(2, minmax(0, max-content));" in css
    toolbar_button_section = css.split(".preview-toolbar button,\n.preview-toolbar a {", maxsplit=1)[1].split(
        "}",
        maxsplit=1,
    )[0]
    assert "justify-content: center;" in toolbar_button_section
    assert "align-items: center;" in toolbar_button_section
    assert "grid-template-columns: minmax(0, 1fr) minmax(300px, 34vw);" in css
    assert 'grid-template-areas:\n      "badge"\n      "actions";' in css
    assert "grid-template-columns: repeat(2, minmax(0, 1fr));" in css
    assert "min-height: clamp(220px, 30dvh, 280px);" in css
    assert ".preview-toolbar button:disabled {" in css
    assert "object-fit: contain;" in css
    assert 'body[data-theme="warm"] {' in css
    assert "@media (max-width: 768px)" in css
