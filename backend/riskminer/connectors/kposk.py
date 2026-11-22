"""KPOŚK – the official annual report of the national urban waste-water programme (dane.gov.pl dataset 3213).

For each project of the organizer's list we find the agglomeration(s) its municipality belongs to and record the
context an analyst needs: agglomeration id and name, RLM, sewer coverage, network length. Each value cites the
exact sheet / row / column of the downloaded XLSX (raw file kept in the raw store).
"""

from __future__ import annotations

import io
import re
import uuid
from typing import Any

import openpyxl
from sqlalchemy.orm import Session

from riskminer.connectors.public import PublicClient, deep_projects, gmina_of, norm, put_fact, save_raw
from riskminer.core.evidence import add_evidence

DATASET = "https://dane.gov.pl/pl/dataset/3213"
RESOURCES_API = "https://api.dane.gov.pl/1.4/datasets/3213/resources"
SHEET_PREFIX = "Aglomeracje"
# column indexes (0-based) in the "Aglomeracje <rok>" sheet, header row 5
COLS = {"id": 1, "name": 2, "status": 3, "voivodeship": 7, "gminas": 15, "rlm": 21, "coverage": 41, "network_km": 53}
FIELDS = [  # fact_type, column, unit
    ("kposk_agglomeration", "name", None), ("kposk_rlm", "rlm", "RLM"), ("kposk_coverage", "coverage", "%"),
    ("kposk_network_km", "network_km", "km"), ("kposk_status", "status", None),
]


def latest_resource(client: PublicClient) -> dict[str, Any]:
    r = client.request("GET", RESOURCES_API, operation="list_resources", params={"per_page": 50},
                       n_results=lambda x: len(x.json().get("data", [])))
    best = None
    for item in r.json().get("data", []):
        a = item["attributes"]
        title = a.get("title") or ""
        year = next((int(t) for t in title.split() if t.isdigit() and len(t) == 4), 0)
        if a.get("format") in ("xlsx", "xls") and (best is None or year > best["year"]):
            best = {"year": year, "title": title, "url": a.get("download_url") or a.get("link"), "id": item["id"]}
    if not best:
        raise RuntimeError("no KPOŚK XLSX resource on dane.gov.pl")
    return best


def run(session: Session, project_ids: list[uuid.UUID] | None = None, job_id: uuid.UUID | None = None) -> dict[str, Any]:
    client = PublicClient("kposk", job_id=job_id)
    res = latest_resource(client)
    r = client.request("GET", res["url"], operation="download", n_results=lambda x: 1)
    raw_id = save_raw(session, "kposk", f"resource:{res['id']}", url=f"{DATASET}/resource/{res['id']}",
                      retrieved_from=res["url"], blob=r.content, ext=".xlsx",
                      content_type=r.headers.get("content-type"))
    wb = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    ws = next(w for w in wb.worksheets if w.title.strip().startswith(SHEET_PREFIX))
    rows: list[tuple[int, tuple]] = []
    for i, row in enumerate(ws.iter_rows(min_row=7, values_only=True), start=7):
        if row and row[COLS["id"]] and str(row[COLS["id"]]).startswith("PL"):
            rows.append((i, row))
    by_gmina: dict[str, list[tuple[int, tuple]]] = {}
    for i, row in rows:
        for g in re.split(r"[,;\n]|\.\s", str(row[COLS["gminas"]] or "")):
            if g.strip():
                by_gmina.setdefault(norm(g), []).append((i, row))

    out = {"resource": res["title"], "agglomerations": len(rows), "projects": 0, "matched": 0, "facts": 0, "unmatched": []}
    for p in deep_projects(session, project_ids):
        out["projects"] += 1
        g = gmina_of(session, p)
        cands = by_gmina.get(norm(g), []) if g else []
        if p.voivodeship:
            cands = [c for c in cands if norm(str(c[1][COLS["voivodeship"]])) == norm(p.voivodeship)] or cands
        # prefer the agglomeration named after the project's town; otherwise all agglomerations of the municipality
        exact = [c for c in cands if norm(str(c[1][COLS["name"]])) in (norm(p.city), norm(g))]
        chosen, conf = (exact, 1.0) if exact else (cands[:3], 0.7)
        if not chosen:
            out["unmatched"].append(f"{p.code} ({g})")
            continue
        out["matched"] += 1
        for rown, row in chosen:
            agg = str(row[COLS["id"]])
            for fact_type, col, unit in FIELDS:
                v = row[COLS[col]]
                if v is None:
                    continue
                c = COLS[col]
                eid = add_evidence(session, source_code="kposk", kind="xlsx_cell", key=(res["id"], ws.title, rown, c),
                                   url=f"{DATASET}/resource/{res['id']}", retrieved_from=res["url"],
                                   locator={"sheet": ws.title.strip(), "row": rown, "column": c + 1, "field": col},
                                   quote=str(v), raw_record_id=raw_id)
                num = float(v) * (100 if col == "coverage" and float(v) <= 1 else 1) if isinstance(v, int | float) else None
                text = f"{agg} {v}" if col == "name" else (str(v) if num is None else None)
                put_fact(session, subject_type="project", subject_id=p.id, fact_type=fact_type, key=(agg,),
                         evidence_ids=[eid], value_text=text, value_num=num, unit=unit,
                         method="key" if conf == 1.0 else "fuzzy", confidence=conf)
                out["facts"] += 1
    return out
