"""op_log: every external query/fetch is logged (jury integration test reads this)."""

from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from typing import Any

from riskminer.core.db import SessionLocal
from riskminer.models import OpLog


@contextmanager
def logged_op(connector: str, operation: str, url: str | None = None, params: dict[str, Any] | None = None,
              job_id: uuid.UUID | None = None):
    """Usage:  with logged_op("bzp", "search", url, params) as op: ...; op["n_results"] = len(items)"""
    rec: dict[str, Any] = {"status_code": None, "n_results": None, "bytes": None, "error": None}
    t0 = time.monotonic()
    try:
        yield rec
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"[:2000]
        raise
    finally:
        s = SessionLocal()
        try:
            s.add(OpLog(connector=connector, operation=operation, url=url, params=params or {}, job_id=job_id,
                        duration_ms=int((time.monotonic() - t0) * 1000), **rec))
            s.commit()
        finally:
            s.close()
