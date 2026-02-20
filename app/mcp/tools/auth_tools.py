"""Auth tools - get_token for development testing."""

from fastmcp import FastMCP

from app.auth.jwt import create_token
from app.core.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def register_auth_tools(mcp: FastMCP) -> None:
    """Register auth-related tools."""

    @mcp.tool()
    def get_token(user_id: str | None = None) -> str:
        """Get a JWT token for API access (development/testing).

        In production, use proper login with password verification.
        For dev: returns token for default user if user_id omitted.

        Args:
            user_id: User UUID. If omitted, uses default user.

        Returns:
            JSON with token and expires_in (hours).
        """
        uid = user_id or settings.default_user_id
        token = create_token(uid, role="user")
        logger.info("get_token issued", extra={"user_id": uid})
        import json
        return json.dumps({
            "token": token,
            "expires_in_hours": settings.jwt_expire_hours,
        })
