"""BZP connector – live API (HackNation mirror, falls back to the official e-Zamówienia API).

Verified behaviour: required NoticeType + PublicationDateFrom/To; PageSize ≤ 500 with SearchAfter=<last objectId>;
working filters NoticeNumber, OrganizationName (substring), CpvCode; *ignored* filters TenderId,
OrganizationNationalId, OrganizationId, BzpNumber → we filter by NIP client-side and group by OCID.
Python's default User-Agent gets 403 → we always send our own. Every request is logged in op_log.
"""

from __future__ import annotations

import datetime as dt
import logging
import re
import time
import uuid
from typing import Any

import httpx
from sqlalchemy.orm import Session

from riskminer.core.config import get_config
from riskminer.core.oplog import logged_op

log = logging.getLogger("riskminer.bzp")
NOTICE_TYPES = ("ContractNotice", "TenderResultNotice", "AgreementUpdateNotice", "ContractPerformingNotice")
OFFICIAL = "https://ezamowienia.gov.pl/mo-board/api/v1/notice"
PAGE_SIZE = 500


class BzpBadRequest(RuntimeError):
    pass


class BzpClient:
    def __init__(self, base_url: str | None = None, job_id: uuid.UUID | None = None):
        cfg = get_config()
        cc = cfg.connectors.get("bzp")
        self.base_url = base_url or (cc.base_url if cc and cc.base_url else OFFICIAL)
        self.fallback = (cc.extra.get("fallback_base_url") if cc else None) or OFFICIAL
        self.min_interval = cc.min_interval_s if cc else 0.0
        self.timeout = cc.timeout_s if cc else 60.0
        self.ua = cfg.user_agent
        self.job_id = job_id
        self._last = 0.0
        self.n_requests = 0
        self.errors: list[str] = []
        self.client = httpx.Client(headers={"User-Agent": self.ua, "Accept": "application/json"}, timeout=self.timeout)

    def _get(self, params: dict[str, Any], retries: int = 4) -> list[dict[str, Any]]:
        base = self.base_url
        for attempt in range(retries):
            interval = self.min_interval if base == self.base_url else max(self.min_interval, 2.1)
            wait = interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            try:
                with logged_op("bzp", "search", base, params, job_id=self.job_id) as op:
                    self.n_requests += 1
                    r = self.client.get(base, params=params)
                    op["status_code"], op["bytes"] = r.status_code, len(r.content)
                    if r.status_code == 200:
                        data = r.json()
                        op["n_results"] = len(data) if isinstance(data, list) else None
                        return data if isinstance(data, list) else []
                    if r.status_code == 400:
                        raise BzpBadRequest(f"HTTP 400: {r.text[:300]}")
                    op["error"] = f"HTTP {r.status_code}"
            except BzpBadRequest:
                raise
            except (httpx.HTTPError, ValueError) as e:  # network error / bad JSON
                self.errors.append(f"{type(e).__name__}: {e}"[:300])
            if attempt >= 1 and base != self.fallback:  # mirror down → official API
                log.warning("BZP mirror failing, switching to %s", self.fallback)
                base = self.fallback
            else:
                time.sleep(min(65, 2 ** attempt) if base == self.fallback else 1)
        self.errors.append(f"giving up: {params}")
        return []

    def search(self, notice_type: str, date_from: dt.date, date_to: dt.date, max_pages: int = 40,
               **filters: Any) -> list[dict[str, Any]]:
        params = {"NoticeType": notice_type, "PublicationDateFrom": f"{date_from.isoformat()}T00:00:00Z",
                  "PublicationDateTo": f"{date_to.isoformat()}T23:59:59Z", "PageSize": PAGE_SIZE,
                  **{k: v for k, v in filters.items() if v}}
        out, seen, after = [], set(), None
        for _ in range(max_pages):
            page = self._get({**params, **({"SearchAfter": after} if after else {})})
            fresh = [x for x in page if x.get("objectId") not in seen]
            out.extend(fresh)
            seen.update(x.get("objectId") for x in page)
            if len(page) < PAGE_SIZE or not fresh:
                break
            after = page[-1].get("objectId")
        return out

    def by_notice_number(self, number: str) -> list[dict[str, Any]]:
        m = re.match(r"^(\d{4})/BZP", number)
        if not m:
            return []
        y = int(m.group(1))
        out = []
        for t in NOTICE_TYPES:
            out += self.search(t, dt.date(y, 1, 1), dt.date(y, 12, 31), max_pages=1, NoticeNumber=number)
            if out:
                break
        return out

    def by_organization(self, name: str, date_from: dt.date, date_to: dt.date,
                        types: tuple[str, ...] = NOTICE_TYPES) -> list[dict[str, Any]]:
        out = []
        for t in types:
            out += self.search(t, date_from, date_to, OrganizationName=name)
        return out


def name_variants(name: str | None, city: str | None) -> list[str]:
    """'Gmina Kartuzy – Urząd Miejski w Kartuzach' → ['Kartuzy', 'Gmina Kartuzy']; seat as the last resort."""
    out: list[str] = []
    if name:
        core = re.split(r"\s+[–-]\s+", name)[0].strip()
        stripped = re.sub(r"^(Gmina( Miasto| Miejska)?|Miasto( i Gmina)?|Urząd (Miejski|Gminy)( w)?)\s+", "", core,
                          flags=re.I).strip()
        out += [stripped, core]
    if city:
        out.append(city)
    seen: list[str] = []
    for v in out:
        if v and len(v) >= 3 and v not in seen:
            seen.append(v)
    return seen


def fetch_for_nip(client: BzpClient, nip: str, name: str | None, city: str | None, date_from: dt.date,
                  date_to: dt.date) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """All 4 notice types of a buyer: query name variants, keep only rows whose NIP matches (client-side)."""
    got: dict[str, dict[str, Any]] = {}
    queries = []
    variants = name_variants(name, None)
    if city and city not in variants:
        variants.append(city)  # the seat (e.g. Kleszczewo, not the village) – only if names found nothing
    for v in variants:
        if v == city and got and v not in name_variants(name, None):
            break
        rows = client.by_organization(v, date_from, date_to)
        mine = [r for r in rows if re.sub(r"\D", "", r.get("organizationNationalId") or "") == nip]
        queries.append({"name": v, "rows": len(rows), "matching_nip": len(mine)})
        for r in mine:
            got[r["objectId"]] = r
    return list(got.values()), {"queries": queries}


def store_records(session: Session, records: list[dict[str, Any]], client: BzpClient, tier: str = "deep") -> set[str]:
    from riskminer.connectors.bzp_store import store_notice

    ocids = set()
    now = dt.datetime.now(dt.UTC)
    for r in records:
        store_notice(session, r, source_code="bzp", retrieved_from=f"{client.base_url}?NoticeNumber={r.get('noticeNumber')}",
                     retrieved_at=now, tier=tier, keep_html=True)
        if r.get("tenderId"):
            ocids.add(r["tenderId"])
    return ocids
