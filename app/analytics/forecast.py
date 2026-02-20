"""Balance forecast - linear regression for 3-month projection."""

from dataclasses import dataclass

from app.analytics.types import AccountRecord, TransactionRecord

from app.analytics.calculator import balance_by_account, monthly_flow


@dataclass
class ForecastPoint:
    """Forecasted balance for a period."""

    period: str  # YYYY-MM
    value: float


@dataclass
class ForecastResult:
    """Forecast result for an account or total."""

    points: list[ForecastPoint]
    slope: float  # per-period change


def forecast_balance(
    accounts: list[AccountRecord],
    transactions: list[TransactionRecord],
    account_id: str | None = None,
    months_ahead: int = 3,
) -> ForecastResult:
    """Project balance for the next N months using linear regression on monthly net flow.

    If account_id is given, forecasts that account only. Otherwise forecasts total.
    """
    flow = monthly_flow(transactions)

    # Filter by account if requested
    if account_id:
        flow_tx = [t for t in transactions if t.account_id == account_id]
        flow = monthly_flow(flow_tx)

    if not flow:
        # No history: use current balance only
        balances = balance_by_account(accounts, transactions)
        if account_id:
            current = balances.get(account_id, 0.0)
        else:
            current = sum(balances.values())
        points = []
        from datetime import date

        base = date.today()
        y, m = base.year, base.month
        for _ in range(months_ahead):
            m += 1
            if m > 12:
                m = 1
                y += 1
            points.append(ForecastPoint(period=f"{y:04d}-{m:02d}", value=current))
        return ForecastResult(points=points, slope=0.0)

    # Build cumulative net per month (simplified: use average net as slope)
    net_values = [f.net for f in flow]
    n = len(net_values)
    avg_net = sum(net_values) / n if n else 0.0

    # Current balance
    balances = balance_by_account(accounts, transactions)
    if account_id:
        current = balances.get(account_id, 0.0)
    else:
        current = sum(balances.values())

    # Generate forecast points
    last = flow[-1]
    points: list[ForecastPoint] = []
    y, m = last.year, last.month
    cum = current
    for _ in range(months_ahead):
        m += 1
        if m > 12:
            m = 1
            y += 1
        cum += avg_net
        points.append(ForecastPoint(period=f"{y:04d}-{m:02d}", value=round(cum, 2)))

    return ForecastResult(points=points, slope=avg_net)
