"""LLM usage aggregation for the ops page (S6 `/ops/llm-usage` calls `usage_summary`)."""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import Integer, case, func, select
from sqlalchemy.orm import Session

from riskminer.llm.base import price_known
from riskminer.models import LLMCall


def usage_summary(session: Session, since: dt.datetime | None = None, task: str | None = None) -> list[dict[str, Any]]:
    """Rows per (task, provider, model, data_location): calls, cached, errors, tokens, cost (LLMUsageRow shape)."""
    q = select(
        LLMCall.task, LLMCall.provider, LLMCall.model, LLMCall.data_location,
        func.count().label("calls"),
        func.sum(case((LLMCall.cached.is_(True), 1), else_=0)).label("cached"),
        func.sum(case((LLMCall.ok.is_(False), 1), else_=0)).label("errors"),
        func.coalesce(func.sum(LLMCall.tokens_in), 0).cast(Integer).label("tokens_in"),
        func.coalesce(func.sum(LLMCall.tokens_out), 0).cast(Integer).label("tokens_out"),
        func.coalesce(func.sum(LLMCall.cost_usd), 0.0).label("cost_usd"),
        func.avg(LLMCall.latency_ms).label("avg_latency_ms"),
    ).group_by(LLMCall.task, LLMCall.provider, LLMCall.model, LLMCall.data_location)
    if since:
        q = q.where(LLMCall.at >= since)
    if task:
        q = q.where(LLMCall.task == task)
    out = []
    for r in session.execute(q.order_by(LLMCall.task, LLMCall.provider)):
        d = dict(r._mapping)
        d["cost_usd"] = float(d["cost_usd"] or 0)
        d["avg_latency_ms"] = int(d["avg_latency_ms"] or 0)
        d["price_known"] = d["provider"] == "none" or d["data_location"] == "local" or price_known(d["model"])
        out.append(d)
    return out


def totals(session: Session, since: dt.datetime | None = None) -> dict[str, Any]:
    rows = usage_summary(session, since)
    return {"calls": sum(r["calls"] for r in rows), "cost_usd": round(sum(r["cost_usd"] for r in rows), 6),
            "errors": sum(r["errors"] for r in rows), "cached": sum(r["cached"] for r in rows),
            "data_locations": sorted({r["data_location"] for r in rows if r["data_location"]})}
