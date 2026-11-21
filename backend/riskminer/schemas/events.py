from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from pydantic import BaseModel, Field

from riskminer.schemas.common import ORM, ReviewFields


class EventOut(ReviewFields):
    id: uuid.UUID
    project_id: uuid.UUID | None = None
    project_code: str | None = None
    procedure_id: uuid.UUID | None = None
    contract_id: uuid.UUID | None = None
    change_id: uuid.UUID | None = None
    notice_id: uuid.UUID | None = None
    document_id: uuid.UUID | None = None
    event_type: str
    event_date: dt.date | None = None
    risk_codes: list[str] = Field(default_factory=list)
    title: str | None = None
    cause: str | None = None
    signal: str | None = None
    effect: str | None = None
    effect_days: float | None = None
    effect_pln: float | None = None
    effect_pct: float | None = None
    mitigation: str | None = None
    mitigation_effect: str | None = None
    mitigation_rule: str | None = None
    quote: str | None = None
    model_label: str | None = None
    exemplary: bool = False
    tier: str = "deep"


class EventPatch(BaseModel):
    changes: dict[str, Any]
    comment: str | None = None


class DataIssueOut(ReviewFields):
    id: uuid.UUID
    project_id: uuid.UUID | None = None
    procedure_id: uuid.UUID | None = None
    kind: str
    field: str | None = None
    state: str | None = None  # potwierdzone | częściowe | brak | sprzeczne
    message: str
    what_to_add: str | None = None
    impact: str | None = None


class CompletenessOut(BaseModel):
    project_id: uuid.UUID
    score: float
    items: list[DataIssueOut]


class RiskCategoryOut(ReviewFields):
    id: uuid.UUID
    sector: str
    code: str
    name: str
    effects: str | None = None
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)
    parent_code: str | None = None
    version: int = 1


class LessonOut(ReviewFields):
    id: uuid.UUID
    project_id: uuid.UUID | None = None
    document_id: uuid.UUID | None = None
    source_kind: str | None = None
    title: str | None = None
    cause: str | None = None
    signal: str | None = None
    effect: str | None = None
    recommendation: str | None = None
    risk_codes: list[str] = Field(default_factory=list)
    subsectors: list[str] = Field(default_factory=list)


class ClauseOut(ReviewFields):
    id: uuid.UUID
    code: str | None = None
    risk_code: str | None = None
    title: str | None = None
    trigger: str | None = None
    legal_basis: str | None = None
    text: str
    version: int = 1


class ReanalysisDiff(BaseModel):
    project_id: uuid.UUID
    new: list[EventOut] = Field(default_factory=list)
    confirmed: list[EventOut] = Field(default_factory=list)
    changed: list[dict[str, Any]] = Field(default_factory=list)
    closed: list[EventOut] = Field(default_factory=list)


class _Unused(ORM):
    pass
