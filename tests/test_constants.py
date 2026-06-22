"""Tests for pendle.constants."""

from pendle.constants import DEFAULT_BASE_URL, ChainId


def test_default_base_url_is_pendle_core() -> None:
    assert DEFAULT_BASE_URL == "https://api-v2.pendle.finance/core"


def test_chain_id_values_match_known_chains() -> None:
    assert ChainId.ETHEREUM.value == 1
    assert ChainId.ARBITRUM.value == 42161
    assert ChainId.BASE.value == 8453
    assert ChainId.BSC.value == 56
    assert ChainId.OPTIMISM.value == 10


def test_chain_id_is_int_enum() -> None:
    # Plain int usage must work, and int() must unwrap to the number (not name).
    assert int(ChainId.ETHEREUM) == 1
    assert str(int(ChainId.ARBITRUM)) == "42161"
