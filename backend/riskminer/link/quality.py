"""Link quality vs the hand-verified gold set (tests/fixtures/gold/links_gold.csv) – for /api/quality and the report.

Notice level: a notice counts as *predicted* for a project when its procedure is linked (status ≠ rejected) and,
for lot projects (część N), the notice is the ContractNotice/TenderResult of the procedure or belongs to the
contract of part N. Gold rows labelled `link` are positives; `decoy` / `other_part` are known negatives;
`missing_in_bzp` rows are reported, not scored.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from riskminer.models import Contract, Notice, Project, ProjectProcedure, ReviewStatus

GOLD = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "gold" / "links_gold.csv"


def load_gold(path: Path = GOLD) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def predicted_notices(session: Session) -> dict[str, dict[str, dict[str, Any]]]:
    """{rm_code: {object_id: {method, confidence, status, procedure_id}}}"""
    out: dict[str, dict[str, dict[str, Any]]] = {}
    rows = session.execute(select(ProjectProcedure, Project).join(Project, Project.id == ProjectProcedure.project_id)
                           .where(ProjectProcedure.status != ReviewStatus.rejected.value)).all()
    for link, proj in rows:
        notices = session.execute(select(Notice).where(Notice.procedure_id == link.procedure_id)).scalars().all()
        allowed: set | None = None
        if link.part_no:
            contracts = session.execute(select(Contract).where(Contract.procedure_id == link.procedure_id,
                                                               Contract.part_no == link.part_no)).scalars().all()
            allowed = set()
            for c in contracts:
                allowed |= {str(c.performing_notice_id), *((c.meta or {}).get("agreement_update_ids") or [])}
        d = out.setdefault(proj.code, {})
        for n in notices:
            if allowed is not None and n.notice_type in ("ContractPerformingNotice", "AgreementUpdateNotice") \
                    and str(n.id) not in allowed:
                continue
            d[n.object_id] = {"method": link.method, "confidence": link.confidence, "status": link.status,
                              "procedure_id": str(link.procedure_id), "part_no": link.part_no}
    return out


def evaluate(session: Session, gold: list[dict[str, str]] | None = None) -> dict[str, Any]:
    gold = gold or load_gold()
    pred = predicted_notices(session)
    pos = {(g["rm_id"], g["object_id"]) for g in gold if g["label"] == "link"}
    neg = {(g["rm_id"], g["object_id"]) for g in gold if g["label"] in ("decoy", "other_part")}
    projects = sorted({g["rm_id"] for g in gold})
    pset = {(rm, oid) for rm in projects for oid in pred.get(rm, {})}
    tp = len(pos & pset)
    fp_known = sorted(neg & pset)
    fp = len(pset - pos)
    fn = sorted(pos - pset)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / len(pos) if pos else 0.0
    per_project = []
    for rm in projects:
        gp = {oid for r, oid in pos if r == rm}
        pp = set(pred.get(rm, {}))
        meta = next(iter(pred.get(rm, {}).values()), {})
        per_project.append({"rm_id": rm, "gold": len(gp), "predicted": len(pp), "tp": len(gp & pp),
                            "fp": len(pp - gp), "fn": len(gp - pp), "method": meta.get("method"),
                            "confidence": meta.get("confidence"), "status": meta.get("status"),
                            "correct": gp == pp})
    uncertain = sum(1 for p in per_project if p["confidence"] is not None and p["confidence"] < 0.95)
    return {
        "gold_file": str(GOLD.name), "n_projects": len(projects), "n_gold_links": len(pos), "n_predicted": len(pset),
        "tp": tp, "fp": fp, "fn": len(fn), "precision": round(precision, 4), "recall": round(recall, 4),
        "f1": round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0.0,
        "projects_fully_correct": sum(p["correct"] for p in per_project),
        "projects_uncertain": uncertain,
        "decoys_linked": [{"rm_id": a, "object_id": b} for a, b in fp_known],
        "missed": [{"rm_id": a, "object_id": b} for a, b in fn],
        "organizer_errors": [g for g in gold if g["label"] == "missing_in_bzp"],
        "per_project": per_project,
    }
