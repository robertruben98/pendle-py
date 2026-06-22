"""Shared request-building and response/error-handling helpers.

These are used by both the sync and async clients so the behaviour (URL
normalization, error detection) is identical.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import httpx

from pendle._errors import PendleAPIError

#: A parsed JSON body: most endpoints return an object, a few (e.g.
#: ``/v1/{chainId}/assets/all``) return a bare array.
JSONResponse = Union[Dict[str, Any], List[Any]]


def normalize_base_url(base_url: str) -> str:
    """Strip a single trailing slash so path joins are predictable."""
    return base_url.rstrip("/")


def build_convert_body(
    *,
    receiver: str,
    slippage: float,
    inputs: List[Dict[str, str]],
    outputs: List[str],
    enable_aggregator: Optional[bool] = None,
    aggregators: Optional[List[str]] = None,
    redeem_rewards: Optional[bool] = None,
    use_limit_order: Optional[bool] = None,
    need_scale: Optional[bool] = None,
    additional_data: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the JSON body for ``POST /v3/sdk/{chainId}/convert``.

    Only the four core fields (``receiver``, ``slippage``, ``inputs``,
    ``outputs``) are always sent; the rest are omitted unless set, so the API's
    own defaults apply. ``extra`` is merged last as an escape hatch for params
    not modelled here.
    """
    body: Dict[str, Any] = {
        "receiver": receiver,
        "slippage": slippage,
        "inputs": inputs,
        "outputs": outputs,
    }
    if enable_aggregator is not None:
        body["enableAggregator"] = enable_aggregator
    if aggregators is not None:
        body["aggregators"] = aggregators
    if redeem_rewards is not None:
        body["redeemRewards"] = redeem_rewards
    if use_limit_order is not None:
        body["useLimitOrder"] = use_limit_order
    if need_scale is not None:
        body["needScale"] = need_scale
    if additional_data is not None:
        body["additionalData"] = additional_data
    if extra:
        body.update(extra)
    return body


def parse_response(response: httpx.Response) -> JSONResponse:
    """Return the parsed JSON body, raising ``PendleAPIError`` on any error.

    Pendle signals errors with a non-2xx HTTP status and a JSON body of the
    shape ``{"message", "error", "statusCode"}``. ``message`` is usually a
    string but is a list of strings for NestJS validation errors; both are
    flattened into the raised exception's ``message``.

    Returns either a ``dict`` (most endpoints) or a ``list`` (e.g.
    ``/v1/{chainId}/assets/all`` returns a bare array).
    """
    data: JSONResponse
    try:
        data = response.json()
    except ValueError:
        # Non-JSON body (e.g. an HTML 5xx page). Surface the status.
        raise PendleAPIError(
            message=response.text or f"HTTP {response.status_code}",
            error=None,
            status_code=response.status_code,
        ) from None

    if response.is_error:
        body = data if isinstance(data, dict) else {}
        raw_message = body.get("message")
        if isinstance(raw_message, list):
            message = "; ".join(str(m) for m in raw_message)
        else:
            message = str(raw_message or "") or f"HTTP {response.status_code}"
        raise PendleAPIError(
            message=message,
            error=body.get("error"),
            status_code=response.status_code,
        )

    return data
