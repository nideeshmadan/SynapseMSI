"""Regression: public OKX/HL inventory bounds match retained-archive evidence."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from synapse_msi.historical_corpus.inventory import lookup_regime

OKX_REST_END = "2026-04-16T22:58:38.155839Z"
OKX_WS_START = "2026-04-16T23:06:13.935233Z"
HL_WS_START = "2026-04-16T23:35:16.846026Z"
HL_REST_END = "2026-04-16T23:35:19.963617Z"

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DOC = ROOT / "docs" / "historical-acquisition-regimes.md"

_DOCUMENTED_ARCHIVE_BOUNDS = {
    "okx.pure_rest.canonical_v1": ("effective_end", OKX_REST_END),
    "okx.ws_top_of_book.conditional_native_mark": ("effective_start", OKX_WS_START),
    "hyperliquid.pure_rest.canonical_v1": ("effective_end", HL_REST_END),
    "hyperliquid.ws_top_of_book.l1_only": ("effective_start", HL_WS_START),
    "binance.ws_merged_ticker.midpoint_proxy": ("effective_start", None),
}


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def test_okx_hyperliquid_retained_observation_bounds_exact():
    okx_rest = lookup_regime("okx.pure_rest.canonical_v1")
    okx_ws = lookup_regime("okx.ws_top_of_book.conditional_native_mark")
    hl_rest = lookup_regime("hyperliquid.pure_rest.canonical_v1")
    hl_ws = lookup_regime("hyperliquid.ws_top_of_book.l1_only")
    assert okx_rest is not None and okx_ws is not None
    assert hl_rest is not None and hl_ws is not None
    assert okx_rest.effective_end == OKX_REST_END
    assert okx_ws.effective_start == OKX_WS_START
    assert hl_rest.effective_end == HL_REST_END
    assert hl_ws.effective_start == HL_WS_START


def test_okx_retained_observation_gap_preserved():
    okx_rest = lookup_regime("okx.pure_rest.canonical_v1")
    okx_ws = lookup_regime("okx.ws_top_of_book.conditional_native_mark")
    assert okx_rest is not None and okx_ws is not None
    gap = _parse_utc(okx_ws.effective_start) - _parse_utc(okx_rest.effective_end)
    assert gap.total_seconds() > 0
    assert abs(gap.total_seconds() - 455.779394) < 0.001


def test_hyperliquid_retained_observation_overlap_accepted():
    hl_rest = lookup_regime("hyperliquid.pure_rest.canonical_v1")
    hl_ws = lookup_regime("hyperliquid.ws_top_of_book.l1_only")
    assert hl_rest is not None and hl_ws is not None
    overlap = _parse_utc(hl_rest.effective_end) - _parse_utc(hl_ws.effective_start)
    assert overlap.total_seconds() > 0
    assert abs(overlap.total_seconds() - 3.117591) < 0.001


def test_binance_ws_merged_ticker_start_remains_unknown():
    entry = lookup_regime("binance.ws_merged_ticker.midpoint_proxy")
    assert entry is not None
    assert entry.effective_start is None


def test_public_inventory_bounds_match_documented_archive_evidence():
    for regime_id, (field, value) in _DOCUMENTED_ARCHIVE_BOUNDS.items():
        entry = lookup_regime(regime_id)
        assert entry is not None
        assert getattr(entry, field) == value


def test_public_docs_table_matches_inventory():
    text = PUBLIC_DOC.read_text(encoding="utf-8")
    assert (
        f"| `okx.pure_rest.canonical_v1` | okx | `pure_rest` | `canonical_v1` | `rest` | "
        f"`2026-04-13T00:00:00Z` | `{OKX_REST_END}` | false |"
    ) in text
    assert (
        f"| `okx.ws_top_of_book.conditional_native_mark` | okx | "
        f"`ws_top_of_book_conditional_native` | `ws_top_of_book` | `websocket` | "
        f"`{OKX_WS_START}` | open | true |"
    ) in text
    assert (
        f"| `hyperliquid.pure_rest.canonical_v1` | hyperliquid | `pure_rest` | "
        f"`canonical_v1` | `rest` | `2026-04-13T00:00:00Z` | `{HL_REST_END}` | false |"
    ) in text
    assert (
        f"| `hyperliquid.ws_top_of_book.l1_only` | hyperliquid | "
        f"`ws_top_of_book_midpoint` | `ws_top_of_book` | `websocket` | "
        f"`{HL_WS_START}` | open | true |"
    ) in text
    assert "2026-05-18T00:00:00Z" not in text


def test_no_may18_inventory_literal():
    inventory = ROOT / "synapse_msi" / "historical_corpus" / "inventory.py"
    text = inventory.read_text(encoding="utf-8")
    assert "2026-05-18T00:00:00Z" not in text
    assert not re.search(r"2026-05-18T00:00:00Z", PUBLIC_DOC.read_text(encoding="utf-8"))
