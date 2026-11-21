"""S1: DOM parser + typed extraction on real notices of the 22 projects (fixture notices22)."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from riskminer.parse.bzp_dom import parse_dom
from riskminer.parse.bzp_notices import legal_basis_code, parse_notice, period_end


@pytest.fixture(scope="module")
def by_no(notices22):
    return {r["noticeNumber"]: r for r in notices22}


def test_offsets_exact_on_all_notices(notices22):
    for r in notices22:
        dom = parse_dom(r["htmlBody"])
        assert dom.fields, r["noticeNumber"]
        for f in dom.fields:
            if f.value:
                assert dom.canonical_text[f.offset:f.offset + len(f.value)] == f.value


def test_all_types_parse(notices22):
    for r in notices22:
        _, parsed, _ = parse_notice(r)
        assert parsed["type"] == r["noticeType"]
        if r["noticeType"] != "ContractNotice":
            assert parsed["ocid"] == r["tenderId"]


def test_lots_biecz(by_no):
    _, cn, _ = parse_notice(by_no["2026/BZP 00084760/01"])
    assert cn["n_parts"] == 4 and set(cn["parts"]) == {"1", "2", "3", "4"}
    _, tr, x = parse_notice(by_no["2026/BZP 00166534/01"])
    p1 = tr["parts"]["1"]
    assert p1["contractor"]["id"] == "7380005265" and p1["value"] == Decimal("1952120.53")
    assert p1["n_offers"] == 9 and p1["signed_at"] == dt.date(2026, 3, 12)
    assert tr["parts"]["4"]["contractor"]["id"] == "7381000991"
    assert ("2.14", "2026/BZP 00084760", "prior_notice") in [(a["section"], a["notice_number"], a["kind"]) for a in x]


def test_changes_nowogard(by_no):
    _, a1, _ = parse_notice(by_no["2025/BZP 00558908/01"])
    assert a1["change"]["legal_basis_code"] == "455.1.4"
    assert "służebności przesyłu na działce nr 3/39" in a1["change"]["reason"]
    assert a1["change"]["new_end"] == dt.date(2025, 11, 30)
    _, a2, x2 = parse_notice(by_no["2026/BZP 00280220/01"])
    assert "wysoki poziom wód gruntowych" in a2["change"]["reason"]
    assert a2["change"]["new_end"] == dt.date(2025, 12, 31)
    assert {"earlier_change", "result_notice", "prior_notice"} <= {a["kind"] for a in x2}


def test_performing_changes_and_xrefs_wolin(by_no):
    _, cp, x = parse_notice(by_no["2023/BZP 00580488/01"])
    assert cp["prior_notice"] == "2023/BZP 00110672"  # organizer number – the missing ContractNotice
    assert cp["contractor"]["id"] == "6690503086" and cp["lot_no"] == 1
    assert {a["notice_number"] for a in x} == {"2023/BZP 00110672", "2023/BZP 00178669"}
    _, cp2, _ = parse_notice(by_no["2025/BZP 00555312/01"])
    assert len(cp2["changes"]) == 2 and cp2["changes"][1]["value"] == Decimal("8658000.00")
    assert cp2["on_time"] is False and cp2["paid"] == Decimal("8658000.00")


def test_kpo_number_in_notice(by_no):
    _, cn, _ = parse_notice(by_no["2026/BZP 00139226/01"])
    assert cn["eu"]["kpo_numbers"] == ["KPOD.03.15-IW.15-0081/25"]


def test_helpers():
    assert period_end("10 miesiące", dt.date(2024, 3, 6))[0] == dt.date(2025, 1, 6)
    assert period_end("do 2026-04-27", dt.date(2026, 3, 12)) == (dt.date(2026, 4, 27), 46)
    assert period_end("160 dni", dt.date(2024, 1, 1))[1] == 160
    assert legal_basis_code("art. 455 ust. 1 pkt 4 ustawy") == "455.1.4"
    assert legal_basis_code("art. 455 ust. 2 ustawy") == "455.2"
