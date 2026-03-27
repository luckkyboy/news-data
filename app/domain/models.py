from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AccountConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    wechat_id: str
    fake_id: str
    query: str
    parser_profile: str = "generic"
    enabled: bool = True
    priority: int = 0


class CandidateArticle(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str
    link: str
    cover: str = ""
    create_ts: int
    update_ts: int


class ParsedArticle(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str
    news: list[str] = Field(min_length=1)
    sources: list[str] = Field(default_factory=list)
    cover: str = ""
    quote: str = ""
    publish_date: str


class DailyNewsDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")

    date: str
    news: list[str] = Field(min_length=1)
    sources: list[str] = Field(default_factory=list)
    cover: str = ""
    image: str = ""
    title: str
    quote: str = ""
    link: str
    publish_date: str
    create_date: str
    update_date: str


class JobRunResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Literal["skipped", "updated", "backfilled_image"]
    target_date: str
    document: DailyNewsDocument | None = None
