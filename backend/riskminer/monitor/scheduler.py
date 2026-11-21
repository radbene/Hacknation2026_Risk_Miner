"""APScheduler inside the worker: periodically enqueue a `monitor` job (the job queue does the work).

Interval from env MONITOR_INTERVAL_MIN (default 360 = every 6 h); 0 disables the scheduler.
"""

from __future__ import annotations

import logging
import os

log = logging.getLogger("riskminer.monitor.scheduler")


def _enqueue_monitor() -> None:
    from sqlalchemy import select

    from riskminer.core.db import SessionLocal
    from riskminer.core.jobs import enqueue
    from riskminer.models import Job

    s = SessionLocal()
    try:
        busy = s.execute(select(Job.id).where(Job.kind == "monitor", Job.state.in_(("queued", "running")))
                         .limit(1)).first()
        if busy:
            log.info("monitor job already queued/running – skipping tick")
            return
        enqueue(s, "monitor", {"live": True}, user="scheduler")
        log.info("monitor job enqueued")
    except Exception:  # noqa: BLE001  never kill the worker because of the scheduler
        log.exception("could not enqueue monitor job")
        s.rollback()
    finally:
        s.close()


def start_scheduler(interval_min: int | None = None):
    interval_min = int(os.environ.get("MONITOR_INTERVAL_MIN", "360")) if interval_min is None else interval_min
    if interval_min <= 0:
        log.info("monitor scheduler disabled")
        return None
    from apscheduler.schedulers.background import BackgroundScheduler

    sched = BackgroundScheduler(timezone="Europe/Warsaw")
    sched.add_job(_enqueue_monitor, "interval", minutes=interval_min, id="monitor", coalesce=True,
                  max_instances=1, replace_existing=True)
    sched.start()
    log.info("monitor scheduler started (every %d min)", interval_min)
    return sched
