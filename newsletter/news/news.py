from __future__ import annotations

import datetime
from pathlib import Path

from pydantic import BaseModel

from newsletter.settings import settings


class News(BaseModel):
    title: str
    description: str
    sources: list[str]


class Newsletter(BaseModel):
    news: list[News]
    name: str
    created_at: datetime.datetime
    path: Path

    @classmethod
    def from_path(cls, path: Path) -> Newsletter:
        raw_text = path.read_text()
        return Newsletter.model_validate_json(raw_text)

    def save(self):
        self.path.write_text(self.model_dump_json(indent=2), encoding="utf-8")


def get_newsletters() -> list[Path]:
    return sorted(
        settings.storage.newsletter_folder.iterdir(),
        key=lambda f: f.stat().st_ctime,
        reverse=True,
    )
