"""Tests for pendle pydantic models, built from real API response fixtures."""

from pendle.models import (
    Asset,
    ConvertResponse,
    ConvertRoute,
    HistoricalDataResponse,
    Market,
    MarketsResponse,
    Token,
)

# --- fixtures trimmed from live responses ---

MARKET_JSON = {
    "id": "1-0x9c560ebaf78e596cbcc27411d633a74d628dd7dc",
    "chainId": 1,
    "address": "0x9c560ebaf78e596cbcc27411d633a74d628dd7dc",
    "symbol": "PENDLE-LPT",
    "expiry": "2026-11-26T00:00:00.000Z",
    "pt": {
        "id": "1-0xdc169abe56461a2e0c034da431ac2a3ebf596094",
        "chainId": 1,
        "address": "0xdc169abe56461a2e0c034da431ac2a3ebf596094",
        "symbol": "PT-sUSDS-26NOV2026",
        "decimals": 18,
        "expiry": "2026-11-26T00:00:00.000Z",
        "price": {"usd": 0.9788979497443677},
        "name": "PT-sUSDS-26NOV2026",
        "baseType": "PT",
    },
    "yt": {
        "id": "1-0xc7b8551c6b286ce0b44952320e940bd3dee58a09",
        "chainId": 1,
        "address": "0xc7b8551c6b286ce0b44952320e940bd3dee58a09",
        "symbol": "YT-sUSDS-26NOV2026",
        "decimals": 18,
        "price": {"usd": 0.0207},
        "baseType": "YT",
    },
    "sy": {
        "id": "1-0xbe3d4ec488a0a042bb86f9176c24f8cd54018ba7",
        "chainId": 1,
        "address": "0xbe3d4ec488a0a042bb86f9176c24f8cd54018ba7",
        "symbol": "SY-sUSDS",
        "decimals": 18,
        "price": {"usd": 1.10},
        "baseType": "SY",
    },
    "lp": {
        "id": "1-0x9c560ebaf78e596cbcc27411d633a74d628dd7dc",
        "chainId": 1,
        "address": "0x9c560ebaf78e596cbcc27411d633a74d628dd7dc",
        "symbol": "PLP-sUSDS-26NOV2026",
        "decimals": 18,
        "price": {"usd": 3.08},
        "baseType": "PENDLE_LP",
    },
}

MARKETS_RESPONSE_JSON = {"total": 469, "limit": 1, "skip": 0, "results": [MARKET_JSON]}

ASSET_JSON = {
    "id": "1-0x808507121b80c02388fad14726482e061b8da827",
    "chainId": 1,
    "address": "0x808507121b80c02388fad14726482e061b8da827",
    "symbol": "PENDLE",
    "decimals": 18,
    "price": {"usd": 1.4331215245823112},
    "name": "PENDLE",
    "baseType": "GENERIC",
    "protocol": "Pendle",
}

CONVERT_RESPONSE_JSON = {
    "action": "swap",
    "inputs": [{"token": "0xcbc7", "amount": "1000000000000000000"}],
    "requiredApprovals": [{"token": "0xcbc7", "amount": "1000000000000000000"}],
    "routes": [
        {
            "contractParamInfo": {
                "method": "swapExactSyForPt",
                "contractCallParamsName": ["receiver", "market"],
                "contractCallParams": ["0xdead", "0x3428"],
            },
            "tx": {"data": "0x2a50917c", "to": "0x8888", "from": "0xdead"},
            "outputs": [{"token": "0xb253", "amount": "1285460626110433069"}],
            "data": {
                "aggregatorType": "VOID",
                "priceImpact": -0.0009,
                "priceImpactBreakDown": {
                    "internalPriceImpact": -0.0009,
                    "externalPriceImpact": 0,
                },
                "fee": {"usd": 1.64},
            },
        }
    ],
}

HISTORICAL_JSON = {
    "total": 172,
    "timestamp_start": "2023-05-28T00:00:00.000Z",
    "timestamp_end": "2026-06-22T00:00:00.000Z",
    "results": [
        {
            "timestamp": "2023-05-28T00:00:00.000Z",
            "maxApy": 0.368,
            "baseApy": 0.199,
            "underlyingApy": 0.046,
            "impliedApy": 0.032,
            "tvl": 3630657.25,
        }
    ],
}


def test_token_parses_nested_price() -> None:
    token = Token.model_validate(MARKET_JSON["pt"])
    assert token.symbol == "PT-sUSDS-26NOV2026"
    assert token.decimals == 18
    assert token.price.usd == 0.9788979497443677
    assert token.base_type == "PT"


def test_market_exposes_pt_yt_sy_lp() -> None:
    market = Market.model_validate(MARKET_JSON)
    assert market.address == "0x9c560ebaf78e596cbcc27411d633a74d628dd7dc"
    assert market.chain_id == 1
    assert market.pt.symbol == "PT-sUSDS-26NOV2026"
    assert market.yt.symbol.startswith("YT-")
    assert market.sy.symbol == "SY-sUSDS"
    assert market.lp is not None
    assert market.lp.base_type == "PENDLE_LP"


def test_markets_response_pagination_fields() -> None:
    resp = MarketsResponse.model_validate(MARKETS_RESPONSE_JSON)
    assert resp.total == 469
    assert resp.limit == 1
    assert resp.skip == 0
    assert len(resp.results) == 1
    assert resp.results[0].symbol == "PENDLE-LPT"


def test_asset_parses() -> None:
    asset = Asset.model_validate(ASSET_JSON)
    assert asset.symbol == "PENDLE"
    assert asset.decimals == 18
    assert asset.price.usd == 1.4331215245823112
    assert asset.protocol == "Pendle"


def test_convert_response_parses_action_and_routes() -> None:
    resp = ConvertResponse.model_validate(CONVERT_RESPONSE_JSON)
    assert resp.action == "swap"
    assert resp.inputs[0].amount == "1000000000000000000"
    assert resp.required_approvals[0].token == "0xcbc7"
    assert len(resp.routes) == 1


def test_convert_route_exposes_tx_and_calldata() -> None:
    route = ConvertRoute.model_validate(CONVERT_RESPONSE_JSON["routes"][0])
    assert route.tx.data == "0x2a50917c"
    assert route.tx.to == "0x8888"
    assert route.tx.value is None  # absent for non-native inputs
    assert route.contract_param_info.method == "swapExactSyForPt"
    assert route.outputs[0].amount == "1285460626110433069"
    assert route.data.price_impact == -0.0009
    assert route.data.fee is not None
    assert route.data.fee.usd == 1.64


def test_historical_data_response_parses_timeseries() -> None:
    resp = HistoricalDataResponse.model_validate(HISTORICAL_JSON)
    assert resp.total == 172
    point = resp.results[0]
    assert point.implied_apy == 0.032
    assert point.tvl == 3630657.25
    assert point.max_apy == 0.368


def test_models_tolerate_unknown_fields() -> None:
    # Forward-compat: API adding fields must not break parsing.
    payload = dict(ASSET_JSON, somethingNew="x", anotherNew=123)
    asset = Asset.model_validate(payload)
    assert asset.symbol == "PENDLE"
