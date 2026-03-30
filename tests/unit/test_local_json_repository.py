from datetime import datetime

from pathlib import Path

from app.domain.models import DailyNewsDocument
from app.infrastructure.storage.local_json_repository import LocalJsonRepository


def test_local_json_repository_creates_output_dir_and_saves_json(tmp_path: Path) -> None:
    output_dir = tmp_path / "static" / "60s"
    repository = LocalJsonRepository(
        output_dir,
        now_provider=lambda: datetime(2026, 3, 27, 8, 0, 0),
    )
    document = DailyNewsDocument(
        date="2026-03-27",
        news=["A", "B"],
        sources=["人民日报", "新华社"],
        cover="https://example.com/cover.png",
        image="",
        title="每日简报｜3月27日",
        quote="",
        link="https://mp.weixin.qq.com/s/example",
        publish_date="2026-03-27 06:30:00",
        create_date="",
        update_date="",
    )

    assert output_dir.exists()
    assert repository.exists("2026-03-27") is False

    repository.save(document)

    saved_path = output_dir / "2026-03-27.json"
    assert repository.exists("2026-03-27") is True
    assert saved_path.read_text(encoding="utf-8") == (
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
        '  "quote": "",\n'
        '  "link": "https://mp.weixin.qq.com/s/example",\n'
        '  "publish_date": "2026-03-27 06:30:00",\n'
        '  "create_date": "2026-03-27 08:00:00",\n'
        '  "update_date": "2026-03-27 08:00:00"\n'
        '}\n'
    )
