#!/usr/bin/env python3
"""Pobiera ogloszenia BZP z publicznego API e-Zamowienia do plikow JSONL (cache na dysku).

  python3 bzp_fetch.py --type ContractPerformingNotice --from 2026-10-01 --to 2026-10-31 \
      --order-type Works --out data/bzp_raw

Fakty o API sprawdzone na zywo 2026-11-16 (research/03_dane_i_api.md):
- GET https://ezamowienia.gov.pl/mo-board/api/v1/notice, bez klucza.
- Wymagane: NoticeType, PublicationDateFrom, PublicationDateTo. PageSize <= 500.
- Stronicowanie: SearchAfter=<objectId ostatniego rekordu poprzedniej strony>.
- Limit: 30 zapytan/min z jednego IP, po przekroczeniu HTTP 403 (strona integracji UZP).
Skrypt pobiera dzien po dniu, zapisuje <out>/<typ>/<YYYY-MM-DD>.jsonl i pomija dni juz pobrane.
Tylko biblioteka standardowa.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

BASE = os.environ.get("BZP_API_BASE", "https://ezamowienia.gov.pl/mo-board/api/v1/notice")
USER_AGENT = os.environ.get("BZP_USER_AGENT", "riskminer-hacknation/0.1 (kontakt: uzupelnij w .env)")
MIN_INTERVAL = float(os.environ.get("BZP_MIN_INTERVAL_S", "2.1"))  # 30/min => >= 2 s
PAGE_SIZE = 500
_last_call = 0.0


def _get(params: dict, retries: int = 5) -> list:
    """Jedno zapytanie z ograniczeniem tempa i ponawianiem (403 = limit, 5xx, bledy sieci)."""
    global _last_call
    url = BASE + "?" + urllib.parse.urlencode(params)
    for attempt in range(retries):
        wait = MIN_INTERVAL - (time.monotonic() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.monotonic()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 400:
                raise SystemExit(f"HTTP 400 (zle parametry): {e.read().decode('utf-8', 'replace')[:400]}")
            pause = 65 if e.code == 403 else 5 * (attempt + 1)
            print(f"  HTTP {e.code}, proba {attempt + 1}/{retries}, czekam {pause}s", file=sys.stderr)
            time.sleep(pause if MIN_INTERVAL > 0 else 0)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            print(f"  blad sieci: {e}, proba {attempt + 1}/{retries}", file=sys.stderr)
            time.sleep(5 * (attempt + 1) if MIN_INTERVAL > 0 else 0)
    raise SystemExit(f"Nie udalo sie pobrac po {retries} probach: {url}")


def fetch_day(notice_type: str, day: date, order_type: str | None, cpv: str | None) -> list:
    """Wszystkie ogloszenia danego typu z jednego dnia (API traktuje daty z dokladnoscia do dnia)."""
    params = {
        "NoticeType": notice_type,
        "PublicationDateFrom": f"{day.isoformat()}T00:00:00Z",
        "PublicationDateTo": f"{day.isoformat()}T00:00:00Z",
        "PageSize": PAGE_SIZE,
    }
    if order_type:
        params["OrderType"] = order_type
    if cpv:
        params["CpvCode"] = cpv
    out, seen, after = [], set(), None
    while True:
        page = _get({**params, **({"SearchAfter": after} if after else {})})
        if not isinstance(page, list):
            raise SystemExit(f"Nieoczekiwana odpowiedz: {str(page)[:300]}")
        fresh = [x for x in page if x.get("objectId") not in seen]
        # API zwraca tez rekordy z dnia nastepnego, gdy okno jest na granicy: tnij po dacie.
        fresh = [x for x in fresh if (x.get("publicationDate") or "")[:10] == day.isoformat()] or (
            [] if page else fresh
        )
        out.extend(fresh)
        seen.update(x.get("objectId") for x in page)
        if len(page) < PAGE_SIZE or not fresh:
            break
        after = page[-1].get("objectId")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--type", required=True, help="np. ContractPerformingNotice, TenderResultNotice, AgreementUpdateNotice, ContractNotice")
    ap.add_argument("--from", dest="d_from", required=True, type=date.fromisoformat)
    ap.add_argument("--to", dest="d_to", required=True, type=date.fromisoformat)
    ap.add_argument("--order-type", choices=["Works", "Delivery", "Services"])
    ap.add_argument("--cpv", help="filtr CpvCode, np. 45233120-6")
    ap.add_argument("--out", type=Path, default=Path("data/bzp_raw"))
    ap.add_argument("--force", action="store_true", help="pobierz ponownie dni obecne w cache")
    a = ap.parse_args()

    sub = a.type + (f"_{a.order_type}" if a.order_type else "") + (f"_{a.cpv}" if a.cpv else "")
    folder = a.out / sub
    folder.mkdir(parents=True, exist_ok=True)
    total, day = 0, a.d_from
    while day <= a.d_to:
        dest = folder / f"{day.isoformat()}.jsonl"
        if dest.exists() and not a.force:
            n = sum(1 for _ in dest.open(encoding="utf-8"))
            print(f"{day} cache ({n})")
        else:
            recs = fetch_day(a.type, day, a.order_type, a.cpv)
            tmp = dest.with_suffix(".tmp")
            with tmp.open("w", encoding="utf-8") as f:
                for r in recs:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            tmp.replace(dest)
            n = len(recs)
            print(f"{day} pobrano {n}")
        total += n
        day += timedelta(days=1)
    print(f"Razem {total} ogloszen w {folder}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
