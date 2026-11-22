"""KRS – current extract (odpis aktualny) of contractors and beneficiaries that have a KRS number.

The KRS number comes from the VAT white list. We record the legal form and whether the extract shows liquidation,
bankruptcy or restructuring proceedings (section 6) – a contractor-capacity signal (risk R12).
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from sqlalchemy.orm import Session

from riskminer.connectors.public import PublicClient, put_fact, save_raw
from riskminer.connectors.vat_whitelist import entities_to_check
from riskminer.core.evidence import add_evidence

API = "https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/{krs}"
SEARCH = "https://wyszukiwarka-krs.ms.gov.pl/"
PROCEEDINGS = {"likwidacja": "likwidacja", "postepowanieUpadlosciowe": "upadłość",
               "postepowanieRestrukturyzacyjne": "restrukturyzacja", "rozwiazanieUniewaznienie": "rozwiązanie",
               "zawieszenieDzialalnosci": "zawieszenie działalności"}


def _status(dane: dict[str, Any]) -> tuple[str, list[str]]:
    d6 = dane.get("dzial6") or {}
    found = [label for key, label in PROCEEDINGS.items() if d6.get(key)]
    return ("aktywny w KRS" if not found else "w KRS: " + ", ".join(found)), found


def run(session: Session, project_ids: list[uuid.UUID] | None = None, job_id: uuid.UUID | None = None) -> dict[str, Any]:
    client = PublicClient("krs", job_id=job_id, min_interval=0.4)
    ents = [e for e in entities_to_check(session, project_ids) if e.krs and e.krs.strip().isdigit()]
    out = {"entities": len(ents), "found": 0, "with_proceedings": 0}
    for e in ents:
        krs = e.krs.strip().zfill(10)
        odpis = None
        for rejestr in ("P", "S"):
            url = API.format(krs=krs)
            r = client.request("GET", url, operation="odpis_aktualny", params={"rejestr": rejestr, "format": "json"},
                               ok_status=(200, 404), n_results=lambda x: int(x.status_code == 200))
            if r.status_code == 200:
                odpis = r.json().get("odpis") or {}
                break
        if not odpis:
            continue
        dane = odpis.get("dane") or {}
        status, found = _status(dane)
        form = ((dane.get("dzial1") or {}).get("danePodmiotu") or {}).get("formaPrawna")
        stamp = (odpis.get("naglowekA") or {}).get("stanZDnia") or dt.date.today().isoformat()
        raw_id = save_raw(session, "krs", f"krs:{krs}:{stamp}", url=SEARCH, retrieved_from=f"{url}?rejestr={rejestr}",
                          payload={"naglowekA": odpis.get("naglowekA"), "dzial1": {"danePodmiotu": (dane.get("dzial1") or {}).get("danePodmiotu")},
                                   "dzial6": dane.get("dzial6")})
        eid = add_evidence(session, source_code="krs", kind="api_field", key=(krs, stamp), url=SEARCH,
                           retrieved_from=f"{url}?rejestr={rejestr}&format=json", retrieved_at=dt.datetime.now(dt.UTC),
                           locator={"krs": krs, "field": "dzial6", "stan_z_dnia": stamp}, quote=status, raw_record_id=raw_id)
        e.verified_by = sorted(set(e.verified_by or []) | {"KRS"})
        e.evidence_ids = sorted(set(e.evidence_ids or []) | {str(eid)})
        put_fact(session, subject_type="entity", subject_id=e.id, fact_type="krs_status", key=(stamp,),
                 evidence_ids=[eid], value_text=status + (f" ({form})" if form else ""))
        out["found"] += 1
        out["with_proceedings"] += bool(found)
    return out
