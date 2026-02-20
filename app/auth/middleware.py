"""Auth middleware - resolve user from token or default."""

import uuid

from app.core.config import settings
from app.auth.jwt import get_user_id_from_token


def resolve_user_id(auth_token: str | None = None) -> uuid.UUID:
    """Resolve user ID from auth_token or fall back to default.

    For development: when auth_token is None/empty, use default_user_id.
    For production: validate token; if invalid, raise or return None (caller decides).
    """
    if auth_token:
        user_id_str = get_user_id_from_token(auth_token)
        if user_id_str:
            try:
                return uuid.UUID(user_id_str)
            except ValueError:
                pass
    return uuid.UUID(settings.default_user_id)
