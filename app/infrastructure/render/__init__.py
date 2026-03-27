from __future__ import annotations

from pathlib import Path

TEMPLATE_PATH = Path(__file__).with_name("template.html")


def load_template_text() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")
