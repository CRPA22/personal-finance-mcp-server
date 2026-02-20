"""Report tools - generate_expense_report, generate_income_expense_report."""

import base64
import json
import uuid
from datetime import date

from fastmcp import FastMCP

from app.core.config import settings
from app.core.exceptions import FinanceMCPError, NotFoundError
from app.db.repositories.account_repository import AccountRepository
from app.db.repositories.transaction_repository import TransactionRepository
from app.db.repositories.user_repository import UserRepository
from app.db.session import session_context
from app.reports.pdf_generator import (
    generate_expense_report_pdf,
    generate_income_expense_report_pdf,
)
from app.reports.report_service import ReportService
from app.utils.errors import error_response
from app.utils.logging import get_logger

logger = get_logger(__name__)


def register_report_tools(mcp: FastMCP) -> None:
    """Register PDF report tools."""

    def _generate_report(
        report_type: str,
        from_date: str,
        to_date: str,
        user_id: str | None = None,
    ) -> str:
        """Common logic for report generation."""
        try:
            uid = uuid.UUID(user_id) if user_id else uuid.UUID(settings.default_user_id)
        except ValueError:
            return error_response("Invalid user_id format. Must be a valid UUID.")

        try:
            fdate = date.fromisoformat(from_date)
            tdate = date.fromisoformat(to_date)
        except ValueError:
            return error_response("Invalid date format. Use YYYY-MM-DD.")

        if fdate > tdate:
            return error_response("from_date must be before or equal to to_date.")

        logger.info(
            f"generate_{report_type}_report",
            extra={"from_date": from_date, "to_date": to_date, "user_id": str(uid)},
        )

        try:
            with session_context() as session:
                account_repo = AccountRepository(session)
                transaction_repo = TransactionRepository(session)
                user_repo = UserRepository(session)
                service = ReportService(account_repo, transaction_repo, user_repo)
                ctx = service.get_report_data(uid, fdate, tdate)

                if report_type == "expense":
                    pdf_bytes = generate_expense_report_pdf(ctx)
                else:
                    pdf_bytes = generate_income_expense_report_pdf(ctx)

                pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")
                return json.dumps({
                    "success": True,
                    "format": "pdf",
                    "base64_content": pdf_b64,
                    "message": "Reporte generado. Decodifica base64_content para obtener el PDF.",
                })

        except NotFoundError as e:
            logger.info("report not found", extra={"detail": str(e)})
            return error_response(str(e))
        except FinanceMCPError as e:
            return error_response(str(e))
        except Exception as e:
            logger.exception("report generation error", extra={"error_type": type(e).__name__})
            return error_response(f"Error generando reporte: {e!s}")

    @mcp.tool()
    def generate_expense_report(
        from_date: str,
        to_date: str,
        user_id: str | None = None,
    ) -> str:
        """Generate expense report PDF: expenses by category, subtotals, pie chart.

        Args:
            from_date: Start date YYYY-MM-DD.
            to_date: End date YYYY-MM-DD.
            user_id: User UUID. If omitted, uses default user.

        Returns:
            JSON with base64_content (PDF), decode and save as .pdf file.
        """
        return _generate_report("expense", from_date, to_date, user_id)

    @mcp.tool()
    def generate_income_expense_report(
        from_date: str,
        to_date: str,
        user_id: str | None = None,
    ) -> str:
        """Generate income/expense report PDF: flow, savings ratio, bar chart.

        Args:
            from_date: Start date YYYY-MM-DD.
            to_date: End date YYYY-MM-DD.
            user_id: User UUID. If omitted, uses default user.

        Returns:
            JSON with base64_content (PDF), decode and save as .pdf file.
        """
        return _generate_report("income_expense", from_date, to_date, user_id)
