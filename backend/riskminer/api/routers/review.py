"""Expert review queue, actions, bulk-confirm, relink, history (owner: S5)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from riskminer.api.deps import DB, CurrentUser, Session, require_role
from riskminer.models import ProjectProcedure
from riskminer.review import audit
from riskminer.review import queue as rq
from riskminer.schemas.common import Page
from riskminer.schemas.review import (
    BulkConfirmIn,
    BulkResult,
    ObjectType,
    QueueItem,
    RelinkIn,
    ReviewActionIn,
    ReviewOut,
)

router = APIRouter(tags=["review"])
OWNER = "S5"
EXPERT = require_role("expert")


def _err(e: audit.ReviewError) -> HTTPException:
    msg = str(e)
    return HTTPException(404 if "nie istnieje" in msg else 422, msg)


@router.get("/review/queue", response_model=Page[QueueItem])
def review_queue(object_type: ObjectType | None = None, project_id: uuid.UUID | None = None,
                 status: str = "proposed", offset: int = 0, limit: int = 50, db: Session = DB):
    """Proposed-first, uncertain items on top (status: proposed | approved | edited | rejected | all)."""
    items, total = rq.queue(db, object_type=object_type, project_id=project_id, status=status,
                            offset=offset, limit=min(limit, 500))
    return Page(items=items, total=total, offset=offset, limit=limit)


@router.get("/review/counts", response_model=dict[str, int])
def review_counts(db: Session = DB):
    """Pending items per object type (badge in navigation)."""
    return rq.counts(db)


@router.post("/review/bulk-confirm", response_model=BulkResult)
def bulk_confirm(body: BulkConfirmIn, db: Session = DB, user: CurrentUser = EXPERT):
    try:
        # with explicit ids the default min_confidence (1.0) does not apply unless it was sent
        min_conf = body.min_confidence if (not body.ids or "min_confidence" in body.model_fields_set) else None
        n, skipped = audit.bulk_confirm(db, body.object_type, user.username, ids=body.ids, min_confidence=min_conf,
                                        method=body.method, project_id=body.project_id, comment=body.comment)
    except audit.ReviewError as e:
        raise _err(e) from e
    db.commit()
    return BulkResult(confirmed=n, skipped=skipped)


@router.post("/review/project_procedure/{object_id}/relink", response_model=ReviewOut)
def relink(object_id: uuid.UUID, body: RelinkIn, db: Session = DB, user: CurrentUser = EXPERT):
    """Replace a link: pick a candidate (procedure_id) or give an OCID / notice number (fetched by S1 later).
    Stored as a link_override rule that survives rebuilds."""
    try:
        rev = audit.relink(db, object_id, user.username, procedure_id=body.procedure_id, ocid=body.ocid,
                           notice_number=body.notice_number, part_no=body.part_no, comment=body.comment)
    except audit.ReviewError as e:
        raise _err(e) from e
    db.commit()
    return rev


@router.post("/review/{object_type}/{object_id}", response_model=ReviewOut)
def review_action(object_type: ObjectType, object_id: uuid.UUID, body: ReviewActionIn, db: Session = DB,
                  user: CurrentUser = EXPERT):
    action = body.action
    if body.accept_proposal and action == "accept":
        action = "accept_proposal"
    try:
        if action == "dismiss_proposal":
            rev = audit.dismiss_proposal(db, object_type, object_id, user.username, body.comment)
        else:
            rev = audit.apply_action(db, object_type, object_id, action, user.username, body.changes, body.comment)
    except audit.ReviewError as e:
        raise _err(e) from e
    db.commit()
    return rev


@router.get("/review/{object_type}/{object_id}/fields", response_model=list[str])
def editable_fields(object_type: ObjectType, object_id: uuid.UUID):
    """Fields the expert may edit on this object type (UI edit form)."""
    return sorted(audit.editable_fields(audit.model_for(object_type)))


@router.get("/history", response_model=Page[ReviewOut])
def history(object_type: str | None = None, object_id: uuid.UUID | None = None, project_id: uuid.UUID | None = None,
            reviewer: str | None = None, offset: int = 0, limit: int = 100, db: Session = DB):
    ids = None
    if project_id is not None:
        ids = [project_id] + [pp.id for pp in db.execute(
            select(ProjectProcedure).where(ProjectProcedure.project_id == project_id)).scalars()]
        from riskminer import models

        for name in ("Event", "DataIssue", "Lesson", "Document"):
            m = getattr(models, name)
            ids += list(db.execute(select(m.id).where(m.project_id == project_id)).scalars())
    rows, total = audit.history(db, object_type=object_type, object_id=object_id, reviewer=reviewer,
                                object_ids=ids, offset=offset, limit=min(limit, 1000))
    return Page(items=rows, total=total, offset=offset, limit=limit)
