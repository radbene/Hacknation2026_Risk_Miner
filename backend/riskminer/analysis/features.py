"""Feature extraction from a new-investment description (path B, step 1).

Rules first (regex + knowledge `subsector_rules`), optionally refined by `llm.complete("features", …)`.
Every value carries its source (regex | llm | user …) and a verbatim quote from the input text. An LLM value
whose quote is not found in the text is dropped (rules value kept). Net/gross is never guessed: if the text
does not say, `vat_basis = unknown` and the user is asked.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from riskminer.analysis.knowledge import rows as krows
from riskminer.llm import complete, strip_personal_data, wrap_untrusted
from riskminer.schemas.analysis import FeatureExtractOut, Features, FeatureValue

VOIVODESHIPS = ["dolnośląskie", "kujawsko-pomorskie", "lubelskie", "lubuskie", "łódzkie", "małopolskie",
                "mazowieckie", "opolskie", "podkarpackie", "podlaskie", "pomorskie", "śląskie",
                "świętokrzyskie", "warmińsko-mazurskie", "wielkopolskie", "zachodniopomorskie"]
# TERYT 2-digit code → name; BZP organizationProvince "PL02" uses the same code
TERYT_VOIV = {f"{i:02d}": v for i, v in zip(range(2, 33, 2), VOIVODESHIPS, strict=True)}
_VOIV_STEM = {v: v[:-3] for v in VOIVODESHIPS}  # "dolnośląsk" matches -ie/-iego/-im

WORK_TYPES = [("przebudow", "przebudowa"), ("rozbudow", "rozbudowa"), ("modernizacj", "modernizacja"),
              ("budow", "budowa"), ("remont", "remont"), ("renowacj", "renowacja")]
FUNDING = [(r"\bKPO\b|Krajow\w+ Plan\w* Odbudowy", "KPO"), (r"FEnIKS|Fundusze Europejskie na Infrastruktur", "FEnIKS"),
           (r"\bPROW\b|Program\w* Rozwoju Obszarów Wiejskich|EFRROW", "PROW"),
           (r"\bRPO\b|Regionaln\w+ Program\w* Operacyjn", "RPO"), (r"\bFE[A-Z]{2,4}\b", "FE regionalny"),
           (r"WFOŚiGW|Wojewódzki\w* Fundusz\w* Ochrony", "WFOŚiGW"), (r"NFOŚiGW|Narodow\w+ Fundusz\w* Ochrony", "NFOŚiGW"),
           (r"Polsk\w+ Ład|Rządow\w+ Program\w* Inwestycji Strategicznych", "Polski Ład"),
           (r"\bRFIL\b|Rządow\w+ Fundusz\w* Inwestycji Lokalnych", "RFIL"), (r"POIiŚ|POIŚ", "POIiŚ"),
           (r"środk\w+ własn\w+|budżet\w* gminy", "środki własne"), (r"kredyt|pożyczk", "kredyt/pożyczka")]
CUES = {
    "land": r"właścicie\w*|własnoś\w+ prywatn\w*|służebnoś\w*|dział\w+ prywatn\w*|zgód\w*|zgody|wywłaszcz\w*|prawo do dysponowania|prawa do nieruchomoś\w*",
    "permits": r"pozwoleni\w* (?:na budowę|wodnoprawn\w*)|warunk\w* techniczn\w*|decyzj\w*|uzgodnie\w*|ZRID|zgłoszeni\w* robót|operat\w* wodnoprawn\w*",
    "environment": r"Natura 2000|środowiskow\w*|ochron\w+ przyrody|obszar\w* chronion\w*|zalewow\w*|teren\w* zalewow\w*|wód gruntow\w*|wody gruntow\w*|wysoki poziom wód",
    "operator": r"operator\w*|przedsiębiorstw\w+ wodociąg\w*|zakład\w* komunaln\w*|\bPWiK\b|\bZGK\b|\bMPGK\b|\bGZK\b|eksploatac\w*",
    "collisions": r"kolizj\w*|koliduje|gazociąg\w*|melioracyj\w*|przekroczeni\w+ (?:drogi|rzeki|cieku|torów)|przewiert\w*",
    "existing_asset": r"czynn\w+ obiekc\w*|istniejąc\w+ (?:sieci|oczyszczalni|stacji|system\w*)|bez przerw\w* w pracy|przy czynnej",
    "pfu": r"program\w* funkcjonalno-użytkow\w*|\bPFU\b",
    "design_ready": r"projekt\w* budowlan\w*|dokumentacj\w+ projektow\w*|pozwoleni\w+ na budowę z",
    "lump_sum": r"ryczałt\w*",
    "startup": r"rozruch\w*|prób\w* (?:parametrów|technologiczn\w*)|odbi[oó]r\w* końcow\w*",
}
CUE_LABELS = {"land": "grunty / prawa do nieruchomości", "permits": "decyzje i uzgodnienia",
              "environment": "środowisko / warunki gruntowo-wodne", "operator": "operator / eksploatacja",
              "collisions": "kolizje z infrastrukturą", "existing_asset": "roboty przy czynnym obiekcie",
              "pfu": "PFU (zaprojektuj i wybuduj)", "design_ready": "gotowa dokumentacja projektowa",
              "lump_sum": "wynagrodzenie ryczałtowe", "startup": "rozruch / próby / odbiór"}
KEY_FIELDS = ["subsector_main", "work_type", "formula", "value", "vat_basis", "duration_months", "voivodeship"]
SIZE_FIELDS = ["length_km", "rlm", "capacity_m3d"]

_NUM = r"\d{1,3}(?:[  .]\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?"


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").replace("\xa0", " ").replace("³", "3")
    return re.sub(r"\s+", " ", s).strip()


def to_float(s: str) -> float | None:
    s = s.strip()
    if re.fullmatch(r"\d{1,3}(?:[  .]\d{3})+(?:,\d+)?", s):
        s = re.sub(r"[  .]", "", s)
    s = s.replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _sentence(text: str, start: int, end: int, pad: int = 90) -> str:
    a = max(text.rfind(".", 0, start) + 1, start - pad, 0)
    b_dot = text.find(".", end)
    b = min(b_dot + 1 if b_dot >= 0 else len(text), end + pad, len(text))
    return text[a:b].strip()


def _fv(value: Any, quote: str | None, unit: str | None = None, conf: float = 0.7, source: str = "regex") -> FeatureValue:
    return FeatureValue(value=value, unit=unit, source=source, quote=quote, confidence=conf)


# ---------------------------------------------------------------- individual rules


def find_length_km(text: str) -> FeatureValue | None:
    """Total network length in km. 'o łącznej długości X km' wins; else sum of distinct km mentions;
    else sum of metre lengths following 'długości'."""
    m = re.search(rf"łączn\w+ długoś\w+\s*(?:ok\.|około)?\s*({_NUM})\s*(km|kilometr\w*|mb|m)\b", text, re.I)
    if m:
        v = to_float(m.group(1))
        if v is not None:
            km = v if m.group(2).lower().startswith("k") else v / 1000
            return _fv(round(km, 3), m.group(0), "km", 0.9)
    kms = [x for x in re.finditer(rf"(?<![\d,.])({_NUM})\s*(km|kilometr\w*)\b", text, re.I)
           if not re.search(r"odległoś\w*|oddalon\w*|od granicy|od obszaru", text[max(0, x.start() - 40):x.start()], re.I)]
    if kms:
        vals = [to_float(x.group(1)) for x in kms]
        vals = [v for v in vals if v is not None and 0 < v < 500]
        if vals:
            quote = " … ".join(x.group(0) for x in kms[:4])
            return _fv(round(sum(vals), 3), quote, "km", 0.8 if len(vals) == 1 else 0.6)
    ms = list(re.finditer(rf"długoś\w+\s*(?:ok\.|około)?\s*({_NUM})\s*(?:mb|m)\b(?!\s*[3²³/])", text, re.I))
    if ms:
        vals = [to_float(x.group(1)) for x in ms]
        vals = [v for v in vals if v]
        if vals:
            return _fv(round(sum(vals) / 1000, 3), " … ".join(x.group(0) for x in ms[:4]), "km", 0.6)
    return None


def find_count(text: str, word: str, cap: int = 100000) -> FeatureValue | None:
    m = re.search(rf"(?<![\d,.])(\d[\d ]{{0,6}})\s+(?:szt\.?\s+)?(?:\w+\s+)?({word})", text, re.I)
    if m:
        v = to_float(m.group(1))
        if v is not None and 0 < v < cap:
            return _fv(int(v), m.group(0).strip(), "szt.", 0.8)
    return None


def find_pumps(text: str) -> FeatureValue | None:
    fv = find_count(text, r"(?:prze)?pompown\w*|tłoczni\w*", cap=200)
    if fv:
        return fv
    m = re.search(r"\b(?:prze)?pompown\w*\b", text, re.I)
    if m:
        return _fv(1, _sentence(text, m.start(), m.end()), "szt.", 0.4)
    return None


def find_rlm(text: str) -> FeatureValue | None:
    ms = list(re.finditer(rf"({_NUM})\s*(?:RLM|równoważn\w+ liczb\w+ mieszkańców)", text))
    if not ms:
        return None
    vals = [(to_float(x.group(1)), x) for x in ms]
    vals = [(v, x) for v, x in vals if v and v > 1]
    if not vals:
        return None
    v, x = max(vals, key=lambda t: t[0])
    return _fv(int(v), x.group(0), "RLM", 0.85)


def find_capacity(text: str) -> FeatureValue | None:
    ms = list(re.finditer(rf"({_NUM})\s*m3\s*/\s*(?:d|dobę|dob\w*)\b", text))
    vals = [(to_float(x.group(1)), x) for x in ms]
    vals = [(v, x) for v, x in vals if v]
    if not vals:
        return None
    v, x = max(vals, key=lambda t: t[0])
    return _fv(v, x.group(0), "m3/d", 0.8)


_MONEY = re.compile(rf"({_NUM})\s*(mln|mld|tys\.?)?\s*(zł|złotych|PLN)", re.I)
_VALUE_CTX = re.compile(r"wartoś\w*|budżet\w*|koszt\w*|szacun\w*|kwot\w*|nakład\w*|przeznacz\w*", re.I)
_NOT_VALUE_CTX = re.compile(r"dofinansowan\w*|dotacj\w*|grant\w*|wkład własny", re.I)


def find_value(text: str) -> tuple[FeatureValue | None, FeatureValue]:
    """(value, vat_basis). VAT basis from 'netto'/'brutto'/'bez VAT'/'z VAT' next to the amount, else unknown."""
    best: tuple[int, float, re.Match] | None = None
    for m in _MONEY.finditer(text):
        v = to_float(m.group(1))
        if v is None:
            continue
        mult = {"mln": 1e6, "mld": 1e9, "tys": 1e3, "tys.": 1e3}.get((m.group(2) or "").lower(), 1)
        v *= mult
        before = text[max(0, m.start() - 70):m.start()]
        score = (2 if _VALUE_CTX.search(before) else 0) - (3 if _NOT_VALUE_CTX.search(before[-40:]) else 0)
        if v < 10000:
            score -= 5
        if best is None or score > best[0]:
            best = (score, v, m)
    if best is None or best[0] < -2:
        return None, _fv("unknown", None, conf=1.0, source="default")
    _, v, m = best
    around = text[max(0, m.start() - 60):min(len(text), m.end() + 40)]
    quote = _sentence(text, m.start(), m.end(), pad=60)
    if re.search(r"\bnetto\b|bez (?:podatku )?VAT", around, re.I):
        vat = _fv("net", around.strip(), conf=0.9)
    elif re.search(r"\bbrutto\b|z (?:podatkiem )?VAT|wraz z (?:podatkiem )?VAT", around, re.I):
        vat = _fv("gross", around.strip(), conf=0.9)
    else:
        vat = _fv("unknown", None, conf=1.0, source="default")
    return _fv(round(v, 2), quote, "PLN", 0.8), vat


def find_duration(text: str) -> FeatureValue | None:
    m = re.search(r"(\d{1,3})\s*(miesięc\w*|miesiąc\w*|mies\.)", text, re.I)
    if m:
        return _fv(int(m.group(1)), _sentence(text, m.start(), m.end(), 50), "mies.", 0.8)
    m = re.search(r"(\d{2,4})\s*dni", text, re.I)
    if m and re.search(r"termin|realizac|okres|czas", text[max(0, m.start() - 60):m.start()], re.I):
        return _fv(round(int(m.group(1)) / 30, 1), _sentence(text, m.start(), m.end(), 50), "mies.", 0.7)
    m = re.search(r"(\d{1,2})\s*(?:lat|lata)\b", text)
    if m and re.search(r"termin|realizac|okres|czas", text[max(0, m.start() - 60):m.start()], re.I):
        return _fv(int(m.group(1)) * 12, _sentence(text, m.start(), m.end(), 50), "mies.", 0.6)
    return None


_ROMAN = {"I": 1, "II": 4, "III": 7, "IV": 10}


def find_start(text: str) -> FeatureValue | None:
    m = re.search(r"\b(IV|III|II|I)\s*kw(?:artał|\.)\w*\s*(20\d{2})", text)
    if m:
        return _fv(f"{m.group(2)}-{_ROMAN[m.group(1)]:02d}-01", m.group(0), None, 0.7)
    m = re.search(r"(?:rozpocz\w*|start\w*)[^.]{0,40}?(20\d{2})", text, re.I)
    if m:
        return _fv(f"{m.group(1)}-01-01", m.group(0), None, 0.5)
    return None


def find_work_type(text: str) -> FeatureValue | None:
    low = text.lower()
    hits = [(low.find(stem), label) for stem, label in WORK_TYPES if stem in low]
    if not hits:
        return None
    # "przebudow" contains "budow" – earliest *specific* stem wins
    pos, label = min(hits, key=lambda t: (t[0], t[1] == "budowa"))
    if label == "budowa":
        for stem, lab in WORK_TYPES[:3]:
            if low.find(stem) >= 0 and low.find(stem) <= pos:
                pos, label = low.find(stem), lab
    return _fv(label, _sentence(text, pos, pos + 10, 40), None, 0.7)


def find_formula(text: str) -> FeatureValue | None:
    m = re.search(r"zaprojektuj i wybuduj|zaprojektuj-wybuduj|zaprojektowani\w+ i (?:wy)?budow\w+|program\w* funkcjonalno-użytkow\w*|\bPFU\b|design\s*&?\s*build", text, re.I)
    if m:
        return _fv("zaprojektuj i wybuduj", _sentence(text, m.start(), m.end(), 50), None, 0.85)
    m = re.search(r"tradycyjn\w*|wybuduj\b|na podstawie (?:gotowej )?dokumentacji projektowej|wg dokumentacji projektowej", text, re.I)
    if m:
        return _fv("tradycyjna", _sentence(text, m.start(), m.end(), 50), None, 0.7)
    return None


def find_subsectors(text: str, session: Session | None = None) -> tuple[FeatureValue | None, FeatureValue | None]:
    low = text.lower()
    scores: list[tuple[int, int, str, str]] = []
    for r in krows("subsector_rules", session):
        best_pos, n, q = None, 0, None
        for kw in r.get("keywords") or []:
            k = kw.lower()
            if len(k) <= 4:  # short acronyms (SUW) as whole words, case-sensitive
                found = [m.start() for m in re.finditer(rf"\b{re.escape(kw)}\b", text)]
            else:
                found = [m.start() for m in re.finditer(re.escape(k), low)]
            if found:
                n += len(found)
                if best_pos is None or found[0] < best_pos:
                    best_pos, q = found[0], text[found[0]:found[0] + len(kw)]
        if n:
            scores.append((n, -best_pos, r["subsector"], q))
    if not scores:
        return None, None
    scores.sort(reverse=True)
    n, negpos, main, q = scores[0]
    main_fv = _fv(main, _sentence(text, -negpos, -negpos + len(q or ""), 60), None, min(0.95, 0.6 + 0.1 * n))
    extra = [s[2] for s in scores[1:]]
    extra_fv = _fv(extra, " … ".join(s[3] for s in scores[1:] if s[3]), None, 0.6) if extra else None
    return main_fv, extra_fv


def find_voivodeship(text: str) -> FeatureValue | None:
    low = text.lower()
    hits = []
    for v, stem in _VOIV_STEM.items():
        for m in re.finditer(rf"(?<![\w-]){re.escape(stem)}\w*", low):
            hits.append((m.start(), m.end(), v))
    if not hits:
        return None
    # "pomorskie" must not win inside "kujawsko-pomorskie"/"zachodniopomorskie" (handled by lookbehind) – keep longest
    a, b, v = min(hits, key=lambda h: (h[0], -(h[1] - h[0])))
    return _fv(v, text[max(0, a - 6):b].strip(), None, 0.9)


def find_location(text: str) -> FeatureValue | None:
    m = re.search(r"\b(?:[Gg]min\w+|[Mm]iejscowoś\w+|w m\.|m\.)\s+([A-ZŁŚŻŹĆ][\wąćęłńóśźż-]+(?:\s+[A-ZŁŚŻŹĆ][\wąćęłńóśźż-]+)?)", text)
    if m:
        return _fv(m.group(1), m.group(0), None, 0.6)
    return None


def find_funding(text: str) -> FeatureValue | None:
    found, quotes = [], []
    for pat, label in FUNDING:
        m = re.search(pat, text)
        if m and label not in found:
            found.append(label)
            quotes.append(m.group(0))
    if not found:
        return None
    return _fv(", ".join(found), " … ".join(quotes), None, 0.8)


def find_cues(text: str) -> dict[str, FeatureValue]:
    out: dict[str, FeatureValue] = {}
    for key, pat in CUES.items():
        ms = list(re.finditer(pat, text, re.I))
        if ms:
            m = ms[0]
            out[key] = FeatureValue(value=CUE_LABELS[key], source="regex", quote=_sentence(text, m.start(), m.end(), 80),
                                    confidence=0.6, unit=None)
    # explicit negatives that matter for flags ("brak zgód", "nie wydał", "w przygotowaniu")
    for m in re.finditer(r"(brak\w*|nie wydał\w*|nie uzyskan\w*|w przygotowaniu|do ustalenia|w ocenie|nie posiada\w*)", text, re.I):
        sent = _sentence(text, m.start(), m.end(), 80)
        out.setdefault(f"gap_{len([k for k in out if k.startswith('gap_')]) + 1}",
                       FeatureValue(value="sygnał braku / niepewności", source="regex", quote=sent, confidence=0.6))
    return out


# ---------------------------------------------------------------- orchestration


def extract_rules(text: str, session: Session | None = None) -> Features:
    t = norm(text)
    main, extra = find_subsectors(t, session)
    value, vat = find_value(t)
    return Features(
        subsector_main=main, subsector_extra=extra, work_type=find_work_type(t), formula=find_formula(t),
        length_km=find_length_km(t), connections=find_count(t, r"przyłącz\w*|przykanalik\w*|sięgacz\w*"),
        pump_stations=find_pumps(t), rlm=find_rlm(t), capacity_m3d=find_capacity(t), value=value, vat_basis=vat,
        duration_months=find_duration(t), start_date=find_start(t), voivodeship=find_voivodeship(t),
        location=find_location(t), funding=find_funding(t), cues=find_cues(t),
    )


class _LLMField(BaseModel):
    value: str | float | int | bool | list[str] | None = None
    quote: str | None = Field(None, description="dosłowny cytat z opisu potwierdzający wartość")


class LLMFeatures(BaseModel):
    """Schema for complete('features'). Every value needs a verbatim quote from the description."""

    subsector_main: _LLMField | None = None
    subsector_extra: _LLMField | None = None
    work_type: _LLMField | None = None
    formula: _LLMField | None = None
    length_km: _LLMField | None = None
    connections: _LLMField | None = None
    pump_stations: _LLMField | None = None
    rlm: _LLMField | None = None
    capacity_m3d: _LLMField | None = None
    value: _LLMField | None = None
    vat_basis: _LLMField | None = None
    duration_months: _LLMField | None = None
    voivodeship: _LLMField | None = None
    location: _LLMField | None = None
    funding: _LLMField | None = None
    cues: dict[str, _LLMField] = Field(default_factory=dict)


SYSTEM = (
    "Jesteś analitykiem inwestycji wodno-kanalizacyjnych. Z opisu nowej inwestycji wyodrębnij cechy według schematu "
    "JSON. Dla każdej wartości podaj dosłowny cytat (quote) z opisu. Nie zgaduj: gdy opis nie mówi, czy kwota jest "
    "netto czy brutto, ustaw vat_basis=unknown. Podsektor wybierz z listy: {subsectors}. work_type: budowa | "
    "przebudowa | rozbudowa | modernizacja. formula: tradycyjna | zaprojektuj i wybuduj. length_km w km, "
    "duration_months w miesiącach, value w PLN. cues: land, permits, environment, operator, collisions."
)


def quote_ok(quote: str | None, text: str) -> bool:
    if not quote:
        return False
    nq, nt = norm(quote).lower().strip(" .…\"'„”"), norm(text).lower()
    parts = [p.strip() for p in re.split(r"…|\.\.\.", nq) if p.strip()]
    return bool(parts) and all(p in nt for p in parts)


def _num_or_none(v: Any) -> float | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, int | float):
        return float(v)
    if isinstance(v, str):
        return to_float(re.sub(r"[^\d,. ]", "", v)) if re.search(r"\d", v) else None
    return None


NUMERIC = {"length_km", "connections", "pump_stations", "rlm", "capacity_m3d", "value", "duration_months"}


def merge_llm(rules: Features, llm: LLMFeatures, text: str, model_label: str) -> tuple[Features, list[str]]:
    """LLM values replace rule values only when their quote is verbatim in the text. Returns (features, notes)."""
    f = rules.model_copy(deep=True)
    notes: list[str] = []
    for name in LLMFeatures.model_fields:
        if name == "cues":
            for k, lf in (llm.cues or {}).items():
                if lf and lf.value not in (None, "", False) and quote_ok(lf.quote, text) and k not in f.cues:
                    f.cues[k] = FeatureValue(value=lf.value, source="llm", quote=lf.quote, confidence=0.6)
            continue
        lf: _LLMField | None = getattr(llm, name)
        if lf is None or lf.value in (None, "", []):
            continue
        if not quote_ok(lf.quote, text):
            notes.append(f"{name}: cytat modelu nie występuje w opisie – pominięto")
            continue
        val: Any = lf.value
        if name in NUMERIC:
            val = _num_or_none(val)
            if val is None:
                continue
        if name == "vat_basis" and val not in ("net", "gross"):
            continue
        cur = getattr(f, name)
        if cur is None or cur.source in ("default",) or (cur.confidence or 0) < 0.7:
            setattr(f, name, FeatureValue(value=val, source="llm", quote=lf.quote, confidence=0.75,
                                          unit=cur.unit if cur else None))
        elif cur.value != val:
            f.extra[f"llm_{name}"] = FeatureValue(value=val, source="llm", quote=lf.quote, confidence=0.6)
            notes.append(f"{name}: model proponuje {val!r}, reguły {cur.value!r} – zostawiono reguły")
    f.extra["_model_label"] = FeatureValue(value=model_label, source="llm")
    return f, notes


def missing_and_questions(f: Features) -> tuple[list[str], list[str]]:
    missing = [k for k in KEY_FIELDS if getattr(f, k) is None or getattr(f, k).value in (None, "unknown")]
    if not any(getattr(f, k) is not None for k in SIZE_FIELDS):
        missing.append("length_km|rlm|capacity_m3d")
    q: list[str] = []
    if f.value is not None and (f.vat_basis is None or f.vat_basis.value == "unknown"):
        q.append(f"Czy kwota {f.value.value:,.0f} zł to wartość netto (bez VAT) czy brutto (z VAT)?".replace(",", " "))
    if f.value is None:
        q.append("Jaka jest szacunkowa wartość inwestycji (zł) i czy jest to kwota netto czy brutto?")
    if f.duration_months is None:
        q.append("Jaki jest planowany czas realizacji (w miesiącach)?")
    if f.formula is None:
        q.append("Jaka formuła realizacji: tradycyjna (wg dokumentacji projektowej) czy „zaprojektuj i wybuduj”?")
    if f.subsector_main is None:
        q.append("Którego podsektora dotyczy inwestycja (sieć wodociągowa, kanalizacja sanitarna, oczyszczalnia, SUW …)?")
    if "length_km|rlm|capacity_m3d" in missing:
        q.append("Podaj skalę: długość sieci (km), RLM albo przepustowość (m3/d).")
    if f.voivodeship is None:
        q.append("W jakim województwie jest inwestycja?")
    return missing, q


def extract_features(text: str, session: Session | None = None, use_llm: bool = True) -> FeatureExtractOut:
    rules = extract_rules(text, session)
    model_label = None
    if use_llm and text and text.strip():
        subs = ", ".join(r["subsector"] for r in krows("subsector_rules", session))
        res = complete("features", [{"role": "user", "content": "Opis inwestycji:\n" + wrap_untrusted(
            strip_personal_data(text[:12000]), "opis nowej inwestycji")}], LLMFeatures,
            system=SYSTEM.format(subsectors=subs), prompt_version="features-v1")
        if res.data is not None:
            model_label = res.label
            rules, notes = merge_llm(rules, res.data, norm(text), res.label)
            for i, n in enumerate(notes):
                rules.extra[f"_note_{i}"] = FeatureValue(value=n, source="llm")
    missing, questions = missing_and_questions(rules)
    return FeatureExtractOut(features=rules, missing=missing, questions=questions, model_label=model_label)


def feature_value(f: Features | dict, name: str) -> Any:
    """Plain value of a feature (works for the Features model and its JSON dict)."""
    if isinstance(f, dict):
        v = f.get(name)
        return v.get("value") if isinstance(v, dict) else v
    v = getattr(f, name, None)
    return v.value if v is not None else None
