"""Demo users with roles + signed bearer tokens (stdlib only: scrypt + HMAC-SHA256).

Roles: admin (everything, LLM routing, demo reset) · expert (review, knowledge edits) · analyst (analyses) ·
viewer (read only). `riskminer users seed` creates the four demo accounts; their password comes from env
`DEMO_PASSWORD` (see .env.example; a fixed demo default is used only when DEMO_MODE is on and it is unset).

Token = base64url(json{u, r, n, exp}) + "." + base64url(hmac_sha256(SECRET_KEY, payload)); 12 h validity.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from riskminer.core.config import get_env
from riskminer.ids import make_id
from riskminer.models import User

ROLES = ("admin", "expert", "analyst", "viewer")
DEMO_USERS = [
    ("admin", "Administrator systemu", "admin"),
    ("ekspert", "Ekspert MFiPR", "expert"),
    ("analityk", "Analityk inwestycji", "analyst"),
    ("gosc", "Gość (tylko odczyt)", "viewer"),
]
TOKEN_TTL_S = 12 * 3600
_DEMO_DEFAULT = "demo-riskminer"


class AuthError(ValueError):
    pass


@dataclass
class TokenUser:
    username: str
    role: str
    display_name: str


def demo_password() -> str:
    pw = os.environ.get("DEMO_PASSWORD")
    if pw:
        return pw
    if not get_env().demo_mode:
        raise AuthError("ustaw DEMO_PASSWORD (DEMO_MODE wyłączony)")
    return _DEMO_DEFAULT


def hash_password(password: str, *, n: int = 2**14, r: int = 8, p: int = 1) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p, dklen=32)
    return f"scrypt${n}${r}${p}${_b64(salt)}${_b64(dk)}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored or not stored.startswith("scrypt$"):
        return False
    _, n, r, p, salt, dk = stored.split("$")
    got = hashlib.scrypt(password.encode(), salt=_unb64(salt), n=int(n), r=int(r), p=int(p), dklen=32)
    return hmac.compare_digest(got, _unb64(dk))


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _sign(payload: bytes) -> str:
    return _b64(hmac.new(get_env().secret_key.encode(), payload, hashlib.sha256).digest())


def make_token(user: User | TokenUser, ttl_s: int = TOKEN_TTL_S) -> str:
    payload = json.dumps({"u": user.username, "r": user.role, "n": user.display_name,
                          "exp": int(time.time()) + ttl_s}, separators=(",", ":"), ensure_ascii=False).encode()
    return f"{_b64(payload)}.{_sign(payload)}"


def parse_token(token: str) -> TokenUser:
    try:
        body, sig = token.split(".", 1)
        payload = _unb64(body)
    except ValueError as e:
        raise AuthError("niepoprawny token") from e
    if not hmac.compare_digest(sig, _sign(payload)):
        raise AuthError("niepoprawny podpis tokenu")
    data = json.loads(payload)
    if data.get("exp", 0) < time.time():
        raise AuthError("token wygasł – zaloguj się ponownie")
    if data.get("r") not in ROLES:
        raise AuthError("nieznana rola")
    return TokenUser(username=data["u"], role=data["r"], display_name=data.get("n") or data["u"])


def authenticate(session: Session, username: str, password: str) -> User:
    u = session.execute(select(User).where(User.username == username.strip().lower())).scalars().first()
    if u is None or not u.active or not verify_password(password, u.password_hash):
        raise AuthError("nieprawidłowy login lub hasło")
    return u


def seed_users(session: Session, password: str | None = None) -> list[User]:
    """Create or refresh the 4 demo users (idempotent; resets their password and role)."""
    pw = password or demo_password()
    out = []
    for username, name, role in DEMO_USERS:
        u = session.execute(select(User).where(User.username == username)).scalars().first()
        if u is None:
            u = User(id=make_id("user", username), username=username)
            session.add(u)
        u.display_name, u.role, u.active, u.password_hash = name, role, True, hash_password(pw)
        out.append(u)
    session.flush()
    return out


def demo_role(username: str) -> str:
    """Role for the dev `X-User` header: demo account names map to their role, anyone else is an expert."""
    return {u: r for u, _, r in DEMO_USERS}.get(username, "expert")
