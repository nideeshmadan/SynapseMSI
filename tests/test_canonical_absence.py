"""Exact zero-as-unavailable boundaries for scoped canonical fields."""

from __future__ import annotations

from decimal import Decimal

import pytest

from synapse_msi.canonical_absence import (
    ZERO_UNAVAILABLE_FIELDS,
    canonical_nonzero_decimal,
    is_exact_zero,
    mark_price_available,
    parse_exact_decimal,
)
from synapse_msi.consensus import build_consensus
from synapse_msi.investigation_reproduction import (
    observation_to_normalized,
    recompute_from_observations,
)
from synapse_msi.types import NormalizedVenueData
from datetime import datetime, timezone


def _norm(venue: str, mark: object, funding: object = "0.0001") -> NormalizedVenueData:
    return NormalizedVenueData(
        venue=venue,
        instrument_canonical="ETHUSDT_PERP",
        timestamp=datetime(2026, 7, 21, tzinfo=timezone.utc),
        mark_price=None if mark is None else str(mark),
        bid_price="1",
        ask_price="1",
        funding_rate=None if funding is None else str(funding),
        oi_usd="0",
        volume_24h_usd="0",
        spread_bps="0",
        price_change_24h_bps="0",
        staleness_ms=0.0,
        usable=True,
        provenance_id=f"t:{venue}",
        normalization_rules_applied=[],
    )


@pytest.mark.parametrize(
    "value",
    [
        0,
        0.0,
        -0.0,
        Decimal("0"),
        Decimal("0E-18"),
        Decimal("-0E-18"),
        "0",
        "0.0",
        "0E-18",
    ],
)
def test_exact_zeros_are_unavailable_for_mark(value):
    assert is_exact_zero(value) is True
    assert mark_price_available(value) is False
    assert canonical_nonzero_decimal("mark_price", value) is None


@pytest.mark.parametrize("value", [None, "", "   "])
def test_missing_mark_is_unavailable(value):
    assert parse_exact_decimal(value) is None
    assert mark_price_available(value) is False


@pytest.mark.parametrize(
    "value",
    [
        Decimal("0.000000000001"),
        Decimal("-0.000000000001"),
        "1939.95017829",
        Decimal("1893.85"),
    ],
)
def test_nonzero_marks_remain_available(value):
    assert is_exact_zero(value) is False
    assert mark_price_available(value) is True
    assert canonical_nonzero_decimal("mark_price", value) == Decimal(str(value))


def test_helper_rejects_unrelated_fields():
    with pytest.raises(ValueError, match="scoped"):
        canonical_nonzero_decimal("bid_price", 0)


def test_zero_unavailable_field_set_is_narrow():
    assert ZERO_UNAVAILABLE_FIELDS == frozenset(
        {"mark_price", "native_mark_price", "funding_rate"}
    )


def test_consensus_excludes_parquet_style_zero_marks():
    rows = [
        _norm("binance", "1893.85"),
        _norm("bybit", "1902.99"),
        _norm("okx", "0E-18"),
        _norm("hyperliquid", Decimal("0")),
    ]
    consensus = build_consensus(rows, "ETHUSDT_PERP")
    # Median of nonzero marks 1893.85 and 1902.99 only (zeros excluded).
    assert Decimal(consensus.mark_price_consensus) == Decimal("1898.42")


def test_observation_projection_maps_zero_mark_to_sentinel_string():
    row = observation_to_normalized(
        {
            "venue": "okx",
            "instrument": "ETHUSDT_PERP",
            "mark_price": Decimal("0E-18"),
            "funding_rate": Decimal("0E-8"),
            "scan_timestamp": "2026-07-21T08:55:48.911654Z",
            "venue_timestamp": "2026-07-21T08:55:48.911654Z",
            "usable": True,
        }
    )
    assert row.mark_price == "0"
    assert row.funding_rate == "0.0001"


def test_jsonl_and_decimal_zero_marks_same_eligibility():
    base = {
        "venue": "okx",
        "instrument": "ETHUSDT_PERP",
        "scan_timestamp": "2026-07-21T08:55:48.911654Z",
        "venue_timestamp": "2026-07-21T08:55:48.911654Z",
        "usable": True,
        "acquisition": {
            "exchange": "okx",
            "ingest_type": "ws_top_of_book",
            "transport": "websocket",
            "collector_service_name": "synapse-collector-okx-ws",
            "payload": {},
        },
    }
    jsonl_style = [{**base, "mark_price": "0", "venue": "okx"}, {**base, "venue": "binance", "mark_price": "1893.85"}]
    parquet_style = [
        {**base, "mark_price": Decimal("0E-18"), "venue": "okx"},
        {**base, "venue": "binance", "mark_price": Decimal("1893.850000000000000000")},
    ]
    a = recompute_from_observations(
        jsonl_style,
        episode_id="t",
        instrument="ETHUSDT_PERP",
        window_start="2026-07-21T08:55:48.911654Z",
        window_end="2026-07-21T08:55:48.911654Z",
    )
    b = recompute_from_observations(
        parquet_style,
        episode_id="t",
        instrument="ETHUSDT_PERP",
        window_start="2026-07-21T08:55:48.911654Z",
        window_end="2026-07-21T08:55:48.911654Z",
    )
    assert a.excluded_venues == b.excluded_venues == {"okx": "missing_or_zero_mark_price"}
    assert a.included_venues == b.included_venues == ("binance",)
