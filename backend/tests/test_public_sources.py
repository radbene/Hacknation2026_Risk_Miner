"""Public-source connectors: offline checks of name matching, KRS status and VAT payload cleaning."""

from riskminer.connectors.krs import _status
from riskminer.connectors.public import _GMINA, norm
from riskminer.connectors.ted import _title
from riskminer.connectors.vat_whitelist import _clean


def test_norm_strips_municipality_prefixes():
    assert norm("Gmina Miasto Elbląg") == "elbląg"
    assert norm("  m. Sanok ") == "sanok"
    assert norm("Kartuzy (gm. wiejska)") == "kartuzy"
    assert _GMINA.sub("", "Miasto i Gmina Nowogard") == "Nowogard"


def test_ted_title_prefers_polish():
    assert _title({"hun": ["Lengyelország"], "pol": ["Polska – Roboty"]}) == "Polska – Roboty"
    assert _title(["only"]) == "only"


def test_krs_status_reads_section_6():
    assert _status({"dzial6": {}}) == ("aktywny w KRS", [])
    status, found = _status({"dzial6": {"likwidacja": [{"x": 1}]}})
    assert found == ["likwidacja"] and "likwidacja" in status


def test_vat_payload_drops_accounts_and_natural_person_data():
    sub = {"name": "Jan Kowalski", "nip": "1234567890", "statusVat": "Czynny", "accountNumbers": ["1", "2"],
           "residenceAddress": "x", "representatives": [{"name": "y"}]}
    kept = _clean(sub, natural=True)
    assert kept["accountNumbers_count"] == 2 and "accountNumbers" not in kept
    assert "name" not in kept and "residenceAddress" not in kept and "representatives" not in kept
    assert _clean(sub, natural=False)["name"] == "Jan Kowalski"
