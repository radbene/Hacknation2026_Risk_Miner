"""Expert review actions on any reviewable model (models.REVIEWABLE) with a full audit trail.

    record(session, "event", obj, "edit", before, after, reviewer, comment)   # append to `review`
    apply_action(session, "event", id, "accept" | "edit" | "reject" | "exemplary" | "reopen"
                 | "accept_proposal", reviewer, changes=None, comment=None)
    bulk_confirm(session, "project_procedure", reviewer, ids=[...] | min_confidence=1.0)

Rows an expert reviewed (approved/edited/rejected) are never overwritten by reruns: the pipeline stores a
`proposal` diff (core/upsert.upsert_reviewable) which the expert applies with `accept_proposal`.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from riskminer import models
from riskminer.core.upsert import jsonable, row_dict
from riskminer.models import Review, ReviewStatus

ACTIONS = ("accept", "edit", "reject", "exemplary", "reopen", "accept_proposal")
_PROTECTED = {"id", "created_at", "updated_at", "status", "proposal", "reviewed_by", "reviewed_at"}


class ReviewError(ValueError):
    pass


def model_for(object_type: str) -> type:
    name = models.REVIEWABLE.get(object_type)
    if name is None:
        raise ReviewError(f"nieznany typ obiektu: {object_type}")
    return getattr(models, name)


def record(session: Session, object_type: str, obj: Any, action: str, before: dict | None,
           after: dict | None, reviewer: str | None, comment: str | None = None) -> Review:
    rev = Review(object_type=object_type, object_id=obj.id, action=action, before=jsonable(before),
                 after=jsonable(after), reviewer=reviewer, comment=comment)
    session.add(rev)
    return rev


def _stamp(obj: Any, status: str, reviewer: str) -> None:
    obj.status, obj.reviewed_by, obj.reviewed_at = status, reviewer, dt.datetime.now(dt.UTC)


def _set_fields(obj: Any, changes: dict[str, Any]) -> dict[str, Any]:
    cols = {c.key for c in obj.__table__.columns}
    bad = set(changes) - (cols - _PROTECTED)
    if bad:
        raise ReviewError(f"pola niedozwolone do edycji: {sorted(bad)}")
    for k, v in changes.items():
        setattr(obj, k, v)
    return changes


def apply_action(session: Session, object_type: str, object_id: uuid.UUID | str, action: str,
                 reviewer: str, changes: dict[str, Any] | None = None, comment: str | None = None) -> Any:
    if action not in ACTIONS:
        raise ReviewError(f"nieznana akcja: {action}")
    model = model_for(object_type)
    obj = session.get(model, uuid.UUID(str(object_id)))
    if obj is None:
        raise ReviewError("obiekt nie istnieje")
    before = row_dict(obj)
    if action == "accept":
        _stamp(obj, ReviewStatus.approved.value, reviewer)
    elif action == "edit":
        if not changes:
            raise ReviewError("edycja wymaga zmian")
        _set_fields(obj, changes)
        if hasattr(obj, "method"):
            obj.method = obj.method if obj.method == "expert" else (obj.method or "expert")
        _stamp(obj, ReviewStatus.edited.value, reviewer)
    elif action == "reject":
        _stamp(obj, ReviewStatus.rejected.value, reviewer)
    elif action == "exemplary":
        if not hasattr(obj, "exemplary"):
            raise ReviewError("ten typ obiektu nie ma oznaczenia 'wzorcowy'")
        obj.exemplary = not bool((changes or {}).get("exemplary") is False)
        if obj.status == ReviewStatus.proposed.value:
            _stamp(obj, ReviewStatus.approved.value, reviewer)
    elif action == "reopen":
        _stamp(obj, ReviewStatus.proposed.value, reviewer)
    elif action == "accept_proposal":
        if not obj.proposal:
            raise ReviewError("brak propozycji do zaakceptowania")
        _set_fields(obj, {k: v for k, v in obj.proposal.items() if k not in _PROTECTED})
        obj.proposal = None
        _stamp(obj, ReviewStatus.approved.value, reviewer)
    session.flush()
    after = row_dict(obj)
    diff_before = {k: before[k] for k in after if before.get(k) != after.get(k) and k != "updated_at"}
    diff_after = {k: after[k] for k in diff_before}
    record(session, object_type, obj, action, diff_before, diff_after, reviewer, comment)
    return obj


def bulk_confirm(session: Session, object_type: str, reviewer: str, *, ids: list[str] | None = None,
                 min_confidence: float | None = None, method: str | None = None,
                 comment: str | None = None) -> int:
    """Approve many *proposed* rows at once (e.g. all key-based links at confidence 1.0)."""
    if not ids and min_confidence is None:
        raise ReviewError("podaj ids albo min_confidence")
    model = model_for(object_type)
    q = select(model).where(model.status == ReviewStatus.proposed.value)
    if ids:
        q = q.where(model.id.in_([uuid.UUID(str(i)) for i in ids]))
    if min_confidence is not None:
        q = q.where(model.confidence >= min_confidence)
    if method:
        q = q.where(model.method == method)
    n = 0
    for obj in session.execute(q).scalars():
        _stamp(obj, ReviewStatus.approved.value, reviewer)
        record(session, object_type, obj, "bulk_confirm", {"status": "proposed"}, {"status": "approved"},
               reviewer, comment)
        n += 1
    session.flush()
    return n


def history(session: Session, *, object_type: str | None = None, object_id: str | None = None,
            reviewer: str | None = None, limit: int = 200) -> list[Review]:
    q = select(Review).order_by(Review.at.desc()).limit(limit)
    if object_type:
        q = q.where(Review.object_type == object_type)
    if object_id:
        q = q.where(Review.object_id == uuid.UUID(str(object_id)))
    if reviewer:
        q = q.where(Review.reviewer == reviewer)
    return list(session.execute(q).scalars())
