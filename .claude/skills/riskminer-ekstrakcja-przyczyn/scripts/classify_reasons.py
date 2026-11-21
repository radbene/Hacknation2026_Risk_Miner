#!/usr/bin/env python3
"""Klasyfikuje przyczyny zmian umow (tekst z BZP) do taksonomii przyczyn: baseline na slowach kluczowych.

  python3 classify_reasons.py --text "Konieczność wykonania robót dodatkowych i zamiennych."
  python3 classify_reasons.py --csv contracts.csv --col change_reasons --out reasons_labeled.csv
  python3 classify_reasons.py --gold change_reasons_gold_26.jsonl        # precision/recall wzgledem zlotego zbioru

To punkt odniesienia dla LLM (prompt: references/prompty.md): jesli LLM nie bije tego baseline'u
na zlotym zbiorze, nie warto placic za LLM. Tylko biblioteka standardowa (pandas dla --csv).
"""
from __future__ import annotations

import argparse
import json
import re
import sys

TAXONOMY = {
    "ZAKRES": ("Roboty dodatkowe, zamienne, zwiekszenie zakresu",
               r"rob[oó]t\w* dodatk|dodatkow\w+ (rob|prac|zakres|instalacj|długoś)|zamienn|zwiększeni\w+ zakresu|rozszerzeni\w+ zakresu|niemożliw\w+ do przewidzenia|dodatkowym zakresem"),
    "PROJEKT": ("Bledy lub braki dokumentacji projektowej, zmiana rozwiazan technicznych",
                r"dokumentacj\w+ projekt|błęd\w+ projekt|nieujęt\w+ w projekcie|inn\w+ rozwiązań techn|rozwiąza\w+ zamienn|korekt\w+ niwelety|zmian\w+ projekt|przeprojektow"),
    "GRUNT_KOLIZJE": ("Warunki gruntowe i wodne, kolizje z sieciami, odkrycia",
                      r"kolizj|niezinwentaryz|warunk\w+ (grunt|hydro|geolog)|wód gruntow|zastoisk|archeolog|niewybuch|fundament"),
    "POGODA": ("Warunki atmosferyczne", r"atmosferyczn|pogod|opad|mroz|mróz|zimow|temperatur"),
    "DECYZJE": ("Pozwolenia, uzgodnienia, decyzje administracyjne, gestorzy sieci",
                r"pozwoleni|decyzj\w+ (o |pozw|admin|środow)|uzgodnie|konserwator|procedur\w+ administr|zgłoszeni\w+ na wykonanie|zarządc\w+ sieci|gestor"),
    "STRONA_TRZECIA": ("Prace lub opoznienia innych podmiotow na terenie budowy",
                       r"prace rozpoczęł|inn\w+ wykonawc|wodociągi|zakład\w* energetyczn|operator\w* sieci|przekazani\w+ (terenu|placu|frontu)"),
    "KADRY": ("Zmiana kierownika budowy lub personelu", r"kierownik\w* budowy|zmian\w+ osoby|personel|inspektor\w* nadzoru"),
    "ROZLICZENIE": ("Rozliczenie obmiarowe, kosztorys powykonawczy, waloryzacja",
                    r"obmiar|kosztorys\w* powykonawcz|rozliczeni\w+ powykonawcz|waloryzac|wynagrodzeni\w+ kosztorysow"),
    "FINANSOWANIE": ("Finansowanie, dotacja, terminy programu", r"dotacj|dofinansowan|kwalifikowalno|środk\w+ finansow|budżet\w* (gminy|miasta|powiatu)"),
    "PRAWO": ("Zmiana przepisow", r"wejści\w+ w życie przepis|zmian\w+ (stawki|przepis)|KSeF|stawk\w+ VAT"),
    "DOSTAWY": ("Dostawy materialow i urzadzen", r"dostaw\w* (materiał|urządze)|termin\w* dostaw|producent|łańcuch\w* dostaw|brak\w* materiał"),
    "WYKONAWCA": ("Przyczyny po stronie wykonawcy", r"zwłok|z winy wykonawc|upadłoś|opóźnieni\w+ wykonawc"),
}
FALLBACK = "NIEOKRESLONA"  # np. sama "koniecznosc zmiany terminu" albo odeslanie do protokolu


def classify(text: str) -> list[str]:
    labels = [k for k, (_, rx) in TAXONOMY.items() if re.search(rx, text or "", flags=re.I)]
    return labels or [FALLBACK]


def evaluate(path: str) -> dict:
    tp = fp = fn = exact = n = 0
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        g = json.loads(line)
        gold, pred = set(g["labels"]), set(classify(g["text"]))
        tp += len(gold & pred); fp += len(pred - gold); fn += len(gold - pred)
        exact += gold == pred; n += 1
    p, r = tp / (tp + fp) if tp + fp else 0, tp / (tp + fn) if tp + fn else 0
    return {"n": n, "precision": round(p, 3), "recall": round(r, 3),
            "f1": round(2 * p * r / (p + r), 3) if p + r else 0, "exact_match": round(exact / n, 3)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--text")
    ap.add_argument("--csv")
    ap.add_argument("--col", default="change_reasons")
    ap.add_argument("--out")
    ap.add_argument("--gold")
    a = ap.parse_args()
    if a.text:
        print(json.dumps({"labels": classify(a.text)}, ensure_ascii=False))
    elif a.gold:
        print(json.dumps(evaluate(a.gold), ensure_ascii=False))
    elif a.csv:
        import pandas as pd
        d = pd.read_csv(a.csv)
        has = d[a.col].notna()
        d.loc[has, "reason_labels"] = d.loc[has, a.col].map(lambda t: "|".join(sorted({l for part in str(t).split(" || ") for l in classify(part)})))
        d.to_csv(a.out or "reasons_labeled.csv", index=False)
        counts = d.loc[has, "reason_labels"].str.split("|").explode().value_counts()
        print(f"Umowy z przyczynami: {int(has.sum())} z {len(d)}"); print(counts.to_string())
    else:
        ap.error("podaj --text, --csv albo --gold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
