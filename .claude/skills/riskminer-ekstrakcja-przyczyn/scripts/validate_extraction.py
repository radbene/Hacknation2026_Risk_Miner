#!/usr/bin/env python3
"""Sprawdza wynik ekstrakcji ryzyk z dokumentu przez LLM: schemat i to, czy kazdy cytat jest w dokumencie.

  python3 validate_extraction.py --doc dokument.txt --llm wynik.json [--out raport.json]

Wynik LLM: {"ryzyka": [{"kategoria", "opis", "cytat", "prawdopodobienstwo", "skutek", "mitygacja"}]}
(schemat: references/schemat-ryzyka.json). Ryzyko z cytatem, ktorego nie ma w dokumencie, jest odrzucane:
to najtansza ochrona przed halucynacja. Kod wyjscia 1, gdy odrzucono cokolwiek. Tylko biblioteka standardowa.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata

CATEGORIES = {"ZAKRES", "PROJEKT", "GRUNT_KOLIZJE", "POGODA", "DECYZJE", "STRONA_TRZECIA", "KADRY",
              "ROZLICZENIE", "FINANSOWANIE", "PRAWO", "DOSTAWY", "WYKONAWCA", "HARMONOGRAM", "INNE"}
LEVELS = {"niskie", "srednie", "wysokie"}
REQUIRED = ("kategoria", "opis", "cytat", "prawdopodobienstwo", "skutek", "mitygacja")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").lower()
    s = s.replace("„", '"').replace("”", '"').replace("–", "-").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


def validate(doc: str, data: dict) -> dict:
    nd = norm(doc)
    ok, rejected = [], []
    items = data.get("ryzyka") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return {"accepted": [], "rejected": [{"reason": "brak listy 'ryzyka'"}], "quote_ok_rate": 0.0}
    for i, r in enumerate(items):
        errs = [f"brak pola {k}" for k in REQUIRED if not (isinstance(r, dict) and str(r.get(k, "")).strip())]
        if not errs:
            if r["kategoria"] not in CATEGORIES:
                errs.append(f"nieznana kategoria {r['kategoria']}")
            for k in ("prawdopodobienstwo", "skutek"):
                if r[k] not in LEVELS:
                    errs.append(f"{k} spoza {sorted(LEVELS)}")
            q = norm(r["cytat"])
            if len(q) < 15:
                errs.append("cytat krotszy niz 15 znakow")
            elif q not in nd:
                errs.append("cytatu nie ma w dokumencie")
        (rejected if errs else ok).append({"index": i, **({"errors": errs} if errs else {}), "ryzyko": r})
    return {"accepted": ok, "rejected": rejected,
            "quote_ok_rate": round(len(ok) / len(items), 3) if items else 0.0}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--doc", required=True)
    ap.add_argument("--llm", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    doc = open(a.doc, encoding="utf-8").read()
    raw = open(a.llm, encoding="utf-8").read()
    m = re.search(r"\{.*\}", raw, flags=re.S)  # model moze dodac tekst wokol JSON
    try:
        data = json.loads(m.group(0) if m else raw)
    except json.JSONDecodeError as e:
        print(f"Wynik LLM nie jest poprawnym JSON: {e}", file=sys.stderr)
        return 2
    rep = validate(doc, data)
    if a.out:
        json.dump(rep, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Przyjete: {len(rep['accepted'])}, odrzucone: {len(rep['rejected'])}, udzial poprawnych: {rep['quote_ok_rate']}")
    for r in rep["rejected"]:
        print(f"  odrzucone #{r.get('index')}: {'; '.join(r.get('errors', [r.get('reason', '')]))}")
    return 1 if rep["rejected"] else 0


if __name__ == "__main__":
    sys.exit(main())
