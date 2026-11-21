"""TEST-ONLY helper: notice/procedure/contract rows for one procedure of notices22 via S1's real store and parser.

After the merge S2 tests run on S1's output (same uuid5 ids as the live pipeline, so no duplicates in a shared DB).
`sections()` is kept for tests that only need the section split. Do not import from application code.
"""

from __future__ import annotations

import datetime as dt
import html
import re

from riskminer.core.upsert import upsert
from riskminer.ids import make_id
from riskminer.models import Contract, Project, ProjectProcedure

_H = re.compile(r"<h3[^>]*>(.*?)</h3>|<h2[^>]*>(.*?)</h2>", re.S | re.I)
_SEC = re.compile(r"^\s*(\d+(?:\.\d+)*)\.?\)\s*(.*)$", re.S)


def _text(fragment: str) -> str:
    s = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    s = re.sub(r"</p>", "\n", s, flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    return re.sub(r"\s*\n\s*", "\n", s).strip()


def sections(body: str) -> tuple[list[dict], str]:
    body = body[body.find("<main>"):] if "<main>" in body else body
    body = re.sub(r"<footer.*", "", body, flags=re.S)
    heads = list(_H.finditer(body))
    out, canon, part = [], [], None
    for i, m in enumerate(heads):
        inner = m.group(1) or m.group(2) or ""
        nxt = heads[i + 1].start() if i + 1 < len(heads) else len(body)
        if m.group(2) is not None:
            t = _text(inner)
            pm = re.search(r"Część\s+(\d+)", t)
            if pm:
                part = int(pm.group(1))
            tail = _text(body[m.end():nxt])
            canon.append(f"{t}\n{tail}" if tail else t)
            continue
        span = re.search(r"<span[^>]*>(.*)</span>", inner, re.S)
        label_html = inner[:span.start()] if span else inner
        value = _text(span.group(1)) if span else _text(body[m.end():nxt])
        label = _text(label_html)
        sm = _SEC.match(label)
        if not sm:
            continue
        sec, lab = sm.group(1), sm.group(2).strip().rstrip(":")
        off = len("\n".join(canon)) + (1 if canon else 0) + len(label) + 1
        canon.append(f"{label} {value}".strip())
        out.append({"section": sec, "label": lab, "value": value, "offset": off, "part_no": part})
    return out, "\n".join(canon)


def _sv(secs, num, nth=0):
    rows = [s for s in secs if s["section"] == num]
    return rows[nth]["value"] if len(rows) > nth else None


def _num(v):
    if not v:
        return None
    m = re.search(r"\d[\d ]*(?:[,.]\d{1,2})?", v)
    return float(m.group(0).replace(" ", "").replace(",", ".")) if m else None


def _date(v):
    m = re.search(r"\d{4}-\d{2}-\d{2}", v or "")
    return dt.date.fromisoformat(m.group(0)) if m else None


def _yn(v):
    return {"Tak": True, "Nie": False}.get((v or "").strip()[:3].strip())


def _basis_code(v):
    m = re.search(r"art\.\s*455\s*ust\.\s*(\d)(?:\s*pkt\s*(\d))?", v or "")
    return None if not m else ("455." + m.group(1) + ("." + m.group(2) if m.group(2) else ""))


def load(session, notices: list[dict], project_code: str | None = None) -> dict:
    """Rows for the notices of one procedure via S1's real store/parser (ids match the live pipeline). Returns ids."""
    from sqlalchemy import select

    from riskminer.connectors.bzp_store import build_procedure, ensure_sources, store_notice

    ocid = notices[0]["tenderId"]
    ensure_sources(session)
    nids = {}
    for n in notices:
        nid, _ = store_notice(session, n, source_code="bzp_zip", retrieved_from="zip:notices_by_nip", tier="deep",
                              keep_html=False)
        nids[n["objectId"]] = nid
    session.flush()
    pid = build_procedure(session, ocid, tier="deep")
    session.flush()
    contracts = list(session.execute(select(Contract.id).where(Contract.procedure_id == pid)).scalars())
    project_id = None
    if project_code:
        project_id = make_id("project", project_code)
        if session.get(Project, project_id) is None:
            session.add(Project(id=project_id, code=project_code, title=notices[0]["orderObject"], tier="deep",
                                project_status="Zakończone"))
            session.flush()
        upsert(session, ProjectProcedure, dict(id=make_id("project_procedure", project_id, pid, None),
                                               project_id=project_id, procedure_id=pid, part_no=None,
                                               method="test", status="approved"))
    session.flush()
    return {"procedure_id": pid, "notice_ids": nids, "contract_ids": contracts, "project_id": project_id}


def by_ocid(notices22: list[dict], ocid: str) -> list[dict]:
    return sorted([n for n in notices22 if n["tenderId"] == ocid], key=lambda n: n["publicationDate"])
