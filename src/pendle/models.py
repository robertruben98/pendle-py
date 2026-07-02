"""Pydantic models for Pendle Finance v2 API payloads.

These models use ``extra="allow"`` so that fields the API adds over time
(new price sources, APY breakdowns, etc.) do not break parsing. Field names are
snake_case in Python and aliased to the API's camelCase via ``populate_by_name``
+ ``alias``.

On-chain amounts are kept as strings because they routinely exceed the safe
integer range and are returned as decimal strings in wei. Prices and APYs are
floats. Callers convert as needed.
"""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class _Model(BaseModel):
    """Base config shared by every model: alias support + forward-compat.

    ``populate_by_name=True`` lets models be built from either the API's
    camelCase aliases or the snake_case field names, and ``extra="allow"``
    preserves any fields Pendle adds in the future instead of rejecting them.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")


# --- shared ---


class Price(_Model):
    """A token's USD price."""

    usd: Optional[float] = Field(default=None, description="Price of the token in USD.")


class Token(_Model):
    """A Pendle token leg (PT / YT / SY / LP), as embedded in a market.

    The ``base_type`` discriminates the kind: ``"PT"``, ``"YT"``, ``"SY"``,
    ``"PENDLE_LP"``, or ``"GENERIC"`` for plain assets.
    """

    id: str = Field(description="Composite id, e.g. '1-0x...' (chainId-address).")
    chain_id: int = Field(alias="chainId", description="Chain id this token lives on.")
    address: str = Field(description="Token contract address (0x-hex).")
    symbol: str = Field(description="Ticker symbol, e.g. 'PT-sUSDS-26NOV2026'.")
    decimals: Optional[int] = Field(default=None, description="Number of token decimals.")
    expiry: Optional[str] = Field(
        default=None, description="ISO-8601 expiry timestamp (PT/YT/LP); null for SY."
    )
    name: Optional[str] = Field(default=None, description="Full token name.")
    price: Price = Field(default_factory=Price, description="USD price of the token.")
    base_type: Optional[str] = Field(
        default=None,
        alias="baseType",
        description="Token kind: 'PT', 'YT', 'SY', 'PENDLE_LP', or 'GENERIC'.",
    )
    protocol: Optional[str] = Field(
        default=None, description="Underlying protocol name (e.g. 'Sky Protocol'), if known."
    )


# --- /v1/{chainId}/markets and /markets/{address} ---


class Market(_Model):
    """A Pendle market from ``GET /v1/{chainId}/markets`` (and ``/markets/{address}``).

    Bundles the four token legs of a Pendle market: the principal token
    (:attr:`pt`), yield token (:attr:`yt`), standardized-yield wrapper
    (:attr:`sy`), and the LP token (:attr:`lp`).
    """

    id: str = Field(description="Composite market id, '<chainId>-<address>'.")
    chain_id: int = Field(alias="chainId", description="Chain id of the market.")
    address: str = Field(description="Market (LP) contract address.")
    symbol: str = Field(description="Market symbol, e.g. 'PENDLE-LPT'.")
    expiry: Optional[str] = Field(default=None, description="ISO-8601 market expiry timestamp.")
    pt: Token = Field(description="The principal token (PT) of this market.")
    yt: Token = Field(description="The yield token (YT) of this market.")
    sy: Token = Field(description="The standardized-yield (SY) wrapper of this market.")
    lp: Optional[Token] = Field(default=None, description="The LP token of this market.")


class MarketsResponse(_Model):
    """Paginated response of ``GET /v1/{chainId}/markets``."""

    total: int = Field(description="Total number of markets matching the query.")
    limit: int = Field(description="Page size used for this response.")
    skip: int = Field(description="Number of markets skipped (offset).")
    results: List[Market] = Field(default_factory=list, description="The markets on this page.")


# --- /v1/{chainId}/markets/active ---


class ActiveMarketDetails(_Model):
    """The ``details`` block of an active-market entry: liquidity and APYs."""

    liquidity: Optional[float] = Field(default=None, description="Market liquidity in USD.")
    pendle_apy: Optional[float] = Field(
        default=None, alias="pendleApy", description="PENDLE incentive APY (fraction)."
    )
    implied_apy: Optional[float] = Field(
        default=None, alias="impliedApy", description="Market-implied fixed APY (fraction)."
    )
    fee_rate: Optional[float] = Field(
        default=None, alias="feeRate", description="Swap fee rate (fraction)."
    )
    aggregated_apy: Optional[float] = Field(
        default=None, alias="aggregatedApy", description="Aggregated LP APY (fraction)."
    )
    max_boosted_apy: Optional[float] = Field(
        default=None, alias="maxBoostedApy", description="Maximum boosted LP APY (fraction)."
    )


class ActiveMarket(_Model):
    """An entry from ``GET /v1/{chainId}/markets/active``.

    Unlike :class:`Market`, the ``pt``/``yt``/``sy`` fields here are composite
    id strings (``'<chainId>-<address>'``), not nested token objects, and the
    APY/liquidity figures live under :attr:`details`.
    """

    name: str = Field(description="Market display name, e.g. 'wstETH'.")
    address: str = Field(description="Market (LP) contract address.")
    expiry: Optional[str] = Field(default=None, description="ISO-8601 market expiry timestamp.")
    pt: str = Field(description="PT composite id ('<chainId>-<address>').")
    yt: str = Field(description="YT composite id.")
    sy: str = Field(description="SY composite id.")
    underlying_asset: Optional[str] = Field(
        default=None, alias="underlyingAsset", description="Underlying asset composite id."
    )
    details: ActiveMarketDetails = Field(
        default_factory=ActiveMarketDetails,
        description="Liquidity and APY metrics for the market.",
    )
    is_new: Optional[bool] = Field(
        default=None, alias="isNew", description="Whether the market is newly listed."
    )
    is_prime: Optional[bool] = Field(
        default=None, alias="isPrime", description="Whether the market is a 'prime' market."
    )
    category_ids: List[str] = Field(
        default_factory=list, alias="categoryIds", description="Category tags for the market."
    )


class ActiveMarketsResponse(_Model):
    """Response of ``GET /v1/{chainId}/markets/active``."""

    markets: List[ActiveMarket] = Field(
        default_factory=list, description="The chain's currently active markets."
    )


# --- /v1/{chainId}/assets/all ---


class Asset(_Model):
    """Asset metadata from ``GET /v1/{chainId}/assets/all`` (a bare array of these)."""

    id: str = Field(description="Composite asset id, '<chainId>-<address>'.")
    chain_id: int = Field(alias="chainId", description="Chain id of the asset.")
    address: str = Field(description="Asset contract address.")
    symbol: str = Field(description="Ticker symbol, e.g. 'PENDLE'.")
    decimals: Optional[int] = Field(default=None, description="Number of asset decimals.")
    name: Optional[str] = Field(default=None, description="Full asset name.")
    price: Price = Field(default_factory=Price, description="USD price of the asset.")
    base_type: Optional[str] = Field(
        default=None, alias="baseType", description="Asset kind, e.g. 'GENERIC', 'PT', 'SY'."
    )
    protocol: Optional[str] = Field(
        default=None, description="Originating protocol name, if known."
    )


# --- /v3/{chainId}/markets/{address}/historical-data ---


class HistoricalDataPoint(_Model):
    """One time-series sample of a market's APYs and TVL."""

    timestamp: str = Field(description="ISO-8601 timestamp of this sample.")
    max_apy: Optional[float] = Field(
        default=None, alias="maxApy", description="Max LP APY at this time (fraction)."
    )
    base_apy: Optional[float] = Field(
        default=None, alias="baseApy", description="Base LP APY at this time (fraction)."
    )
    underlying_apy: Optional[float] = Field(
        default=None, alias="underlyingApy", description="Underlying-asset APY (fraction)."
    )
    implied_apy: Optional[float] = Field(
        default=None, alias="impliedApy", description="Implied fixed APY (fraction)."
    )
    tvl: Optional[float] = Field(default=None, description="Total value locked in USD.")


class HistoricalDataResponse(_Model):
    """Response of ``GET /v3/{chainId}/markets/{address}/historical-data``."""

    total: int = Field(description="Total number of samples in the range.")
    timestamp_start: Optional[str] = Field(
        default=None, description="ISO-8601 start of the returned range."
    )
    timestamp_end: Optional[str] = Field(
        default=None, description="ISO-8601 end of the returned range."
    )
    results: List[HistoricalDataPoint] = Field(
        default_factory=list, description="The time-series samples."
    )


# --- POST /v3/sdk/{chainId}/convert ---


class TokenAmount(_Model):
    """A token address paired with an amount in wei (decimal string)."""

    token: str = Field(description="Token address (0x-hex).")
    amount: str = Field(description="Amount in the token's smallest unit (wei), as a string.")


class Transaction(_Model):
    """An unsigned EVM transaction to broadcast.

    ``value`` is only present when the input is the chain's native token; it is
    ``None`` otherwise.
    """

    data: str = Field(description="Encoded calldata (0x-hex).")
    to: str = Field(description="Target contract address.")
    from_: Optional[str] = Field(
        default=None, alias="from", description="Sender address (the receiver you passed)."
    )
    value: Optional[str] = Field(
        default=None, description="Native value to send in wei; None for ERC-20 inputs."
    )


class ContractParamInfo(_Model):
    """The decoded router method and its ordered call parameters.

    Useful for inspection/debugging; broadcasting only needs :attr:`Transaction`.
    """

    method: str = Field(description="Router method name, e.g. 'swapExactSyForPt'.")
    contract_call_params_name: List[str] = Field(
        default_factory=list,
        alias="contractCallParamsName",
        description="Ordered names of the call parameters.",
    )
    contract_call_params: List[Any] = Field(
        default_factory=list,
        alias="contractCallParams",
        description="Ordered call parameter values (strings or nested objects).",
    )


class PriceImpactBreakdown(_Model):
    """Internal vs. external (aggregator) components of the price impact."""

    internal_price_impact: Optional[float] = Field(
        default=None,
        alias="internalPriceImpact",
        description="Pendle pool price impact (fraction).",
    )
    external_price_impact: Optional[float] = Field(
        default=None, alias="externalPriceImpact", description="Aggregator price impact (fraction)."
    )


class ImpliedApy(_Model):
    """The market-implied APY before and after the action."""

    before: Optional[float] = Field(default=None, description="Implied APY before the action.")
    after: Optional[float] = Field(default=None, description="Implied APY after the action.")


class FeeUsd(_Model):
    """A fee amount denominated in USD."""

    usd: Optional[float] = Field(default=None, description="Fee in USD.")


class ConvertData(_Model):
    """Economics of a single convert route: price impact, APYs, and fee."""

    aggregator_type: Optional[str] = Field(
        default=None, alias="aggregatorType", description="Aggregator used, or 'VOID' if none."
    )
    price_impact: Optional[float] = Field(
        default=None, alias="priceImpact", description="Total price impact (fraction)."
    )
    price_impact_break_down: Optional[PriceImpactBreakdown] = Field(
        default=None, alias="priceImpactBreakDown", description="Price impact components."
    )
    implied_apy: Optional[ImpliedApy] = Field(
        default=None, alias="impliedApy", description="Implied APY before/after (if requested)."
    )
    effective_apy: Optional[float] = Field(
        default=None,
        alias="effectiveApy",
        description="Effective APY of the action (if requested).",
    )
    fee: Optional[FeeUsd] = Field(default=None, description="Action fee in USD.")


class ConvertRoute(_Model):
    """One executed route of a convert: its tx, outputs, and economics.

    A convert may decompose into multiple routes; each carries its own
    :attr:`tx` to broadcast in order.
    """

    contract_param_info: ContractParamInfo = Field(
        alias="contractParamInfo", description="Decoded router method + params for this route."
    )
    tx: Transaction = Field(description="The unsigned transaction to broadcast for this route.")
    outputs: List[TokenAmount] = Field(
        default_factory=list, description="Token amounts produced by this route."
    )
    data: ConvertData = Field(
        default_factory=ConvertData, description="Economics of this route (impact, fee, APY)."
    )


class ConvertResponse(_Model):
    """Response of ``POST /v3/sdk/{chainId}/convert``.

    Pendle infers the :attr:`action` (``swap``, ``add-liquidity``,
    ``remove-liquidity``, ``mint-py``, ``redeem-py``, etc.) from the input and
    output token kinds, and returns the calldata as one or more
    :attr:`routes`, plus the ERC-20 :attr:`required_approvals` you must grant
    before broadcasting.

    Example::

        resp = client.swap(
            chain_id=1, token_in="0x...sy", token_out="0x...pt",
            amount_in="1000000000000000000", receiver="0xYou", slippage=0.01,
        )
        for approval in resp.required_approvals:
            ...  # approve approval.token for approval.amount
        for route in resp.routes:
            ...  # sign & broadcast route.tx
    """

    action: str = Field(description="Inferred action, e.g. 'swap', 'add-liquidity', 'mint-py'.")
    inputs: List[TokenAmount] = Field(
        default_factory=list, description="Input token amounts for the action."
    )
    required_approvals: List[TokenAmount] = Field(
        default_factory=list,
        alias="requiredApprovals",
        description="ERC-20 approvals to grant before broadcasting.",
    )
    routes: List[ConvertRoute] = Field(
        default_factory=list, description="The route(s) whose transactions perform the action."
    )
    rewards: List[TokenAmount] = Field(
        default_factory=list, description="Reward token amounts (for redeem actions)."
    )


__all__ = [
    "ActiveMarket",
    "ActiveMarketDetails",
    "ActiveMarketsResponse",
    "Asset",
    "ContractParamInfo",
    "ConvertData",
    "ConvertResponse",
    "ConvertRoute",
    "FeeUsd",
    "HistoricalDataPoint",
    "HistoricalDataResponse",
    "ImpliedApy",
    "Market",
    "MarketsResponse",
    "Price",
    "PriceImpactBreakdown",
    "Token",
    "TokenAmount",
    "Transaction",
]
