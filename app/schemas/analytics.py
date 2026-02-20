"""Analytics output schemas."""

from pydantic import BaseModel


class BalanceSummarySchema(BaseModel):
    """Total and per-account balance."""

    total: float
    by_account: dict[str, float]


class MonthlyFlowSchema(BaseModel):
    """Monthly income/expense flow."""

    year: int
    month: int
    income: float
    expense: float
    net: float


class CategoryDistributionSchema(BaseModel):
    """Distribution by category."""

    by_category: dict[str, float]
    total: float


class MonthlyTrendSchema(BaseModel):
    """Monthly trend."""

    monthly: list[tuple[str, float]]
    average: float


class ForecastPointSchema(BaseModel):
    """Forecast point."""

    period: str
    value: float


class ForecastSchema(BaseModel):
    """Forecast result."""

    points: list[ForecastPointSchema]
    slope: float


class AnomalyPointSchema(BaseModel):
    """Single anomaly."""

    index: int
    amount: float
    type: str
    category: str
    date: str
    z_score: float
    account_id: str


class AnomaliesSchema(BaseModel):
    """Anomaly detection result."""

    anomalies: list[AnomalyPointSchema]
    threshold: float
    mean: float
    std: float


class FinancialStatusSchema(BaseModel):
    """Aggregated financial status."""

    total_balance: float
    by_account: dict[str, float]
    savings_ratio: float | None
    monthly_flow: list[MonthlyFlowSchema]
    category_distribution: CategoryDistributionSchema
