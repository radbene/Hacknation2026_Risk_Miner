#!/usr/bin/env python3
"""Laczy umowy (ogloszenia o wykonaniu) z cechami z ogloszen o wyniku i liczy cechy pochodne.

  python3 bzp_join.py --contracts contracts.csv --results results.csv --out dataset.csv

Klucz: contracts.result_notice == results.notice_no (np. '2026/BZP 00384546/01').
Ogloszenia o wyniku z wieloma czesciami (n_parts != 1) sa pomijane, bo nie wiadomo,
ktorej czesci dotyczy umowa. Wymaga pandas (BSD-3-Clause).
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

RESULT_COLS = ["n_offers", "n_sme", "n_rejected", "n_abn_low", "price_min", "price_max",
               "est_value", "joint", "contractor_size", "subcontract", "in_plan"]


def add_features(d: pd.DataFrame) -> pd.DataFrame:
    """Cechy znane w dniu zawarcia umowy (bez przecieku etykiety)."""
    d = d.copy()
    d["log_value"] = np.log10(d["value"].clip(lower=1))
    d["cpv3"] = d["cpv"].astype(str).str[:3]
    d["cpv5"] = d["cpv"].astype(str).str[:5]
    sd = pd.to_datetime(d["signed_date"], errors="coerce")
    d["signed_month"] = sd.dt.month
    d["signed_year"] = sd.dt.year
    if "n_offers" in d:
        d["single_bid"] = (d["n_offers"] == 1).astype("Int64").where(d["n_offers"].notna())
        # est_value jest netto, ceny ofert brutto: przyblizenie stawka 23% (roboty; czesc ma 8%).
        gross_est = d["est_value"] * 1.23
        d["won_to_est"] = (d["value"] / gross_est).where(gross_est > 0)
        d["spread"] = (d["price_max"] / d["price_min"]).where(d["price_min"] > 0)
    return d


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--contracts", required=True)
    ap.add_argument("--results")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    c = pd.read_csv(a.contracts, dtype={"cpv": str, "buyer_nip": str, "contractor_nip": str})
    n0 = len(c)
    if a.results:
        r = pd.read_csv(a.results)
        r = r[r["n_parts"] == 1].drop_duplicates("notice_no")
        keep = ["notice_no"] + [k for k in RESULT_COLS if k in r.columns]
        c = c.merge(r[keep], how="left", left_on="result_notice", right_on="notice_no", suffixes=("", "_res"))
        matched = int(c["n_offers"].notna().sum()) if "n_offers" in c else 0
        print(f"Dolaczono cechy z ogloszen o wyniku dla {matched} z {n0} umow.")
    c = add_features(c)
    c.to_csv(a.out, index=False)
    print(f"Zapisano {len(c)} wierszy, {c.shape[1]} kolumn do {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
