"""Expert review actions on any reviewable model (models.REVIEWABLE) with a full audit trail.

    record(session, "event", obj, "edit", before, after, reviewer, comment)   # append to `review`
    apply_action(session, "event", id, "accept" | "edit" | "reject" | "exemplary" | "unexemplary"
                 | "reopen" | "accept_proposal", reviewer, changes=None, comment=None) -> Review
    bulk_confirm(session, "project_procedure", reviewer, ids=[...] | min_confidence=1.0) -> (confirmed, skipped)
    relink(session, link_id, reviewer, procedure_id=... | ocid=... | notice_number=...)  -> Review

Rows an expert reviewed (approved/edited/rejected) are never overwritten by reruns: the pipeline stores a
`proposal` diff (core/upsert.upsert_reviewable) which the expert applies with `accept_proposal`.
Every action also feeds the learning loop (review/learning.py): reject → blacklist, relink → link_override,
exemplary → few-shot examples.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from riskminer import models
from riskminer.core.upsert import jsonable, row_dict
from riskminer.ids import make_id
from riskminer.models import Procedure, ProjectProcedure, Review, ReviewStatus
from riskminer.review import learning

ACTIONS = ("accept", "edit", "reject", "exemplary", "unexemplary", "reopen", "accept_proposal")
_PROTECTED = {"id", "created_at", "updated_at", "status", "proposal", "reviewed_by", "reviewed_at"}


class ReviewError(ValueError):
    pass


def model_for(object_type: str) -> type:
    name = models.REVIEWABLE.get(object_type)
    if name is None:
        raise ReviewError(f"nieznany typ obiektu: {object_type}")
    return getattr(models, name)


def get_object(session: Session, object_type: str, object_id: uuid.UUID | str) -> Any:
    obj = session.get(model_for(object_type), uuid.UUID(str(object_id)))
    if obj is None:
        raise ReviewError("obiekt nie istnieje")
    return obj


def record(session: Session, object_type: str, obj: Any, action: str, before: dict | None,
           after: dict | None, reviewer: str | None, comment: str | None = None) -> Review:
    rev = Review(id=uuid.uuid4(), object_type=object_type, object_id=obj.id, action=action,
                 before=jsonable(before), after=jsonable(after), reviewer=reviewer, comment=comment,
                 at=dt.datetime.now(dt.UTC))
    session.add(rev)
    session.flush()
    return rev


def _stamp(obj: Any, status: str, reviewer: str) -> None:
    obj.status, obj.reviewed_by, obj.reviewed_at = status, reviewer, dt.datetime.now(dt.UTC)


def editable_fields(model: type) -> set[str]:
    return {c.key for c in model.__table__.columns} - _PROTECTED


def _coerce(obj: Any, key: str, value: Any) -> Any:
    """JSON values from the UI → column python types (dates, decimals, uuids)."""
    if value is None or value == "":
        return None if value == "" and key not in ("title", "text", "name", "message") else value
    col = obj.__table__.columns[key]
    try:
        pytype = col.type.python_type
    except NotImplementedError:
        return value
    if isinstance(value, pytype):
        return value
    if pytype is dt.date and isinstance(value, str):
        return dt.date.fromisoformat(value[:10])
    if pytype is dt.datetime and isinstance(value, str):
        return dt.datetime.fromisoformat(value)
    if pytype is uuid.UUID:
        return uuid.UUID(str(value))
    if pytype in (int, float) and isinstance(value, str | int | float) and not isinstance(value, bool):
        return pytype(value)
    if pytype.__name__ == "Decimal":
        return pytype(str(value))
    return value


def _set_fields(obj: Any, changes: dict[str, Any]) -> None:
    bad = set(changes) - editable_fields(type(obj))
    if bad:
        raise ReviewError(f"pola niedozwolone do edycji: {sorted(bad)}")
    for k, v in changes.items():
        setattr(obj, k, _coerce(obj, k, v))


def _diff(before: dict, after: dict) -> tuple[dict, dict]:
    keys = [k for k in after if before.get(k) != after.get(k) and k != "updated_at"]
    return {k: before.get(k) for k in keys}, {k: after[k] for k in keys}


def apply_action(session: Session, object_type: str, object_id: uuid.UUID | str, action: str,
                 reviewer: str, changes: dict[str, Any] | None = None, comment: str | None = None) -> Review:
    if action not in ACTIONS:
        raise ReviewError(f"nieznana akcja: {action}")
    obj = get_object(session, object_type, object_id)
    before = row_dict(obj)
    if action == "accept":
        if changes:
            raise ReviewError("akceptacja nie przyjmuje zmian – użyj 'edit'")
        _stamp(obj, ReviewStatus.approved.value, reviewer)
    elif action == "edit":
        if not changes:
            raise ReviewError("edycja wymaga zmian")
        _set_fields(obj, changes)
        _stamp(obj, ReviewStatus.edited.value, reviewer)
    elif action == "reject":
        _stamp(obj, ReviewStatus.rejected.value, reviewer)
        learning.on_reject(session, object_type, obj, reviewer, comment)
    elif action in ("exemplary", "unexemplary"):
        on = action == "exemplary"
        if obj.status == ReviewStatus.rejected.value and on:
            raise ReviewError("odrzucony element nie może być wzorcowy")
        if hasattr(obj, "exemplary"):
            obj.exemplary = on
        if on and obj.status == ReviewStatus.proposed.value:
            _stamp(obj, ReviewStatus.approved.value, reviewer)
        learning.on_exemplary(session, object_type, obj, reviewer, on)
    elif action == "reopen":
        was_rejected = obj.status == ReviewStatus.rejected.value
        _stamp(obj, ReviewStatus.proposed.value, reviewer)
        if was_rejected:
            learning.on_reopen(session, object_type, obj, reviewer)
    elif action == "accept_proposal":
        if not obj.proposal:
            raise ReviewError("brak propozycji do zaakceptowania")
        _set_fields(obj, {k: v for k, v in obj.proposal.items() if k in editable_fields(type(obj))})
        obj.proposal = None
        _stamp(obj, ReviewStatus.approved.value, reviewer)
    session.flush()
    b, a = _diff(before, row_dict(obj))
    return record(session, object_type, obj, action, b, a, reviewer, comment)


def dismiss_proposal(session: Session, object_type: str, object_id: Any, reviewer: str,
                     comment: str | None = None) -> Review:
    """Keep the expert's data, drop the rerun proposal (still logged)."""
    obj = get_object(session, object_type, object_id)
    if not obj.proposal:
        raise ReviewError("brak propozycji")
    prop, obj.proposal = obj.proposal, None
    session.flush()
    return record(session, object_type, obj, "dismiss_proposal", {"proposal": prop}, None, reviewer, comment)


def bulk_confirm(session: Session, object_type: str, reviewer: str, *, ids: list[Any] | None = None,
                 min_confidence: float | None = None, method: str | None = None,
                 project_id: Any = None, comment: str | None = None) -> tuple[int, int]:
    """Approve many *proposed* rows at once (e.g. all key-based links at confidence 1.0).

    Returns (confirmed, skipped); skipped = requested ids that were not proposed (already reviewed/missing)."""
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
    if project_id is not None:
        if object_type == "project":
            q = q.where(model.id == uuid.UUID(str(project_id)))
        elif "project_id" in model.__table__.columns:
            q = q.where(model.project_id == uuid.UUID(str(project_id)))
    n = 0
    for obj in session.execute(q).scalars():
        _stamp(obj, ReviewStatus.approved.value, reviewer)
        record(session, object_type, obj, "bulk_confirm", {"status": "proposed"}, {"status": "approved"},
               reviewer, comment or (f"Zbiorcze potwierdzenie (pewność ≥ {min_confidence})"
                                     if min_confidence is not None else "Zbiorcze potwierdzenie"))
        n += 1
    session.flush()
    skipped = (len(ids) - n) if ids else 0
    return n, max(skipped, 0)


def relink(session: Session, link_id: Any, reviewer: str, *, procedure_id: Any = None, ocid: str | None = None,
           notice_number: str | None = None, part_no: int | None = None, comment: str | None = None) -> Review:
    """Expert relink: reject the current link, link the project to another procedure (override rule).

    If the target procedure is not in the DB yet (only an OCID / notice number given), the override rule is
    stored and S1's linker/harvester resolves it on the next run (fetch + link)."""
    old = get_object(session, "project_procedure", link_id)
    target = None
    if procedure_id:
        target = session.get(Procedure, uuid.UUID(str(procedure_id)))
    elif ocid:
        target = session.execute(select(Procedure).where(Procedure.ocid == ocid)).scalars().first()
    elif notice_number:
        bzp = notice_number.rsplit("/", 1)[0] if notice_number.count("/") >= 2 else notice_number
        target = session.execute(select(Procedure).where(Procedure.bzp_number == bzp)).scalars().first()
    else:
        raise ReviewError("podaj procedure_id, OCID albo numer ogłoszenia")
    if target is not None and target.id == old.procedure_id and part_no == old.part_no:
        raise ReviewError("to jest już bieżące powiązanie")
    before = row_dict(old)
    if old.status != ReviewStatus.rejected.value:
        _stamp(old, ReviewStatus.rejected.value, reviewer)
        learning.on_reject(session, "project_procedure", old, reviewer, comment or "Zmiana powiązania przez eksperta")
    new_link = None
    if target is not None:
        nid = make_id("project_procedure", old.project_id, target.id, part_no)
        new_link = session.get(ProjectProcedure, nid)
        if new_link is None:
            new_link = ProjectProcedure(id=nid, project_id=old.project_id, procedure_id=target.id, part_no=part_no)
            session.add(new_link)
        new_link.method, new_link.confidence, new_link.is_override = "expert", 1.0, True
        new_link.components = [{"name": "expert", "score": 1.0, "weight": 1.0,
                                "detail": comment or "Powiązanie wskazane przez eksperta"}]
        _stamp(new_link, ReviewStatus.approved.value, reviewer)
        session.flush()
        learning.deactivate_rule(session, "blacklist", f"project_procedure:{new_link.id}", reviewer)
        learning.deactivate_rule(session, "link_override", learning._link_key(old.project_id, target.id, part_no),
                                 reviewer)
    learning.add_link_override(session, mode="force", project_id=old.project_id,
                               procedure_id=target.id if target else None, part_no=part_no,
                               ocid=ocid or (target.ocid if target else None), notice_number=notice_number,
                               replaces=old.id, actor=reviewer, comment=comment)
    session.flush()
    after = {"status": old.status, "new_link_id": str(new_link.id) if new_link else None,
             "procedure_id": str(target.id) if target else None, "ocid": ocid, "notice_number": notice_number,
             "part_no": part_no, "pending_fetch": target is None}
    return record(session, "project_procedure", old, "relink", {"procedure_id": before["procedure_id"],
                  "part_no": before["part_no"], "status": before["status"]}, after, reviewer, comment)


def history(session: Session, *, object_type: str | None = None, object_id: Any = None,
            reviewer: str | None = None, object_ids: list[Any] | None = None,
            offset: int = 0, limit: int = 200) -> tuple[list[Review], int]:
    from sqlalchemy import func

    q = select(Review)
    if object_type:
        q = q.where(Review.object_type == object_type)
    if object_id:
        q = q.where(Review.object_id == uuid.UUID(str(object_id)))
    if object_ids is not None:
        q = q.where(Review.object_id.in_(object_ids))
    if reviewer:
        q = q.where(Review.reviewer == reviewer)
    total = session.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    rows = session.execute(q.order_by(Review.at.desc()).offset(offset).limit(limit)).scalars()
    return list(rows), total
