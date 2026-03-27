from __future__ import annotations

import json
from pathlib import Path

from app.domain.models import DailyNewsDocument


class LocalJsonRepository:
    def __init__(self, base_dir: Path | str) -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def exists(self, date: str) -> bool:
        return self._path_for(date).exists()

    def save(self, document: DailyNewsDocument) -> None:
        path = self._path_for(document.date)
        path.write_text(
            json.dumps(document.model_dump(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _path_for(self, date: str) -> Path:
        return self._base_dir / f"{date}.json"
