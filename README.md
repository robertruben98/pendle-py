# pendle-py

[![CI](https://github.com/robertruben98/pendle-py/actions/workflows/ci.yml/badge.svg)](https://github.com/robertruben98/pendle-py/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/pendle-py.svg)](https://pypi.org/project/pendle-py/)
[![Python versions](https://img.shields.io/pypi/pyversions/pendle-py.svg)](https://pypi.org/project/pendle-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/robertruben98/pendle-py/blob/main/LICENSE)

Typed Python client for the [Pendle Finance v2 API](https://api-v2.pendle.finance/core/docs).
Read PT/YT/SY/LP markets, asset metadata and APY history, and build swap / liquidity /
mint / redeem **calldata** — sync **and** async, with full type hints (`py.typed`),
built on `httpx` + `pydantic v2`.

The API is public and keyless. Signing and broadcasting the returned transaction is
left to you (optionally with the `[exec]` extra, which pulls in `web3.py`).

## Install

```bash
pip install pendle-py
# optional signing/broadcasting helpers:
pip install "pendle-py[exec]"
```

## Quickstart

List active Ethereum markets with their implied APY in a few lines:

```python
from pendle import PendleClient
from pendle.constants import ChainId

with PendleClient() as client:
    active = client.get_active_markets(ChainId.ETHEREUM)
    for m in active.markets[:5]:
        implied = (m.details.implied_apy or 0) * 100
        print(f"{m.name:<12} implied APY {implied:5.2f}%  liquidity ${m.details.liquidity:,.0f}")
```

### Build swap calldata

`convert` is Pendle's universal calldata endpoint; `swap` / `add_liquidity` /
`remove_liquidity` / `mint_py` / `redeem_py` are ergonomic wrappers over it. The
returned `action` (e.g. `"swap"`) is inferred from the tokens you pass.

```python
with PendleClient() as client:
    market = client.get_markets(ChainId.ETHEREUM, limit=1).results[0]

    resp = client.swap(
        ChainId.ETHEREUM,
        token_in=market.sy.address,        # spend SY
        amount_in="1000000000000000000",   # 1.0 (18 decimals), in wei
        token_out=market.pt.address,       # receive PT
        receiver="0xYourAddress",
        slippage=0.01,                     # 1%
    )

    print(resp.action)                     # "swap"
    for approval in resp.required_approvals:
        ...                                # grant ERC-20 approval first
    tx = resp.routes[0].tx                 # unsigned tx to sign & broadcast
    print(tx.to, tx.data, tx.value)
```

### Async

```python
import asyncio
from pendle import AsyncPendleClient

async def main():
    async with AsyncPendleClient() as client:
        markets = await client.get_markets(1, limit=5)
        print(markets.total)

asyncio.run(main())
```

## API surface

| Method | Endpoint | Returns |
| --- | --- | --- |
| `get_markets(chain_id, limit=, skip=)` | `GET /v1/{chainId}/markets` | `MarketsResponse` |
| `get_market(chain_id, address)` | `GET /v1/{chainId}/markets/{address}` | `Market` |
| `get_active_markets(chain_id)` | `GET /v1/{chainId}/markets/active` | `ActiveMarketsResponse` |
| `get_assets(chain_id)` | `GET /v1/{chainId}/assets/all` | `list[Asset]` |
| `get_historical_data(chain_id, address, time_frame=)` | `GET /v3/{chainId}/markets/{address}/historical-data` | `HistoricalDataResponse` |
| `convert(chain_id, *, receiver, slippage, inputs, outputs, ...)` | `POST /v3/sdk/{chainId}/convert` | `ConvertResponse` |
| `swap` / `add_liquidity` / `remove_liquidity` / `mint_py` / `redeem_py` | (wrappers over `convert`) | `ConvertResponse` |

All methods exist on both `PendleClient` (sync) and `AsyncPendleClient` (async).
Every chain-id argument accepts a plain `int` or a `pendle.constants.ChainId` member.

> **Note on the SDK endpoint.** Pendle consolidated its per-action SDK routes
> (separate swap / add-liquidity / mint / redeem endpoints) into a single
> `POST /v3/sdk/{chainId}/convert`. This library exposes that endpoint directly
> as `convert()` and adds the named wrappers above for convenience.

## Errors

Every method raises `PendleAPIError` (a subclass of `PendleError`) on a non-2xx
response, exposing `.status_code`, `.error` and `.message`:

```python
from pendle import PendleClient, PendleAPIError

with PendleClient() as client:
    try:
        client.get_market(1, "0xnot-a-market")
    except PendleAPIError as exc:
        print(exc.status_code, exc.message)   # 404 'Not Found'
```

Network-level failures propagate as `httpx` exceptions.

## Configuration

```python
# Custom base URL (e.g. a proxy) and timeout, or inject your own httpx client:
PendleClient(base_url="https://my-proxy.example/core", timeout=15.0)
PendleClient(client=my_httpx_client)   # caller owns its lifecycle
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md). In short:

```bash
uv venv --python 3.9 && source .venv/bin/activate
uv pip install -e ".[dev]"
ruff check . && ruff format --check . && mypy && pytest
```

Live integration tests are marked `integration` and deselected by default; run
them with `pytest -m integration`.

## License

MIT — see [LICENSE](LICENSE).
