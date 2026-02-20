"""FastMCP server - Personal Finance MCP Server."""

from fastmcp import FastMCP

from app.mcp.tools.accounts import register_account_tools
from app.mcp.tools.auth_tools import register_auth_tools
from app.utils.logging import configure_logging, get_logger
from app.mcp.tools.analysis import register_analysis_tools
from app.mcp.tools.health import register_health_tools
from app.mcp.tools.status import register_status_tools
from app.mcp.tools.transactions import register_transaction_tools

mcp = FastMCP(
    "Personal Finance MCP Server",
    instructions="MCP server for personal finance: accounts, transactions, analytics.",
)

register_health_tools(mcp)
register_auth_tools(mcp)
register_account_tools(mcp)
register_transaction_tools(mcp)
register_status_tools(mcp)
register_analysis_tools(mcp)


def main() -> None:
    """Entry point for running the MCP server."""
    configure_logging()
    logger = get_logger(__name__)
    logger.info("Starting Personal Finance MCP Server")
    mcp.run()


if __name__ == "__main__":
    main()
