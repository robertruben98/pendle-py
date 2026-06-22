"""Live integration test against the real Pendle API.

Marked ``integration`` and deselected by default (see pyproject ``addopts``).
Run explicitly with::

    pytest -m integration
"""

import pytest

from pendle import PendleClient
from pendle.constants import ChainId

pytestmark = pytest.mark.integration


def test_live_get_markets() -> None:
    with PendleClient() as client:
        resp = client.get_markets(ChainId.ETHEREUM, limit=5)
    assert resp.total > 0
    assert len(resp.results) <= 5
    market = resp.results[0]
    # Every Pendle market has a PT, YT and SY leg.
    assert market.pt.base_type == "PT"
    assert market.yt.base_type == "YT"
    assert market.sy.base_type == "SY"


def test_live_active_markets_have_apys() -> None:
    with PendleClient() as client:
        resp = client.get_active_markets(ChainId.ETHEREUM)
    assert len(resp.markets) > 0
    # At least one active market should report an implied APY.
    assert any(m.details.implied_apy is not None for m in resp.markets)
