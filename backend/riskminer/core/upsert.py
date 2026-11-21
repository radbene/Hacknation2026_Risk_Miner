"""Idempotent writes that respect expert review.

`upsert(session, Model, values)` – plain ON CONFLICT (id) DO UPDATE (for non-reviewable tables).
`upsert_reviewable(session, Model, values)` – insert as *proposed*; if the row exists and is still
*proposed*, update it; if an expert already approved/edited/rejected it, do NOT touch the data –
store the new machine output in `proposal` (shown as a diff in the review queue) instead.
"""

from __future__ import annotations

import datetime as dt
import json
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from riskminer.models import Review, ReviewStatus

REVIEWED = {ReviewStatus.approved.value, ReviewStatus.edited.value, ReviewStatus.rejected.value}
_SKIP_DIFF = {"id", "created_at", "updated_at", "status", "proposal", "reviewed_by", "reviewed_at"}


def jsonable(v: Any) -> Any:
    if isinstance(v, uuid.UUID):
        return str(v)
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, dt.date | dt.datetime):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: jsonable(x) for k, x in v.items()}
    if isinstance(v, list | tuple):
        return [jsonable(x) for x in v]
    return v


def row_dict(obj: Any) -> dict[str, Any]:
    return {c.key: jsonable(getattr(obj, c.key)) for c in obj.__table__.columns}


def upsert(session: Session, model: type, values: dict[str, Any], index_elements: list[str] | None = None) -> None:
    cols = {c.key for c in model.__table__.columns}
    vals = {k: v for k, v in values.items() if k in cols}
    keys = index_elements or ["id"]
    stmt = insert(model).values(**vals)
    upd = {k: stmt.excluded[k] for k in vals if k not in keys and k != "created_at"}
    stmt = stmt.on_conflict_do_update(index_elements=keys, set_=upd) if upd else stmt.on_conflict_do_nothing()
    session.execute(stmt)


def upsert_reviewable(session: Session, model: type, values: dict[str, Any], actor: str = "system") -> str:
    """Returns 'inserted' | 'updated' | 'unchanged' | 'proposal' (reviewed row kept, diff stored)."""
    obj = session.get(model, values["id"])
    cols = {c.key for c in model.__table__.columns}
    vals = {k: v for k, v in values.items() if k in cols and k not in ("status", "proposal")}
    if obj is None:
        session.add(model(**vals, status=ReviewStatus.proposed.value))
        session.flush()
        return "inserted"
    diff = {
        k: jsonable(v)
        for k, v in vals.items()
        if k not in _SKIP_DIFF and json.dumps(jsonable(getattr(obj, k)), sort_keys=True, default=str)
        != json.dumps(jsonable(v), sort_keys=True, default=str)
    }
    if not diff:
        return "unchanged"
    if obj.status in REVIEWED:
        if obj.proposal != diff:
            obj.proposal = diff
            session.add(Review(object_type=model.__tablename__, object_id=obj.id, action="rerun_proposal",
                                before=None, after=diff, reviewer=actor,
                                comment="Ponowne przetworzenie zaproponowało zmiany; dane eksperta nie zostały nadpisane."))
        return "proposal"
    for k, v in vals.items():
        setattr(obj, k, v)
    return "updated"


def find_one(session: Session, model: type, **where: Any) -> Any:
    return session.execute(select(model).filter_by(**where)).scalars().first()
