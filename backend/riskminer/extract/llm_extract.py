"""LLM cause extraction ("Wniosek modelu"): reason text → {risk_codes, cause, effect, mitigation, quote, confidence}.

Only through `riskminer.llm.complete("causes", …)`. The source text is wrapped as untrusted and stripped of
personal data. A model answer is used only if its quote is found verbatim in the cited text (validate.py);
otherwise the rule result stays. Few-shot examples come from exemplary approved events
(`review.learning.get_few_shot("causes")` when S5 provides it, else a direct query).
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from riskminer.extract.catalog import ensure_proposed, slug_code
from riskminer.extract.common import derivation_evidence, risk_names
from riskminer.extract.validate import check_quote
from riskminer.llm import complete, strip_personal_data, wrap_untrusted
from riskminer.models import Event

log = logging.getLogger("riskminer.extract.llm")
PROMPT_VERSION = "causes-v1"


class CauseOut(BaseModel):
    risk_codes: list[str] = Field(default_factory=list, description="Kody R01–R15; pusta lista gdy żaden nie pasuje")
    cause: str = Field(description="Przyczyna zdarzenia, 1 zdanie, po polsku")
    effect: str | None = Field(None, description="Skutek (termin/koszt/zakres), jeśli wynika z tekstu")
    mitigation: str | None = Field(None, description="Podjęte lub zalecane środki zaradcze")
    quote: str = Field(description="Dosłowny cytat z tekstu źródłowego uzasadniający klasyfikację")
    confidence: float = Field(ge=0, le=1)
    new_category: str | None = Field(None, description="Krótka nazwa nowej kategorii, gdy żaden kod R nie pasuje")


SYSTEM = (
    "Jesteś ekspertem ds. ryzyk inwestycji wodno-kanalizacyjnych. Klasyfikujesz przyczyny zmian i opóźnień umów "
    "do katalogu ryzyk R01–R15. Zwracasz wyłącznie JSON zgodny ze schematem. Pole quote musi być dosłownym "
    "fragmentem tekstu źródłowego. Jeżeli tekst nie podaje przyczyny (np. tylko 'zmiana terminu'), zwróć pustą "
    "listę risk_codes i confidence ≤ 0.3."
)


def _catalog_text(session: Session) -> str:
    return "\n".join(f"{c}: {r.get('name')} – skutki: {r.get('effects')}" for c, r in sorted(risk_names(session).items()))


def few_shot(session: Session, task: str = "causes", k: int = 4) -> list[dict[str, Any]]:
    try:
        from riskminer.review.learning import get_few_shot  # S5

        shots = get_few_shot(task)
        if shots:
            return list(shots)[:k]
    except Exception:  # noqa: BLE001 – S5 module optional
        pass
    rows = session.execute(select(Event).where(Event.exemplary.is_(True), Event.status.in_(("approved", "edited")),
                                               Event.cause.is_not(None)).limit(k)).scalars().all()
    return [{"input": e.cause, "output": {"risk_codes": e.risk_codes, "cause": e.cause, "effect": e.effect,
                                          "mitigation": e.mitigation, "quote": e.quote, "confidence": 1.0}}
            for e in rows]


def build_messages(session: Session, text: str, context: str = "") -> list[dict[str, Any]]:
    shots = few_shot(session)
    ex = "\n\n".join(f"Przykład zatwierdzony przez eksperta:\nTEKST: {s['input']}\nJSON: "
                     f"{json.dumps(s['output'], ensure_ascii=False)}" for s in shots)
    body = wrap_untrusted(strip_personal_data(text), source="ogłoszenie BZP")
    return [{"role": "user", "content": f"Katalog ryzyk:\n{_catalog_text(session)}\n\n{ex}\n\n{context}\n"
                                        f"Tekst do klasyfikacji:\n{body}"}]


def classify_with_llm(session: Session, text: str, context: str = "", profiles: list[str] | None = None):
    """Returns (CauseOut | None, LLMResult). None when no model, validation failed or the quote is not verbatim."""
    res = complete("causes", build_messages(session, text, context), CauseOut, system=SYSTEM,
                   prompt_version=PROMPT_VERSION, profiles=profiles)
    out = res.data
    if out is None:
        return None, res
    if not check_quote(out.quote, text):
        log.info("llm quote not verbatim – discarded: %r", out.quote[:80])
        return None, res
    valid = set(risk_names(session))
    out.risk_codes = [c for c in out.risk_codes if c in valid]
    return out, res


def enrich_event(session: Session, ev: Event, profiles: list[str] | None = None) -> str:
    """Apply the model's cause to one proposed event. Returns 'llm' | 'rules' | 'skipped'."""
    if ev.status != "proposed" or not ev.cause:
        return "skipped"
    out, res = classify_with_llm(session, ev.cause, context=f"Typ zdarzenia: {ev.event_type}. {ev.title or ''}",
                                 profiles=profiles)
    if out is None:
        return "rules"
    codes = out.risk_codes
    if not codes and out.new_category:  # open catalog
        code = slug_code(out.new_category)
        ensure_proposed(session, code, out.new_category, f"Zaproponowane przez model: {out.cause}",
                        method="llm", confidence=out.confidence, evidence_ids=ev.evidence_ids)
        codes = [code]
    der = derivation_evidence(session, key=("llm_cause", ev.id, res.model), inputs=list(ev.evidence_ids or []),
                              formula=f"Wniosek modelu ({res.label}, {PROMPT_VERSION}); cytat zweryfikowany",
                              values={"rule_codes": ev.risk_codes, "llm_codes": codes, "confidence": out.confidence},
                              quote=out.quote)
    ev.risk_codes = codes or ev.risk_codes
    ev.effect = ev.effect or out.effect
    ev.mitigation = ev.mitigation if ev.mitigation and not out.mitigation else (out.mitigation or ev.mitigation)
    ev.quote, ev.confidence = out.quote, out.confidence
    ev.method, ev.model_label = "llm", res.label
    ev.evidence_ids = list(dict.fromkeys([*(ev.evidence_ids or []), str(der)]))
    return "llm"


def enrich_events(session: Session, event_ids: list[uuid.UUID | str] | None = None, *, project_id=None,
                  tier: str | None = None, limit: int = 500) -> dict[str, int]:
    """Batch LLM cause run (auto tier or one project). Events without a cause text are skipped."""
    q = select(Event).where(Event.status == "proposed", Event.cause.is_not(None), Event.method == "rule")
    if event_ids:
        q = q.where(Event.id.in_([uuid.UUID(str(i)) for i in event_ids]))
    if project_id:
        q = q.where(Event.project_id == project_id)
    if tier:
        q = q.where(Event.tier == tier)
    counts = {"llm": 0, "rules": 0, "skipped": 0}
    for ev in session.execute(q.limit(limit)).scalars():
        counts[enrich_event(session, ev)] += 1
    session.flush()
    return counts
