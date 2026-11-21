"""DB-backed job queue. Long work never runs inside a request.

    @job_handler("enrich")
    def run_enrich(ctx: JobContext) -> dict: ...   # returns the run report (stored in job.result)

    enqueue(session, "enrich", {"all": True})      # from API / CLI
    riskminer worker                               # polls `job` (FOR UPDATE SKIP LOCKED)
"""

from __future__ import annotations

import datetime as dt
import logging
import time
import traceback
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from riskminer.core.db import SessionLocal
from riskminer.models import Job

log = logging.getLogger("riskminer.jobs")
HANDLERS: dict[str, Callable[[JobContext], dict | None]] = {}


@dataclass
class JobContext:
    job_id: uuid.UUID
    params: dict[str, Any]
    session: Session

    def progress(self, p: float, message: str | None = None) -> None:
        self.session.execute(text("UPDATE job SET progress=:p, message=COALESCE(:m, message) WHERE id=:id"),
                             {"p": p, "m": message, "id": self.job_id})
        self.session.commit()


def job_handler(kind: str):
    def deco(fn):
        HANDLERS[kind] = fn
        return fn
    return deco


def enqueue(session: Session, kind: str, params: dict | None = None, user: str | None = None) -> Job:
    job = Job(kind=kind, params=params or {}, state="queued", created_by=user)
    session.add(job)
    session.commit()
    return job


def run_job(job_id: uuid.UUID) -> None:
    s = SessionLocal()
    try:
        job = s.get(Job, job_id)
        handler = HANDLERS.get(job.kind)
        if handler is None:
            raise RuntimeError(f"no handler for job kind {job.kind!r}")
        result = handler(JobContext(job_id=job.id, params=job.params or {}, session=s))
        s.rollback()  # discard any half-open transaction from the handler
        job = s.get(Job, job_id)
        job.state, job.result, job.progress, job.finished_at = "done", result or {}, 1.0, dt.datetime.now(dt.UTC)
        s.commit()
    except Exception as e:  # noqa: BLE001
        s.rollback()
        job = s.get(Job, job_id)
        job.state, job.error, job.finished_at = "failed", f"{e}\n{traceback.format_exc()[-4000:]}", dt.datetime.now(dt.UTC)
        s.commit()
        log.exception("job %s failed", job_id)
    finally:
        s.close()


def claim_next() -> uuid.UUID | None:
    s = SessionLocal()
    try:
        row = s.execute(select(Job).where(Job.state == "queued").order_by(Job.created_at)
                        .with_for_update(skip_locked=True).limit(1)).scalars().first()
        if row is None:
            s.rollback()
            return None
        row.state, row.started_at, row.attempts = "running", dt.datetime.now(dt.UTC), (row.attempts or 0) + 1
        s.commit()
        return row.id
    finally:
        s.close()


def worker_loop(poll_s: float = 1.0, once: bool = False) -> None:
    import riskminer.core.handlers  # noqa: F401  (registers all handlers)

    log.info("worker started; handlers: %s", sorted(HANDLERS))
    while True:
        jid = claim_next()
        if jid:
            run_job(jid)
        elif once:
            return
        else:
            time.sleep(poll_s)
