"""Live BZP feed for monitoring.

Prefers S1's connector (`riskminer.connectors.bzp`) when it is importable; otherwise falls back to a
minimal, op-logged day-by-day query against the configured BZP API (mirror or official). The API ignores
TenderId filters, so we fetch a day window per notice type and filter by OCID client-side.
"""

from __future__ import annotations

import datetime as dt
import logging
import time
from collections.abc import Iterable
from typing import Any

import httpx

from riskminer.core.config import get_config
from riskminer.core.oplog import logged_op

log = logging.getLogger("riskminer.monitor.feed")

NOTICE_TYPES = ("ContractNotice", "TenderResultNotice", "AgreementUpdateNotice", "ContractPerformingNotice")
PAGE_SIZE = 500


def _bzp_cfg():
    cfg = get_config()
    c = cfg.connectors.get("bzp")
    base = (c.base_url if c and c.base_url else None) or "https://ezamowienia.gov.pl/mo-board/api/v1/notice"
    return base, (c.min_interval_s if c else 2.1), (c.timeout_s if c else 60.0), cfg.user_agent


def fetch_day(day: dt.date, notice_type: str, *, client: httpx.Client | None = None,
              job_id=None) -> list[dict[str, Any]]:
    """All notices of one type published on `day` (paged with SearchAfter)."""
    base, min_interval, timeout, ua = _bzp_cfg()
    own = client is None
    client = client or httpx.Client(timeout=timeout, headers={"User-Agent": ua, "Accept": "application/json"})
    params: dict[str, Any] = {
        "NoticeType": notice_type,
        "PublicationDateFrom": f"{day.isoformat()}T00:00:00Z",
        "PublicationDateTo": f"{day.isoformat()}T00:00:00Z",
        "PageSize": PAGE_SIZE,
    }
    out: list[dict] = []
    seen: set[str] = set()
    after = None
    try:
        while True:
            q = {**params, **({"SearchAfter": after} if after else {})}
            with logged_op("bzp", "monitor_day", base, q, job_id=job_id) as op:
                r = client.get(base, params=q)
                op["status_code"] = r.status_code
                op["bytes"] = len(r.content)
                r.raise_for_status()
                page = r.json()
                op["n_results"] = len(page) if isinstance(page, list) else None
            if not isinstance(page, list):
                break
            fresh = [x for x in page if x.get("objectId") not in seen
                     and (x.get("publicationDate") or "")[:10] == day.isoformat()]
            seen.update(x.get("objectId") for x in page)
            out.extend(fresh)
            if len(page) < PAGE_SIZE or not fresh:
                break
            after = page[-1].get("objectId")
            if min_interval:
                time.sleep(min_interval)
    finally:
        if own:
            client.close()
    return out


def fetch_for_ocids(ocids: Iterable[str], date_from: dt.date, date_to: dt.date, job_id=None,
                    max_days: int = 14) -> list[dict[str, Any]]:
    """Notices (API items) of the given OCIDs published in [date_from, date_to] (at most `max_days` days)."""
    wanted = {o for o in ocids if o}
    if not wanted or date_from > date_to:
        return []
    try:  # S1's connector, if it exposes a helper for this
        from riskminer.connectors import bzp as s1  # type: ignore

        fn = getattr(s1, "fetch_for_ocids", None)
        if callable(fn):
            return list(fn(wanted, date_from, date_to))
    except ImportError:
        pass
    date_from = max(date_from, date_to - dt.timedelta(days=max_days - 1))
    _, _, timeout, ua = _bzp_cfg()
    found: list[dict] = []
    with httpx.Client(timeout=timeout, headers={"User-Agent": ua, "Accept": "application/json"}) as client:
        day = date_from
        while day <= date_to:
            for nt in NOTICE_TYPES:
                try:
                    found += [x for x in fetch_day(day, nt, client=client, job_id=job_id) if x.get("tenderId") in wanted]
                except httpx.HTTPError as e:
                    log.warning("monitor fetch %s %s failed: %s", day, nt, e)
            day += dt.timedelta(days=1)
    return found


def probe(url: str | None = None, timeout: float = 20.0) -> dict[str, Any]:
    """Connectivity check used by `riskminer monitor probe` (and the deploy smoke test)."""
    base, _, _, ua = _bzp_cfg()
    url = url or base
    day = (dt.date.today() - dt.timedelta(days=3)).isoformat()
    params = {"NoticeType": "ContractPerformingNotice", "PublicationDateFrom": f"{day}T00:00:00Z",
              "PublicationDateTo": f"{day}T00:00:00Z", "PageSize": 5}
    res: dict[str, Any] = {"url": url}
    try:
        r = httpx.get(url, params=params, headers={"User-Agent": ua, "Accept": "application/json"}, timeout=timeout)
        res.update(status=r.status_code, n=len(r.json()) if r.status_code == 200 else None)
    except Exception as e:  # noqa: BLE001
        res.update(status=None, error=f"{type(e).__name__}: {e}")
    return res
