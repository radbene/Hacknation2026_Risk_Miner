"""Helpers for creating evidence rows (every fact must cite one)."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from sqlalchemy.orm import Session

from riskminer.core.upsert import upsert
from riskminer.ids import make_id
from riskminer.models import Evidence

NOTICE_PAGE = "https://ezamowienia.gov.pl/mo-client-board/bzp/notice-details/id/{object_id}"
NOTICE_PDF = "https://ezamowienia.gov.pl/mo-board/api/v1/Board/GetNoticePdfById?noticeId={object_id}"


def evidence_id(source_code: str, kind: str, *key: object) -> uuid.UUID:
    return make_id("evidence", source_code, kind, *key)


def add_evidence(
    session: Session,
    *,
    source_code: str,
    kind: str,
    key: tuple,
    url: str | None = None,
    retrieved_from: str | None = None,
    retrieved_at: dt.datetime | None = None,
    locator: dict[str, Any] | None = None,
    quote: str | None = None,
    derivation: dict[str, Any] | None = None,
    **fks: Any,
) -> uuid.UUID:
    """Idempotent: same (source, kind, key) → same evidence id."""
    eid = evidence_id(source_code, kind, *key)
    upsert(session, Evidence, dict(
        id=eid, source_code=source_code, kind=kind, url=url, retrieved_from=retrieved_from,
        retrieved_at=retrieved_at, locator=locator or {}, quote=quote, derivation=derivation, **fks,
    ))
    return eid


def derivation_evidence(session: Session, *, key: tuple, inputs: list[uuid.UUID | str], formula: str,
                        values: dict[str, Any] | None = None, quote: str | None = None) -> uuid.UUID:
    """Evidence for a calculation: input evidence ids + formula (+ input values)."""
    return add_evidence(session, source_code="calc", kind="derivation", key=key, quote=quote,
                        derivation={"inputs": [str(i) for i in inputs], "formula": formula, "values": values or {}})
