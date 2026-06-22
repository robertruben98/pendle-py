"""Synchronous and asynchronous clients for the Pendle Finance v2 API."""

from __future__ import annotations

from types import TracebackType
from typing import Any, Dict, List, Optional, Type, cast

import httpx

from pendle._transport import (
    JSONResponse,
    build_convert_body,
    normalize_base_url,
    parse_response,
)
from pendle.constants import DEFAULT_BASE_URL
from pendle.models import (
    ActiveMarketsResponse,
    Asset,
    ConvertResponse,
    HistoricalDataResponse,
    Market,
    MarketsResponse,
)


class _BaseClient:
    """Shared configuration for the sync/async clients."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        self.base_url = normalize_base_url(base_url)

    # -- shared request shaping (VM-agnostic, no I/O) --

    def _markets_params(self, limit: Optional[int], skip: Optional[int]) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = str(int(limit))
        if skip is not None:
            params["skip"] = str(int(skip))
        return params

    def _historical_params(
        self,
        time_frame: str,
        timestamp_start: Optional[str],
        timestamp_end: Optional[str],
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"time_frame": time_frame}
        if timestamp_start is not None:
            params["timestamp_start"] = timestamp_start
        if timestamp_end is not None:
            params["timestamp_end"] = timestamp_end
        return params


class PendleClient(_BaseClient):
    """Synchronous client for the Pendle Finance v2 API.

    Wraps the public, keyless endpoints: market/asset data, APY history, and the
    universal ``convert`` calldata endpoint (with ergonomic ``swap`` /
    ``add_liquidity`` / ``remove_liquidity`` / ``mint_py`` / ``redeem_py``
    wrappers). Every method raises :class:`PendleAPIError` on an API error.

    Use it as a context manager so the underlying ``httpx`` connection pool is
    closed for you; otherwise call :meth:`close` when done.

    Example::

        from pendle import PendleClient
        from pendle.constants import ChainId

        with PendleClient() as client:
            markets = client.get_active_markets(ChainId.ETHEREUM)
            for m in markets.markets[:5]:
                print(m.name, m.details.implied_apy)
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        timeout: float = 30.0,
        client: Optional[httpx.Client] = None,
    ) -> None:
        """Create a synchronous client.

        Args:
            base_url: Pendle Core API base URL. Defaults to the public endpoint
                (:data:`pendle.constants.DEFAULT_BASE_URL`); a trailing slash is
                tolerated. Point this at a compatible proxy if needed.
            timeout: Per-request timeout in seconds, applied when this client
                creates its own ``httpx.Client``. Ignored if ``client`` is given.
            client: An existing ``httpx.Client`` to reuse. When supplied, the
                caller owns its lifecycle and :meth:`close` will not close it.
        """
        super().__init__(base_url)
        self._client = client or httpx.Client(timeout=timeout)
        self._owns_client = client is None

    # -- lifecycle --

    def close(self) -> None:
        """Close the underlying HTTP client.

        No-op when an external ``httpx.Client`` was injected via the constructor
        (the caller owns that client's lifecycle).
        """
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> PendleClient:
        """Enter the runtime context and return this client."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        """Exit the runtime context, closing the client via :meth:`close`."""
        self.close()

    # -- internal --

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> JSONResponse:
        response = self._client.get(f"{self.base_url}{path}", params=params)
        return parse_response(response)

    def _post(self, path: str, json_body: Dict[str, Any]) -> JSONResponse:
        response = self._client.post(f"{self.base_url}{path}", json=json_body)
        return parse_response(response)

    # -- data endpoints --

    def get_markets(
        self,
        chain_id: int,
        *,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
    ) -> MarketsResponse:
        """Fetch the (paginated) list of markets on a chain.

        Calls ``GET /v1/{chainId}/markets``.

        Args:
            chain_id: Chain id (an ``int`` or a :class:`pendle.constants.ChainId`).
            limit: Page size. Omit to use the API default.
            skip: Number of markets to skip (offset pagination).

        Returns:
            A :class:`MarketsResponse` with ``total``/``limit``/``skip`` and the
            page of :class:`pendle.models.Market` entries (each with its PT, YT,
            SY and LP token legs).

        Raises:
            PendleAPIError: If the API returns an error.
        """
        data = self._get(f"/v1/{int(chain_id)}/markets", params=self._markets_params(limit, skip))
        return MarketsResponse.model_validate(data)

    def get_market(self, chain_id: int, address: str) -> Market:
        """Fetch detail for a single market.

        Calls ``GET /v1/{chainId}/markets/{address}``.

        Args:
            chain_id: Chain id (int or ``ChainId``).
            address: Market (LP) contract address.

        Returns:
            A :class:`pendle.models.Market`.

        Raises:
            PendleAPIError: If the market is unknown or the address is malformed.
        """
        data = self._get(f"/v1/{int(chain_id)}/markets/{address}")
        return Market.model_validate(data)

    def get_active_markets(self, chain_id: int) -> ActiveMarketsResponse:
        """Fetch the chain's active markets with liquidity and APY metrics.

        Calls ``GET /v1/{chainId}/markets/active``.

        Args:
            chain_id: Chain id (int or ``ChainId``).

        Returns:
            An :class:`ActiveMarketsResponse`; each entry exposes implied/pendle
            APY and liquidity under ``details``.

        Raises:
            PendleAPIError: If the API returns an error.
        """
        data = self._get(f"/v1/{int(chain_id)}/markets/active")
        return ActiveMarketsResponse.model_validate(data)

    def get_assets(self, chain_id: int) -> List[Asset]:
        """Fetch metadata for every asset Pendle knows about on a chain.

        Calls ``GET /v1/{chainId}/assets/all`` (which returns a bare array).

        Args:
            chain_id: Chain id (int or ``ChainId``).

        Returns:
            A list of :class:`pendle.models.Asset`.

        Raises:
            PendleAPIError: If the API returns an error.
        """
        data = self._get(f"/v1/{int(chain_id)}/assets/all")
        items = cast(List[Any], data)
        return [Asset.model_validate(item) for item in items]

    def get_historical_data(
        self,
        chain_id: int,
        address: str,
        *,
        time_frame: str = "day",
        timestamp_start: Optional[str] = None,
        timestamp_end: Optional[str] = None,
    ) -> HistoricalDataResponse:
        """Fetch a market's APY/TVL time series.

        Calls ``GET /v3/{chainId}/markets/{address}/historical-data``.

        Args:
            chain_id: Chain id (int or ``ChainId``).
            address: Market (LP) contract address.
            time_frame: Sample granularity: ``"hour"``, ``"day"`` (default), or
                ``"week"``.
            timestamp_start: ISO-8601 start of the range (optional).
            timestamp_end: ISO-8601 end of the range (optional).

        Returns:
            A :class:`HistoricalDataResponse` of
            :class:`pendle.models.HistoricalDataPoint` samples (max/base/implied
            APY and TVL).

        Raises:
            PendleAPIError: If the API returns an error.
        """
        data = self._get(
            f"/v3/{int(chain_id)}/markets/{address}/historical-data",
            params=self._historical_params(time_frame, timestamp_start, timestamp_end),
        )
        return HistoricalDataResponse.model_validate(data)

    # -- SDK / calldata --

    def convert(
        self,
        chain_id: int,
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
    ) -> ConvertResponse:
        """Build calldata for any Pendle action via the universal convert endpoint.

        Calls ``POST /v3/sdk/{chainId}/convert``. Pendle infers the action
        (swap, add/remove-liquidity, mint/redeem PY, etc.) from the kinds of the
        ``inputs`` and ``outputs`` tokens. For common actions prefer the
        higher-level :meth:`swap`, :meth:`add_liquidity`,
        :meth:`remove_liquidity`, :meth:`mint_py` and :meth:`redeem_py` wrappers.

        Args:
            chain_id: Chain id (int or ``ChainId``).
            receiver: Address that receives the output (must be a valid address;
                the API rejects placeholders such as ``0x...01``).
            slippage: Max slippage as a fraction in ``[0, 1]`` (``0.01`` = 1%).
            inputs: Input tokens as ``[{"token": addr, "amount": wei_str}, ...]``.
            outputs: Output token addresses (the asset(s) you want to receive).
            enable_aggregator: Allow an external swap aggregator for tokens that
                can't be natively converted.
            aggregators: Restrict to these aggregator names (see
                ``GET /v1/sdk/{chainId}/supported-aggregators``).
            redeem_rewards: Also redeem accrued rewards (for redeem actions).
            use_limit_order: Use the limit-order book when converting (API
                default is ``True``).
            need_scale: Set ``True`` only when amounts were updated on-chain;
                buffer ``amountIn`` by ~2% when enabling.
            additional_data: Comma-separated extra fields to compute, e.g.
                ``"impliedApy,effectiveApy"``.
            extra: Additional raw body fields, merged last (escape hatch).

        Returns:
            A :class:`ConvertResponse` with the inferred ``action``,
            ``required_approvals`` to grant, and the ``routes`` whose ``tx``
            calldata performs the action.

        Raises:
            PendleAPIError: If the API rejects the request (bad token pair,
                invalid receiver, etc.).

        Example:
            Swap 1 SY for PT on Ethereum::

                resp = client.convert(
                    1,
                    receiver="0xYourAddress",
                    slippage=0.01,
                    inputs=[{"token": SY, "amount": "1000000000000000000"}],
                    outputs=[PT],
                )
                tx = resp.routes[0].tx          # sign & broadcast
                print(resp.action)              # "swap"
        """
        body = build_convert_body(
            receiver=receiver,
            slippage=slippage,
            inputs=inputs,
            outputs=outputs,
            enable_aggregator=enable_aggregator,
            aggregators=aggregators,
            redeem_rewards=redeem_rewards,
            use_limit_order=use_limit_order,
            need_scale=need_scale,
            additional_data=additional_data,
            extra=extra,
        )
        data = self._post(f"/v3/sdk/{int(chain_id)}/convert", body)
        return ConvertResponse.model_validate(data)

    def swap(
        self,
        chain_id: int,
        *,
        token_in: str,
        amount_in: str,
        token_out: str,
        receiver: str,
        slippage: float,
        **kwargs: Any,
    ) -> ConvertResponse:
        """Build calldata to swap ``amount_in`` of ``token_in`` into ``token_out``.

        Thin wrapper over :meth:`convert` with a single input and output (e.g.
        token -> PT, PT -> token, token -> YT). Extra keyword args are forwarded
        to :meth:`convert` (e.g. ``enable_aggregator=True``).

        Args:
            chain_id: Chain id (int or ``ChainId``).
            token_in: Address of the token you are spending.
            amount_in: Amount of ``token_in`` in wei (decimal string).
            token_out: Address of the token you want to receive.
            receiver: Address that receives ``token_out``.
            slippage: Max slippage fraction in ``[0, 1]``.

        Returns:
            A :class:`ConvertResponse` (``action == "swap"``).

        Raises:
            PendleAPIError: If the API rejects the request.
        """
        return self.convert(
            chain_id,
            receiver=receiver,
            slippage=slippage,
            inputs=[{"token": token_in, "amount": amount_in}],
            outputs=[token_out],
            **kwargs,
        )

    def add_liquidity(
        self,
        chain_id: int,
        *,
        market: str,
        token_in: str,
        amount_in: str,
        receiver: str,
        slippage: float,
        **kwargs: Any,
    ) -> ConvertResponse:
        """Build calldata to add liquidity to ``market`` with ``token_in``.

        Thin wrapper over :meth:`convert` whose output is the market (LP) token.

        Args:
            chain_id: Chain id (int or ``ChainId``).
            market: Market (LP) contract address — the LP token you receive.
            token_in: Address of the token you are depositing.
            amount_in: Amount of ``token_in`` in wei (decimal string).
            receiver: Address that receives the LP token.
            slippage: Max slippage fraction in ``[0, 1]``.

        Returns:
            A :class:`ConvertResponse` (``action == "add-liquidity"``).

        Raises:
            PendleAPIError: If the API rejects the request.
        """
        return self.convert(
            chain_id,
            receiver=receiver,
            slippage=slippage,
            inputs=[{"token": token_in, "amount": amount_in}],
            outputs=[market],
            **kwargs,
        )

    def remove_liquidity(
        self,
        chain_id: int,
        *,
        market: str,
        amount_in: str,
        token_out: str,
        receiver: str,
        slippage: float,
        **kwargs: Any,
    ) -> ConvertResponse:
        """Build calldata to remove liquidity from ``market`` into ``token_out``.

        Thin wrapper over :meth:`convert` whose input is the market (LP) token.

        Args:
            chain_id: Chain id (int or ``ChainId``).
            market: Market (LP) contract address — the LP token you burn.
            amount_in: Amount of LP token to remove, in wei (decimal string).
            token_out: Address of the token you want to receive.
            receiver: Address that receives ``token_out``.
            slippage: Max slippage fraction in ``[0, 1]``.

        Returns:
            A :class:`ConvertResponse` (``action == "remove-liquidity"``).

        Raises:
            PendleAPIError: If the API rejects the request.
        """
        return self.convert(
            chain_id,
            receiver=receiver,
            slippage=slippage,
            inputs=[{"token": market, "amount": amount_in}],
            outputs=[token_out],
            **kwargs,
        )

    def mint_py(
        self,
        chain_id: int,
        *,
        token_in: str,
        amount_in: str,
        pt: str,
        yt: str,
        receiver: str,
        slippage: float,
        **kwargs: Any,
    ) -> ConvertResponse:
        """Build calldata to mint PT + YT from ``token_in``.

        Thin wrapper over :meth:`convert` whose outputs are the PT and YT.

        Args:
            chain_id: Chain id (int or ``ChainId``).
            token_in: Address of the token you are depositing (SY or underlying).
            amount_in: Amount of ``token_in`` in wei (decimal string).
            pt: Principal-token address to receive.
            yt: Yield-token address to receive.
            receiver: Address that receives the PT and YT.
            slippage: Max slippage fraction in ``[0, 1]``.

        Returns:
            A :class:`ConvertResponse` (``action == "mint-py"``).

        Raises:
            PendleAPIError: If the API rejects the request.
        """
        return self.convert(
            chain_id,
            receiver=receiver,
            slippage=slippage,
            inputs=[{"token": token_in, "amount": amount_in}],
            outputs=[pt, yt],
            **kwargs,
        )

    def redeem_py(
        self,
        chain_id: int,
        *,
        pt: str,
        yt: str,
        amount_in: str,
        token_out: str,
        receiver: str,
        slippage: float,
        **kwargs: Any,
    ) -> ConvertResponse:
        """Build calldata to redeem PT + YT back into ``token_out``.

        Thin wrapper over :meth:`convert` whose inputs are equal amounts of PT
        and YT.

        Args:
            chain_id: Chain id (int or ``ChainId``).
            pt: Principal-token address to redeem.
            yt: Yield-token address to redeem.
            amount_in: Amount of each of PT and YT to redeem, in wei.
            token_out: Address of the token you want to receive (SY or underlying).
            receiver: Address that receives ``token_out``.
            slippage: Max slippage fraction in ``[0, 1]``.

        Returns:
            A :class:`ConvertResponse` (``action == "redeem-py"``).

        Raises:
            PendleAPIError: If the API rejects the request.
        """
        return self.convert(
            chain_id,
            receiver=receiver,
            slippage=slippage,
            inputs=[
                {"token": pt, "amount": amount_in},
                {"token": yt, "amount": amount_in},
            ],
            outputs=[token_out],
            **kwargs,
        )


class AsyncPendleClient(_BaseClient):
    """Asynchronous counterpart of :class:`PendleClient`.

    Exposes the same endpoints as coroutines, backed by ``httpx.AsyncClient``.
    Use it as an async context manager so the connection pool is closed for you;
    otherwise call :meth:`aclose`.

    Example::

        import asyncio
        from pendle import AsyncPendleClient

        async def main():
            async with AsyncPendleClient() as client:
                markets = await client.get_markets(1, limit=5)
                print(markets.total)

        asyncio.run(main())
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        timeout: float = 30.0,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        """Create an asynchronous client.

        Args:
            base_url: Pendle Core API base URL. Defaults to the public endpoint
                (:data:`pendle.constants.DEFAULT_BASE_URL`); a trailing slash is
                tolerated.
            timeout: Per-request timeout in seconds, applied when this client
                creates its own ``httpx.AsyncClient``. Ignored if ``client`` is
                given.
            client: An existing ``httpx.AsyncClient`` to reuse. When supplied,
                the caller owns its lifecycle and :meth:`aclose` will not close
                it.
        """
        super().__init__(base_url)
        self._client = client or httpx.AsyncClient(timeout=timeout)
        self._owns_client = client is None

    # -- lifecycle --

    async def aclose(self) -> None:
        """Close the underlying async HTTP client.

        No-op when an external ``httpx.AsyncClient`` was injected via the
        constructor (the caller owns that client's lifecycle).
        """
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> AsyncPendleClient:
        """Enter the async runtime context and return this client."""
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        """Exit the async runtime context, closing the client via :meth:`aclose`."""
        await self.aclose()

    # -- internal --

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> JSONResponse:
        response = await self._client.get(f"{self.base_url}{path}", params=params)
        return parse_response(response)

    async def _post(self, path: str, json_body: Dict[str, Any]) -> JSONResponse:
        response = await self._client.post(f"{self.base_url}{path}", json=json_body)
        return parse_response(response)

    # -- data endpoints --

    async def get_markets(
        self,
        chain_id: int,
        *,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
    ) -> MarketsResponse:
        """Fetch the (paginated) list of markets on a chain.

        Async equivalent of :meth:`PendleClient.get_markets`.

        Args:
            chain_id: Chain id (int or ``ChainId``).
            limit: Page size. Omit to use the API default.
            skip: Number of markets to skip (offset pagination).

        Returns:
            A :class:`MarketsResponse`.

        Raises:
            PendleAPIError: If the API returns an error.
        """
        data = await self._get(
            f"/v1/{int(chain_id)}/markets", params=self._markets_params(limit, skip)
        )
        return MarketsResponse.model_validate(data)

    async def get_market(self, chain_id: int, address: str) -> Market:
        """Fetch detail for a single market.

        Async equivalent of :meth:`PendleClient.get_market`.

        Args:
            chain_id: Chain id (int or ``ChainId``).
            address: Market (LP) contract address.

        Returns:
            A :class:`pendle.models.Market`.

        Raises:
            PendleAPIError: If the market is unknown or the address is malformed.
        """
        data = await self._get(f"/v1/{int(chain_id)}/markets/{address}")
        return Market.model_validate(data)

    async def get_active_markets(self, chain_id: int) -> ActiveMarketsResponse:
        """Fetch the chain's active markets with liquidity and APY metrics.

        Async equivalent of :meth:`PendleClient.get_active_markets`.

        Args:
            chain_id: Chain id (int or ``ChainId``).

        Returns:
            An :class:`ActiveMarketsResponse`.

        Raises:
            PendleAPIError: If the API returns an error.
        """
        data = await self._get(f"/v1/{int(chain_id)}/markets/active")
        return ActiveMarketsResponse.model_validate(data)

    async def get_assets(self, chain_id: int) -> List[Asset]:
        """Fetch metadata for every asset Pendle knows about on a chain.

        Async equivalent of :meth:`PendleClient.get_assets`.

        Args:
            chain_id: Chain id (int or ``ChainId``).

        Returns:
            A list of :class:`pendle.models.Asset`.

        Raises:
            PendleAPIError: If the API returns an error.
        """
        data = await self._get(f"/v1/{int(chain_id)}/assets/all")
        items = cast(List[Any], data)
        return [Asset.model_validate(item) for item in items]

    async def get_historical_data(
        self,
        chain_id: int,
        address: str,
        *,
        time_frame: str = "day",
        timestamp_start: Optional[str] = None,
        timestamp_end: Optional[str] = None,
    ) -> HistoricalDataResponse:
        """Fetch a market's APY/TVL time series.

        Async equivalent of :meth:`PendleClient.get_historical_data`.

        Args:
            chain_id: Chain id (int or ``ChainId``).
            address: Market (LP) contract address.
            time_frame: ``"hour"``, ``"day"`` (default), or ``"week"``.
            timestamp_start: ISO-8601 start of the range (optional).
            timestamp_end: ISO-8601 end of the range (optional).

        Returns:
            A :class:`HistoricalDataResponse`.

        Raises:
            PendleAPIError: If the API returns an error.
        """
        data = await self._get(
            f"/v3/{int(chain_id)}/markets/{address}/historical-data",
            params=self._historical_params(time_frame, timestamp_start, timestamp_end),
        )
        return HistoricalDataResponse.model_validate(data)

    # -- SDK / calldata --

    async def convert(
        self,
        chain_id: int,
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
    ) -> ConvertResponse:
        """Build calldata for any Pendle action via the universal convert endpoint.

        Async equivalent of :meth:`PendleClient.convert`; see that method for
        full argument and return documentation.

        Args:
            chain_id: Chain id (int or ``ChainId``).
            receiver: Address that receives the output.
            slippage: Max slippage fraction in ``[0, 1]``.
            inputs: Input tokens as ``[{"token": addr, "amount": wei_str}, ...]``.
            outputs: Output token addresses.
            enable_aggregator: Allow an external swap aggregator.
            aggregators: Restrict to these aggregator names.
            redeem_rewards: Also redeem accrued rewards.
            use_limit_order: Use the limit-order book (API default ``True``).
            need_scale: Set ``True`` only for on-chain-updated amounts.
            additional_data: Comma-separated extra fields, e.g. ``"impliedApy"``.
            extra: Additional raw body fields, merged last.

        Returns:
            A :class:`ConvertResponse`.

        Raises:
            PendleAPIError: If the API rejects the request.
        """
        body = build_convert_body(
            receiver=receiver,
            slippage=slippage,
            inputs=inputs,
            outputs=outputs,
            enable_aggregator=enable_aggregator,
            aggregators=aggregators,
            redeem_rewards=redeem_rewards,
            use_limit_order=use_limit_order,
            need_scale=need_scale,
            additional_data=additional_data,
            extra=extra,
        )
        data = await self._post(f"/v3/sdk/{int(chain_id)}/convert", body)
        return ConvertResponse.model_validate(data)

    async def swap(
        self,
        chain_id: int,
        *,
        token_in: str,
        amount_in: str,
        token_out: str,
        receiver: str,
        slippage: float,
        **kwargs: Any,
    ) -> ConvertResponse:
        """Build calldata to swap ``amount_in`` of ``token_in`` into ``token_out``.

        Async equivalent of :meth:`PendleClient.swap`.

        Args:
            chain_id: Chain id (int or ``ChainId``).
            token_in: Address of the token you are spending.
            amount_in: Amount of ``token_in`` in wei (decimal string).
            token_out: Address of the token you want to receive.
            receiver: Address that receives ``token_out``.
            slippage: Max slippage fraction in ``[0, 1]``.

        Returns:
            A :class:`ConvertResponse` (``action == "swap"``).

        Raises:
            PendleAPIError: If the API rejects the request.
        """
        return await self.convert(
            chain_id,
            receiver=receiver,
            slippage=slippage,
            inputs=[{"token": token_in, "amount": amount_in}],
            outputs=[token_out],
            **kwargs,
        )

    async def add_liquidity(
        self,
        chain_id: int,
        *,
        market: str,
        token_in: str,
        amount_in: str,
        receiver: str,
        slippage: float,
        **kwargs: Any,
    ) -> ConvertResponse:
        """Build calldata to add liquidity to ``market`` with ``token_in``.

        Async equivalent of :meth:`PendleClient.add_liquidity`.

        Args:
            chain_id: Chain id (int or ``ChainId``).
            market: Market (LP) contract address — the LP token you receive.
            token_in: Address of the token you are depositing.
            amount_in: Amount of ``token_in`` in wei (decimal string).
            receiver: Address that receives the LP token.
            slippage: Max slippage fraction in ``[0, 1]``.

        Returns:
            A :class:`ConvertResponse` (``action == "add-liquidity"``).

        Raises:
            PendleAPIError: If the API rejects the request.
        """
        return await self.convert(
            chain_id,
            receiver=receiver,
            slippage=slippage,
            inputs=[{"token": token_in, "amount": amount_in}],
            outputs=[market],
            **kwargs,
        )

    async def remove_liquidity(
        self,
        chain_id: int,
        *,
        market: str,
        amount_in: str,
        token_out: str,
        receiver: str,
        slippage: float,
        **kwargs: Any,
    ) -> ConvertResponse:
        """Build calldata to remove liquidity from ``market`` into ``token_out``.

        Async equivalent of :meth:`PendleClient.remove_liquidity`.

        Args:
            chain_id: Chain id (int or ``ChainId``).
            market: Market (LP) contract address — the LP token you burn.
            amount_in: Amount of LP token to remove, in wei (decimal string).
            token_out: Address of the token you want to receive.
            receiver: Address that receives ``token_out``.
            slippage: Max slippage fraction in ``[0, 1]``.

        Returns:
            A :class:`ConvertResponse` (``action == "remove-liquidity"``).

        Raises:
            PendleAPIError: If the API rejects the request.
        """
        return await self.convert(
            chain_id,
            receiver=receiver,
            slippage=slippage,
            inputs=[{"token": market, "amount": amount_in}],
            outputs=[token_out],
            **kwargs,
        )

    async def mint_py(
        self,
        chain_id: int,
        *,
        token_in: str,
        amount_in: str,
        pt: str,
        yt: str,
        receiver: str,
        slippage: float,
        **kwargs: Any,
    ) -> ConvertResponse:
        """Build calldata to mint PT + YT from ``token_in``.

        Async equivalent of :meth:`PendleClient.mint_py`.

        Args:
            chain_id: Chain id (int or ``ChainId``).
            token_in: Address of the token you are depositing (SY or underlying).
            amount_in: Amount of ``token_in`` in wei (decimal string).
            pt: Principal-token address to receive.
            yt: Yield-token address to receive.
            receiver: Address that receives the PT and YT.
            slippage: Max slippage fraction in ``[0, 1]``.

        Returns:
            A :class:`ConvertResponse` (``action == "mint-py"``).

        Raises:
            PendleAPIError: If the API rejects the request.
        """
        return await self.convert(
            chain_id,
            receiver=receiver,
            slippage=slippage,
            inputs=[{"token": token_in, "amount": amount_in}],
            outputs=[pt, yt],
            **kwargs,
        )

    async def redeem_py(
        self,
        chain_id: int,
        *,
        pt: str,
        yt: str,
        amount_in: str,
        token_out: str,
        receiver: str,
        slippage: float,
        **kwargs: Any,
    ) -> ConvertResponse:
        """Build calldata to redeem PT + YT back into ``token_out``.

        Async equivalent of :meth:`PendleClient.redeem_py`.

        Args:
            chain_id: Chain id (int or ``ChainId``).
            pt: Principal-token address to redeem.
            yt: Yield-token address to redeem.
            amount_in: Amount of each of PT and YT to redeem, in wei.
            token_out: Address of the token you want to receive.
            receiver: Address that receives ``token_out``.
            slippage: Max slippage fraction in ``[0, 1]``.

        Returns:
            A :class:`ConvertResponse` (``action == "redeem-py"``).

        Raises:
            PendleAPIError: If the API rejects the request.
        """
        return await self.convert(
            chain_id,
            receiver=receiver,
            slippage=slippage,
            inputs=[
                {"token": pt, "amount": amount_in},
                {"token": yt, "amount": amount_in},
            ],
            outputs=[token_out],
            **kwargs,
        )
