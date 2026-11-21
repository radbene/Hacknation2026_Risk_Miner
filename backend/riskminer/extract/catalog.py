"""Open catalog: reasons that fit no R-code become *proposed* risk categories (P-…) in the expert queue."""

from __future__ import annotations

import re
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from riskminer.core.config import get_config
from riskminer.core.upsert import upsert_reviewable
from riskminer.ids import make_id
from riskminer.models import RiskCategory


def category_id(code: str, sector: str | None = None) -> uuid.UUID:
    return make_id("risk_category", sector or get_config().sector, code)


def ensure_proposed(session: Session, code: str, name: str, description: str | None = None,
                    keywords: list[str] | None = None, evidence_ids: list[Any] | None = None,
                    method: str = "rule", confidence: float = 0.5) -> uuid.UUID:
    """Insert (or refresh, if still proposed) a P-code category. Never touches reviewed rows' data."""
    sector = get_config().sector
    existing = session.execute(select(RiskCategory).where(RiskCategory.sector == sector, RiskCategory.code == code)
                               ).scalars().first()
    cid = existing.id if existing is not None else category_id(code, sector)
    ev = sorted({str(e) for e in (evidence_ids or [])} | {str(e) for e in ((existing.evidence_ids if existing else None) or [])})
    upsert_reviewable(session, RiskCategory, dict(
        id=cid, sector=sector, code=code, name=name, description=description, keywords=keywords or [],
        method=method, confidence=confidence, evidence_ids=ev[:50], version=1))
    return cid


def slug_code(text: str) -> str:
    """P-code from a short label: 'Zmiana przepisów prawa' → 'P-ZMIANA-PRZEPISOW'."""
    import unicodedata

    s = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().upper()
    words = [w for w in re.findall(r"[A-Z]{3,}", s)][:2]
    return "P-" + "-".join(words or ["INNE"])


def list_categories(session: Session, sector: str | None = None, include_proposed: bool = True) -> list[RiskCategory]:
    q = select(RiskCategory).where(RiskCategory.sector == (sector or get_config().sector))
    if not include_proposed:
        q = q.where(~RiskCategory.code.like("P-%"))
    return list(session.execute(q.order_by(RiskCategory.code)).scalars())
