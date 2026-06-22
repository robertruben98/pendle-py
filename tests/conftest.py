"""Shared test fixtures: response payloads trimmed from live Pendle responses."""

BASE = "https://api-v2.pendle.finance/core"

PT_ADDR = "0xb253eff1104802b97ac7e3ac9fdd73aece295a2c"
SY_ADDR = "0xcbc72d92b2dc8187414f6734718563898740c0bc"
MARKET_ADDR = "0x34280882267ffa6383b363e278b027be083bbe3b"
RECEIVER = "0x000000000000000000000000000000000000dEaD"

TOKEN = {
    "id": "1-" + PT_ADDR,
    "chainId": 1,
    "address": PT_ADDR,
    "symbol": "PT-sUSDS-26NOV2026",
    "decimals": 18,
    "price": {"usd": 0.97},
    "baseType": "PT",
}

MARKET = {
    "id": "1-" + MARKET_ADDR,
    "chainId": 1,
    "address": MARKET_ADDR,
    "symbol": "PENDLE-LPT",
    "expiry": "2026-11-26T00:00:00.000Z",
    "pt": TOKEN,
    "yt": dict(TOKEN, symbol="YT-sUSDS-26NOV2026", baseType="YT"),
    "sy": dict(TOKEN, symbol="SY-sUSDS", baseType="SY", expiry=None),
    "lp": dict(TOKEN, symbol="PLP-sUSDS-26NOV2026", baseType="PENDLE_LP"),
}

MARKETS = {"total": 469, "limit": 1, "skip": 0, "results": [MARKET]}

ACTIVE = {
    "markets": [
        {
            "name": "wstETH",
            "address": MARKET_ADDR,
            "expiry": "2027-12-30T00:00:00.000Z",
            "pt": "1-" + PT_ADDR,
            "yt": "1-0x04",
            "sy": "1-" + SY_ADDR,
            "underlyingAsset": "1-0x7f",
            "details": {
                "liquidity": 2877000.44,
                "pendleApy": 0.0108,
                "impliedApy": 0.0259,
                "feeRate": 0.0005,
                "aggregatedApy": 0.0347,
                "maxBoostedApy": 0.051,
            },
            "isNew": False,
            "isPrime": True,
            "categoryIds": ["eth", "lido"],
        }
    ]
}

ASSETS = [
    {
        "id": "1-0x808507121b80c02388fad14726482e061b8da827",
        "chainId": 1,
        "address": "0x808507121b80c02388fad14726482e061b8da827",
        "symbol": "PENDLE",
        "decimals": 18,
        "price": {"usd": 1.43},
        "name": "PENDLE",
        "baseType": "GENERIC",
        "protocol": "Pendle",
    }
]

HISTORICAL = {
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

CONVERT = {
    "action": "swap",
    "inputs": [{"token": SY_ADDR, "amount": "1000000000000000000"}],
    "requiredApprovals": [{"token": SY_ADDR, "amount": "1000000000000000000"}],
    "routes": [
        {
            "contractParamInfo": {
                "method": "swapExactSyForPt",
                "contractCallParamsName": ["receiver", "market"],
                "contractCallParams": [RECEIVER, MARKET_ADDR],
            },
            "tx": {"data": "0x2a50917c", "to": "0x8888", "from": RECEIVER},
            "outputs": [{"token": PT_ADDR, "amount": "1285460626110433069"}],
            "data": {
                "aggregatorType": "VOID",
                "priceImpact": -0.0009,
                "priceImpactBreakDown": {"internalPriceImpact": -0.0009, "externalPriceImpact": 0},
                "fee": {"usd": 1.64},
            },
        }
    ],
}
