from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from pydantic import BaseModel, Field

from riskminer.schemas.common import ORM, ReviewFields


class DocumentOut(ReviewFields):
    id: uuid.UUID
    project_id: uuid.UUID | None = None
    procedure_id: uuid.UUID | None = None
    analysis_id: uuid.UUID | None = None
    doc_type: str | None = None
    phase: str | None = None
    title: str | None = None
    url: str | None = None
    file_name: str | None = None
    mime: str | None = None
    sha256: str | None = None
    version: int = 1
    pages: int | None = None
    source_code: str | None = None
    retrieved_at: dt.datetime | None = None
    text_status: str | None = None
    created_at: dt.datetime | None = None


class ChunkOut(ORM):
    id: uuid.UUID
    document_id: uuid.UUID | None = None
    notice_id: uuid.UUID | None = None
    ord: int
    page: int | None = None
    paragraph: int | None = None
    section: str | None = None
    start: int | None = None
    end: int | None = None
    locator: dict[str, Any] = Field(default_factory=dict)
    text: str


class DocumentFromUrlIn(BaseModel):
    url: str
    project_id: uuid.UUID | None = None
    analysis_id: uuid.UUID | None = None
    doc_type: str | None = None


class SearchHit(BaseModel):
    chunk: ChunkOut
    score: float
    highlight: str | None = None
