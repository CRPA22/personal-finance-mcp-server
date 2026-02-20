"""JWT create and validate."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings


def create_token(user_id: str, role: str = "user", extra_claims: dict | None = None) -> str:
    """Create a JWT token for the user."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=settings.jwt_expire_hours)
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "exp": expire,
        "iat": now,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict | None:
    """Decode and validate JWT. Returns payload or None if invalid."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


def get_user_id_from_token(token: str | None) -> str | None:
    """Extract user_id from token. Returns None if token invalid or missing."""
    if not token or not token.strip():
        return None
    payload = decode_token(token.strip())
    if not payload:
        return None
    return payload.get("sub")
