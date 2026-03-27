from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.models import DailyNewsDocument


@runtime_checkable
class ImageRenderer(Protocol):
    def render(self, document: DailyNewsDocument) -> bytes:
        ...
