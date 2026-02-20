"""Tests for ReportService."""

import uuid
from datetime import date
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.models import Account, Transaction
from app.reports.report_service import ReportService


def test_report_service_get_report_data_success() -> None:
    """get_report_data returns ReportContext with grouped data."""
    user_id = uuid.uuid4()
    account_id = uuid.uuid4()
    user = MagicMock()
    user.email = "test@example.com"

    account = MagicMock(spec=Account)
    account.id = account_id
    account.name = "Main"
    account.type = "checking"
    account.currency = "USD"
    account.balance = 100.0

    tx = MagicMock(spec=Transaction)
    tx.account_id = account_id
    tx.date = date(2025, 1, 15)
    tx.description = "Test"
    tx.category = "comida"
    tx.amount = 25.0
    tx.type = "expense"

    user_repo = MagicMock()
    user_repo.get_by_id.return_value = user
    account_repo = MagicMock()
    account_repo.get_by_user.return_value = [account]
    transaction_repo = MagicMock()
    transaction_repo.get_by_accounts.return_value = [tx]

    service = ReportService(account_repo, transaction_repo, user_repo)
    ctx = service.get_report_data(user_id, date(2025, 1, 1), date(2025, 1, 31))

    assert ctx.user_name == "test@example.com"
    assert ctx.from_date == date(2025, 1, 1)
    assert ctx.to_date == date(2025, 1, 31)
    assert "USD" in ctx.by_currency
    usd_data = ctx.by_currency["USD"]
    assert len(usd_data.accounts) == 1
    assert usd_data.accounts[0].name == "Main"
    assert len(usd_data.transactions) == 1
    assert usd_data.transactions[0].category == "comida"
    assert usd_data.total_expenses == 25.0


def test_report_service_user_not_found() -> None:
    """get_report_data raises NotFoundError when user does not exist."""
    user_repo = MagicMock()
    user_repo.get_by_id.return_value = None
    account_repo = MagicMock()
    transaction_repo = MagicMock()

    service = ReportService(account_repo, transaction_repo, user_repo)

    with pytest.raises(NotFoundError, match="User .* not found"):
        service.get_report_data(uuid.uuid4(), date(2025, 1, 1), date(2025, 1, 31))
