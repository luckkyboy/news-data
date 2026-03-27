from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.models import DailyNewsDocument


@runtime_checkable
class DailyNewsRepository(Protocol):
    def exists(self, date: str) -> bool:
        ...

    def save(self, document: DailyNewsDocument) -> None:
        ...


@runtime_checkable
class StaticAssetsRepository(DailyNewsRepository, Protocol):
    def json_exists(self, date: str) -> bool:
        ...

    def image_exists(self, date: str) -> bool:
        ...

    def load_document(self, date: str) -> DailyNewsDocument | None:
        ...

    def save_document(self, document: DailyNewsDocument) -> None:
        ...

    def save_image(self, date: str, content: bytes) -> None:
        ...

    def build_image_url(self, date: str) -> str:
        ...
