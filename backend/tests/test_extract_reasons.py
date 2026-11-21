"""Reason pre-labeler vs prep gold/holdout sets relabelled to R-codes (accuracy reported in docs/status.md)."""

import json

from riskminer.extract.reasons import evaluate, reason_codes


def _rows(fixtures_dir, name):
    return [json.loads(x) for x in (fixtures_dir / f"change_reasons_{name}_rcodes.jsonl").read_text().splitlines() if x]


def test_gold_and_holdout(fixtures_dir):
    gold, hold = evaluate(_rows(fixtures_dir, "gold_26")), evaluate(_rows(fixtures_dir, "holdout_32"))
    print("gold", gold, "holdout", hold)
    assert gold["f1"] >= 0.85 and hold["f1"] >= 0.8


def test_showcase_reasons():
    assert reason_codes("Konieczność ustanowienia służebności przesyłu na działce nr 3/39 obręb Konarzewo")[0] == "R03"
    assert "R02" in reason_codes("ujawniono niekorzystne warunki gruntowe oraz miejscowy wysoki poziom wód gruntowych")
    assert reason_codes("Konieczność przedłużenia terminu realizacji umowy.") == []
