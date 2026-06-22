"""Tests for the shared transport helpers (URL normalization + error handling)."""

import httpx
import pytest

from pendle import PendleAPIError
from pendle._transport import normalize_base_url, parse_response


def test_normalize_base_url_strips_trailing_slash() -> None:
    assert normalize_base_url("https://api-v2.pendle.finance/core/") == (
        "https://api-v2.pendle.finance/core"
    )


def test_normalize_base_url_leaves_clean_url_untouched() -> None:
    assert normalize_base_url("https://api-v2.pendle.finance/core") == (
        "https://api-v2.pendle.finance/core"
    )


def test_parse_response_returns_dict_body() -> None:
    resp = httpx.Response(200, json={"total": 1, "results": []})
    assert parse_response(resp) == {"total": 1, "results": []}


def test_parse_response_returns_list_body() -> None:
    # /v1/{chainId}/assets/all returns a bare JSON array.
    resp = httpx.Response(200, json=[{"symbol": "PENDLE"}])
    assert parse_response(resp) == [{"symbol": "PENDLE"}]


def test_parse_response_raises_on_400_with_pendle_body() -> None:
    resp = httpx.Response(
        400,
        json={"message": "Invalid receiver address", "error": "Bad Request", "statusCode": 400},
    )
    with pytest.raises(PendleAPIError) as exc:
        parse_response(resp)
    assert exc.value.status_code == 400
    assert exc.value.error == "Bad Request"
    assert exc.value.message == "Invalid receiver address"


def test_parse_response_raises_on_404() -> None:
    resp = httpx.Response(
        404,
        json={"message": "Cannot GET /v1/1/markets/0xbad", "error": "Not Found", "statusCode": 404},
    )
    with pytest.raises(PendleAPIError) as exc:
        parse_response(resp)
    assert exc.value.status_code == 404


def test_parse_response_handles_message_array() -> None:
    # NestJS validation errors return ``message`` as a list of strings.
    resp = httpx.Response(
        400,
        json={
            "message": ["slippage must be a number", "inputs should not be empty"],
            "error": "Bad Request",
            "statusCode": 400,
        },
    )
    with pytest.raises(PendleAPIError) as exc:
        parse_response(resp)
    assert "slippage must be a number" in exc.value.message


def test_parse_response_non_json_error_surfaces_status() -> None:
    resp = httpx.Response(502, text="<html>Bad Gateway</html>")
    with pytest.raises(PendleAPIError) as exc:
        parse_response(resp)
    assert exc.value.status_code == 502
