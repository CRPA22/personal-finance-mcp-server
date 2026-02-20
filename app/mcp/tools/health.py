"""Health check tool - validates server and DB connectivity."""

from fastmcp import FastMCP

from app.utils.logging import get_logger

logger = get_logger(__name__)


def register_health_tools(mcp: FastMCP) -> None:
    """Register health-related tools."""

    @mcp.tool()
    def health_check() -> str:
        """Check server health and database connectivity.
        Returns status message. Use this to verify the MCP server is running correctly.
        """
        try:
            from app.db.session import session_context
            from sqlalchemy import text

            with session_context() as session:
                session.execute(text("SELECT 1"))
            logger.info("health_check", extra={"status": "OK"})
            return "OK: Server and database connection healthy."
        except Exception as e:
            logger.warning("health_check db unreachable", extra={"error": str(e)})
            return f"WARN: Server running but database unreachable: {e!s}"
