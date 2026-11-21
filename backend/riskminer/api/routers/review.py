"""Expert review queue, actions, bulk-confirm, history (owner: S5)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from riskminer.api.deps import DB, USER, CurrentUser, Session, not_implemented
from riskminer.schemas.common import Page
from riskminer.schemas.review import (
    BulkConfirmIn,
    BulkResult,
    ObjectType,
    QueueItem,
    ReviewActionIn,
    ReviewOut,
)

router = APIRouter(tags=["review"])
OWNER = "S5"


@router.get("/review/queue", response_model=Page[QueueItem])
def review_queue(object_type: ObjectType | None = None, project_id: uuid.UUID | None = None,
                 status: str = "proposed", offset: int = 0, limit: int = 50, db: Session = DB):
    """Proposed-first, uncertain items on top."""
    raise not_implemented(OWNER)


@router.post("/review/{object_type}/{object_id}", response_model=ReviewOut)
def review_action(object_type: ObjectType, object_id: uuid.UUID, body: ReviewActionIn, db: Session = DB,
                  user: CurrentUser = USER):
    raise not_implemented(OWNER)


@router.post("/review/bulk-confirm", response_model=BulkResult)
def bulk_confirm(body: BulkConfirmIn, db: Session = DB, user: CurrentUser = USER):
    raise not_implemented(OWNER)


@router.get("/history", response_model=Page[ReviewOut])
def history(object_type: str | None = None, object_id: uuid.UUID | None = None, project_id: uuid.UUID | None = None,
            reviewer: str | None = None, offset: int = 0, limit: int = 100, db: Session = DB):
    raise not_implemented(OWNER)
