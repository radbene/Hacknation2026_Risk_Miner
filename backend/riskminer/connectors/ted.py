"""TED (Tenders Electronic Daily) – EU-level notices of the same buyers.

For each project of the organizer's list we search the official TED Search API v3 (no key needed) for notices of
the beneficiary (buyer name contains the municipality, country PL, works CPV 45*). Above-threshold works are rare
for small municipalities, so "checked, 0 notices" is recorded too – the jury can see the source was queried.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from sqlalchemy.orm import Session

from riskminer.connectors.public import PublicClient, deep_projects, gmina_of, norm, put_fact, save_raw
from riskminer.core.evidence import add_evidence

API = "https://api.ted.europa.eu/v3/notices/search"
NOTICE = "https://ted.europa.eu/pl/notice/{pub}"
FIELDS = ["publication-number", "notice-title", "buyer-name", "publication-date", "classification-cpv", "notice-type"]


def _names(v: Any) -> list[str]:
    if isinstance(v, dict):
        return [x for vals in v.values() for x in (vals if isinstance(vals, list) else [vals])]
    return v if isinstance(v, list) else [v] if v else []


def _title(v: Any) -> str | None:
    if isinstance(v, dict):  # {"pol": "...", "eng": "...", ...}
        for lang in ("pol", "eng"):
            if v.get(lang):
                return v[lang] if isinstance(v[lang], str) else v[lang][0]
    return next(iter(_names(v)), None)


def run(session: Session, project_ids: list[uuid.UUID] | None = None, job_id: uuid.UUID | None = None) -> dict[str, Any]:
    client = PublicClient("ted", job_id=job_id, min_interval=1.5)
    out = {"projects": 0, "queries": 0, "notices": 0, "projects_with_notices": 0}
    for p in deep_projects(session, project_ids):
        g = gmina_of(session, p)
        if not g:
            continue
        out["projects"] += 1
        query = f'organisation-name-buyer ~ "{g}" AND buyer-country=POL AND publication-date>=20190101'
        body = {"query": query, "fields": FIELDS, "limit": 100, "scope": "ALL"}
        r = client.request("POST", API, operation="search", json_body=body,
                           n_results=lambda x: len(x.json().get("notices", [])))
        out["queries"] += 1
        data = r.json()
        raw_id = save_raw(session, "ted", f"search:{p.code}", url=None, retrieved_from=API, payload={"query": body, **data})
        hits = []
        for n in data.get("notices", []):
            buyers = _names(n.get("buyer-name"))
            cpv = [str(c) for c in _names(n.get("classification-cpv"))]
            if not any(norm(g) in norm(b) for b in buyers) or not any(c.startswith("45") for c in cpv):
                continue  # another buyer with a similar name, or not works
            hits.append(n)
        q_eid = add_evidence(session, source_code="ted", kind="api_field", key=("search", p.code, query),
                             url="https://ted.europa.eu/pl/search", retrieved_from=API,
                             locator={"query": query, "results": len(hits)}, raw_record_id=raw_id)
        put_fact(session, subject_type="project", subject_id=p.id, fact_type="ted_notices_found", key=("search",),
                 evidence_ids=[q_eid], value_num=len(hits), unit="ogłoszeń",
                 value_text=f"zamawiający „{g}”, roboty (CPV 45), od 2019 r.: liczba ogłoszeń {len(hits)}")
        for n in hits:
            pub = n.get("publication-number")
            title = _title(n.get("notice-title"))
            date = (n.get("publication-date") or "")[:10]
            eid = add_evidence(session, source_code="ted", kind="api_field", key=("notice", pub),
                               url=NOTICE.format(pub=pub), retrieved_from=API,
                               locator={"field": "notice-title", "publication-number": pub}, quote=title,
                               raw_record_id=raw_id)
            put_fact(session, subject_type="project", subject_id=p.id, fact_type="ted_notice", key=(pub,),
                     evidence_ids=[eid], value_text=f"{pub}: {title}",
                     value_date=dt.date.fromisoformat(date) if len(date) == 10 else None,
                     method="fuzzy", confidence=0.6)
        out["notices"] += len(hits)
        out["projects_with_notices"] += bool(hits)
    return out
