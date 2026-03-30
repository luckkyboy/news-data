from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from app.domain.models import DailyNewsDocument
from app.infrastructure.clock import current_beijing_datetime


class LocalJsonRepository:
    def __init__(
        self,
        base_dir: Path | str,
        *,
        now_provider: Callable[[], object] | None = None,
    ) -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._now_provider = now_provider or current_beijing_datetime

    def exists(self, date: str) -> bool:
        return self._path_for(date).exists()

    def save(self, document: DailyNewsDocument) -> None:
        self._stamp_document(document)
        path = self._path_for(document.date)
        path.write_text(
            json.dumps(document.model_dump(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _path_for(self, date: str) -> Path:
        return self._base_dir / f"{date}.json"

    def _stamp_document(self, document: DailyNewsDocument) -> None:
        now_text = self._now_provider().strftime("%Y-%m-%d %H:%M:%S")
        if not document.create_date:
            document.create_date = now_text
        document.update_date = now_text
