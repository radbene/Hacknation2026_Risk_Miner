"""Embedding component: used when similarities are available, left out (weights renormalise) when not."""

from __future__ import annotations

from riskminer.analysis import embeddings, similarity
from riskminer.analysis.caseset import Case


def _case(code: str, title: str) -> Case:
    import uuid

    return Case(project_id=uuid.uuid4(), code=code, title=title, description=None, tier="auto",
                subsector_main="kanalizacja", subsector_extra=[], work_type="budowa", formula=None,
                voivodeship=None, features={}, project_status="Zakończone")


def test_case_text_joins_title_and_description():
    c = _case("A", "Budowa kanalizacji")
    c.description = "Sieć grawitacyjna 5 km z przepompownią"
    assert embeddings.case_text(c) == "Budowa kanalizacji. Sieć grawitacyjna 5 km z przepompownią"


def test_embedding_component_changes_ranking():
    cases = [_case("A", "Budowa kanalizacji sanitarnej"), _case("B", "Budowa kanalizacji sanitarnej")]
    feats = {"subsector_main": "kanalizacja", "work_type": "budowa"}
    res = similarity.find_neighbours(cases, feats, "kanalizacja", embeddings={"A": 0.1, "B": 0.9}, k=2, pool="all")
    assert [n["case"].code for n in res["neighbours"]] == ["B", "A"]
    assert res["weights"]["embedding"] > 0 and res["embeddings"]["used"]


def test_embeddings_unavailable_falls_back(monkeypatch):
    monkeypatch.setattr(embeddings, "similarities", lambda cases, text: (None, "model niedostępny lokalnie"))
    cases = [_case("A", "Budowa kanalizacji sanitarnej"), _case("B", "Przebudowa sieci kanalizacyjnej")]
    res = similarity.find_neighbours(cases, {"subsector_main": "kanalizacja"}, "kanalizacja", k=2, pool="all")
    assert res["weights"]["embedding"] == 0.0
    assert res["embeddings"] == {"used": False, "note": "model niedostępny lokalnie"}
