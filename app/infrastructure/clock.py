from __future__ import annotations

from datetime import datetime, timedelta, timezone

BEIJING_TZ = timezone(timedelta(hours=8))


def to_beijing_datetime(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp, tz=BEIJING_TZ)


def format_beijing_datetime(timestamp: int) -> str:
    return to_beijing_datetime(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def current_beijing_datetime() -> datetime:
    return datetime.now(BEIJING_TZ)
