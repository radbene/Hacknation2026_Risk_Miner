"""Case completeness in the expert's four non-equivalent states (extra/completeness_states.yaml).

    nie_ma_w_paczce · dokument_nie_wspomina · brak_potwierdzenia · potwierdzono_niewykonanie
plus `potwierdzone` (present, with evidence) and `sprzeczne` (contradiction between sources, e.g. the xlsx says
"Zakończone" but BZP has no ContractPerforming notice – Bobrowniki). Every item says what to add and how the gap
limits the analysis. Stored as `data_issue` rows (kind completeness | contradiction), reviewable by the expert.
"""

from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from riskminer.core.upsert import upsert_reviewable
from riskminer.extract.common import knowledge_rows
from riskminer.extract.reasons import reason_codes
from riskminer.ids import make_id
from riskminer.models import Contract, ContractChange, DataIssue, Document, Notice, Project, ProjectProcedure

OK = "potwierdzone"
CONTRA = "sprzeczne"

# doc group → (doc types that satisfy it, what to add, impact)
DOC_GROUPS: list[tuple[str, set[str], str, str]] = [
    ("dokumenty: SWZ", {"SWZ"}, "SWZ z platformy zakupowej zamawiającego (wersja po modyfikacjach).",
     "Nie można ocenić warunków udziału ani wymagań wobec wykonawców (R11, R12)."),
    ("dokumenty: OPZ/PFU/projekt", {"OPZ", "PFU", "STWiORB", "przedmiar"},
     "OPZ lub PFU, przedmiar i dokumentacja projektowa.",
     "Ocena kompletności zakresu i rozpoznania terenu (R01, R02, R09) opiera się tylko na ogłoszeniach."),
    ("dokumenty: umowa/PPU", {"umowa", "PPU", "SWU"}, "Podpisana umowa albo PPU/SWU (załącznik do SWZ).",
     "Brak klauzul zmian, kar i odbiorów – nie da się ocenić, czy zmiany były przewidziane (art. 455 ust. 1 pkt 1)."),
    ("dokumenty: aneksy/protokoły", {"aneks", "protokół"}, "Aneksy i protokoły konieczności (BIP, wniosek o informację).",
     "Przyczyny zmian znane tylko z krótkich opisów w ogłoszeniach."),
]


@dataclass
class Item:
    field: str
    state: str
    message: str
    what_to_add: str | None = None
    impact: str | None = None
    kind: str = "completeness"
    procedure_id: uuid.UUID | None = None
    evidence_ids: list[Any] = field(default_factory=list)


def state_labels(session: Session | None = None) -> dict[str, str]:
    labels = {r["state"]: r.get("label", r["state"]) for r in knowledge_rows("completeness_states", session)}
    return {**labels, OK: "potwierdzone", CONTRA: "sprzeczne"}


def _check_project(session: Session, project: Project, today: dt.date) -> list[Item]:
    items: list[Item] = []
    links = session.execute(select(ProjectProcedure).where(ProjectProcedure.project_id == project.id,
                                                           ProjectProcedure.status != "rejected")).scalars().all()
    pev = list(project.evidence_ids or [])
    finished = "zakończ" in (project.project_status or "").lower()
    if not links:
        items.append(Item("postępowanie", "nie_ma_w_paczce", "Brak powiązanego postępowania w BZP.",
                          "Numer ogłoszenia BZP lub OCID (albo zatwierdzenie kandydata w kolejce powiązań).",
                          "Brak zdarzeń z ogłoszeń: nie da się ustalić terminów, zmian ani wypłaty.", evidence_ids=pev))
    for link in links:
        pid = link.procedure_id
        notices = session.execute(select(Notice).where(Notice.procedure_id == pid)).scalars().all()
        types = {n.notice_type for n in notices}
        tag = f" (część {link.part_no})" if link.part_no else ""
        for ntype, label, add, impact in (
            ("ContractNotice", "ogłoszenie o zamówieniu", "Ogłoszenie o zamówieniu (BZP).",
             "Brak trybu, terminu składania ofert i pierwotnego okresu realizacji z ogłoszenia."),
            ("TenderResultNotice", "ogłoszenie o wyniku", "Ogłoszenie o wyniku postępowania (BZP).",
             "Brak liczby ofert i cen – nie można ocenić konkurencji ani oferty vs budżet (R11, R13)."),
        ):
            n = next((x for x in notices if x.notice_type == ntype), None)
            items.append(Item(f"{label}{tag}", OK if n else "nie_ma_w_paczce",
                              f"{label.capitalize()}: {n.notice_number}" if n else f"Brak: {label}.",
                              None if n else add, None if n else impact, procedure_id=pid,
                              evidence_ids=[] if n is None else []))
        contracts = session.execute(select(Contract).where(Contract.procedure_id == pid)).scalars().all()
        if link.part_no is not None:
            contracts = [c for c in contracts if c.part_no in (link.part_no, None)] or contracts
        if not contracts:
            items.append(Item(f"umowa{tag}", "brak_potwierdzenia", "Brak danych o zawartej umowie w ogłoszeniach.",
                              "Ogłoszenie o wyniku z sekcją VIII albo ogłoszenie o zmianie/wykonaniu umowy.",
                              "Nie można policzyć opóźnienia ani wzrostu kosztu.", procedure_id=pid))
            if finished and "ContractPerformingNotice" not in types:
                items.append(Item(f"wykonanie umowy{tag}", CONTRA,
                                  f"Arkusz: „{project.project_status}”, ale w BZP brak ogłoszenia o wykonaniu umowy.",
                                  "Ogłoszenie o wykonaniu umowy (art. 448 Pzp) albo protokół odbioru końcowego.",
                                  "Brak terminu wykonania i wypłaty – opóźnienie i koszt końcowy nieznane; "
                                  "projekt nie zasila rozkładów odchyleń.", kind="contradiction", procedure_id=pid,
                                  evidence_ids=pev))
            continue
        for c in contracts:
            ctag = tag + (f" / umowa {c.signed_at}" if len(contracts) > 1 and c.signed_at else "")
            perf = session.get(Notice, c.performing_notice_id) if c.performing_notice_id else None
            if perf is not None:
                if c.performed is False:
                    items.append(Item(f"wykonanie umowy{ctag}", "potwierdzono_niewykonanie",
                                      f"Ogłoszenie {perf.notice_number}: umowa niewykonana (5.1 = Nie).",
                                      "Informacja o przyczynie (rozwiązanie / odstąpienie) i dalszym trybie.",
                                      "Efekt inwestycji niepotwierdzony; potrzebne kolejne postępowanie.", procedure_id=pid))
                else:
                    items.append(Item(f"wykonanie umowy{ctag}", OK, f"Ogłoszenie o wykonaniu umowy: {perf.notice_number}.",
                                      procedure_id=pid))
                if c.paid_gross is None:
                    items.append(Item(f"wypłata (5.5){ctag}", "dokument_nie_wspomina",
                                      "Ogłoszenie o wykonaniu nie podaje łącznej wypłaty.",
                                      "Rozliczenie końcowe / sprawozdanie z wykonania budżetu.",
                                      "Nie można ocenić wzrostu kosztu (paid/value).", procedure_id=pid))
                if not finished and project.project_status:
                    items.append(Item(f"status projektu{ctag}", CONTRA,
                                      f"Arkusz: „{project.project_status}”, a BZP zawiera ogłoszenie o wykonaniu umowy "
                                      f"{perf.notice_number}.", "Potwierdzenie statusu u beneficjenta.",
                                      "Status w arkuszu może być nieaktualny – przyjęto dane z BZP.", kind="contradiction",
                                      procedure_id=pid, evidence_ids=pev))
            else:
                end = c.planned_end
                if finished:
                    items.append(Item(f"wykonanie umowy{ctag}", CONTRA,
                                      f"Arkusz: „{project.project_status}”, ale w BZP brak ogłoszenia o wykonaniu umowy.",
                                      "Ogłoszenie o wykonaniu umowy (art. 448 Pzp) albo protokół odbioru końcowego.",
                                      "Brak terminu wykonania i wypłaty – opóźnienie i koszt końcowy nieznane; "
                                      "projekt nie zasila rozkładów odchyleń.", kind="contradiction", procedure_id=pid,
                                      evidence_ids=pev))
                elif end and end < today:
                    items.append(Item(f"wykonanie umowy{ctag}", "brak_potwierdzenia",
                                      f"Termin umowny {end} minął, brak ogłoszenia o wykonaniu umowy.",
                                      "Ogłoszenie o wykonaniu umowy lub informacja o aneksie terminowym.",
                                      "Możliwe opóźnienie – niepotwierdzone.", procedure_id=pid))
                else:
                    items.append(Item(f"wykonanie umowy{ctag}", "nie_ma_w_paczce", "Umowa w realizacji – brak ogłoszenia o wykonaniu.",
                                      "Ogłoszenie o wykonaniu po zakończeniu (monitoring).",
                                      "Wynik realizacji jeszcze nieznany.", procedure_id=pid))
            for ch in session.execute(select(ContractChange).where(ContractChange.contract_id == c.id)).scalars():
                reason = (ch.reason or "").strip()
                if not reason or (not reason_codes(reason) and len(reason) < 120):
                    items.append(Item(f"przyczyna zmiany nr {ch.change_no}{ctag}", "dokument_nie_wspomina",
                                      f"Ogłoszenie nie podaje rzeczywistej przyczyny zmiany: „{reason[:160] or 'brak'}”.",
                                      "Aneks i protokół konieczności (uzasadnienie faktyczne zmiany).",
                                      "Zmiana nie może zostać przypisana do kategorii ryzyka R01–R15.", procedure_id=pid))
    doc_types = set(session.execute(select(Document.doc_type).where(Document.project_id == project.id)).scalars())
    for label, needed, add, impact in DOC_GROUPS:
        have = doc_types & needed
        items.append(Item(label, OK if have else "nie_ma_w_paczce",
                          f"W paczce: {', '.join(sorted(have))}." if have else f"Brak w paczce: {label.split(': ')[1]}.",
                          None if have else add, None if have else impact))
    return items


def compute(session: Session, project_id: uuid.UUID, today: dt.date | None = None) -> tuple[float, list[DataIssue]]:
    project = session.get(Project, project_id)
    if project is None:
        return 0.0, []
    items = _check_project(session, project, today or dt.date.today())
    ids = []
    for it in items:
        iid = make_id("data_issue", project_id, it.kind, it.field)
        ids.append(iid)
        upsert_reviewable(session, DataIssue, dict(
            id=iid, project_id=project_id, procedure_id=it.procedure_id, kind=it.kind, field=it.field[:128],
            state=it.state, message=it.message, what_to_add=it.what_to_add, impact=it.impact, method="rule",
            confidence=0.9, evidence_ids=[str(e) for e in it.evidence_ids]))
    # drop stale machine items (no longer produced, never reviewed)
    session.execute(delete(DataIssue).where(DataIssue.project_id == project_id,
                                            DataIssue.kind.in_(("completeness", "contradiction")),
                                            DataIssue.status == "proposed", DataIssue.id.not_in(ids)))
    session.flush()
    rows = session.execute(select(DataIssue).where(DataIssue.id.in_(ids)).order_by(DataIssue.kind, DataIssue.field)).scalars().all()
    score = round(sum(1 for r in rows if r.state == OK) / len(rows), 3) if rows else 0.0
    return score, list(rows)
