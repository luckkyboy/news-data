from pathlib import Path

from app.entrypoints.preview_page_index import build_preview_index


def test_build_preview_index_returns_sorted_items(tmp_path: Path) -> None:
    news_dir = tmp_path / "news"
    image_dir = tmp_path / "images"
    news_dir.mkdir()
    image_dir.mkdir()
    (news_dir / "2026-03-27.json").write_text("{}", encoding="utf-8")
    (news_dir / "2026-03-30.json").write_text("{}", encoding="utf-8")
    (image_dir / "2026-03-27.png").write_bytes(b"png")
    (image_dir / "2026-03-30.png").write_bytes(b"png")

    payload = build_preview_index(news_dir=news_dir, image_dir=image_dir)

    assert payload["latest"] == "2026-03-30"
    assert payload["items"] == [
        {
            "date": "2026-03-27",
            "json_path": "./static/news/2026-03-27.json",
            "image_path": "./static/images/2026-03-27.png",
        },
        {
            "date": "2026-03-30",
            "json_path": "./static/news/2026-03-30.json",
            "image_path": "./static/images/2026-03-30.png",
        },
    ]
