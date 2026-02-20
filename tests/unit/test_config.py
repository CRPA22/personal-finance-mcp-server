"""Tests for configuration."""

import pytest

from app.core.config import settings


def test_settings_loads() -> None:
    """Settings loads with defaults."""
    assert settings.database_url.startswith("postgresql://")
    assert settings.log_level == "INFO"
