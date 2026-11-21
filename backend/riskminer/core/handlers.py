"""Import every module that registers @job_handler so the worker knows them.

Each Phase 1 session adds its own import line here (one line each, to keep merges trivial).
"""

import contextlib

for _mod in (
    "riskminer.connectors.jobs",   # S1: import, enrich, harvest
    "riskminer.extract.jobs",      # S2: extract, documents, reanalyze
    "riskminer.analysis.jobs",     # S3: analyse
    "riskminer.review.jobs",       # S5: knowledge import, learning
    "riskminer.monitor.jobs",      # S6: monitor
):
    with contextlib.suppress(ModuleNotFoundError):
        __import__(_mod)
