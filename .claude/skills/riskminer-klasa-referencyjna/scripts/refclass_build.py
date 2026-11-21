#!/usr/bin/env python3
"""Buduje tabele klasy referencyjnej z zakonczonych umow (wyniki rzeczywiste, nie plany).

  python3 refclass_build.py --data dataset.csv --out reference_table.json

Wejscie: CSV z bzp_parse.py/bzp_join.py (kolumny value, period_days, eu_funded, label_late,
paid, done, signed_date, done_date) albo probka z data-samples (value, period_days, eu, late, paid, done).
Wyjscie: JSON z komorkami wartosc x planowany okres: n, odsetek opoznionych, odsetek ze wzrostem
kosztu (wyplata > 101% wartosci umowy), kwantyle wyplata/wartosc. Zaleznosci: pandas, numpy (BSD).
"""
from __future__ import annotations

import argparse
import json
import sys

import numpy as np
import pandas as pd

VALUE_BINS = [0, 200e3, 1e6, 5e6, float("inf")]
VALUE_LABELS = ["1:<200k", "2:200k-1M", "3:1-5M", "4:>=5M"]
PERIOD_BINS = [-1, 60, 120, 240, 480, float("inf")]
PERIOD_LABELS = ["a:<=60d", "b:61-120d", "c:121-240d", "d:241-480d", "e:>480d"]


def value_bucket(v: float) -> str:
    return VALUE_LABELS[int(np.searchsorted(VALUE_BINS, v, side="right")) - 1]


def period_bucket(d: float | None) -> str:
    if d is None or (isinstance(d, float) and np.isnan(d)) or d <= 0:
        return "x:brak"
    return PERIOD_LABELS[int(np.searchsorted(PERIOD_BINS, d, side="left")) - 1]


def normalize(d: pd.DataFrame) -> pd.DataFrame:
    ren = {"label_late": "late", "eu_funded": "eu"}
    d = d.rename(columns={k: v for k, v in ren.items() if k in d.columns and v not in d.columns})
    for c in ("value", "paid", "period_days", "late", "eu", "done"):
        if c not in d.columns:
            raise SystemExit(f"Brak kolumny '{c}'. Kolumny: {list(d.columns)}")
        d[c] = pd.to_numeric(d[c], errors="coerce")
    if "currency" in d.columns:  # tylko PLN (puste pole traktujemy jak PLN)
        d = d[d["currency"].fillna("PLN").astype(str).str.upper().isin(["PLN", "NAN", ""])]
    d = d[d["value"] > 0].copy()
    if "n_changes" in d.columns:
        d["n_changes"] = pd.to_numeric(d["n_changes"], errors="coerce")
    d["vb"] = d["value"].map(value_bucket)
    d["pb"] = d["period_days"].map(period_bucket)
    ok = (d["done"] == 1) & (d["paid"] > 0)
    d["ratio"] = (d["paid"] / d["value"]).where(ok)
    d["cost_up"] = (d["ratio"] > 1.01).astype(float).where(ok)
    return d


def cell(g: pd.DataFrame) -> dict:
    r = g["ratio"].dropna()
    q = (lambda p: round(float(np.quantile(r, p)), 3)) if len(r) else (lambda p: None)
    lt = g["late"].dropna()
    return {
        "n": int(len(g)),
        "late_pct": round(100 * float(lt.mean()), 1) if len(lt) else None,
        "cost_up_pct": round(100 * float(g["cost_up"].mean()), 1) if g["cost_up"].notna().any() else None,
        "changed_pct": round(100 * float((g["n_changes"] > 0).mean()), 1) if "n_changes" in g else None,
        "not_done_pct": round(100 * float((g["done"] == 0).mean()), 1),
        "ratio_p50": q(0.5), "ratio_p80": q(0.8), "ratio_p95": q(0.95),
    }


def build(d: pd.DataFrame, source: str) -> dict:
    d = normalize(d)
    out = {
        "meta": {"source": source, "n": int(len(d)),
                 "definitions": {"late": "zamawiajacy zadeklarowal: umowy nie wykonano w pierwotnie okreslonym terminie",
                                 "cost_up": "laczna wyplata > 101% pierwotnej wartosci umowy (umowy wykonane)",
                                 "ratio": "laczna wyplata / pierwotna wartosc umowy"}},
        "global": cell(d),
        "by_value": {k: cell(g) for k, g in d.groupby("vb")},
        "by_period": {k: cell(g) for k, g in d.groupby("pb")},
        "by_value_period": {f"{a}|{b}": cell(g) for (a, b), g in d.groupby(["vb", "pb"])},
        "by_value_eu": {f"{a}|eu={int(b)}": cell(g) for (a, b), g in d.dropna(subset=["eu"]).groupby(["vb", "eu"])},
    }
    # Rozklad opoznienia wsrod umow opoznionych (wymaga dat zawarcia i wykonania umowy).
    out["delay_rel_q_among_late"] = None
    if {"signed_date", "done_date"} <= set(d.columns):
        sd, dd = pd.to_datetime(d["signed_date"], errors="coerce"), pd.to_datetime(d["done_date"], errors="coerce")
        days_over = (dd - sd).dt.days - d["period_days"]
        ok = (d["late"] == 1) & (d["period_days"] > 0) & days_over.notna() & (days_over > 0)
        if int(ok.sum()) >= 30:
            rel = (days_over / d["period_days"])[ok]
            qs = (0.25, 0.5, 0.75, 0.9, 0.95)
            out["delay_rel_q_among_late"] = {f"p{int(p * 100)}": round(float(np.quantile(rel, p)), 2) for p in qs}
            out["delay_days_q_among_late"] = {f"p{int(p * 100)}": int(np.quantile(days_over[ok], p)) for p in qs}
            out["delay_rel_n"] = int(ok.sum())
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--source", default="", help="opis zrodla i okresu, trafia do meta")
    a = ap.parse_args()
    d = pd.read_csv(a.data, dtype=str)
    table = build(d, a.source or a.data)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(table, f, ensure_ascii=False, indent=1)
    g = table["global"]
    if not table.get("delay_rel_q_among_late"):
        print("UWAGA: brak dat (signed_date, done_date) albo mniej niz 30 opoznionych umow z datami: tabela nie ma "
              "rozkladu dlugosci opoznienia; prognoza uzyje rozkladu domyslnego z BZP 11.2026.", file=sys.stderr)
    print(f"Klasa referencyjna: n={g['n']}, opoznione {g['late_pct']}%, wzrost kosztu {g['cost_up_pct']}%, "
          f"komorek {len(table['by_value_period'])}. Zapisano {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
