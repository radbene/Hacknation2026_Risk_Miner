"""LLM routing / data location, auth, demo users, sandbox reset (owner: S5)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from riskminer.api.deps import DB, USER, CurrentUser, Session, require_role
from riskminer.core.config import get_config, get_env
from riskminer.core.jobs import enqueue
from riskminer.llm import routing
from riskminer.llm.base import price_known
from riskminer.models import Setting, User
from riskminer.review import auth, sandbox
from riskminer.schemas.common import JobOut, Message
from riskminer.schemas.ops import (
    LLMProfileOut,
    LLMRoutingIn,
    LLMRoutingOut,
    LLMTestIn,
    LoginIn,
    SandboxStatus,
    TokenOut,
    UserOut,
)

router = APIRouter(tags=["settings"])
OWNER = "S5"
ADMIN = require_role("admin")
EXPERT = require_role("expert")


def _routing_out(db: Session | None = None) -> LLMRoutingOut:
    cfg = routing.effective_llm()
    profiles = []
    for n, p in cfg.profiles.items():
        reason = routing.missing_credentials(p)
        profiles.append(LLMProfileOut(
            name=n, provider=p.provider, model=p.model, base_url=p.base_url, data_location=p.data_location,
            has_key=reason is None or p.provider == "none", effort=p.effort, available=reason is None,
            unavailable_reason=reason, max_tokens=p.max_tokens,
            price_known=p.provider == "none" or p.data_location == "local" or price_known(p.model)))
    row = db.get(Setting, routing.SETTING_KEY) if db is not None else None
    return LLMRoutingOut(
        mode=cfg.mode, profiles=profiles, tasks=cfg.tasks, default=cfg.default,
        active_data_locations=routing.data_locations(cfg), data_location_labels=routing.LOCATION_LABEL,
        task_locations={t: cfg.profiles[c[0]].data_location for t, c in cfg.tasks.items() if c and c[0] in cfg.profiles},
        overridden=bool(row and row.value), data_processing_note=get_config().data_processing_note or None,
        version=row.version if row else None, updated_by=row.updated_by if row else None)


@router.get("/settings/llm", response_model=LLMRoutingOut)
def get_llm_routing(db: Session = DB):
    """Profiles, per-task fallback order and the active data locations (banner)."""
    try:
        return _routing_out(db)
    except Exception:  # noqa: BLE001 – banner must render even without a DB
        db.rollback()
        return _routing_out(None)


@router.put("/settings/llm", response_model=LLMRoutingOut)
def put_llm_routing(body: LLMRoutingIn, db: Session = DB, user: CurrentUser = ADMIN):
    """Persist routing in the DB (overrides config/settings.yaml); every change is versioned and in the history."""
    try:
        routing.save_override(db, body.model_dump(exclude_none=True, exclude={"comment"}), user.username, body.comment)
    except routing.RoutingError as e:
        raise HTTPException(422, str(e)) from e
    db.commit()
    routing.invalidate()
    return _routing_out(db)


@router.delete("/settings/llm", response_model=LLMRoutingOut)
def reset_llm_routing(db: Session = DB, user: CurrentUser = ADMIN):
    """Drop the UI override – back to config/settings.yaml."""
    routing.reset_override(db, user.username)
    db.commit()
    routing.invalidate()
    return _routing_out(db)


@router.post("/settings/llm/test", response_model=JobOut)
def test_llm_profile(body: LLMTestIn, db: Session = DB, user: CurrentUser = EXPERT):
    """'Testuj połączenie': one tiny live call through a profile, run as a job (local models can take a minute).
    Poll GET /api/jobs/{id}; result = {ok, latency_ms, provider, model, data_location, sample | error}."""
    if body.profile not in routing.effective_llm().profiles:
        raise HTTPException(404, f"Nieznany profil {body.profile}")
    return enqueue(db, "llm_test", body.model_dump(), user=user.username)


# ---------------------------------------------------------------- auth


@router.post("/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = DB):
    try:
        u = auth.authenticate(db, body.username, body.password)
    except auth.AuthError as e:
        raise HTTPException(401, str(e)) from e
    return TokenOut(token=auth.make_token(u), user=UserOut.model_validate(u))


@router.get("/auth/me", response_model=UserOut)
def me(user: CurrentUser = USER, db: Session = DB):
    u = db.execute(select(User).where(User.username == user.username)).scalars().first()
    if u is not None:
        out = UserOut.model_validate(u)
        return out.model_copy(update={"role": user.role})
    from riskminer.ids import make_id

    return UserOut(id=make_id("user", user.username), username=user.username, display_name=user.display_name,
                   role=user.role)


@router.get("/auth/users", response_model=list[UserOut])
def list_users(db: Session = DB, user: CurrentUser = ADMIN):
    return db.execute(select(User).order_by(User.username)).scalars().all()


@router.get("/auth/demo-users", response_model=list[dict[str, str]])
def demo_users():
    """Demo accounts for the login screen (names and roles only – the password is in the jury instructions)."""
    if not get_env().demo_mode:
        return []
    return [{"username": u, "display_name": n, "role": r} for u, n, r in auth.DEMO_USERS]


# ---------------------------------------------------------------- juror sandbox


@router.get("/admin/demo-status", response_model=SandboxStatus)
def demo_status():
    try:
        st = sandbox.status()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(503, f"Nie można sprawdzić stanu demo: {e}") from e
    return SandboxStatus(**st, demo_mode=get_env().demo_mode)


@router.post("/admin/reset-demo", response_model=Message)
def reset_demo(user: CurrentUser = ADMIN):
    """'Przywróć stan demo' – restore the golden DB snapshot for the juror sandbox (see review/sandbox.py)."""
    if not get_env().demo_mode:
        raise HTTPException(403, "Reset dostępny tylko w trybie demo (DEMO_MODE)")
    try:
        msg = sandbox.restore()
    except sandbox.SandboxError as e:
        raise HTTPException(409, str(e)) from e
    routing.invalidate()
    return Message(ok=True, message=msg)
