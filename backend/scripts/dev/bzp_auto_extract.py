#!/usr/bin/env python3
"""DEV-ONLY (S3): BZP zip → compact per-notice records for seeding the analysis DB.

Not production code. S1 owns the real parse/link pipeline; this exists only so S3 can build and test the
analysis on a realistic auto tier before S1's data lands. Reuses the prep label regexes (bzp_parse.py).

    uv run python scripts/dev/bzp_auto_extract.py [--zip PATH] [--out ../data/dev/bzp_auto.jsonl.gz] [--limit N]
"""

from __future__ import annotations

import argparse
import gzip
import json
import lzma
import re
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3] / ".claude/skills/riskminer-dane-i-zrodla/scripts"))
from bzp_parse import AMT, _date, _m, _num, _yn, html_to_text, period_to_days  # noqa: E402

DEFAULT_ZIP = "/home/radek/workspace/hacknation/risk_miner/risk-miner/data/raw/zip/risk_miner_bzp_kopia/bzp_kopia/notices.jsonl.xz"
TYPES = {"ContractPerformingNotice", "TenderResultNotice", "AgreementUpdateNotice", "ContractNotice"}


def basis_code(s: str | None) -> str | None:
    if not s:
        return None
    m = re.search(r"art\.?\s*455\s*ust\.?\s*(\d)(?:\s*pkt\.?\s*(\d))?", s)
    if not m:
        return None
    return f"455.{m.group(1)}" + (f".{m.group(2)}" if m.group(2) else "")


def _base(x: dict) -> dict:
    c = (x.get("contractors") or [{}])[0] or {}
    return {
        "type": x["noticeType"], "object_id": x["objectId"], "notice_no": x.get("noticeNumber"),
        "bzp": x.get("bzpNumber"), "pub": (x.get("publicationDate") or "")[:10], "ocid": x.get("tenderId"),
        "title": x.get("orderObject"), "cpv": (x.get("cpvCode") or "")[:8], "cpv_all": x.get("cpvCode"),
        "buyer_nip": x.get("organizationNationalId"), "buyer": x.get("organizationName"),
        "city": x.get("organizationCity"), "province": x.get("organizationProvince"),
        "order_type": x.get("orderType"), "contractor_nip": c.get("contractorNationalId"),
        "contractor": c.get("contractorName"), "result": x.get("procedureResult"),
    }


def parse(line: str) -> dict | None:
    x = json.loads(line)
    nt = x.get("noticeType")
    if nt not in TYPES:
        return None
    r = _base(x)
    t = html_to_text(x.get("htmlBody", ""))
    if nt == "ContractNotice":
        r.update(
            est=_num(_m(t, r"Wartość zamówienia[^:]*: " + AMT)),
            parts=_num(_m(t, r"Liczba części: (\d+)")),
            period_raw=_m(t, r"Okres realizacji zamówienia albo umowy ramowej: (.*?)\s*\d+\.\d+\.\)"),
            dnb=bool(re.search(r"zaprojektuj i wybuduj|zaprojektowanie i (?:wy)?budow", t, re.I)),
        )
        return r
    i = t.find("SEKCJA V")
    s5 = t[i:] if i >= 0 else ""
    if nt == "ContractPerformingNotice":
        signed = _m(t, r"4\.1\.\) Data zawarcia umowy: (\d{4}-\d{2}-\d{2})")
        period = _m(t, r"4\.2\.\) Okres realizacji zamówienia: (.*?)\s*4\.3\.\)")
        blocks = re.split(r"5\.4\.2\.\) Numer zmiany:", s5)[1:]
        changes = []
        for k, b in enumerate(blocks, 1):
            basis = _m(b, r"5\.4\.3\.\) Podstawa prawna zmiany: (.*?)\s*5\.4\.4\.\)")
            changes.append({
                "no": k, "basis": basis, "code": basis_code(basis),
                "reason": _m(b, r"5\.4\.4\.\) Przyczyny dokonania zmian: (.*?)\s*5\.4\.5\.\)"),
                "desc": _m(b, r"5\.4\.5\.\) Krótki opis zamówienia po zmianie: (.*?)\s*(?:5\.4\.\d\.\)|5\.5\.\)|$)"),
                "delta": _num(_m(b, r"5\.4\.6\.\) Wartość zmiany: " + AMT)),
                "price_up": _yn(_m(b, r"5\.4\.8\.\) Wzrost ceny[^:]*: (Tak|Nie)")),
            })
        r.update(
            signed=signed, period_raw=period, period_days=period_to_days(period, signed),
            value=_num(_m(t, r"4\.4\.\) Wartość umowy: " + AMT)),
            currency=_m(t, r"4\.4\.\) Wartość umowy: [\d ,.]+ ?([A-Z]{3})"),
            result_notice=_m(t, r"4\.5\.\) Numer ogłoszenia o wyniku[^:]*: (.*?)\s*SEKCJA V"),
            prior_notice=_m(t, r"3\.2\.1\.\) Numer ogłoszenia w BZP lub Dz\. Urz\. UE: (.*?)\s*3\.3\.\)"),
            eu=_yn(_m(t, r"3\.3\.\) Czy zamówienie dotyczy projektu lub programu współfinansowanego ze środków Unii Europejskiej: (Tak|Nie)")),
            eu_name=_m(t, r"3\.4\.\) Nazwa projektu lub programu: (.*?)\s*3\.5\.\)"),
            mode=_m(t, r"3\.5\.\) Tryb udzielenia zamówienia wraz z podstawą prawną: (.*?)\s*3\.6\.\)"),
            done=_yn(_m(s5, r"5\.1\.\) Czy umowa została wykonana: (Tak|Nie)")),
            done_date=_m(s5, r"5\.2\.\) Termin wykonania umowy: (\d{4}-\d{2}-\d{2})"),
            on_time=_yn(_m(s5, r"5\.3\.\) Czy umowę wykonano w pierwotnie określonym terminie: (Tak|Nie)")),
            n_changes=int(_num(_m(s5, r"5\.4\.1\.\) Liczba zmian: (\d+)")) or 0),
            changes=changes,
            paid=_num(_m(s5, r"5\.5\.\) Łączna wartość wynagrodzenia wypłacona z tytułu zrealizowanej umowy: " + AMT)),
            proper=_yn(_m(s5, r"5\.6\.\) Czy umowa została wykonana należycie: (Tak|Nie)")),
            extra=(_m(s5, r"SEKCJA VI INFORMACJE DODATKOWE (.*?)\s*\d{4}-\d{2}-\d{2} Biuletyn") or "")[:500] or None,
            part_title=_m(x.get("orderObject") or "", r"[Cc]zęś\w* (?:nr )?(\d+)"),
        )
        return r
    if nt == "TenderResultNotice":
        r.update(
            prior_notice=_m(t, r"2\.14\.\) Numer ogłoszenia: (.*?)\s*(?:SEKCJA|2\.15|3\.1)"),
            est=_num(_m(t, r"4\.3\.\) Wartość zamówienia: " + AMT)),
            n_parts=len(re.findall(r"6\.1\.\) Liczba otrzymanych ofert lub wniosków", t)) or None,
            cancel_basis=_m(s5, r"5\.2\.\) Podstawa prawna unieważnienia postępowania: (.*?)\s*5\.2\.1\.\)"),
            cancel_reason=(_m(s5, r"5\.2\.1\.\) Przyczyna unieważnienia postępowania: (.*?)\s*SEKCJA VI") or "")[:600] or None,
            n_offers=_num(_m(t, r"6\.1\.\) Liczba otrzymanych ofert lub wniosków: (\d+)")),
            price_min=_num(_m(t, r"6\.2\.\)[^:]*: " + AMT)),
            price_max=_num(_m(t, r"6\.3\.\)[^:]*: " + AMT)),
            price_won=_num(_m(t, r"6\.4\.\)[^:]*: " + AMT)),
            budget=_num(_m(t, r"(?:kwot\w+,? jak\w+ zamawiający zamierza przeznaczyć|Kwota, jaką zamawiający zamierza przeznaczyć)[^:]*: " + AMT)),
            signed=_m(t, r"8\.1\.\) Data zawarcia umowy: (\d{4}-\d{2}-\d{2})"),
            value=_num(_m(t, r"8\.2\.\) Wartość umowy/umowy ramowej: " + AMT)),
        )
        return r
    # AgreementUpdateNotice
    basis = _m(s5, r"5\.2\.\) Podstawa prawna zmiany umowy/umowy ramowej: (.*?)\s*5\.3\.\)")
    r.update(
        signed=_m(t, r"4\.1\.\) Data zawarcia umowy/umowy ramowej: (\d{4}-\d{2}-\d{2})"),
        value=_num(_m(t, r"4\.4\.\) Wartość umowy/umowy ramowej: " + AMT)),
        result_notice=_m(t, r"4\.5\.\) Numer ogłoszenia o wyniku postępowania[^:]*: (.*?)\s*SEKCJA V"),
        change_date=_m(s5, r"5\.1\.\) Data zmiany umowy/umowy ramowej\)?: (\d{4}-\d{2}-\d{2})"),
        basis=basis, code=basis_code(basis),
        reason=(_m(s5, r"5\.3\.\) Przyczyny dokonania zmian umowy/umowy ramowej: (.*?)\s*5\.4\.\)") or "")[:1500] or None,
        desc=(_m(s5, r"5\.4\.\) Krótki opis zmiany umowy/umowy ramowej: (.*?)\s*5\.5\.\)") or "")[:1500] or None,
        price_up=_yn(_m(s5, r"5\.5\.3\.\) Wzrost ceny[^:]*: (Tak|Nie)")),
    )
    return r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", default=DEFAULT_ZIP)
    ap.add_argument("--out", default=str(HERE.parents[3] / "data/dev/bzp_auto.jsonl.gz"))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    _ = _date  # re-exported helper kept for loaders
    with lzma.open(a.zip, "rt", encoding="utf-8") as f, gzip.open(out, "wt", encoding="utf-8") as w, \
            Pool(a.workers) as pool:
        src = (line for i, line in enumerate(f) if not a.limit or i < a.limit)
        for rec in pool.imap_unordered(parse, src, chunksize=64):
            if rec:
                w.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
                if n % 10000 == 0:
                    print(n, flush=True)
    print(f"wrote {n} records → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
