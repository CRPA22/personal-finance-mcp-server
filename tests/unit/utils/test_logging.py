"""Tests for logging configuration."""

import logging

import pytest

from app.utils.logging import configure_logging, get_logger, JsonFormatter


def test_get_logger() -> None:
    """get_logger returns a logger with correct name."""
    logger = get_logger("app.test")
    assert logger.name == "app.test"


def test_configure_logging_sets_level() -> None:
    """configure_logging sets root logger level."""
    configure_logging(log_level="WARNING")
    root = logging.getLogger()
    assert root.level == logging.WARNING
    # Restore for other tests
    configure_logging(log_level="INFO")


def test_json_formatter_produces_json() -> None:
    """JsonFormatter outputs valid JSON."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="hello",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    import json
    parsed = json.loads(output)
    assert parsed["level"] == "INFO"
    assert parsed["message"] == "hello"
    assert "timestamp" in parsed
