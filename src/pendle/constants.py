"""Constants for the Pendle Finance v2 API: base URL and chain ids."""

from __future__ import annotations

from enum import IntEnum

#: Default Pendle Core API base URL. Override via ``PendleClient(base_url=...)``.
DEFAULT_BASE_URL = "https://api-v2.pendle.finance/core"


class ChainId(IntEnum):
    """Native chain ids for the chains Pendle currently supports.

    These are the chains' canonical EVM ids (Pendle uses native ids directly,
    unlike some bridges). Plain ``int`` values are accepted everywhere the
    client takes a chain id; this enum is just a convenience. Values verified
    live against ``GET /v1/chains``.
    """

    ETHEREUM = 1
    OPTIMISM = 10
    BSC = 56
    SONIC = 146
    MONAD = 143
    HYPEREVM = 999
    PLASMA = 9745
    BASE = 8453
    MANTLE = 5000
    ARBITRUM = 42161
    BERACHAIN = 80094
