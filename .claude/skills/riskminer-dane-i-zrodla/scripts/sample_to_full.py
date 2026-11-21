#!/usr/bin/env python3
"""Zamienia probke data-samples/bzp/contracts_works_sample_500.csv na pelny schemat zbioru
(taki jak z bzp_parse.py + bzp_join.py), zeby pozostale skrypty dalo sie uruchomic bez pobierania danych.

  python3 sample_to_full.py --sample contracts_works_sample_500.csv --out dataset_sample.csv
"""
from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bzp_join import add_features  # noqa: E402

MODE = {"P1": "tryb podstawowy, art. 275 pkt 1", "P2": "tryb podstawowy, art. 275 pkt 2",
        "P3": "tryb podstawowy, art. 275 pkt 3", "WR": "zamówienie z wolnej ręki",
        "PN": "przetarg nieograniczony, art. 132", "NB": "negocjacje bez ogłoszenia", "IN": "inny"}
SIZE = {"MI": "Mikro przedsiębiorca", "MA": "Mały przedsiębiorca", "SR": "Średni przedsiębiorca",
        "DU": "Duży przedsiębiorca"}


def convert(s: pd.DataFrame) -> pd.DataFrame:
    signed = pd.to_datetime("20" + s["signed"].astype(str).str.zfill(6), format="%Y%m%d", errors="coerce")
    d = pd.DataFrame({
        "bzp": [f"probka-{i:04d}" for i in range(len(s))],
        "pub_date": "2026-11-" + s["pub_day"].astype(str).str.zfill(2),
        "province": "PL" + s["prov"].astype(str).str.zfill(2),
        "buyer_nip": s["bid"], "contractor_nip": s["cid"], "below_eu": s["below_eu"],
        "cpv": s["cpv"].astype(str), "eu_funded": s["eu"], "has_eu_project_no": s["has_eu_no"],
        "mode": s["mode"].map(MODE), "signed_date": signed.dt.date.astype(str),
        "period_days": s["period_days"], "value": s["value"], "done": s["done"],
        "on_time": 1 - s["late"], "n_changes": s["n_changes"], "price_up": s["price_up"],
        "paid": s["paid"], "proper": s["proper"],
        "n_offers": s["n_offers"], "est_value": s["est_net"], "price_min": s["p_min"], "price_max": s["p_max"],
        "contractor_size": s["size"].map(SIZE), "subcontract": s["subc"], "joint": s["joint"],
        "label_late": s["late"],
    })
    ok = (d["done"] == 1) & (d["value"] > 0)
    d["label_cost_up"] = (d["paid"] / d["value"] > 1.01).astype(float).where(ok)
    d["label_failed"] = 1 - d["done"]
    d["done_date"] = pd.NA  # w probce brak daty wykonania
    return add_features(d)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    s = pd.read_csv(a.sample, dtype={"pub_day": str, "prov": str, "signed": str, "cpv": str})
    d = convert(s)
    d.to_csv(a.out, index=False)
    print(f"Zapisano {len(d)} wierszy, {d.shape[1]} kolumn do {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
