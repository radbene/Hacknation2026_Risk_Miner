"""Semantic similarity of descriptions: a local multilingual sentence-embedding model (fastembed / ONNX, CPU).

- Model and cache dir from config (`embeddings_model`, `embeddings_cache_dir`); default
  paraphrase-multilingual-MiniLM-L12-v2 (384 dim, Apache-2.0). Runs on the server, nothing leaves it.
- Case vectors are stored in `<cache_dir>/vectors-<model>.npz` keyed by case code + text hash, so the ~18k
  wod-kan cases are embedded once (`riskminer embed`) and only new/changed cases later.
- At request time the model is loaded only from local files (never downloads), and at most
  `MAX_ONLINE` missing cases are embedded inline; otherwise the embedding component is left out of the score
  (the weights renormalise) and the reason is returned.
"""

from __future__ import annotations

import hashlib
import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from riskminer.core.config import get_config, repo_path

if TYPE_CHECKING:
    from riskminer.analysis.caseset import Case

log = logging.getLogger("riskminer.analysis.embeddings")
MAX_ONLINE = 300
TEXT_CHARS = 600
_lock = threading.Lock()
_state: dict = {"model": None, "model_err": None, "vecs": None}


def _cache_dir() -> Path:
    d = repo_path(get_config().embeddings_cache_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _store_path() -> Path:
    slug = get_config().embeddings_model.replace("/", "__")
    return _cache_dir() / f"vectors-{slug}.npz"


def _model(download: bool = False):
    if _state["model"] is not None:
        return _state["model"]
    if _state["model_err"] and not download:
        raise RuntimeError(_state["model_err"])
    try:
        from fastembed import TextEmbedding

        _state["model"] = TextEmbedding(get_config().embeddings_model, cache_dir=str(_cache_dir()),
                                        local_files_only=not download)
        _state["model_err"] = None
    except Exception as e:  # noqa: BLE001
        _state["model_err"] = f"model niedostępny lokalnie ({type(e).__name__}); uruchom `riskminer embed`"
        raise RuntimeError(_state["model_err"]) from e
    return _state["model"]


def _normalise(a: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(a, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return (a / n).astype(np.float32)


def embed_texts(texts: list[str], download: bool = False) -> np.ndarray:
    m = _model(download)
    return _normalise(np.array(list(m.embed(texts, batch_size=64)), dtype=np.float32))


def embed_local(texts: list[str]) -> list[list[float]]:
    """Router entry point (`riskminer.llm.router.embed`)."""
    return embed_texts(texts).tolist()


def case_text(c: Case) -> str:
    desc = (c.description or "").strip()
    t = c.title.strip()
    return (t if not desc or desc.startswith(t[:60]) else f"{t}. {desc}")[:TEXT_CHARS] if t else desc[:TEXT_CHARS]


def _h(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def _load_store() -> dict[str, tuple[str, np.ndarray]]:
    if _state["vecs"] is not None:
        return _state["vecs"]
    out: dict[str, tuple[str, np.ndarray]] = {}
    p = _store_path()
    if p.exists():
        z = np.load(p, allow_pickle=False)
        out = {str(c): (str(h), v) for c, h, v in zip(z["codes"], z["hashes"], z["vecs"], strict=True)}
    _state["vecs"] = out
    return out


def _save_store(store: dict[str, tuple[str, np.ndarray]]) -> None:
    codes = list(store)
    p = _store_path()
    tmp = p.with_name(p.stem + ".tmp.npz")
    np.savez(tmp, codes=np.array(codes), hashes=np.array([store[c][0] for c in codes]),
             vecs=np.stack([store[c][1] for c in codes]) if codes else np.zeros((0, get_config().embeddings_dim)))
    tmp.replace(p)


def ensure_vectors(cases: list[Case], *, download: bool = False, max_missing: int | None = None) -> int:
    """Embed cases whose text is new or changed. Returns how many were embedded."""
    with _lock:
        store = _load_store()
        todo = [(c.code, t) for c in cases if (t := case_text(c)) and store.get(c.code, ("",))[0] != _h(t)]
        if not todo:
            return 0
        if max_missing is not None and len(todo) > max_missing:
            raise RuntimeError(f"brak wektorów dla {len(todo)} przypadków; uruchom `riskminer embed`")
        for i in range(0, len(todo), 2048):
            part = todo[i:i + 2048]
            vecs = embed_texts([t for _, t in part], download=download)
            for (code, t), v in zip(part, vecs, strict=True):
                store[code] = (_h(t), v)
            log.info("embedded %d/%d cases", min(i + 2048, len(todo)), len(todo))
        _save_store(store)
        return len(todo)


def similarities(cases: list[Case], text: str) -> tuple[dict[str, float] | None, str | None]:
    """case code → cosine similarity in [0, 1] with the new investment's description, or (None, reason)."""
    if not get_config().embeddings_enabled:
        return None, "wyłączone w konfiguracji"
    if not (text or "").strip():
        return None, "brak opisu"
    try:
        ensure_vectors(cases, max_missing=MAX_ONLINE)
        q = embed_texts([text[:TEXT_CHARS * 2]])[0]
    except Exception as e:  # noqa: BLE001 – rules-only fallback: the component is left out
        log.info("embeddings skipped: %s", e)
        return None, str(e)
    store = _load_store()
    codes = [c.code for c in cases if c.code in store]
    if not codes:
        return None, "brak wektorów przypadków"
    sims = np.stack([store[c][1] for c in codes]) @ q
    return {c: float(max(0.0, min(1.0, s))) for c, s in zip(codes, sims, strict=True)}, None
