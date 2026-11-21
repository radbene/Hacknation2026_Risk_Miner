"""LLM routing / data location, auth, demo reset (owner: S5)."""

from __future__ import annotations

from fastapi import APIRouter

from riskminer.api.deps import DB, USER, CurrentUser, Session, not_implemented
from riskminer.core.config import get_config, secret
from riskminer.schemas.common import Message
from riskminer.schemas.ops import LLMProfileOut, LLMRoutingIn, LLMRoutingOut, LoginIn, TokenOut, UserOut

router = APIRouter(tags=["settings"])
OWNER = "S5"


@router.get("/settings/llm", response_model=LLMRoutingOut)
def get_llm_routing():
    cfg = get_config().llm
    profiles = [LLMProfileOut(name=n, provider=p.provider, model=p.model, base_url=p.base_url,
                              data_location=p.data_location, has_key=bool(secret(p.api_key_env)) or p.provider == "none",
                              effort=p.effort) for n, p in cfg.profiles.items()]
    used = {n for chain in cfg.tasks.values() for n in chain[:1]}
    locs = sorted({cfg.profiles[n].data_location for n in used if n in cfg.profiles})
    return LLMRoutingOut(mode=cfg.mode, profiles=profiles, tasks=cfg.tasks, active_data_locations=locs)


@router.put("/settings/llm", response_model=LLMRoutingOut)
def put_llm_routing(body: LLMRoutingIn, db: Session = DB, user: CurrentUser = USER):
    raise not_implemented(OWNER)


@router.post("/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/auth/me", response_model=UserOut)
def me(user: CurrentUser = USER):
    raise not_implemented(OWNER)


@router.post("/admin/reset-demo", response_model=Message)
def reset_demo(db: Session = DB, user: CurrentUser = USER):
    """'Przywróć stan demo' – restore the golden DB snapshot for the juror sandbox."""
    raise not_implemented(OWNER)
