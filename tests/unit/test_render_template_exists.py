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


def test_base_template_uses_adaptive_height_layout_contract() -> None:
    base_template = Path(TEMPLATE_PATH).parent / "base.html"
    content = base_template.read_text(encoding="utf-8")
    content_section = content.split(".content {", maxsplit=1)[1].split("}", maxsplit=1)[0]

    assert "#news-card {" in content
    assert "display: flex;" in content
    assert "flex-direction: column;" in content
    assert "height: 1800px;" not in content
    assert "grid-template-rows:" not in content
    assert ".content {" in content
    assert "overflow: hidden;" not in content_section
    assert ".quote-zone {" in content
    assert "margin-bottom: 8px;" in content
