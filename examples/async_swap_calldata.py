"""Build swap calldata asynchronously and inspect the transaction to broadcast.

This picks the first active Ethereum market, then builds calldata to swap its SY
token into its PT. It does NOT sign or send anything — broadcasting the returned
``tx`` (e.g. with web3.py via the optional ``[exec]`` extra) is up to you.

Run with:  python examples/async_swap_calldata.py
"""

import asyncio

from pendle import AsyncPendleClient
from pendle.constants import ChainId

# Use any address you control as the receiver; the API rejects placeholders.
RECEIVER = "0x000000000000000000000000000000000000dEaD"


async def main() -> None:
    async with AsyncPendleClient() as client:
        markets = await client.get_markets(ChainId.ETHEREUM, limit=1)
        market = markets.results[0]
        print(f"Market: {market.symbol}  (expiry {market.expiry})")

        resp = await client.swap(
            ChainId.ETHEREUM,
            token_in=market.sy.address,
            amount_in="1000000000000000000",  # 1.0 SY (18 decimals)
            token_out=market.pt.address,
            receiver=RECEIVER,
            slippage=0.01,  # 1%
            additional_data="impliedApy",
        )

    print(f"Action: {resp.action}")
    for approval in resp.required_approvals:
        print(f"  approve {approval.amount} of {approval.token}")
    route = resp.routes[0]
    print(f"  method: {route.contract_param_info.method}")
    print(f"  tx.to:  {route.tx.to}")
    print(f"  output: {route.outputs[0].amount} of {route.outputs[0].token}")


if __name__ == "__main__":
    asyncio.run(main())
