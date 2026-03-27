from pathlib import Path

from app.infrastructure.render import TEMPLATE_PATH


def test_render_template_exists_and_has_required_placeholders() -> None:
    template_path = Path(TEMPLATE_PATH)
    content = template_path.read_text(encoding="utf-8")

    assert template_path.exists()
    assert 'id="news-card"' in content
    assert "__NEWS_DATA__" in content
    assert "title" in content
    assert "date" in content
    assert "publish_date" in content
    assert "news" in content
    assert "quote" in content
    assert "cover" in content
