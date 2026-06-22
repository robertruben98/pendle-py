"""List active Pendle markets on Ethereum with their implied APY.

Run with:  python examples/list_markets.py
"""

from pendle import PendleClient
from pendle.constants import ChainId


def main() -> None:
    with PendleClient() as client:
        active = client.get_active_markets(ChainId.ETHEREUM)

    # Sort by liquidity, show the top 10 with implied/pendle APY.
    markets = sorted(
        active.markets,
        key=lambda m: m.details.liquidity or 0,
        reverse=True,
    )
    print(f"{'Market':<22}{'Liquidity (USD)':>18}{'Implied APY':>14}{'Pendle APY':>13}")
    for m in markets[:10]:
        liq = m.details.liquidity or 0
        implied = (m.details.implied_apy or 0) * 100
        pendle = (m.details.pendle_apy or 0) * 100
        print(f"{m.name:<22}{liq:>18,.0f}{implied:>13.2f}%{pendle:>12.2f}%")


if __name__ == "__main__":
    main()
