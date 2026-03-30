from datetime import datetime

from pathlib import Path

from app.domain.models import DailyNewsDocument
from app.infrastructure.storage.static_assets_repository import StaticAssetsRepositoryImpl


def test_static_assets_repository_saves_and_loads_json_and_png(tmp_path: Path) -> None:
    json_dir = tmp_path / "json"
    image_dir = tmp_path / "images"
    repository = StaticAssetsRepositoryImpl(
        json_dir=json_dir,
        image_dir=image_dir,
        image_base_url="https://cdn.example.com/assets/",
        now_provider=lambda: datetime(2026, 3, 27, 8, 0, 0),
    )
    document = DailyNewsDocument(
        date="2026-03-27",
        news=["A", "B"],
        sources=["人民日报", "新华社"],
        cover="https://example.com/cover.png",
        image="",
        title="每日简报｜3月27日",
        quote="一句话总结",
        link="https://mp.weixin.qq.com/s/example",
        publish_date="2026-03-27 06:30:00",
        create_date="",
        update_date="",
    )

    assert repository.json_exists("2026-03-27") is False
    assert repository.image_exists("2026-03-27") is False
    assert repository.load_document("2026-03-27") is None
    assert repository.build_image_url("2026-03-27") == (
        "https://cdn.example.com/assets/2026-03-27.png"
    )

    repository.save_document(document)
    repository.save_image("2026-03-27", b"\x89PNG\r\n\x1a\ncontent")

    assert repository.exists("2026-03-27") is True
    assert repository.json_exists("2026-03-27") is True
    assert repository.image_exists("2026-03-27") is True
    saved_document = repository.load_document("2026-03-27")
    assert saved_document is not None
    assert saved_document.create_date == "2026-03-27 08:00:00"
    assert saved_document.update_date == "2026-03-27 08:00:00"
    assert (json_dir / "2026-03-27.json").read_text(encoding="utf-8") == (
        '{\n'
        '  "date": "2026-03-27",\n'
        '  "news": [\n'
        '    "A",\n'
        '    "B"\n'
        '  ],\n'
        '  "sources": [\n'
        '    "人民日报",\n'
        '    "新华社"\n'
        '  ],\n'
        '  "cover": "https://example.com/cover.png",\n'
        '  "image": "",\n'
        '  "title": "每日简报｜3月27日",\n'
        '  "quote": "一句话总结",\n'
        '  "link": "https://mp.weixin.qq.com/s/example",\n'
        '  "publish_date": "2026-03-27 06:30:00",\n'
        '  "create_date": "2026-03-27 08:00:00",\n'
        '  "update_date": "2026-03-27 08:00:00"\n'
        '}\n'
    )
    assert (image_dir / "2026-03-27.png").read_bytes() == b"\x89PNG\r\n\x1a\ncontent"


def test_static_assets_repository_preserves_create_date_and_refreshes_update_date(
    tmp_path: Path,
) -> None:
    json_dir = tmp_path / "json"
    image_dir = tmp_path / "images"
    clock_values = iter(
        (
            datetime(2026, 3, 27, 8, 0, 0),
            datetime(2026, 3, 27, 9, 15, 0),
        )
    )
    repository = StaticAssetsRepositoryImpl(
        json_dir=json_dir,
        image_dir=image_dir,
        image_base_url="https://cdn.example.com/assets/",
        now_provider=lambda: next(clock_values),
    )
    document = DailyNewsDocument(
        date="2026-03-27",
        news=["A"],
        cover="https://example.com/cover.png",
        image="",
        title="每日简报｜3月27日",
        quote="一句话总结",
        link="https://mp.weixin.qq.com/s/example",
        publish_date="2026-03-27 06:30:00",
        create_date="",
        update_date="",
    )

    repository.save_document(document)
    repository.save_document(document.model_copy(update={"image": "https://cdn.example.com/assets/2026-03-27.png"}))

    saved_document = repository.load_document("2026-03-27")
    assert saved_document is not None
    assert saved_document.create_date == "2026-03-27 08:00:00"
    assert saved_document.update_date == "2026-03-27 09:15:00"
