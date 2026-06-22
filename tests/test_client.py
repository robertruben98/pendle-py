"""Tests for the synchronous PendleClient using respx (no real network)."""

import json
from typing import Iterator

import httpx
import pytest
import respx
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

from pendle import PendleAPIError, PendleClient
from pendle.constants import ChainId


@pytest.fixture
def client() -> Iterator[PendleClient]:
    c = PendleClient()
    yield c
    c.close()


# --- data endpoints ---


@respx.mock
def test_get_markets_paginates(client: PendleClient) -> None:
    route = respx.get(f"{BASE}/v1/1/markets").mock(return_value=httpx.Response(200, json=MARKETS))
    resp = client.get_markets(1, limit=1)
    assert route.called
    assert route.calls.last.request.url.params["limit"] == "1"
    assert resp.total == 469
    assert resp.results[0].pt.symbol == "PT-sUSDS-26NOV2026"


@respx.mock
def test_get_markets_accepts_chain_id_enum(client: PendleClient) -> None:
    respx.get(f"{BASE}/v1/42161/markets").mock(return_value=httpx.Response(200, json=MARKETS))
    client.get_markets(ChainId.ARBITRUM)
    assert respx.calls.last.request.url.path == "/core/v1/42161/markets"


@respx.mock
def test_get_market_detail(client: PendleClient) -> None:
    respx.get(f"{BASE}/v1/1/markets/{MARKET_ADDR}").mock(
        return_value=httpx.Response(200, json=MARKET)
    )
    market = client.get_market(1, MARKET_ADDR)
    assert market.address == MARKET_ADDR
    assert market.sy.symbol == "SY-sUSDS"


@respx.mock
def test_get_active_markets(client: PendleClient) -> None:
    respx.get(f"{BASE}/v1/1/markets/active").mock(return_value=httpx.Response(200, json=ACTIVE))
    resp = client.get_active_markets(1)
    assert resp.markets[0].name == "wstETH"
    assert resp.markets[0].details.implied_apy == 0.0259


@respx.mock
def test_get_assets_returns_list(client: PendleClient) -> None:
    respx.get(f"{BASE}/v1/1/assets/all").mock(return_value=httpx.Response(200, json=ASSETS))
    assets = client.get_assets(1)
    assert isinstance(assets, list)
    assert assets[0].symbol == "PENDLE"


@respx.mock
def test_get_historical_data_passes_time_frame(client: PendleClient) -> None:
    route = respx.get(f"{BASE}/v3/1/markets/{MARKET_ADDR}/historical-data").mock(
        return_value=httpx.Response(200, json=HISTORICAL)
    )
    resp = client.get_historical_data(1, MARKET_ADDR, time_frame="week")
    assert route.calls.last.request.url.params["time_frame"] == "week"
    assert resp.results[0].implied_apy == 0.032


# --- convert / SDK calldata ---


@respx.mock
def test_convert_posts_inputs_outputs(client: PendleClient) -> None:
    route = respx.post(f"{BASE}/v3/sdk/1/convert").mock(
        return_value=httpx.Response(200, json=CONVERT)
    )
    resp = client.convert(
        1,
        receiver=RECEIVER,
        slippage=0.01,
        inputs=[{"token": SY_ADDR, "amount": "1000000000000000000"}],
        outputs=[PT_ADDR],
    )
    assert route.called
    body = json.loads(route.calls.last.request.content)
    assert body["receiver"] == RECEIVER
    assert body["slippage"] == 0.01
    assert body["inputs"] == [{"token": SY_ADDR, "amount": "1000000000000000000"}]
    assert body["outputs"] == [PT_ADDR]
    assert resp.action == "swap"
    assert resp.routes[0].tx.data == "0x2a50917c"


@respx.mock
def test_swap_is_convert_with_single_in_out(client: PendleClient) -> None:
    route = respx.post(f"{BASE}/v3/sdk/1/convert").mock(
        return_value=httpx.Response(200, json=CONVERT)
    )
    resp = client.swap(
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
    assert resp.action == "swap"


@respx.mock
def test_add_liquidity_outputs_the_market(client: PendleClient) -> None:
    route = respx.post(f"{BASE}/v3/sdk/1/convert").mock(
        return_value=httpx.Response(200, json=CONVERT)
    )
    client.add_liquidity(
        1,
        market=MARKET_ADDR,
        token_in=SY_ADDR,
        amount_in="1000000000000000000",
        receiver=RECEIVER,
        slippage=0.01,
    )
    body = json.loads(route.calls.last.request.content)
    assert body["outputs"] == [MARKET_ADDR]
    assert body["inputs"][0]["token"] == SY_ADDR


@respx.mock
def test_remove_liquidity_inputs_the_market(client: PendleClient) -> None:
    route = respx.post(f"{BASE}/v3/sdk/1/convert").mock(
        return_value=httpx.Response(200, json=CONVERT)
    )
    client.remove_liquidity(
        1,
        market=MARKET_ADDR,
        amount_in="1000000000000000000",
        token_out=SY_ADDR,
        receiver=RECEIVER,
        slippage=0.01,
    )
    body = json.loads(route.calls.last.request.content)
    assert body["inputs"] == [{"token": MARKET_ADDR, "amount": "1000000000000000000"}]
    assert body["outputs"] == [SY_ADDR]


@respx.mock
def test_mint_py_outputs_pt_and_yt(client: PendleClient) -> None:
    route = respx.post(f"{BASE}/v3/sdk/1/convert").mock(
        return_value=httpx.Response(200, json=CONVERT)
    )
    client.mint_py(
        1,
        token_in=SY_ADDR,
        amount_in="1000000000000000000",
        pt=PT_ADDR,
        yt="0xyt",
        receiver=RECEIVER,
        slippage=0.01,
    )
    body = json.loads(route.calls.last.request.content)
    assert body["inputs"] == [{"token": SY_ADDR, "amount": "1000000000000000000"}]
    assert body["outputs"] == [PT_ADDR, "0xyt"]


@respx.mock
def test_redeem_py_inputs_pt_and_yt(client: PendleClient) -> None:
    route = respx.post(f"{BASE}/v3/sdk/1/convert").mock(
        return_value=httpx.Response(200, json=CONVERT)
    )
    client.redeem_py(
        1,
        pt=PT_ADDR,
        yt="0xyt",
        amount_in="1000000000000000000",
        token_out=SY_ADDR,
        receiver=RECEIVER,
        slippage=0.01,
    )
    body = json.loads(route.calls.last.request.content)
    assert body["inputs"] == [
        {"token": PT_ADDR, "amount": "1000000000000000000"},
        {"token": "0xyt", "amount": "1000000000000000000"},
    ]
    assert body["outputs"] == [SY_ADDR]


@respx.mock
def test_convert_forwards_optional_flags(client: PendleClient) -> None:
    route = respx.post(f"{BASE}/v3/sdk/1/convert").mock(
        return_value=httpx.Response(200, json=CONVERT)
    )
    client.convert(
        1,
        receiver=RECEIVER,
        slippage=0.01,
        inputs=[{"token": SY_ADDR, "amount": "1"}],
        outputs=[PT_ADDR],
        enable_aggregator=True,
        aggregators=["kyberswap"],
        additional_data="impliedApy,effectiveApy",
    )
    body = json.loads(route.calls.last.request.content)
    assert body["enableAggregator"] is True
    assert body["aggregators"] == ["kyberswap"]
    assert body["additionalData"] == "impliedApy,effectiveApy"


# --- errors / config ---


@respx.mock
def test_400_error_raises_api_error(client: PendleClient) -> None:
    respx.post(f"{BASE}/v3/sdk/1/convert").mock(
        return_value=httpx.Response(
            400,
            json={"message": "Invalid receiver address", "error": "Bad Request", "statusCode": 400},
        )
    )
    with pytest.raises(PendleAPIError) as exc:
        client.convert(1, receiver="0x1", slippage=0.01, inputs=[], outputs=[])
    assert exc.value.status_code == 400
    assert "Invalid receiver" in exc.value.message


@respx.mock
def test_404_on_market_detail(client: PendleClient) -> None:
    respx.get(f"{BASE}/v1/1/markets/0xbad").mock(
        return_value=httpx.Response(
            404, json={"message": "Not Found", "error": "Not Found", "statusCode": 404}
        )
    )
    with pytest.raises(PendleAPIError) as exc:
        client.get_market(1, "0xbad")
    assert exc.value.status_code == 404


@respx.mock
def test_custom_base_url_is_used() -> None:
    custom = "https://my-proxy.example/core"
    respx.get(f"{custom}/v1/1/markets").mock(return_value=httpx.Response(200, json=MARKETS))
    with PendleClient(base_url=custom + "/") as c:  # trailing slash tolerated
        c.get_markets(1)
    assert respx.calls.last.request.url.host == "my-proxy.example"


@respx.mock
def test_context_manager_closes() -> None:
    respx.get(f"{BASE}/v1/1/markets").mock(return_value=httpx.Response(200, json=MARKETS))
    with PendleClient() as c:
        c.get_markets(1)
