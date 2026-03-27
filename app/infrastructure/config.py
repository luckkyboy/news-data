from __future__ import annotations

import os
from pathlib import Path

import yaml

from app.domain.models import AccountConfig


def load_accounts(path: Path | str) -> list[AccountConfig]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    accounts = [AccountConfig.model_validate(item) for item in raw.get("accounts", [])]
    return sorted(
        (account for account in accounts if account.enabled),
        key=lambda account: account.priority,
        reverse=True,
    )


def get_image_base_url() -> str:
    return os.getenv(
        "IMAGE_BASE_URL",
        "https://cdn.jsdelivr.net/gh/luckkyboy/news-data@main/static/images/",
    )
