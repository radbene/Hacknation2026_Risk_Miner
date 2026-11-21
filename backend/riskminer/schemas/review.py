from __future__ import annotations

import datetime as dt
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

from riskminer.schemas.common import ORM

ObjectType = Literal["project", "project_procedure", "contract", "contract_change", "fact", "document",
                     "risk_category", "lesson", "clause", "event", "data_issue", "analysis", "analysis_item"]


class QueueItem(BaseModel):
    object_type: ObjectType
    object_id: uuid.UUID
    title: str
    summary: str | None = None
    status: str
    method: str | None = None
    confidence: float | None = None
    uncertainty: float | None = None  # 1 - confidence; queue is sorted by this (uncertain first)
    project_id: uuid.UUID | None = None
    project_code: str | None = None
    evidence_ids: list[uuid.UUID] = Field(default_factory=list)
    has_proposal: bool = False
    created_at: dt.datetime | None = None


class ReviewActionIn(BaseModel):
    action: Literal["accept", "edit", "reject", "exemplary", "unexemplary", "reopen", "accept_proposal",
                    "dismiss_proposal"]
    changes: dict[str, Any] | None = None  # for edit
    comment: str | None = None
    accept_proposal: bool = False  # take the pending rerun proposal


class BulkConfirmIn(BaseModel):
    object_type: ObjectType
    ids: list[uuid.UUID] | None = None
    min_confidence: float | None = 1.0  # e.g. confirm all key-based links with confidence 1.0
    project_id: uuid.UUID | None = None
    method: str | None = None  # e.g. only key-based links (kpo_ref / notice_no / ocid)
    comment: str | None = None


class RelinkIn(BaseModel):
    """Expert relink: a candidate procedure id, or an OCID / BZP notice number (fetched later if unknown)."""

    procedure_id: uuid.UUID | None = None
    ocid: str | None = None
    notice_number: str | None = None
    part_no: int | None = None
    comment: str | None = None


class BulkResult(BaseModel):
    confirmed: int
    skipped: int


class ReviewOut(ORM):
    id: uuid.UUID
    object_type: str
    object_id: uuid.UUID
    action: str
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    comment: str | None = None
    reviewer: str | None = None
    at: dt.datetime
