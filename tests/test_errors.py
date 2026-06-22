"""Tests for the pendle exception hierarchy."""

import pytest

from pendle import PendleAPIError, PendleError


def test_api_error_is_a_pendle_error() -> None:
    err = PendleAPIError(message="boom", status_code=400, error="Bad Request")
    assert isinstance(err, PendleError)


def test_api_error_str_includes_status_and_message() -> None:
    err = PendleAPIError(message="Invalid receiver address", status_code=400, error="Bad Request")
    text = str(err)
    assert "400" in text
    assert "Invalid receiver address" in text


def test_api_error_exposes_attributes() -> None:
    err = PendleAPIError(message="not found", status_code=404, error="Not Found")
    assert err.status_code == 404
    assert err.error == "Not Found"
    assert err.message == "not found"


def test_pendle_error_is_an_exception() -> None:
    with pytest.raises(PendleError):
        raise PendleError("generic")
