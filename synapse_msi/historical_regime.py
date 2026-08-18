"""Historical regime classification for legacy canonical rows."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional


HISTORICAL_REGIMES = frozenset(
    {
        "pure_rest",
        "ws_top_of_book_midpoint",
        "ws_top_of_book_conditional_native",
        "hybrid_ws_book_rest_reference",
        "native_ws_ticker",
        "unknown_or_insufficient_provenance",
    }
)


def _approx_equal(a: Optional[float], b: Optional[float], *, rel_tol: float = 1e-9) -> bool:
    if a is None or b is None:
        return False
    if a == b:
        return True
    denom = max(abs(a), abs(b), 1e-12)
    return abs(a - b) / denom <= rel_tol


def _payload(row: Mapping[str, Any]) -> Dict[str, Any]:
    payload = row.get("payload") or row.get("payload_jsonb") or {}
    return payload if isinstance(payload, dict) else {}


def _venue(row: Mapping[str, Any]) -> str:
    return str(row.get("exchange") or row.get("venue") or "").lower()


def classify_okx_mark_evidence(row: Mapping[str, Any]) -> str:
    """
    Distinguish OKX tickers mark evidence without inventing venue-wide defaults.

    Returns one of: native_present | midpoint_derived | unavailable | insufficient
    """
    payload = _payload(row)
    field_provenance = payload.get("field_provenance")
    if isinstance(field_provenance, dict) and field_provenance.get("native_mark_price") is not None:
        return "native_present"

    native = payload.get("native_mark_price")
    if native is not None or payload.get("mark_price_alias_of") == "native_mark_price":
        return "native_present"

    bid = payload.get("bid_price")
    ask = payload.get("ask_price")
    mark = payload.get("mark_price")
    if mark is None and native is None:
        # Explicit absence of mark keys after a WS top-of-book observation.
        if bid is not None and ask is not None:
            return "unavailable"
        return "insufficient"

    if bid is not None and ask is not None and mark is not None:
        try:
            mid = (float(bid) + float(ask)) / 2.0
            if _approx_equal(float(mark), mid):
                return "midpoint_derived"
        except (TypeError, ValueError):
            return "insufficient"
        # Mark present but not midpoint and not tagged native — insufficient to claim native.
        return "insufficient"

    return "insufficient"


def classify_historical_regime(row: Mapping[str, Any]) -> str:
    """
    Classify historical ingest rows without rewriting raw archive data.

    Rules (conservative):
    - REST-only canonical_v1 / rest transport → pure_rest
    - Binance ws_top_of_book / ws_merged_ticker midpoint-era → ws_top_of_book_midpoint
    - hybrid_book_reference or mixed REST+WS components → hybrid_ws_book_rest_reference
    - bybit ws_ticker with native markPrice source → native_ws_ticker
    - OKX ws_top_of_book → ws_top_of_book_conditional_native (mark evidence separate)
    - Hyperliquid ws_top_of_book → ws_top_of_book_midpoint (L1-only path)
    - otherwise → unknown_or_insufficient_provenance
    """
    ingest_type = str(row.get("ingest_type") or "")
    transport = str(row.get("transport") or "").lower()
    payload = _payload(row)
    venue = _venue(row)

    if ingest_type == "hybrid_book_reference" or payload.get("ingest_type") == "hybrid_book_reference":
        return "hybrid_ws_book_rest_reference"

    if ingest_type in ("canonical_v1", "rest_metadata") or transport == "rest":
        if ingest_type.startswith("ws_"):
            return "hybrid_ws_book_rest_reference"
        return "pure_rest"

    if ingest_type == "ws_merged_ticker":
        book_raw = payload.get("raw_book_message") or {}
        book_data = book_raw.get("data", book_raw) if isinstance(book_raw, dict) else {}
        if book_data.get("e") == "bookTicker" or payload.get("stream_types") == ["bookTicker", "markPrice"]:
            mark = payload.get("mark_price") or payload.get("native_mark_price")
            bid = payload.get("bid_price")
            ask = payload.get("ask_price")
            if bid is not None and ask is not None:
                mid = (float(bid) + float(ask)) / 2.0
                if _approx_equal(float(mark) if mark is not None else None, mid):
                    return "ws_top_of_book_midpoint"
        return "unknown_or_insufficient_provenance"

    if ingest_type == "ws_top_of_book":
        # Venue-specific acquisition families — do not collapse OKX into native_ws_ticker.
        if venue == "okx":
            return "ws_top_of_book_conditional_native"
        if venue == "hyperliquid":
            return "ws_top_of_book_midpoint"

        native = payload.get("native_mark_price")
        if native is not None or payload.get("mark_price_alias_of") == "native_mark_price":
            return "native_ws_ticker"
        bid = payload.get("bid_price")
        ask = payload.get("ask_price")
        mark = payload.get("mark_price")
        if native is None and mark is not None and bid is not None and ask is not None:
            mid = (float(bid) + float(ask)) / 2.0
            if _approx_equal(float(mark), mid):
                return "ws_top_of_book_midpoint"
        return "ws_top_of_book_midpoint"

    if ingest_type == "ws_ticker":
        if payload.get("mark_price_source") == "native_markPrice" or payload.get("native_mark_price") is not None:
            return "native_ws_ticker"
        return "unknown_or_insufficient_provenance"

    return "unknown_or_insufficient_provenance"
