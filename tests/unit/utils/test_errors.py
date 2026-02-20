"""Tests for error utilities."""

import json

from app.utils.errors import error_response


def test_error_response_basic() -> None:
    """error_response returns valid JSON with error key."""
    result = error_response("Something went wrong")
    parsed = json.loads(result)
    assert parsed["error"] == "Something went wrong"
    assert "details" not in parsed


def test_error_response_with_details() -> None:
    """error_response includes details when provided."""
    details = [{"loc": ["field"], "msg": "required"}]
    result = error_response("Validation failed", details=details)
    parsed = json.loads(result)
    assert parsed["error"] == "Validation failed"
    assert parsed["details"] == details
