"""Typed extraction from DOM fields (parse/bzp_dom.py) for the 4 BZP notice types.

Matching is on *labels* (numbers differ between types); every extracted value records the index of the
field it came from in `refs` (→ evidence locator: section, label, part, canonical-text offsets).
Label regexes adapted from the prep `bzp_parse.py` (performing/result/change) + a new ContractNotice parser.
"""

from __future__ import annotations

import calendar
import datetime as dt
import re
from decimal import Decimal, InvalidOperation
from typing import Any

from riskminer.parse.bzp_dom import Field, ParsedDom, parse_dom

BZP_NO_RE = re.compile(r"\b(\d{4}/BZP \d{8})(?:/(\d{2}))?\b")
TED_NO_RE = re.compile(r"\b(\d{3,6}-\d{4})\b")
KPO_RE = re.compile(r"\bKPO[A-Z]\.\d{2}\.\d{2}-IW\.\d{2}-\d{4}/\d{2}\b")
# prep EU_PROJECT_RE: 2021-2027 (FEKP.03.03-IZ.00-0007/25) and 2014-2020 (RPKP.03.04.00-04-0019/17)
EU_PROJECT_RE = re.compile(r"\b([A-Z]{4}\.\d{2}\.\d{2}(?:\.\d{2})?-[A-Z0-9]{2}(?:\.\d{2})?-[A-Z0-9]{2,4}\d{0,2}/\d{2})\b")
AMOUNT_RE = re.compile(r"(\d[\d  ]*(?:[,.]\d{1,2})?)")
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
CPV_RE = re.compile(r"\b(\d{8})-\d\b")
LOT_TITLE_RE = re.compile(r"Umowa dla części nr\s*(\d+)", re.I)
BASIS_RE = re.compile(r"art\.?\s*(\d+)\s*(?:ust\.?\s*(\d+))?\s*(?:pkt\.?\s*(\d+))?(?:\s*lit\.?\s*([a-z]))?", re.I)


# ---------------------------------------------------------------- value helpers

def amount(s: str | None) -> Decimal | None:
    if not s:
        return None
    m = AMOUNT_RE.search(s)
    if not m:
        return None
    try:
        return Decimal(re.sub(r"[\s  ]", "", m.group(1)).replace(",", "."))
    except InvalidOperation:
        return None


def date(s: str | None) -> dt.date | None:
    m = DATE_RE.search(s or "")
    if not m:
        return None
    try:
        return dt.date.fromisoformat(m.group(1))
    except ValueError:
        return None


def yes_no(s: str | None) -> bool | None:
    if not s:
        return None
    t = s.strip().lower()
    if t.startswith("tak"):
        return True
    if t.startswith("nie"):
        return False
    return None


def integer(s: str | None) -> int | None:
    m = re.search(r"\d+", s or "")
    return int(m.group(0)) if m else None


def add_months(d: dt.date, months: float) -> dt.date:
    whole = int(months)
    y, m = divmod(d.month - 1 + whole, 12)
    year, month = d.year + y, m + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    out = dt.date(year, month, day)
    frac = months - whole
    return out + dt.timedelta(days=round(frac * 30)) if frac else out


def period_end(period: str | None, start: dt.date | None) -> tuple[dt.date | None, int | None]:
    """'10 miesiące' (calendar months from the contract date), '160 dni', 'do 2026-04-27', 'od A do B'.

    Returns (planned_end, planned_days)."""
    if not period:
        return None, None
    p = period.strip().lower()
    m = re.match(r"^od\s+(\d{4}-\d{2}-\d{2})\s+do\s+(\d{4}-\d{2}-\d{2})", p)
    if m:
        a, b = dt.date.fromisoformat(m.group(1)), dt.date.fromisoformat(m.group(2))
        return b, (b - a).days
    m = re.match(r"^do\s+(\d{4}-\d{2}-\d{2})", p)
    if m:
        b = dt.date.fromisoformat(m.group(1))
        return b, ((b - start).days if start else None)
    m = re.match(r"^([\d.,]+)\s*mies", p)
    if m:
        n = float(m.group(1).replace(",", "."))
        if start:
            end = add_months(start, n)
            return end, (end - start).days
        return None, round(n * 30)
    m = re.match(r"^([\d.,]+)\s*dni", p)
    if m:
        n = round(float(m.group(1).replace(",", ".")))
        return (start + dt.timedelta(days=n) if start else None), n
    m = re.match(r"^([\d.,]+)\s*(?:tyg|tydz)", p)
    if m:
        n = round(float(m.group(1).replace(",", ".")) * 7)
        return (start + dt.timedelta(days=n) if start else None), n
    m = re.match(r"^([\d.,]+)\s*lat", p)
    if m:
        n = float(m.group(1).replace(",", ".")) * 12
        if start:
            end = add_months(start, n)
            return end, (end - start).days
    return None, None


def legal_basis_code(s: str | None) -> str | None:
    """'art. 455 ust. 1 pkt 4 ustawy' → '455.1.4'; 'art. 455 ust. 2' → '455.2'."""
    if not s:
        return None
    codes = []
    for m in BASIS_RE.finditer(s):
        parts = [m.group(1), m.group(2), m.group(3)]
        code = ".".join(p for p in parts if p)
        if m.group(4):
            code += m.group(4)
        codes.append(code)
    return ";".join(dict.fromkeys(codes)) or None


def change_kinds(basis: str | None, reason: str | None, desc: str | None, value: Decimal | None,
                 price_up: bool | None) -> list[str]:
    text = " ".join(x for x in (reason, desc) if x).lower()
    kinds = []
    if re.search(r"termin|przedłuż|wydłuż|do dnia|\bdni\b|miesi", text):
        kinds.append("termin")
    if price_up or re.search(r"wynagrodzeni|cen[aęy]\b|kwot", text):
        kinds.append("wynagrodzenie")
    if re.search(r"zakres|dodatkow|zamienn|zaniechan|ogranicz", text) or (basis or "").find("pkt 3") >= 0:
        kinds.append("zakres")
    if (basis or "").replace(" ", "").find("ust.1pkt2") >= 0 or re.search(r"nowy wykonawc|zmian[ay] wykonawcy", text):
        kinds.append("wykonawca")
    return kinds or ["inne"]


def contractor_id(raw: str | None) -> tuple[str | None, str | None]:
    """'NIP 738-000-52-65' / 'REGON: 932989044' / '113-285-55-84' / 'NIP:PL 6690503086' → (digits, NIP|REGON)."""
    if not raw:
        return None, None
    first = re.split(r"[,;]", raw)[0]
    digits = re.sub(r"\D", "", first)
    if len(digits) == 10:
        return digits, "NIP"
    if len(digits) in (9, 14):
        return digits, "REGON"
    return (digits or None), None


def norm_notice_no(s: str | None) -> str | None:
    """'2023/BZP 00110672' or '2023/BZP 00110672/01' → '2023/BZP 00110672' (bzp number, no version)."""
    m = BZP_NO_RE.search(s or "")
    return m.group(1) if m else None


# ---------------------------------------------------------------- field lookup

class Fields:
    def __init__(self, dom: ParsedDom):
        self.dom = dom
        self.f = dom.fields
        self.refs: dict[str, int] = {}

    def idx(self, label_re: str, part: int | None | str = "any", section: str | None = None, start: int = 0,
            stop: int | None = None) -> int | None:
        rx = re.compile(label_re, re.I)
        for i in range(start, stop if stop is not None else len(self.f)):
            fld = self.f[i]
            if part != "any" and fld.part_no != part:
                continue
            if section is not None and not fld.section.startswith(section):
                continue
            if rx.search(fld.label):
                return i
        return None

    def get(self, key: str, label_re: str, part: int | None | str = "any", section: str | None = None,
            start: int = 0, stop: int | None = None) -> str | None:
        i = self.idx(label_re, part, section, start, stop)
        if i is None:
            return None
        self.refs[key] = i
        return self.f[i].value or None

    def all(self, label_re: str, part: int | None | str = "any", section: str | None = None) -> list[int]:
        rx = re.compile(label_re, re.I)
        return [i for i, fld in enumerate(self.f) if rx.search(fld.label)
                and (part == "any" or fld.part_no == part) and (section is None or fld.section.startswith(section))]


def _cpvs(s: str | None) -> list[str]:
    return CPV_RE.findall(s or "")


def _eu(fs: Fields, funded_re: str, name_re: str) -> dict[str, Any]:
    funded = yes_no(fs.get("eu.funded", funded_re))
    name = fs.get("eu.name", name_re)
    text = (name or "") + "\n" + fs.dom.canonical_text
    kpo = sorted(set(KPO_RE.findall(text)))
    eu_nos = sorted(set(EU_PROJECT_RE.findall(name or "")))
    return {"funded": funded, "name": name, "kpo_numbers": kpo, "project_numbers": eu_nos,
            "kpo_mentioned": bool(re.search(r"Krajow\w+ Plan\w* Odbudowy|\bKPO\b", text))}


def _contractor(fs: Fields, prefix: str, part: int | None | str = "any", section: str | None = None) -> dict[str, Any]:
    name = fs.get(f"{prefix}.name", r"^Nazwa \(firma\) wykonawcy", part, section)
    raw = fs.get(f"{prefix}.id", r"^Krajowy Numer Identyfikacyjny", part, section)
    cid, kind = contractor_id(raw)
    return {"name": name, "id_raw": raw, "id": cid, "id_type": kind,
            "city": fs.get(f"{prefix}.city", r"^Miejscowość", part, section),
            "size": fs.get(f"{prefix}.size", r"^Wielkość przedsiębiorstwa", part, section)}


def xrefs(fs: Fields, own_no: str | None) -> list[dict[str, Any]]:
    out = []
    own = norm_notice_no(own_no)
    for i, fld in enumerate(fs.f):
        lab = fld.label.lower()
        if not re.search(r"numer ogłoszenia|numer planu|identyfikator wcześniejszego", lab):
            continue
        vals = [(m.group(1), "bzp") for m in BZP_NO_RE.finditer(fld.value)]
        if not vals and "dz. urz" in lab:
            vals = [(m.group(1), "ted") for m in TED_NO_RE.finditer(fld.value)]
        for no, src in vals:
            if src == "bzp" and no == own and "planu" not in lab:
                continue
            if "planu" in lab:
                kind = "plan"
            elif "wyniku" in lab:
                kind = "result_notice"
            elif "o zmianie umowy" in lab:
                kind = "earlier_change"
            elif "wcześniejszego" in lab:
                kind = "earlier_procedure"
            else:
                kind = "prior_notice"
            out.append({"section": fld.section, "label": fld.label, "notice_number": no, "source": src,
                        "kind": kind, "field": i, "part_no": fld.part_no})
    return out


# ---------------------------------------------------------------- per type

def parse_contract_notice(fs: Fields) -> dict[str, Any]:
    d: dict[str, Any] = {
        "title": fs.get("title", r"^Nazwa zamówienia"),
        "ocid": fs.get("ocid", r"^Identyfikator postępowania"),
        "buyer_id": fs.get("buyer_id", r"^Krajowy Numer Identyfikacyjny", section="1"),
        "plan_ref": fs.get("plan_ref", r"^Numer planu postępowań"),
        "mode": fs.get("mode", r"^Tryb udzielenia"),
        "platform_url": fs.get("platform_url", r"^Adres strony internetowej prowadzonego postępowania"),
        "reference_no": fs.get("reference_no", r"^Numer referencyjny"),
        "order_type": fs.get("order_type", r"^Rodzaj zamówienia"),
        "n_parts": integer(fs.get("n_parts", r"^Liczba części")),
        "offers_deadline": fs.get("offers_deadline", r"^Termin składania ofert"),
        "eu": _eu(fs, r"projektu lub programu współfinansowanego", r"^Nazwa projektu lub programu"),
        "est_value": amount(fs.get("est_value", r"^(Szacunkowa )?[Ww]artość zamówienia")),
    }
    parts = sorted({f.part_no for f in fs.f if f.part_no}) or [None]
    d["parts"] = {}
    for p in parts:
        key = str(p or 0)
        period = fs.get(f"parts.{key}.period", r"^Okres realizacji", p)
        cpv_main = _cpvs(fs.get(f"parts.{key}.cpv_main", r"^Główny kod CPV", p))
        crit_names = [fs.f[i].value for i in fs.all(r"^Nazwa kryterium", p)]
        crit_w = [fs.f[i].value for i in fs.all(r"^Waga", p)]
        d["parts"][key] = {
            "description": fs.get(f"parts.{key}.description", r"^Krótki opis przedmiotu", p),
            "cpv_main": cpv_main[0] if cpv_main else None,
            "cpv_extra": _cpvs(fs.get(f"parts.{key}.cpv_extra", r"^Dodatkowy kod CPV", p)),
            "period": period, "planned_end": period_end(period, None)[0], "planned_days": period_end(period, None)[1],
            "criteria": [{"name": n, "weight": w} for n, w in zip(crit_names, crit_w, strict=False)],
            "value": amount(fs.get(f"parts.{key}.value", r"^Wartość części", p)),
        }
    return d


def parse_tender_result(fs: Fields) -> dict[str, Any]:
    d: dict[str, Any] = {
        "title": fs.get("title", r"^Nazwa zamówienia"),
        "ocid": fs.get("ocid", r"^Identyfikator postępowania"),
        "buyer_id": fs.get("buyer_id", r"^Krajowy Numer Identyfikacyjny", section="1"),
        "eu": _eu(fs, r"projektu lub programu współfinansowanego", r"^Nazwa projektu lub programu"),
        "prior_notice": fs.get("prior_notice", r"^Numer ogłoszenia$", section="2.14"),
        "mode": fs.get("mode", r"^Tryb udzielenia"),
        "reference_no": fs.get("reference_no", r"^Numer referencyjny"),
        "est_value": amount(fs.get("est_value", r"^(Wartość zamówienia|Łączna wartość poszczególnych części)")),
    }
    parts = sorted({f.part_no for f in fs.f if f.part_no}) or [None]
    d["n_parts"] = len([p for p in parts if p])
    d["parts"] = {}
    for p in parts:
        key = str(p or 0)
        result = fs.get(f"parts.{key}.result", r"^Postępowanie zakończyło się", p)
        cancelled = bool(result and re.search(r"unieważn", result, re.I))
        signed = date(fs.get(f"parts.{key}.signed_at", r"^Data zawarcia umowy", p))
        period = fs.get(f"parts.{key}.period", r"^Okres realizacji", p)
        pend, pdays = period_end(period, signed)
        cpv_main = _cpvs(fs.get(f"parts.{key}.cpv_main", r"^Główny kod CPV", p))
        d["parts"][key] = {
            "description": fs.get(f"parts.{key}.description", r"^Krótki opis przedmiotu", p),
            "cpv_main": cpv_main[0] if cpv_main else None,
            "part_value": amount(fs.get(f"parts.{key}.part_value", r"^Wartość części", p)),
            "result": result, "cancelled": cancelled,
            "cancel_basis": fs.get(f"parts.{key}.cancel_basis", r"^Podstawa prawna unieważnienia", p),
            "cancel_reason": fs.get(f"parts.{key}.cancel_reason", r"^Przyczyna unieważnienia", p),
            "n_offers": integer(fs.get(f"parts.{key}.n_offers", r"^Liczba otrzymanych ofert lub wniosków", p)),
            "n_sme": integer(fs.get(f"parts.{key}.n_sme", r"^Liczba otrzymanych od MŚP", p)),
            "n_rejected": integer(fs.get(f"parts.{key}.n_rejected", r"^Liczba ofert odrzuconych", p)),
            "n_abnormally_low": integer(fs.get(f"parts.{key}.n_abnormally_low", r"^Liczba ofert zawierających rażąco", p)),
            "price_min": amount(fs.get(f"parts.{key}.price_min", r"najniższą ceną", p)),
            "price_max": amount(fs.get(f"parts.{key}.price_max", r"najwyższą ceną", p)),
            "price_won": amount(fs.get(f"parts.{key}.price_won", r"któremu udzielono zamówienia$", p, section="6")),
            "joint": yes_no(fs.get(f"parts.{key}.joint", r"wykonawcom wspólnie ubiegającym", p)),
            "contractor": _contractor(fs, f"parts.{key}.contractor", p, section="7"),
            "signed_at": signed,
            "value": amount(fs.get(f"parts.{key}.value", r"^Wartość umowy", p)),
            "period": period, "planned_end": pend, "planned_days": pdays,
        }
    return d


def _lot_from_headings(fs: Fields, title: str | None) -> int | None:
    for f in fs.f:
        m = LOT_TITLE_RE.search(f.label) if not f.section else None
        if m:
            return int(m.group(1))
    m = LOT_TITLE_RE.search(title or "")
    return int(m.group(1)) if m else None


def _contract_block(fs: Fields, d: dict[str, Any]) -> None:
    signed = date(fs.get("signed_at", r"^Data zawarcia umowy", section="4"))
    period = fs.get("period", r"^Okres realizacji", section="4")
    pend, pdays = period_end(period, signed)
    d.update(signed_at=signed, period=period, planned_end=pend, planned_days=pdays,
             contractor=_contractor(fs, "contractor", section="4.3"),
             value=amount(fs.get("value", r"^Wartość umowy", section="4")),
             result_notice=fs.get("result_notice", r"^Numer ogłoszenia o wyniku", section="4"))


def parse_agreement_update(fs: Fields) -> dict[str, Any]:
    d: dict[str, Any] = {
        "ocid": fs.get("ocid", r"^Identyfikator postępowania"),
        "buyer_id": fs.get("buyer_id", r"^Krajowy Numer Identyfikacyjny", section="1"),
        "prior_notice": fs.get("prior_notice", r"^Numer ogłoszenia$", section="3.1.1"),
        "eu": _eu(fs, r"projektu lub programu współfinansowanego", r"^Nazwa projektu lub programu"),
        "mode": fs.get("mode", r"^Tryb udzielenia"),
        "title": fs.get("title", r"^Nazwa zamówienia"),
        "description": fs.get("description", r"^Krótki opis przedmiotu", section="3"),
        "cpv_main": (_cpvs(fs.get("cpv_main", r"^Główny kod CPV")) or [None])[0],
    }
    _contract_block(fs, d)
    d["lot_no"] = _lot_from_headings(fs, d.get("title"))
    basis = fs.get("change.legal_basis", r"^Podstawa prawna zmiany", section="5")
    reason = fs.get("change.reason", r"^Przyczyny dokonania zmian", section="5")
    desc = fs.get("change.description", r"^Krótki opis zmiany", section="5")
    value = amount(fs.get("change.value", r"^Wartość zmiany$", section="5"))
    price_up = yes_no(fs.get("change.price_up", r"^Wzrost ceny", section="5"))
    earlier = fs.get("change.earlier", r"^Wcześniejsze zmiany", section="5")
    earlier_nos = [x["notice_number"] for x in xrefs(fs, None) if x["kind"] == "earlier_change"]
    d["change"] = {
        "change_no": 1, "date": date(fs.get("change.date", r"^Data zmiany umowy", section="5")),
        "legal_basis": basis, "legal_basis_code": legal_basis_code(basis), "reason": reason, "description": desc,
        "value": value, "currency": fs.get("change.currency", r"^Kod waluty", section="5"), "price_up": price_up,
        "earlier_changes": yes_no(earlier), "earlier_notices": earlier_nos,
        "new_end": _new_end(desc, reason), "kinds": change_kinds(basis, reason, desc, value, price_up),
    }
    return d


_NEW_END_RE = re.compile(r"(?:do\s+dnia|do|termin[^.]{0,60}?)\s*(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})", re.I)
_NEW_END_ISO_RE = re.compile(r"(?:do\s+dnia|do)\s*(\d{4})-(\d{2})-(\d{2})", re.I)
MONTHS = {"stycznia": 1, "lutego": 2, "marca": 3, "kwietnia": 4, "maja": 5, "czerwca": 6, "lipca": 7, "sierpnia": 8,
          "września": 9, "października": 10, "listopada": 11, "grudnia": 12}
_NEW_END_WORD_RE = re.compile(r"(\d{1,2})\s+(" + "|".join(MONTHS) + r")\s+(\d{4})", re.I)


def _new_end(desc: str | None, reason: str | None) -> dt.date | None:
    """New completion date from the change description ('… do dnia 31.05.2025 r.')."""
    for text in (desc, reason):
        if not text:
            continue
        dates = []
        for m in _NEW_END_RE.finditer(text):
            try:
                dates.append(dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1))))
            except ValueError:
                pass
        if re.search(r"termin|do dnia|wykonania", text, re.I):
            for m in _NEW_END_WORD_RE.finditer(text):
                try:
                    dates.append(dt.date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1))))
                except ValueError:
                    pass
        for m in _NEW_END_ISO_RE.finditer(text):
            try:
                dates.append(dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
            except ValueError:
                pass
        if dates:
            return max(dates)
    return None


def parse_contract_performing(fs: Fields) -> dict[str, Any]:
    d: dict[str, Any] = {
        "ocid": fs.get("ocid", r"^Identyfikator postępowania"),
        "buyer_id": fs.get("buyer_id", r"^Krajowy Numer Identyfikacyjny", section="1"),
        "prior_notice": fs.get("prior_notice", r"^Numer ogłoszenia w BZP", section="3.2.1"),
        "eu": _eu(fs, r"projektu lub programu współfinansowanego", r"^Nazwa projektu lub programu"),
        "mode": fs.get("mode", r"^Tryb udzielenia"),
        "title": fs.get("title", r"^Nazwa zamówienia"),
        "description": fs.get("description", r"^Krótki opis przedmiotu", section="3"),
        "cpv_main": (_cpvs(fs.get("cpv_main", r"^Główny kod CPV")) or [None])[0],
        "cpv_extra": _cpvs(fs.get("cpv_extra", r"^Dodatkowy kod CPV")),
    }
    _contract_block(fs, d)
    d["lot_no"] = _lot_from_headings(fs, d.get("title"))
    d.update(
        performed=yes_no(fs.get("performed", r"^Czy umowa została wykonana$", section="5")),
        end_date=date(fs.get("end_date", r"^Termin wykonania umowy", section="5")),
        on_time=yes_no(fs.get("on_time", r"pierwotnie określonym terminie", section="5")),
        n_changes=integer(fs.get("n_changes", r"^Liczba zmian", section="5")),
        paid=amount(fs.get("paid", r"^Łączna wartość wynagrodzenia", section="5")),
        proper=yes_no(fs.get("proper", r"wykonana należycie", section="5")),
    )
    # one change block per "Numer zmiany"
    starts = fs.all(r"^Numer zmiany", section="5.4")
    changes = []
    for k, s in enumerate(starts):
        stop = starts[k + 1] if k + 1 < len(starts) else len(fs.f)
        pre = f"changes.{k}"
        no = integer(fs.get(f"{pre}.change_no", r"^Numer zmiany", start=s, stop=stop)) or (k + 1)
        basis = fs.get(f"{pre}.legal_basis", r"^Podstawa prawna zmiany", start=s, stop=stop)
        reason = fs.get(f"{pre}.reason", r"^Przyczyny dokonania zmian", start=s, stop=stop)
        desc = fs.get(f"{pre}.description", r"^Krótki opis", start=s, stop=stop)
        value = amount(fs.get(f"{pre}.value", r"^Wartość zmiany", start=s, stop=stop))
        price_up = yes_no(fs.get(f"{pre}.price_up", r"^Wzrost ceny", start=s, stop=stop))
        changes.append({"change_no": no, "legal_basis": basis, "legal_basis_code": legal_basis_code(basis),
                        "reason": reason, "description": desc, "value": value, "price_up": price_up,
                        "currency": fs.get(f"{pre}.currency", r"^Kod waluty", start=s, stop=stop),
                        "new_end": _new_end(desc, reason), "kinds": change_kinds(basis, reason, desc, value, price_up)})
    d["changes"] = changes
    return d


PARSERS = {
    "ContractNotice": parse_contract_notice,
    "TenderResultNotice": parse_tender_result,
    "AgreementUpdateNotice": parse_agreement_update,
    "ContractPerformingNotice": parse_contract_performing,
}


def parse_notice(rec: dict[str, Any]) -> tuple[ParsedDom, dict[str, Any], list[dict[str, Any]]]:
    """API record → (dom, parsed, xrefs). `parsed["refs"]` maps value paths to field indexes."""
    dom = parse_dom(rec.get("htmlBody"))
    fs = Fields(dom)
    fn = PARSERS.get(rec.get("noticeType") or "")
    parsed = fn(fs) if fn else {}
    parsed["type"] = rec.get("noticeType")
    parsed["refs"] = fs.refs
    return dom, parsed, xrefs(fs, rec.get("noticeNumber"))
