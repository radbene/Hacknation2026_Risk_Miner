#!/usr/bin/env python3
"""Parsuje ogloszenia BZP (API e-Zamowienia, pole htmlBody) do plaskich rekordow.

Obslugiwane typy ogloszen (pole noticeType):
  ContractPerformingNotice  - ogloszenie o wykonaniu umowy (etykiety: termin, zmiany, wyplata)
  TenderResultNotice        - ogloszenie o wyniku postepowania (liczba ofert, ceny)
  AgreementUpdateNotice     - ogloszenie o zmianie umowy (sygnal w trakcie realizacji)

Uzycie:
  python3 bzp_parse.py notices.json [wiecej.json ...] --out contracts.csv
  python3 bzp_parse.py notices.json --type TenderResultNotice --out results.csv

Wejscie: plik JSON z lista rekordow dokladnie w ksztalcie odpowiedzi API
(GET /mo-board/api/v1/notice) albo JSONL (jeden rekord w linii).
Tylko biblioteka standardowa (licencja skryptu: do decyzji zespolu; brak zaleznosci).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("style", "script"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("style", "script") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    """Tekst ogloszenia w jednej linii, bez CSS; biale znaki zwiniete do spacji."""
    p = _Text()
    p.feed(html or "")
    return re.sub(r"\s+", " ", "".join(p.parts)).strip()


def _num(s: str | None) -> float | None:
    if not s:
        return None
    s = re.sub(r"\s", "", s).replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _m(text: str, pattern: str) -> str | None:
    m = re.search(pattern, text)
    return m.group(1).strip() if m else None


def _yn(v: str | None) -> int | None:
    return {"Tak": 1, "Nie": 0}.get(v) if v else None


def _date(s: str | None) -> date | None:
    try:
        return date.fromisoformat(s) if s else None
    except ValueError:
        return None


def period_to_days(period: str | None, signed: str | None) -> int | None:
    """'5 miesiace' -> 150, '60 dni' -> 60, 'do 2026-11-13' -> dni od zawarcia umowy."""
    if not period:
        return None
    m = re.match(r"^([\d.,]+)\s*mies", period)
    if m:
        v = _num(m.group(1))
        return round(v * 30) if v is not None else None
    m = re.match(r"^([\d.,]+)\s*dni", period)
    if m:
        v = _num(m.group(1))
        return round(v) if v is not None else None
    m = re.match(r"^od (\d{4}-\d{2}-\d{2}) do (\d{4}-\d{2}-\d{2})", period)
    if m:
        a, b = _date(m.group(1)), _date(m.group(2))
        return (b - a).days if a and b else None
    m = re.match(r"^do (\d{4}-\d{2}-\d{2})", period)
    if m:
        a, b = _date(signed), _date(m.group(1))
        return (b - a).days if a and b else None
    return None


# Numery projektow: perspektywa 2021-2027 (np. FEKP.03.03-IZ.00-0007/25, FENX.01.01-IW.01-0012/23)
# oraz 2014-2020 (np. RPKP.03.04.00-04-0019/17, POIS.02.03.00-00-0123/16).
EU_PROJECT_RE = re.compile(
    r"\b([A-Z]{4}\.\d{2}\.\d{2}(?:\.\d{2})?-[A-Z0-9]{2}(?:\.\d{2})?-[A-Z0-9]{2,4}\d{0,2}/\d{2})\b"
)


def eu_project_no(name: str | None) -> str | None:
    m = EU_PROJECT_RE.search(name or "")
    return m.group(1) if m else None


def _meta(x: dict) -> dict:
    c = (x.get("contractors") or [{}])[0] or {}
    return {
        "bzp": x.get("bzpNumber"),
        "notice_no": x.get("noticeNumber"),
        "pub_date": (x.get("publicationDate") or "")[:10],
        "order_type": x.get("orderType"),
        "province": x.get("organizationProvince"),
        "buyer_nip": x.get("organizationNationalId"),
        "buyer_name": x.get("organizationName"),
        "client_type": x.get("clientType"),
        "tender_type": x.get("tenderType"),
        "below_eu": int(bool(x.get("isTenderAmountBelowEU"))),
        "tender_id": x.get("tenderId"),
        "title": x.get("orderObject"),
        "contractor_nip": c.get("contractorNationalId"),
    }


AMT = r"(\d[\d ]*(?:[,.]\d{1,2})?)"  # kwota: cyfry, spacje, opcjonalnie grosze


def parse_performing(x: dict) -> dict:
    """Ogloszenie o wykonaniu umowy -> jeden rekord umowy z etykietami."""
    t = html_to_text(x.get("htmlBody", ""))
    i = t.find("SEKCJA V")
    s5 = t[i:] if i >= 0 else ""
    row = _meta(x)
    signed = _m(t, r"4\.1\.\) Data zawarcia umowy: (\d{4}-\d{2}-\d{2})")
    period = _m(t, r"4\.2\.\) Okres realizacji zamówienia: (.*?)\s*4\.3\.\)")
    eu_name = _m(t, r"3\.4\.\) Nazwa projektu lub programu: (.*?)\s*3\.5\.\)")
    changes = [v for v in (_num(m) for m in re.findall(r"5\.4\.6\.\) Wartość zmiany: " + AMT, s5)) if v is not None]
    reasons = re.findall(r"5\.4\.4\.\) Przyczyny dokonania zmian: (.*?)\s*5\.4\.5\.\)", s5)
    value = _num(_m(t, r"4\.4\.\) Wartość umowy: " + AMT))
    paid = _num(_m(s5, r"5\.5\.\) Łączna wartość wynagrodzenia wypłacona z tytułu zrealizowanej umowy: " + AMT))
    done = _yn(_m(s5, r"5\.1\.\) Czy umowa została wykonana: (Tak|Nie)"))
    on_time = _yn(_m(s5, r"5\.3\.\) Czy umowę wykonano w pierwotnie określonym terminie: (Tak|Nie)"))
    row.update(
        cpv=_m(t, r"3\.9\.\) Główny kod CPV: (\d{8})") or (x.get("cpvCode") or "")[:8],
        eu_funded=_yn(_m(t, r"3\.3\.\) Czy zamówienie dotyczy projektu lub programu współfinansowanego ze środków Unii Europejskiej: (Tak|Nie)")),
        eu_name=eu_name,
        eu_project_no=eu_project_no(eu_name),
        mode=_m(t, r"3\.5\.\) Tryb udzielenia zamówienia wraz z podstawą prawną: (.*?)\s*3\.6\.\)"),
        prior_notice=_m(t, r"3\.2\.1\.\) Numer ogłoszenia w BZP lub Dz\. Urz\. UE: (.*?)\s*3\.3\.\)"),
        signed_date=signed,
        period_raw=period,
        period_days=period_to_days(period, signed),
        value=value,
        currency=_m(t, r"4\.4\.\) Wartość umowy: " + AMT[1:-1] + r" ?([A-Z]{3})"),
        result_notice=_m(t, r"4\.5\.\) Numer ogłoszenia o wyniku[^:]*: (.*?)\s*SEKCJA V"),
        done=done,
        done_date=_m(s5, r"5\.2\.\) Termin wykonania umowy: (\d{4}-\d{2}-\d{2})"),
        on_time=on_time,
        n_changes=int(_num(_m(s5, r"5\.4\.1\.\) Liczba zmian: (\d+?)\s*(?:5\.4\.2\.\)|5\.5\.\)|$)")) or 0),
        sum_changes=round(sum(changes), 2),
        price_up=int(bool(re.search(r"5\.4\.8\.\) Wzrost ceny[^:]*: Tak", s5))),
        paid=paid,
        proper=_yn(_m(s5, r"5\.6\.\) Czy umowa została wykonana należycie: (Tak|Nie)")),
        change_reasons=" || ".join(r.strip() for r in reasons) or None,
        extra_info=_m(s5, r"SEKCJA VI INFORMACJE DODATKOWE (.*?)\s*\d{4}-\d{2}-\d{2} Biuletyn Zamówień Publicznych"),
    )
    # Etykiety pochodne (definicje: research/04_technologia_i_ewaluacja.md)
    row["label_late"] = None if on_time is None else 1 - on_time
    row["label_cost_up"] = (
        int(paid / value > 1.01) if (value and paid is not None and done == 1) else None
    )
    row["label_failed"] = None if done is None else 1 - done
    return row


def parse_result(x: dict) -> dict:
    """Ogloszenie o wyniku postepowania -> cechy konkurencji i cen (pierwsza czesc)."""
    t = html_to_text(x.get("htmlBody", ""))
    row = _meta(x)
    row.update(
        procedure_result=x.get("procedureResult"),
        n_parts=len(re.findall(r"6\.1\.\) Liczba otrzymanych ofert lub wniosków", t)),
        prior_notice=_m(t, r"2\.14\.\) Numer ogłoszenia: (.*?)\s*(?:SEKCJA|2\.15|3\.1)"),
        eu_funded=_yn(_m(t, r"2\.11\.\)[^:]*: (Tak|Nie)")),
        mode=_m(t, r"3\.1\.\) Tryb udzielenia zamówienia wraz z podstawą prawną:? ?(.*?)\s*SEKCJA IV"),
        est_value=_num(_m(t, r"4\.3\.\) Wartość zamówienia: " + AMT)),
        cpv=_m(t, r"4\.5\.3\.\) Główny kod CPV: (\d{8})"),
        cancel_reason=_m(t, r"5\.2\.1\.\) Przyczyna unieważnienia postępowania: (.*?)\s*SEKCJA VI"),
        n_offers=_num(_m(t, r"6\.1\.\) Liczba otrzymanych ofert lub wniosków: (\d+?)\s*(?:6\.1\.1\.\)|6\.2\.\)|$)")),
        n_sme=_num(_m(t, r"6\.1\.3\.\) Liczba otrzymanych od MŚP: (\d+?)\s*(?:6\.1\.4\.\)|6\.1\.5\.\)|6\.2\.\)|$)")),
        n_rejected=_num(_m(t, r"6\.1\.6\.\)[^:]*: (\d+?)\s*(?:6\.1\.7\.\)|6\.2\.\)|$)")),
        n_abn_low=_num(_m(t, r"6\.1\.7\.\)[^:]*: (\d+?)\s*(?:6\.2\.\)|$)")),
        price_min=_num(_m(t, r"6\.2\.\)[^:]*: " + AMT)),
        price_max=_num(_m(t, r"6\.3\.\)[^:]*: " + AMT)),
        price_won=_num(_m(t, r"6\.4\.\)[^:]*: " + AMT)),
        joint=_yn(_m(t, r"7\.1\.\)[^:]*: (Tak|Nie)")),
        contractor_size=_m(t, r"7\.2\.\) Wielkość przedsiębiorstwa wykonawcy: (.*?)\s*7\.3\.\)"),
        subcontract=_yn(_m(t, r"7\.4\.\)[^:]*\?: (Tak|Nie)")),
        in_plan=_yn(_m(t, r"2\.8\.\)[^:]*: (Tak|Nie)")),
        signed_date=_m(t, r"8\.1\.\) Data zawarcia umowy: (\d{4}-\d{2}-\d{2})"),
        value=_num(_m(t, r"8\.2\.\) Wartość umowy/umowy ramowej: " + AMT)),
        period_raw=_m(t, r"8\.3\.\) Okres realizacji zamówienia albo umowy ramowej: (.*?)\s*(?:8\.4\.\)|\d{4}-\d{2}-\d{2} Biuletyn)"),
    )
    return row


def parse_change(x: dict) -> dict:
    """Ogloszenie o zmianie umowy -> sygnal ostrzegawczy w trakcie realizacji."""
    t = html_to_text(x.get("htmlBody", ""))
    i = t.find("SEKCJA V")
    s5 = t[i:] if i >= 0 else ""
    row = _meta(x)
    eu_name = _m(t, r"3\.3\.\) Nazwa projektu lub programu: (.*?)\s*3\.4\.\)")
    signed = _m(t, r"4\.1\.\) Data zawarcia umowy/umowy ramowej: (\d{4}-\d{2}-\d{2})")
    period = _m(t, r"4\.2\.\) Okres realizacji zamówienia/umowy ramowej: (.*?)\s*4\.3\.\)")
    row.update(
        prior_notice=_m(t, r"3\.1\.1\.\) Numer ogłoszenia: (.*?)\s*3\.2\.\)"),
        eu_funded=_yn(_m(t, r"3\.2\.\) Czy zamówienie albo umowa ramowa dotyczy projektu lub programu współfinansowanego ze środków Unii Europejskiej: (Tak|Nie)")),
        eu_name=eu_name,
        eu_project_no=eu_project_no(eu_name),
        cpv=_m(t, r"3\.8\.\) Główny kod CPV: (\d{8})"),
        signed_date=signed,
        period_raw=period,
        period_days=period_to_days(period, signed),
        value=_num(_m(t, r"4\.4\.\) Wartość umowy/umowy ramowej: " + AMT)),
        result_notice=_m(t, r"4\.5\.\) Numer ogłoszenia o wyniku postępowania[^:]*: (.*?)\s*SEKCJA V"),
        change_date=_m(s5, r"5\.1\.\) Data zmiany umowy/umowy ramowej\)?: (\d{4}-\d{2}-\d{2})"),
        change_basis=_m(s5, r"5\.2\.\) Podstawa prawna zmiany umowy/umowy ramowej: (.*?)\s*5\.3\.\)"),
        change_reason=_m(s5, r"5\.3\.\) Przyczyny dokonania zmian umowy/umowy ramowej: (.*?)\s*5\.4\.\)"),
        change_desc=_m(s5, r"5\.4\.\) Krótki opis zmiany umowy/umowy ramowej: (.*?)\s*5\.5\.\)"),
        price_up=_yn(_m(s5, r"5\.5\.3\.\) Wzrost ceny[^:]*: (Tak|Nie)")),
        earlier_changes=_yn(_m(s5, r"5\.6\.\) Wcześniejsze zmiany[^:]*: (Tak|Nie)")),
    )
    return row


PARSERS = {
    "ContractPerformingNotice": parse_performing,
    "TenderResultNotice": parse_result,
    "AgreementUpdateNotice": parse_change,
}


def load_records(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        return [json.loads(line) for line in raw.splitlines() if line.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("--type", choices=sorted(PARSERS), help="parsuj tylko ten typ (domyslnie: typ z rekordu)")
    ap.add_argument("--out", type=Path, required=True, help="plik CSV")
    a = ap.parse_args()

    rows, skipped = [], 0
    for path in a.inputs:
        for rec in load_records(path):
            ntype = rec.get("noticeType")
            if (a.type and ntype != a.type) or ntype not in PARSERS:
                skipped += 1
                continue
            rows.append(PARSERS[ntype](rec))
    if not rows:
        print("Brak rekordow obslugiwanego typu.", file=sys.stderr)
        return 1
    fields: list[str] = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"Zapisano {len(rows)} rekordow do {a.out} (pominieto {skipped}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
