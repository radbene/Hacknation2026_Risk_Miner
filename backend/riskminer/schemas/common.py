from __future__ import annotations

import datetime as dt
import uuid
from enum import Enum
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ReviewStatus(str, Enum):
    proposed = "proposed"
    approved = "approved"
    edited = "edited"
    rejected = "rejected"


class BlockLabel(str, Enum):
    """Every analysis block is labelled (UI: [Dane źródłowe] / [Obliczenia] / [Wniosek modelu])."""

    dane_zrodlowe = "dane_zrodlowe"
    obliczenia = "obliczenia"
    wniosek_modelu = "wniosek_modelu"


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    offset: int = 0
    limit: int = 50


class ReviewFields(ORM):
    status: ReviewStatus = ReviewStatus.proposed
    method: str | None = None
    confidence: float | None = None
    evidence_ids: list[uuid.UUID] = Field(default_factory=list)
    proposal: dict[str, Any] | None = None
    reviewed_by: str | None = None
    reviewed_at: dt.datetime | None = None


class EvidenceOut(ORM):
    id: uuid.UUID
    source_code: str
    kind: str
    url: str | None = None
    retrieved_from: str | None = None
    retrieved_at: dt.datetime | None = None
    locator: dict[str, Any] = Field(default_factory=dict)
    quote: str | None = None
    quote_verified: bool | None = None
    notice_id: uuid.UUID | None = None
    document_id: uuid.UUID | None = None
    chunk_id: uuid.UUID | None = None
    import_sha256: str | None = None
    derivation: dict[str, Any] | None = None


class JobOut(ORM):
    id: uuid.UUID
    kind: str
    params: dict[str, Any] = Field(default_factory=dict)
    state: Literal["queued", "running", "done", "failed"]
    progress: float = 0
    message: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: dt.datetime
    started_at: dt.datetime | None = None
    finished_at: dt.datetime | None = None
    created_by: str | None = None


class Message(BaseModel):
    ok: bool = True
    message: str | None = None
