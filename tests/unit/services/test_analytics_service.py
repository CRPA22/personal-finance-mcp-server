"""Tests for AnalyticsService with mocked repos."""

import uuid
from datetime import date
from unittest.mock import MagicMock

from app.models import Account, Transaction
from app.services.analytics_service import AnalyticsService


def test_analytics_service_get_financial_status() -> None:
    """get_financial_status returns aggregated data."""
    user_id = uuid.uuid4()
    account = MagicMock(spec=Account)
    account.id = uuid.uuid4()
    account.balance = 150.0  # Updated by transaction service after tx

    tx1 = MagicMock(spec=Transaction)
    tx1.amount = 50
    tx1.type = "income"
    tx1.category = "salary"
    tx1.date = date(2025, 1, 15)
    tx1.account_id = account.id

    account_repo = MagicMock()
    account_repo.get_by_user.return_value = [account]

    transaction_repo = MagicMock()
    transaction_repo.get_by_accounts.return_value = [tx1]

    user_repo = MagicMock()

    service = AnalyticsService(account_repo, transaction_repo, user_repo)
    result = service.get_financial_status(user_id)

    assert result.total_balance == 150.0
    assert len(result.monthly_flow) == 1
    assert result.monthly_flow[0].income == 50
    assert result.monthly_flow[0].expense == 0
