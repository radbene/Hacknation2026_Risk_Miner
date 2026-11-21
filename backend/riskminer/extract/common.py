"""Shared helpers for S2 extraction: knowledge tables, notice-section lookup, notice evidence, dates."""

from __future__ import annotations

import calendar
import datetime as dt
import re
import uuid
from functools import lru_cache
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from riskminer.core.config import get_config, repo_path
from riskminer.core.evidence import NOTICE_PAGE, add_evidence
from riskminer.models import KnowledgeTable, Notice

# ---------------------------------------------------------------- knowledge


@lru_cache(maxsize=64)
def _yaml_rows(sector: str, name: str) -> tuple:
    base = repo_path(get_config().knowledge_dir) / sector
    for p in (base / f"{name}.yaml", base / "extra" / f"{name}.yaml"):
        if p.exists():
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            return tuple(data.get("rows") or [])
    return ()


def knowledge_rows(name: str, session: Session | None = None, sector: str | None = None) -> list[dict[str, Any]]:
    """Current version of an expert table: DB (knowledge_table, highest version) first, then the yaml file."""
    sector = sector or get_config().sector
    if session is not None:
        try:
            row = session.execute(select(KnowledgeTable).where(KnowledgeTable.sector == sector,
                                                               KnowledgeTable.name == name)
                                  .order_by(KnowledgeTable.version.desc()).limit(1)).scalars().first()
            if row is not None and row.rows:
                return list(row.rows)
        except Exception:  # noqa: BLE001 – knowledge must never break extraction
            session.rollback()
    return [dict(r) for r in _yaml_rows(sector, name)]


def risk_names(session: Session | None = None) -> dict[str, dict[str, Any]]:
    return {r["code"]: r for r in knowledge_rows("risks", session)}


# ---------------------------------------------------------------- notice sections


def norm_section(s: str | None) -> str:
    """'5.4.4.)' / '5.4.4)' / '5.4.4' → '5.4.4'."""
    return re.sub(r"[.)\s]+$", "", (s or "").strip())


def sections_of(notice: Notice | None, section: str, part_no: int | None = None) -> list[dict[str, Any]]:
    if notice is None:
        return []
    want = norm_section(section)
    out = [s for s in (notice.sections or []) if norm_section(s.get("section")) == want]
    if part_no is not None:
        lot = [s for s in out if s.get("part_no") in (part_no, None)]
        out = lot or out
    return out


def section_value(notice: Notice | None, section: str, part_no: int | None = None, nth: int = 0) -> str | None:
    rows = sections_of(notice, section, part_no)
    if len(rows) > nth:
        return (rows[nth].get("value") or "").strip() or None
    return None


def notice_url(notice: Notice) -> str:
    return notice.url or NOTICE_PAGE.format(object_id=notice.object_id)


def notice_evidence(session: Session, notice: Notice, section: str, *, quote: str | None = None,
                    part_no: int | None = None, nth: int = 0, extra: dict[str, Any] | None = None) -> uuid.UUID:
    """Evidence for one notice section (permanent ezamowienia URL, mirror only as retrieved_from)."""
    from riskminer.extract.validate import check_quote

    rows = sections_of(notice, section, part_no)
    row = rows[nth] if len(rows) > nth else None
    value = (row or {}).get("value")
    q = quote if quote is not None else value
    if q and len(q) > 1500:
        q = q[:1500].rsplit(" ", 1)[0] + " …"
    locator = {"section": norm_section(section), "label": (row or {}).get("label"), "part_no": part_no,
               "notice_number": notice.notice_number, "notice_type": notice.notice_type, **(extra or {})}
    if nth:
        locator["occurrence"] = nth + 1
    verified = check_quote(q, value, notice.canonical_text) if q else None
    eid = add_evidence(session, source_code="bzp", kind="notice_section",
                       key=(notice.object_id, norm_section(section), part_no, nth, (extra or {}).get("change_no")),
                       url=notice_url(notice), retrieved_from=notice.retrieved_from, retrieved_at=notice.retrieved_at,
                       locator=locator, quote=q, notice_id=notice.id)
    from riskminer.models import Evidence

    ev = session.get(Evidence, eid)
    if ev is not None:
        ev.quote_verified = verified
    return eid


# ---------------------------------------------------------------- dates

_MONTHS = {"stycz": 1, "lut": 2, "marc": 3, "kwie": 4, "maj": 5, "czerw": 6, "lip": 7, "sierp": 8, "wrze": 9,
           "paźdz": 10, "pazdz": 10, "listop": 11, "grud": 12}


def add_months(d: dt.date, months: int) -> dt.date:
    y, m = divmod(d.month - 1 + months, 12)
    y, m = d.year + y, m + 1
    return dt.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def planned_end_from_period(signed: dt.date | None, period: str | None) -> tuple[dt.date | None, str | None]:
    """Calendar-month arithmetic: '6 miesiące' from 2025-04-24 → 2025-10-24. Returns (date, formula)."""
    if not period:
        return None, None
    p = period.strip()
    m = re.search(r"do\s+(\d{4}-\d{2}-\d{2})", p)
    if m:
        return dt.date.fromisoformat(m.group(1)), "termin wskazany wprost"
    if signed is None:
        return None, None
    m = re.match(r"^(\d+)\s*mies", p)
    if m:
        return add_months(signed, int(m.group(1))), f"data zawarcia + {m.group(1)} mies. kalendarzowych"
    m = re.match(r"^(\d+)\s*dni", p)
    if m:
        return signed + dt.timedelta(days=int(m.group(1))), f"data zawarcia + {m.group(1)} dni"
    m = re.match(r"^(\d+)\s*(?:lat|rok)", p)
    if m:
        return add_months(signed, 12 * int(m.group(1))), f"data zawarcia + {m.group(1)} lat"
    return None, None


def find_dates(text: str | None) -> list[dt.date]:
    """Dates in free text: 2025-11-30, 30.11.2025, 30 listopada 2025."""
    out: list[dt.date] = []
    t = text or ""
    for m in re.finditer(r"(\d{4})-(\d{2})-(\d{2})|(\d{1,2})[./](\d{1,2})[./](\d{4})|(\d{1,2})\s+([a-ząćęłńóśźż]+)\s+(\d{4})",
                         t, flags=re.I):
        try:
            if m.group(1):
                out.append(dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
            elif m.group(4):
                out.append(dt.date(int(m.group(6)), int(m.group(5)), int(m.group(4))))
            else:
                word = m.group(8).lower()
                mon = next((v for k, v in _MONTHS.items() if word.startswith(k)), None)
                if mon:
                    out.append(dt.date(int(m.group(9)), mon, int(m.group(7))))
        except ValueError:
            continue
    return out


def to_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def derivation_evidence(session: Session, *, key: tuple, inputs: list, formula: str,
                        values: dict[str, Any] | None = None, quote: str | None = None) -> uuid.UUID:
    """core.evidence.derivation_evidence with JSON-safe values (dates, Decimals) and no empty inputs."""
    from riskminer.core.evidence import derivation_evidence as _d
    from riskminer.core.upsert import jsonable

    return _d(session, key=key, inputs=[i for i in inputs if i], formula=formula, values=jsonable(values or {}),
              quote=quote)
