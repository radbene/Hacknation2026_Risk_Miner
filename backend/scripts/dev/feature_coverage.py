"""Measure regex feature coverage on the 22 organizer descriptions (title + annotation 'Opis')."""
import sys
from pathlib import Path

import openpyxl

from riskminer.analysis.features import extract_rules

XLSX = Path(__file__).resolve().parents[2] / "tests/fixtures/organizer/Risk_Miner_dane_projekty.xlsx"


def descriptions():
    ws = openpyxl.load_workbook(XLSX)["Projekty"]
    for r in list(ws.iter_rows(values_only=True))[1:]:
        if r[1]:
            yield r[1], f"{r[10]}. {r[22] or ''}", r[8]


def main(verbose: bool = False):
    fields = ["subsector_main", "work_type", "formula", "length_km", "rlm", "connections", "pump_stations",
              "value", "voivodeship", "funding"]
    hits = dict.fromkeys(fields, 0)
    n = 0
    for code, text, voiv in descriptions():
        n += 1
        f = extract_rules(text)
        row = {k: (getattr(f, k).value if getattr(f, k) else None) for k in fields}
        for k in fields:
            hits[k] += row[k] is not None
        if verbose:
            print(code, row)
    print(f"n={n}")
    for k in fields:
        print(f"{k:16s} {hits[k]:2d}/{n} = {hits[k] / n:.0%}")


if __name__ == "__main__":
    main("-v" in sys.argv)
