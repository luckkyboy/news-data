from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from app.domain.models import DailyNewsDocument
from app.infrastructure.clock import current_beijing_datetime
from app.ports.repository import StaticAssetsRepository


class StaticAssetsRepositoryImpl(StaticAssetsRepository):
    def __init__(
        self,
        *,
        json_dir: Path | str,
        image_dir: Path | str,
        image_base_url: str,
        now_provider: Callable[[], object] | None = None,
    ) -> None:
        self._json_dir = Path(json_dir)
        self._image_dir = Path(image_dir)
        self._image_base_url = image_base_url.rstrip("/") + "/"
        self._now_provider = now_provider or current_beijing_datetime
        self._json_dir.mkdir(parents=True, exist_ok=True)
        self._image_dir.mkdir(parents=True, exist_ok=True)

    def exists(self, date: str) -> bool:
        return self.json_exists(date)

    def save(self, document: DailyNewsDocument) -> None:
        self.save_document(document)

    def json_exists(self, date: str) -> bool:
        return self._json_path(date).exists()

    def image_exists(self, date: str) -> bool:
        return self._image_path(date).exists()

    def load_document(self, date: str) -> DailyNewsDocument | None:
        path = self._json_path(date)
        if not path.exists():
            return None
        return DailyNewsDocument.model_validate_json(path.read_text(encoding="utf-8"))

    def save_document(self, document: DailyNewsDocument) -> None:
        self._stamp_document(document)
        self._json_path(document.date).write_text(
            json.dumps(document.model_dump(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def save_image(self, date: str, content: bytes) -> None:
        self._image_path(date).write_bytes(content)

    def build_image_url(self, date: str) -> str:
        return f"{self._image_base_url}{date}.png"

    def _json_path(self, date: str) -> Path:
        return self._json_dir / f"{date}.json"

    def _image_path(self, date: str) -> Path:
        return self._image_dir / f"{date}.png"

    def _stamp_document(self, document: DailyNewsDocument) -> None:
        now_text = self._now_provider().strftime("%Y-%m-%d %H:%M:%S")
        if not document.create_date:
            document.create_date = now_text
        document.update_date = now_text
