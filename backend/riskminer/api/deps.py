from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from riskminer.core.db import get_session

DB = Depends(get_session)


@dataclass
class CurrentUser:
    username: str
    role: str  # admin | expert | analyst | viewer
    display_name: str


def current_user(authorization: str | None = Header(default=None), x_user: str | None = Header(default=None)) -> CurrentUser:
    """Who is calling (S5).

    1. `Authorization: Bearer <token>` from POST /api/auth/login (signed, 12 h) – the normal path.
    2. `X-User: <username>` – developer/test shortcut, accepted only when DEMO_MODE is on; demo account names
       map to their role (admin/ekspert/analityk/gosc), any other name is an expert.
    3. No header: DEMO_MODE → anonymous analyst (the end user: case base + new-investment analyses);
       otherwise a read-only viewer. Expert actions need the expert login (the UI's "Panel eksperta").
    """
    from riskminer.core.config import get_env
    from riskminer.review import auth

    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(401, "Nieobsługiwany nagłówek Authorization (oczekiwano Bearer)")
        try:
            u = auth.parse_token(token.strip())
        except auth.AuthError as e:
            raise HTTPException(401, str(e)) from e
        return CurrentUser(username=u.username, role=u.role, display_name=u.display_name)
    demo = get_env().demo_mode
    if x_user and demo:
        return CurrentUser(username=x_user, role=auth.demo_role(x_user), display_name=x_user)
    if demo:
        return CurrentUser(username="analityk", role="analyst", display_name="Użytkownik (demo)")
    return CurrentUser(username="anonim", role="viewer", display_name="Gość")


USER = Depends(current_user)


def not_implemented(owner: str) -> HTTPException:
    return HTTPException(status_code=501, detail=f"Not implemented yet (owner: {owner})")


def require_role(*roles: str):
    """Allow the given roles (admin always passes). Usage: `user: CurrentUser = require_role("expert")`."""

    def dep(user: CurrentUser = USER) -> CurrentUser:
        if user.role not in roles and user.role != "admin":
            raise HTTPException(403, "Brak uprawnień")
        return user
    return Depends(dep)


EXPERT = require_role("expert")  # expert panel: changes to source data, links, events, knowledge, sources, models

__all__ = ["DB", "USER", "EXPERT", "CurrentUser", "Session", "not_implemented", "require_role"]
