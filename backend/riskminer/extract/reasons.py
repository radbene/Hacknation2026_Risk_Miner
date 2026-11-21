"""Rule pre-labeler: change / delay reasons (verbatim BZP text) → expert R-codes (R01–R15) or proposed P-codes.

Adapted from prep `classify_reasons.py` (12-label keyword taxonomy) to the wod-kan catalog. Two pattern sets:
- REASON_PATTERNS: curated regexes for change reasons (tuned on the prep gold set relabelled to R-codes);
- knowledge `risk_signals` (extra/risk_signals.yaml, expert-editable): stems used for document fragments.
Every hit keeps the matched span so the quote is a verbatim piece of the source.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from riskminer.extract.common import knowledge_rows

# code → regex (case-insensitive). Order = priority when a single code is needed.
REASON_PATTERNS: dict[str, str] = {
    "R03": r"służebnoś|kolizj\w*|dostęp\w* do (?:terenu|działk|nieruchomoś)|wej[śs]ci\w* na teren|przekazani\w+ (?:terenu|placu|frontu)"
           r"|właściciel\w* (?:terenu|działk|nieruchomoś)|prawa? do dysponowania|wywłaszcz|zgod\w* właściciel",
    "R02": r"warunk\w+ (?:grunt|geolog|hydrolog|hydrogeolog|wodn)|wód gruntow|wody gruntow|zastoisk|niezinwentaryz|nieinwentaryz"
           r"|niezidentyfikowan|odkryt\w* (?:podczas|w trakcie)|ujawnion\w* (?:w trakcie|podczas)? ?\w* ?(?:uszkodz|instalacj|rur|sieci)"
           r"|zł\w+ stan\w* techniczn|degradacj|kurzawk|grunt\w* nienośn|archeolog|niewybuch|stan\w* istniejąc",
    "R04": r"pozwoleni\w*|decyzj\w+ (?:o |pozw|admin|środow|wodnopraw|zrid)|uzgodnie\w*|warunk\w+ techniczn\w+ przyłącz|operat\w* wodnopraw"
           r"|zezwoleni|ZRID|gestor|zarządc\w+ (?:drogi|sieci|terenu)|konserwator|procedur\w+ administr|zgłoszeni\w+ (?:robót|na wykonanie)",
    "R06": r"atmosferyczn|pogod|opad\w*|mroz|mróz|zimow|temperatur|termin\w* nierealn|zależnoś"
           r"|prace rozpoczęł|inn\w+ (?:wykonawc|podmiot)\w* (?:na terenie|prowadz)|na terenie budowy swoje prace",
    "R07": r"rob[oó]t\w* (?:budowlan\w+ )?(?:dodatk|zamienn|niewykonan)|dodatkow\w+ (?:rob|prac|instalacj|zakres|zjazd|element)"
           r"|nieprzewidzian|niemożliw\w+ do przewidzenia|nie (?:mógł|można było|dało się) przewidzieć|wstrzyman|protok\w+ konieczności"
           r"|konieczno\w+ wykonania (?:dodatk|zabezpiecz|cięcia|wymiany)|zaistniała konieczność wykonania",
    "R01": r"zwiększeni\w+ zakresu|rozszerzeni\w+ zakresu|ograniczeni\w+ zakresu|dostosowania zak|pominięt|nieujęt|nie obejmował\w* dokumentacj"
           r"|błęd\w+ (?:w )?(?:dokumentacj|projekt)|brak\w* w dokumentacj|przedmiar|niespójn|rozbieżnoś|korekt\w+ niwelety"
           r"|dodatkow\w+ długoś|zakres\w* (?:prac|robót) (?:o|zwiększ)",
    "R08": r"ryczałt|kosztorys\w* powykonawcz|wynagrodzeni\w+ kosztorysow|obmiar\w*|rozliczeni\w+ powykonawcz|waloryzac|zmian\w+ cen"
           r"|inflacj|wzrost\w* cen|nośnik\w* cenotwórcz",
    "R09": r"inn\w+ rozwiązań techn|rozwiąza\w+ zamienn|zmian\w+ technologi|parametr\w* techniczn|wymaga\w+ techniczn|równoważn"
           r"|niejednoznaczn|STWiORB",
    "R10": r"rozruch|odbior\w* końcow|odbiór końcow|prób\w* (?:szczelnoś|technolog)|parametr\w* technologiczn",
    "R11": r"odwołani\w+ (?:do KIO|wykonawc)|\bKIO\b|jedn\w+ ofert|ograniczeni\w+ konkurencji",
    "R12": r"dostaw\w* (?:materiał|urządze)|termin\w* dostaw|producent|łańcuch\w* dostaw|brak\w* materiał|upadłoś|likwidacj"
           r"|z winy wykonawc|zwłok\w* wykonawc|kierownik\w* (?:budowy|robót)|zmian\w+ osoby|personel\w* kluczow|podwykonaw|zmian\w+ wykonawc",
    "R13": r"dofinansowan|dotacj|kwalifikowalno|środk\w+ finansow|budżet\w*|finansowa\w* (?:projektu|zadania|zamówienia)|płatnoś"
           r"|przekracza\w* kwot|art\.\s*255 pkt 3",
    "R14": r"eksploatacj|koszt\w* utrzymania|energochłonn",
    "R15": r"efekt\w* ekologiczn|\bRLM\b|wskaźnik\w* (?:rezultatu|produktu)|jakoś\w+ wody|parametr\w* ścieków",
    # proposed categories (open catalog, need expert approval)
    "P-PRAWO": r"wejści\w+ w życie przepis|zmian\w+ (?:stawki|przepis)|KSeF|stawk\w+ VAT|e-Faktur",
    "P-FORMAL": r"omyłk\w+ pisarsk|oczywist\w+ omyłk|numer\w* rachunku|zmian\w+ (?:nazwy|adresu|siedziby)",
}

PROPOSED = {
    "P-PRAWO": ("Zmiana przepisów prawa w trakcie realizacji", "Zmiany wymuszone nowymi przepisami (VAT, KSeF, normy)."),
    "P-FORMAL": ("Zmiany formalne i redakcyjne umowy", "Omyłki, dane stron, rachunki – bez wpływu na termin i koszt."),
}

_RX = {k: re.compile(v, re.I) for k, v in REASON_PATTERNS.items()}


@dataclass
class Hit:
    code: str
    pattern: str
    match: str
    start: int
    end: int


def classify_reason(text: str | None) -> list[Hit]:
    """All R/P-code hits in a change reason (first match per code), ordered by position."""
    hits: list[Hit] = []
    for code, rx in _RX.items():
        m = rx.search(text or "")
        if m:
            hits.append(Hit(code, rx.pattern[:60], m.group(0), m.start(), m.end()))
    return sorted(hits, key=lambda h: h.start)


def reason_codes(text: str | None) -> list[str]:
    return [h.code for h in classify_reason(text)]


def signal_patterns(session: Session | None = None) -> dict[str, list[str]]:
    """Expert-editable stems from knowledge `risk_signals` (DB version first)."""
    return {r["code"]: list(r.get("patterns") or []) for r in knowledge_rows("risk_signals", session)}


def classify_signals(text: str | None, session: Session | None = None) -> list[Hit]:
    """Document fragments: curated regexes + expert stems (risk_signals.yaml); both keep spans."""
    hits = {h.code: h for h in classify_reason(text)}
    low = (text or "").lower()
    for code, pats in signal_patterns(session).items():
        if code in hits:
            continue
        for p in pats:
            i = low.find(p.lower())
            if i >= 0 and len(p) >= 5:
                hits[code] = Hit(code, p, (text or "")[i:i + len(p)], i, i + len(p))
                break
    return sorted(hits.values(), key=lambda h: h.start)


def sentence_around(text: str, start: int, end: int, max_len: int = 400) -> str:
    """The sentence containing [start, end) – a verbatim slice of `text`."""
    a = max(text.rfind(". ", 0, start), text.rfind("\n", 0, start))
    a = 0 if a < 0 else a + 1
    b_candidates = [i for i in (text.find(". ", end), text.find("\n", end)) if i >= 0]
    b = min(b_candidates) + 1 if b_candidates else len(text)
    s = text[a:b].strip()
    if len(s) > max_len:
        mid = start - a
        lo = max(0, mid - max_len // 2)
        s = s[lo:lo + max_len].strip()
    return s


def evaluate(rows: list[dict]) -> dict:
    """Set precision/recall/F1 + exact match against labelled rows {text, labels}."""
    tp = fp = fn = exact = 0
    for r in rows:
        gold, pred = set(r["labels"]), set(reason_codes(r["text"]))
        tp += len(gold & pred)
        fp += len(pred - gold)
        fn += len(gold - pred)
        exact += gold == pred
    p = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    n = len(rows)
    return {"n": n, "precision": round(p, 3), "recall": round(rc, 3),
            "f1": round(2 * p * rc / (p + rc), 3) if p + rc else 0.0, "exact_match": round(exact / n, 3) if n else 0.0}
