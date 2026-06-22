# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0]

Initial release. Not yet published to PyPI.

### Added

- `PendleClient` (sync) and `AsyncPendleClient` (async) for the Pendle Finance
  v2 API, built on `httpx`, usable as (async) context managers.
- Data endpoints: `get_markets` (`/v1/{chainId}/markets`), `get_market`,
  `get_active_markets`, `get_assets` (`/v1/{chainId}/assets/all`), and
  `get_historical_data` (`/v3/{chainId}/markets/{address}/historical-data`) for
  APY/TVL time series.
- Calldata via Pendle's universal `convert` endpoint
  (`POST /v3/sdk/{chainId}/convert`), plus ergonomic `swap`, `add_liquidity`,
  `remove_liquidity`, `mint_py` and `redeem_py` wrappers. The response exposes
  the inferred `action`, ERC-20 `required_approvals`, and per-route `tx`
  calldata to sign and broadcast.
- Typed pydantic v2 models with forward-compatible parsing (`extra="allow"`),
  shipped with `py.typed`.
- `ChainId` enum covering the chains Pendle supports, plus `DEFAULT_BASE_URL`,
  in `pendle.constants`.
- `PendleError` / `PendleAPIError`, surfacing `status_code`, `error` and
  `message` (including NestJS list-style validation messages).
- Optional `[exec]` extra (`web3`) for signing/broadcasting the returned tx.
- Sync and async usage examples, README quickstart, and GitHub Actions CI
  (lint + test matrix on Python 3.9–3.13).

[Unreleased]: https://github.com/robertruben98/pendle-py/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/robertruben98/pendle-py/releases/tag/v0.1.0
