"""Anomaly detection - Z-score on transaction amounts."""

import math
from dataclasses import dataclass

from app.analytics.types import TransactionRecord


@dataclass
class AnomalyPoint:
    """Single detected anomaly."""

    index: int
    amount: float
    type: str
    category: str
    date: str
    z_score: float
    account_id: str


@dataclass
class AnomalyResult:
    """Result of anomaly detection."""

    anomalies: list[AnomalyPoint]
    threshold: float
    mean: float
    std: float


def detect_anomalies(
    transactions: list[TransactionRecord],
    threshold: float = 3.0,
    account_id: str | None = None,
    transaction_type: str | None = None,
) -> AnomalyResult:
    """Detect anomalies using Z-score. Values beyond mean ± threshold*std are anomalies."""
    filtered = transactions
    if account_id:
        filtered = [t for t in filtered if t.account_id == account_id]
    if transaction_type:
        filtered = [t for t in filtered if t.type == transaction_type]

    if len(filtered) < 2:
        return AnomalyResult(
            anomalies=[],
            threshold=threshold,
            mean=0.0,
            std=0.0,
        )

    amounts = [t.amount for t in filtered]
    mean = sum(amounts) / len(amounts)
    variance = sum((x - mean) ** 2 for x in amounts) / len(amounts)
    std = math.sqrt(variance) if variance > 0 else 0.0

    anomalies: list[AnomalyPoint] = []
    for i, tx in enumerate(filtered):
        if std == 0:
            z = 0.0
        else:
            z = (tx.amount - mean) / std
        if abs(z) >= threshold:
            anomalies.append(
                AnomalyPoint(
                    index=i,
                    amount=tx.amount,
                    type=tx.type,
                    category=tx.category,
                    date=tx.date.isoformat(),
                    z_score=round(z, 2),
                    account_id=tx.account_id,
                )
            )

    return AnomalyResult(
        anomalies=anomalies,
        threshold=threshold,
        mean=round(mean, 2),
        std=round(std, 2),
    )
