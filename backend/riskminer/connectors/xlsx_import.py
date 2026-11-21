"""Import of the organizer's project list (.xlsx / .csv) – profile "organizer" (sheet "Projekty").

Every attribute cites its cell (evidence kind=xlsx_cell: sha256 / sheet / row / column / header).
Validation problems become `data_issue` rows (kind=validation). The free-text annotation
("Adnotacja instytucji") is parsed into facts (project value, grant – vat_basis=unknown) + description.
Idempotent: ids from natural keys; reviewed projects are never overwritten (upsert_reviewable).
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from riskminer.core.evidence import add_evidence
from riskminer.core.upsert import upsert, upsert_reviewable
from riskminer.ids import BZP_NUMBER_RE, KPO_NUMBER_RE, make_id, nip_valid, norm_nip
from riskminer.models import DataIssue, Entity, Fact, Project, RawRecord, Source

SOURCE = "xlsx"

# header (organizer profile) → project field
ORGANIZER_PROFILE: dict[str, str] = {
    "Lp.": "lp",
    "Identyfikator rekordu": "code",
    "Rodzaj identyfikatora odbiorcy": "beneficiary_id_type",
    "Identyfikator odbiorcy": "beneficiary_nip",
    "Nazwa odbiorcy": "beneficiary_name",
    "Typ odbiorcy": "beneficiary_type",
    "Kraj": "country",
    "Kod województwa (TERYT)": "teryt",
    "Województwo": "voivodeship",
    "Siedziba odbiorcy": "city",
    "Nazwa przedsięwzięcia": "title",
    "Zakres rekordu": "record_scope",
    "Rodzaj identyfikatora publicznego": "public_id_type",
    "Identyfikator publiczny": "public_id_value",
    "Obszar tematyczny": "theme",
    "Rodzaj zamówienia": "order_type",
    "Reżim prawny": "legal_regime",
    "Waluta rozliczeń": "currency",
    "Status przedsięwzięcia": "project_status",
    "Źródło rekordu": "record_source",
    "Data sporządzenia rekordu": "record_date",
    "Wersja rekordu": "record_version",
    "Adnotacja instytucji": "annotation",
}
PROFILES = {"organizer": ORGANIZER_PROFILE}

TERYT_VOIV = {
    "02": "dolnośląskie", "04": "kujawsko-pomorskie", "06": "lubelskie", "08": "lubuskie", "10": "łódzkie",
    "12": "małopolskie", "14": "mazowieckie", "16": "opolskie", "18": "podkarpackie", "20": "podlaskie",
    "22": "pomorskie", "24": "śląskie", "26": "świętokrzyskie", "28": "warmińsko-mazurskie",
    "30": "wielkopolskie", "32": "zachodniopomorskie",
}
# BZP organizationProvince code (PLxx) ↔ TERYT
TERYT_TO_PL = {"02": "PL02", "04": "PL04", "06": "PL06", "08": "PL08", "10": "PL10", "12": "PL12", "14": "PL14",
               "16": "PL16", "18": "PL18", "20": "PL20", "22": "PL22", "24": "PL24", "26": "PL26", "28": "PL28",
               "30": "PL30", "32": "PL32"}

AMOUNT = r"(\d{1,3}(?:[  ]\d{3})*(?:,\d{2})?)\s*zł"
VALUE_RE = re.compile(r"Wartość przedsięwzięcia:\s*" + AMOUNT)
GRANT_RE = re.compile(r"dofinansowanie:\s*" + AMOUNT)
DESC_RE = re.compile(r"Opis:\s*[„\"](.*)[”\"]\s*$", re.S)
FUNDING_RE = re.compile(r"^(KPO[^.]*?(?:B\d\.\d\.\d)?)\.|^(Program Rozwoju Obszarów Wiejskich[^.]*)", re.S)


def pl_amount(s: str | None) -> Decimal | None:
    if not s:
        return None
    s = re.sub(r"[\s  ]", "", s).replace(",", ".")
    try:
        return Decimal(s)
    except Exception:  # noqa: BLE001
        return None


def parse_annotation(text: str | None) -> dict[str, Any]:
    """'KPO, inwestycja B3.1.1. Wartość przedsięwzięcia: 5 350 782,65 zł; dofinansowanie: … Opis: „…”'."""
    out: dict[str, Any] = {}
    if not text:
        return out
    t = text.strip()
    if m := FUNDING_RE.search(t):
        out["funding"] = (m.group(1) or m.group(2)).strip()
    if m := VALUE_RE.search(t):
        out["project_value"] = pl_amount(m.group(1))
        out["project_value_quote"] = m.group(0)
    if m := GRANT_RE.search(t):
        out["grant_value"] = pl_amount(m.group(1))
        out["grant_value_quote"] = m.group(0)
    if m := DESC_RE.search(t):
        out["description"] = m.group(1).strip()
    return out


def part_from_scope(scope: str | None) -> int | None:
    m = re.search(r"część\s*(\d+)", scope or "", re.I)
    return int(m.group(1)) if m else None


def _cell_str(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, dt.datetime | dt.date):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    s = str(v).strip()
    return s or None


def read_rows(data: bytes, filename: str) -> tuple[str, list[str], list[list[Any]]]:
    """Returns (sheet_name, headers, rows). xlsx: sheet 'Projekty' (or the first sheet); csv: ';' or ','."""
    if filename.lower().endswith(".csv"):
        text = data.decode("utf-8-sig")
        dialect = csv.Sniffer().sniff(text[:2000], delimiters=";,\t")
        rows = list(csv.reader(io.StringIO(text), dialect))
        return "csv", [h.strip() for h in rows[0]], rows[1:]
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    ws = wb["Projekty"] if "Projekty" in wb.sheetnames else wb[wb.sheetnames[0]]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    headers = [_cell_str(h) or "" for h in rows[0]]
    return ws.title, headers, [r for r in rows[1:] if any(c is not None for c in r)]


def col_letter(i: int) -> str:
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def validate(rec: dict[str, Any]) -> list[dict[str, Any]]:
    """Identifier/consistency checks for one row → list of issues {field, message, state}."""
    issues = []
    nip = norm_nip(rec.get("beneficiary_nip"))
    if not nip_valid(nip):
        issues.append(dict(field="beneficiary_nip", state="sprzeczne",
                           message=f"NIP odbiorcy {rec.get('beneficiary_nip')!r} ma błędną sumę kontrolną lub format"))
    teryt = (rec.get("teryt") or "").zfill(2) if rec.get("teryt") else None
    voiv = (rec.get("voivodeship") or "").strip().lower()
    if teryt and TERYT_VOIV.get(teryt) != voiv:
        issues.append(dict(field="teryt", state="sprzeczne",
                           message=f"Kod TERYT {teryt} nie odpowiada województwu {rec.get('voivodeship')!r} "
                                   f"(oczekiwano {TERYT_VOIV.get(teryt)!r})"))
    pid_type = (rec.get("public_id_type") or "").lower()
    pid = (rec.get("public_id_value") or "").strip()
    if not pid:
        issues.append(dict(field="public_id_value", state="brak", message="Brak identyfikatora publicznego"))
    elif "bzp" in pid_type:
        if not BZP_NUMBER_RE.match(pid):
            issues.append(dict(field="public_id_value", state="sprzeczne",
                               message=f"Numer ogłoszenia BZP {pid!r} nie ma formatu RRRR/BZP NNNNNNNN/VV"))
    elif "kpo" in pid_type:
        m = KPO_NUMBER_RE.match(pid)
        if not m:
            issues.append(dict(field="public_id_value", state="sprzeczne",
                               message=f"Numer projektu KPO {pid!r} nie ma formatu KPOD.NN.NN-IW.NN-NNNN/RR"))
        elif teryt and teryt.isdigit():
            expected = 12 + int(teryt) // 2
            if int(m.group(1)) != expected:
                issues.append(dict(field="public_id_value", state="sprzeczne",
                                   message=f"Kod instytucji IW.{m.group(1)} w numerze KPO nie odpowiada województwu "
                                           f"(TERYT {teryt} → oczekiwano IW.{expected}; reguła 12 + TERYT/2)"))
    if rec.get("record_scope") and "część" in rec["record_scope"].lower() and part_from_scope(rec["record_scope"]) is None:
        issues.append(dict(field="record_scope", state="sprzeczne", message="Zakres 'część' bez numeru części"))
    if not rec.get("title"):
        issues.append(dict(field="title", state="brak", message="Brak nazwy przedsięwzięcia"))
    return issues


def _ensure_source(session: Session) -> None:
    upsert(session, Source, dict(id=make_id("source", SOURCE), code=SOURCE, name="Plik organizatora (xlsx/csv)",
                                 licence="Dane organizatora HackNation 2026 (MFiPR)", data_location="local"))


def import_file(session: Session, data: bytes, filename: str, profile: str = "organizer",
                actor: str = "system") -> dict[str, Any]:
    """Import projects from bytes. Returns the ImportReport dict. Caller commits."""
    mapping = PROFILES[profile]
    sha = hashlib.sha256(data).hexdigest()
    now = dt.datetime.now(dt.UTC)
    sheet, headers, rows = read_rows(data, filename)
    _ensure_source(session)
    raw_id = make_id("raw_record", SOURCE, filename, sha)
    upsert(session, RawRecord, dict(id=raw_id, source_code=SOURCE, key=filename, sha256=sha, retrieved_from=filename,
                                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    payload={"sheet": sheet, "headers": headers,
                                             "rows": [[_cell_str(c) for c in r] for r in rows]}),
           index_elements=["source_code", "key", "sha256"])
    report = dict(file=filename, sha256=sha, rows=len(rows), created=0, updated=0, unchanged=0, issues=[])
    unknown = [h for h in headers if h and h not in mapping]
    if unknown:
        report["issues"].append({"row": None, "field": None, "message": f"Nieznane kolumny (pominięte): {unknown}"})

    for ri, row in enumerate(rows):
        excel_row = ri + 2
        rec: dict[str, Any] = {}
        ev: dict[str, str] = {}
        for ci, h in enumerate(headers):
            field = mapping.get(h)
            if not field or ci >= len(row):
                continue
            val = _cell_str(row[ci])
            rec[field] = val
            if val is None:
                continue
            eid = add_evidence(session, source_code=SOURCE, kind="xlsx_cell", key=(sha, sheet, excel_row, ci),
                               url=None, retrieved_from=filename, retrieved_at=now, quote=val, import_sha256=sha,
                               raw_record_id=raw_id,
                               locator={"file": filename, "sheet": sheet, "row": excel_row,
                                        "column": col_letter(ci), "header": h, "field": field})
            ev[field] = str(eid)
        code = rec.get("code")
        if not code:
            report["issues"].append({"row": excel_row, "field": "code", "message": "Brak identyfikatora rekordu – pominięto"})
            continue
        pid = make_id("project", code)
        nip = norm_nip(rec.get("beneficiary_nip"))
        ent_id = None
        if nip:
            ent_id = make_id("entity", nip)
            ent = session.get(Entity, ent_id)
            ent_vals = dict(id=ent_id, name=rec.get("beneficiary_name") or nip, nip=nip, role="beneficiary",
                            entity_type=rec.get("beneficiary_type"), city=rec.get("city"),
                            province=TERYT_TO_PL.get((rec.get("teryt") or "").zfill(2)), country="PL")
            if ent is None:
                ent_vals["evidence_ids"] = [ev[k] for k in ("beneficiary_nip", "beneficiary_name") if k in ev]
                ent_vals["aliases"] = [rec.get("beneficiary_name")] if rec.get("beneficiary_name") else []
                upsert(session, Entity, ent_vals)
            else:  # keep enrichment (VAT/BZP) – only extend aliases / evidence
                aliases = list(ent.aliases or [])
                if rec.get("beneficiary_name") and rec["beneficiary_name"] not in aliases:
                    aliases.append(rec["beneficiary_name"])
                ent.aliases = aliases
                ent.evidence_ids = sorted({*(ent.evidence_ids or []), *[ev[k] for k in ("beneficiary_nip",) if k in ev]})
                if not ent.role:
                    ent.role = "beneficiary"
        ann = parse_annotation(rec.get("annotation"))
        teryt = (rec.get("teryt") or "").zfill(2) if rec.get("teryt") else None
        try:
            rdate = dt.date.fromisoformat(rec["record_date"]) if rec.get("record_date") else None
        except ValueError:
            rdate = None
        values = dict(
            id=pid, code=code, title=rec.get("title") or code, description=ann.get("description"),
            beneficiary_id=ent_id, country=rec.get("country"), teryt=teryt, voivodeship=rec.get("voivodeship"),
            city=rec.get("city"), sector="wodkan", order_type=rec.get("order_type"), legal_regime=rec.get("legal_regime"),
            currency=rec.get("currency"), project_status=rec.get("project_status"), funding=ann.get("funding"),
            project_value=ann.get("project_value"), grant_value=ann.get("grant_value"),
            public_id_type=rec.get("public_id_type"), public_id_value=(rec.get("public_id_value") or "").strip() or None,
            record_scope=rec.get("record_scope"), part_no=part_from_scope(rec.get("record_scope")),
            record_source=rec.get("record_source"), record_date=rdate, record_version=rec.get("record_version"),
            annotation=rec.get("annotation"), tier="deep", method="import", confidence=1.0,
            evidence_ids=list(ev.values()),
            import_row={"file": filename, "sha256": sha, "sheet": sheet, "row": excel_row,
                        "cells": {h: _cell_str(row[i]) if i < len(row) else None for i, h in enumerate(headers) if h},
                        "evidence": ev, "profile": profile},
        )
        res = upsert_reviewable(session, Project, values, actor=actor)
        report["created" if res == "inserted" else "updated" if res in ("updated", "proposal") else "unchanged"] += 1

        # facts from the annotation (amounts: vat_basis unknown – never compared with contract amounts directly)
        for ftype, qkey in (("project_value", "project_value_quote"), ("grant_value", "grant_value_quote")):
            if ann.get(ftype) is None:
                continue
            aev = add_evidence(session, source_code=SOURCE, kind="xlsx_cell", key=(sha, sheet, excel_row, "annotation", ftype),
                               retrieved_from=filename, retrieved_at=now, quote=ann[qkey], import_sha256=sha,
                               raw_record_id=raw_id,
                               locator={"file": filename, "sheet": sheet, "row": excel_row,
                                        "column": col_letter(headers.index("Adnotacja instytucji")),
                                        "header": "Adnotacja instytucji", "field": ftype})
            upsert_reviewable(session, Fact, dict(
                id=make_id("fact", "project", pid, ftype), subject_type="project", subject_id=pid, fact_type=ftype,
                value_num=float(ann[ftype]), unit="PLN", vat_basis="unknown", method="import", confidence=1.0,
                evidence_ids=[str(aev)]), actor=actor)

        for iss in validate(rec):
            evid = [ev[iss["field"]]] if iss["field"] in ev else []
            upsert_reviewable(session, DataIssue, dict(
                id=make_id("data_issue", code, "validation", iss["field"]), project_id=pid, kind="validation",
                field=iss["field"], state=iss["state"], message=iss["message"], method="rule", confidence=1.0,
                evidence_ids=evid, what_to_add="Zweryfikuj wartość w pliku źródłowym / u organizatora",
                impact="Błędny identyfikator utrudnia powiązanie z ogłoszeniami BZP"), actor=actor)
            report["issues"].append({"row": excel_row, "code": code, **iss})
    session.flush()
    return report


def import_path(session: Session, path: str | Path, profile: str = "organizer", actor: str = "system") -> dict[str, Any]:
    p = Path(path)
    return import_file(session, p.read_bytes(), p.name, profile=profile, actor=actor)
