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
    """Phase 0 placeholder. S5 replaces this with real demo-user tokens + roles.

    Until then: `X-User: <username>` or anonymous expert.
    """
    name = x_user or "ekspert"
    return CurrentUser(username=name, role="admin" if name == "admin" else "expert", display_name=name)


USER = Depends(current_user)


def not_implemented(owner: str) -> HTTPException:
    return HTTPException(status_code=501, detail=f"Not implemented yet (owner: {owner})")


def require_role(*roles: str):
    def dep(user: CurrentUser = USER) -> CurrentUser:
        if user.role not in roles and user.role != "admin":
            raise HTTPException(403, "Brak uprawnień")
        return user
    return Depends(dep)


__all__ = ["DB", "USER", "CurrentUser", "Session", "not_implemented", "require_role"]
