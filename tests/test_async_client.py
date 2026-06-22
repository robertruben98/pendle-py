"""Tests for the asynchronous AsyncPendleClient using respx (no real network)."""

import json

import httpx
import pytest
import respx

from pendle import AsyncPendleClient, PendleAPIError
from tests.conftest import (
    ACTIVE,
    ASSETS,
    BASE,
    CONVERT,
    HISTORICAL,
    MARKET,
    MARKET_ADDR,
    MARKETS,
    PT_ADDR,
    RECEIVER,
    SY_ADDR,
)


@respx.mock
async def test_get_markets() -> None:
    respx.get(f"{BASE}/v1/1/markets").mock(return_value=httpx.Response(200, json=MARKETS))
    async with AsyncPendleClient() as client:
        resp = await client.get_markets(1, limit=1)
    assert resp.total == 469


@respx.mock
async def test_get_market_detail() -> None:
    respx.get(f"{BASE}/v1/1/markets/{MARKET_ADDR}").mock(
        return_value=httpx.Response(200, json=MARKET)
    )
    async with AsyncPendleClient() as client:
        market = await client.get_market(1, MARKET_ADDR)
    assert market.pt.symbol == "PT-sUSDS-26NOV2026"


@respx.mock
async def test_get_active_markets() -> None:
    respx.get(f"{BASE}/v1/1/markets/active").mock(return_value=httpx.Response(200, json=ACTIVE))
    async with AsyncPendleClient() as client:
        resp = await client.get_active_markets(1)
    assert resp.markets[0].details.implied_apy == 0.0259


@respx.mock
async def test_get_assets() -> None:
    respx.get(f"{BASE}/v1/1/assets/all").mock(return_value=httpx.Response(200, json=ASSETS))
    async with AsyncPendleClient() as client:
        assets = await client.get_assets(1)
    assert assets[0].symbol == "PENDLE"


@respx.mock
async def test_get_historical_data() -> None:
    respx.get(f"{BASE}/v3/1/markets/{MARKET_ADDR}/historical-data").mock(
        return_value=httpx.Response(200, json=HISTORICAL)
    )
    async with AsyncPendleClient() as client:
        resp = await client.get_historical_data(1, MARKET_ADDR, time_frame="day")
    assert resp.results[0].tvl == 3630657.25


@respx.mock
async def test_swap() -> None:
    route = respx.post(f"{BASE}/v3/sdk/1/convert").mock(
        return_value=httpx.Response(200, json=CONVERT)
    )
    async with AsyncPendleClient() as client:
        resp = await client.swap(
            1,
            token_in=SY_ADDR,
            amount_in="1000000000000000000",
            token_out=PT_ADDR,
            receiver=RECEIVER,
            slippage=0.01,
        )
    body = json.loads(route.calls.last.request.content)
    assert body["inputs"] == [{"token": SY_ADDR, "amount": "1000000000000000000"}]
    assert body["outputs"] == [PT_ADDR]
    assert resp.routes[0].tx.to == "0x8888"


@respx.mock
async def test_mint_py() -> None:
    route = respx.post(f"{BASE}/v3/sdk/1/convert").mock(
        return_value=httpx.Response(200, json=CONVERT)
    )
    async with AsyncPendleClient() as client:
        await client.mint_py(
            1,
            token_in=SY_ADDR,
            amount_in="1000000000000000000",
            pt=PT_ADDR,
            yt="0xyt",
            receiver=RECEIVER,
            slippage=0.01,
        )
    body = json.loads(route.calls.last.request.content)
    assert body["outputs"] == [PT_ADDR, "0xyt"]


@respx.mock
async def test_async_error_raises() -> None:
    respx.get(f"{BASE}/v1/1/markets/0xbad").mock(
        return_value=httpx.Response(
            404, json={"message": "Not Found", "error": "Not Found", "statusCode": 404}
        )
    )
    async with AsyncPendleClient() as client:
        with pytest.raises(PendleAPIError):
            await client.get_market(1, "0xbad")
