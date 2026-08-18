"""Typed historical acquisition-regime inventory derived from repository audit evidence."""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from synapse_msi.historical_corpus.models import (
    ACQUISITION_REGIME_METHODOLOGY_VERSION,
    PROVENANCE_POLICY_VERSION,
    AcquisitionRegime,
    HistoricalRegimeInventoryEntry,
)
from synapse_msi.historical_regime import HISTORICAL_REGIMES

# Inventory effective_* bound semantics (default):
#   - effective_start = earliest retained observation assigned to the regime
#   - effective_end   = latest retained observation assigned to the regime
#   - bounds describe retained archive evidence, not exact deploy/shutdown times
#   - gaps and overlaps between regimes are preserved when present in archives
# Unknown bounds remain None — never inferred.
#
# Documented exceptions (not earliest/latest retained observation):
#   - binance.hybrid_book_reference.native_mark effective_start: advisory exclusive
#     authoritative corpus boundary (see entry comment)
#   - bybit.native_ws_ticker.markPrice effective_start: advisory sole-authoritative
#     corpus boundary after dual-write (see entry comment)
_REGIME_INVENTORY: Tuple[HistoricalRegimeInventoryEntry, ...] = (
    HistoricalRegimeInventoryEntry(
        regime_id="binance.pure_rest.canonical_v1",
        effective_start="2026-04-13T00:00:00Z",
        effective_end="2026-07-13T23:59:59Z",
        collector="synapse-collector-binance",
        ingest_type="canonical_v1",
        transport="rest",
        field_provenance={"mark_price": "rest_premiumIndex_markPrice"},
        known_semantic_differences=("mark_price from REST premiumIndex",),
        comparable_to=("bybit.pure_rest.canonical_v1", "okx.pure_rest.canonical_v1"),
        venue="binance",
        classifier_label="pure_rest",
        comparison_group="rest_composed",
        provenance_policy_version=PROVENANCE_POLICY_VERSION,
        collector_source_mode="relay",
        known_limitations=("legacy REST-composed mark semantics",),
    ),
    HistoricalRegimeInventoryEntry(
        regime_id="binance.ws_top_of_book.midpoint_proxy",
        effective_start="2026-04-16T00:00:00Z",
        effective_end="2026-07-14T16:15:00Z",
        collector="synapse-collector-binance-ws",
        ingest_type="ws_top_of_book",
        transport="websocket",
        field_provenance={"mark_price": "derived_midpoint_when_mark_equals_mid"},
        known_semantic_differences=(
            "mark_price may equal (bid+ask)/2 rather than native mark",
            "coexisted with REST on documented dates",
        ),
        comparable_to=("binance.ws_merged_ticker.midpoint_proxy",),
        venue="binance",
        classifier_label="ws_top_of_book_midpoint",
        comparison_group="l1_midpoint_proxy",
        provenance_policy_version=PROVENANCE_POLICY_VERSION,
        known_limitations=("midpoint stored under mark_price; not native mark",),
    ),
    HistoricalRegimeInventoryEntry(
        regime_id="binance.ws_merged_ticker.midpoint_proxy",
        effective_start=None,
        effective_end="2026-07-14T16:15:00Z",
        collector="synapse-collector-binance-ws",
        ingest_type="ws_merged_ticker",
        transport="websocket",
        field_provenance={"mark_price": "derived_midpoint_bookTicker"},
        known_semantic_differences=("merged bookTicker + markPrice stream",),
        comparable_to=("binance.ws_top_of_book.midpoint_proxy",),
        venue="binance",
        classifier_label="ws_top_of_book_midpoint",
        comparison_group="l1_midpoint_proxy",
        provenance_policy_version=PROVENANCE_POLICY_VERSION,
        known_limitations=(
            "unobserved in retained archives (0 rows with ingest_type=ws_merged_ticker)",
            "effective_start remains unknown; code history is not first-observed proof",
        ),
    ),
    HistoricalRegimeInventoryEntry(
        regime_id="binance.hybrid_book_reference.native_mark",
        # EXCEPTION: advisory exclusive authoritative boundary (not earliest retained
        # observation). First hybrid observation 2026-07-14T15:53:33.634084Z; REST ends
        # 15:56:21Z. Boundary derived from retained-observation cutover audit evidence.
        effective_start="2026-07-14T15:57:00Z",
        effective_end=None,
        collector="synapse-collector-binance-ws",
        ingest_type="hybrid_book_reference",
        transport="hybrid",
        field_provenance={
            "mark_price": "rest_premiumIndex_markPrice",
            "bid_price": "ws_bookTicker",
            "ask_price": "ws_bookTicker",
        },
        known_semantic_differences=(
            "native mark from REST reference; book from WS bookTicker",
            "open_interest not merged into primary hybrid row",
        ),
        comparable_to=("bybit.native_ws_ticker.markPrice",),
        venue="binance",
        classifier_label="hybrid_ws_book_rest_reference",
        comparison_group="native_mark_authoritative",
        current_production=True,
        provenance_policy_version=PROVENANCE_POLICY_VERSION,
        known_limitations=(
            "venue_event_time is min(book_ts, ref_ts)",
            "book and reference freshness/skew gates apply",
            "advisory exclusive boundary 2026-07-14T15:57:00Z; short REST+hybrid overlap precedes it",
            "full collector_service_name from 2026-07-15T14:56:35.078484Z is not the transport cutover",
        ),
    ),
    HistoricalRegimeInventoryEntry(
        regime_id="bybit.pure_rest.canonical_v1",
        effective_start="2026-04-13T00:00:00Z",
        effective_end="2026-07-13T23:59:59Z",
        collector="synapse-collector-bybit",
        ingest_type="canonical_v1",
        transport="rest",
        field_provenance={"mark_price": "rest_composed"},
        known_semantic_differences=("REST-composed canonical payload",),
        comparable_to=("binance.pure_rest.canonical_v1",),
        venue="bybit",
        classifier_label="pure_rest",
        comparison_group="rest_composed",
        provenance_policy_version=PROVENANCE_POLICY_VERSION,
        collector_source_mode="relay",
        known_limitations=("legacy REST-composed mark semantics",),
    ),
    HistoricalRegimeInventoryEntry(
        regime_id="bybit.ws_top_of_book.midpoint_proxy",
        effective_start="2026-05-19T00:00:00Z",
        effective_end="2026-07-14T01:22:00Z",
        collector="synapse-collector-bybit-ws",
        ingest_type="ws_top_of_book",
        transport="websocket",
        field_provenance={"mark_price": "derived_midpoint"},
        known_semantic_differences=("coexisted with REST on 2026-05-19",),
        comparable_to=(),
        venue="bybit",
        classifier_label="ws_top_of_book_midpoint",
        comparison_group="l1_midpoint_proxy",
        provenance_policy_version=PROVENANCE_POLICY_VERSION,
        known_limitations=("midpoint-era Bybit WS; superseded by ws_ticker",),
    ),
    HistoricalRegimeInventoryEntry(
        regime_id="bybit.native_ws_ticker.markPrice",
        # EXCEPTION: advisory sole-authoritative boundary (not earliest retained
        # observation). First ws_ticker appearance 2026-07-14T01:22:39.120466Z is
        # mixed REST+WS until 19:59:34Z.
        # Boundary derived from retained-observation cutover audit evidence.
        effective_start="2026-07-14T20:00:00Z",
        effective_end=None,
        collector="synapse-collector-bybit-ws",
        ingest_type="ws_ticker",
        transport="websocket",
        field_provenance={"mark_price": "ws_tickers_markPrice"},
        known_semantic_differences=("native markPrice from tickers channel",),
        comparable_to=("binance.hybrid_book_reference.native_mark",),
        venue="bybit",
        classifier_label="native_ws_ticker",
        comparison_group="native_mark_authoritative",
        current_production=True,
        provenance_policy_version=PROVENANCE_POLICY_VERSION,
        known_limitations=(
            "venue_event_time from tickers envelope ts",
            "first_target_method_observation 2026-07-14T01:22:39.120466Z is mixed REST+WS, not exclusive",
            "advisory sole-authoritative boundary 2026-07-14T20:00:00Z after last REST 19:59:34.568212Z",
            "full collector_service_name from 2026-07-15T14:51:28.478898Z is not the transport cutover",
        ),
    ),
    HistoricalRegimeInventoryEntry(
        regime_id="okx.pure_rest.canonical_v1",
        effective_start="2026-04-13T00:00:00Z",
        # Latest retained REST observation (full-archive scan 2026-07-21).
        effective_end="2026-04-16T22:58:38.155839Z",
        collector="synapse-collector-okx",
        ingest_type="canonical_v1",
        transport="rest",
        field_provenance={"mark_price": "rest_composed"},
        known_semantic_differences=("superseded by WS; retained-observation gap before first WS",),
        comparable_to=("binance.pure_rest.canonical_v1",),
        venue="okx",
        classifier_label="pure_rest",
        comparison_group="rest_composed",
        provenance_policy_version=PROVENANCE_POLICY_VERSION,
        collector_source_mode="relay",
        known_limitations=(
            "latest retained REST observation 2026-04-16T22:58:38.155839Z",
            "gap to first retained WS 2026-04-16T23:06:13.935233Z (~7.6 min)",
        ),
    ),
    HistoricalRegimeInventoryEntry(
        regime_id="okx.ws_top_of_book.conditional_native_mark",
        # Earliest retained WS observation (full-archive scan 2026-07-21).
        effective_start="2026-04-16T23:06:13.935233Z",
        effective_end=None,
        collector="synapse-collector-okx-ws",
        ingest_type="ws_top_of_book",
        transport="websocket",
        field_provenance={
            "mark_price": "ws_tickers_markPx_when_present",
            "bid_price": "ws_tickers_bidPx",
            "ask_price": "ws_tickers_askPx",
        },
        known_semantic_differences=(
            "mark_price omitted when markPx absent on tickers message",
            "uses tickers channel not books5",
        ),
        comparable_to=("hyperliquid.ws_top_of_book.l1_only",),
        venue="okx",
        classifier_label="ws_top_of_book_conditional_native",
        comparison_group="conditional_native_mark",
        current_production=True,
        provenance_policy_version=PROVENANCE_POLICY_VERSION,
        known_limitations=(
            "native mark is conditional on markPx presence per message",
            "do not infer native mark from venue identity alone",
            "earliest retained WS observation 2026-04-16T23:06:13.935233Z",
            "retained-observation gap after last REST (~7.6 min); not dual-write overlap",
        ),
    ),
    HistoricalRegimeInventoryEntry(
        regime_id="hyperliquid.pure_rest.canonical_v1",
        effective_start="2026-04-13T00:00:00Z",
        # Latest retained REST observation (full-archive scan 2026-07-21).
        effective_end="2026-04-16T23:35:19.963617Z",
        collector="synapse-collector-hyperliquid",
        ingest_type="canonical_v1",
        transport="rest",
        field_provenance={"mark_price": "rest_meta_mids"},
        known_semantic_differences=(
            "REST meta + mids composition",
            "short retained-observation overlap with first WS",
        ),
        comparable_to=(),
        venue="hyperliquid",
        classifier_label="pure_rest",
        comparison_group="rest_composed",
        provenance_policy_version=PROVENANCE_POLICY_VERSION,
        collector_source_mode="relay",
        known_limitations=(
            "latest retained REST observation 2026-04-16T23:35:19.963617Z",
            "overlap with first retained WS 2026-04-16T23:35:16.846026Z (~3.1 s)",
        ),
    ),
    HistoricalRegimeInventoryEntry(
        regime_id="hyperliquid.ws_top_of_book.l1_only",
        # Earliest retained WS observation (full-archive scan 2026-07-21).
        effective_start="2026-04-16T23:35:16.846026Z",
        effective_end=None,
        collector="synapse-collector-hyperliquid-ws",
        ingest_type="ws_top_of_book",
        transport="websocket",
        field_provenance={
            "bid_price": "ws_l2Book",
            "ask_price": "ws_l2Book",
            "mark_price": "absent",
        },
        known_semantic_differences=(
            "no native mark in WS l2Book payload",
            "mark_price resolves to zero at normalization when absent",
        ),
        comparable_to=("okx.ws_top_of_book.conditional_native_mark",),
        venue="hyperliquid",
        classifier_label="ws_top_of_book_midpoint",
        comparison_group="l1_midpoint_proxy",
        current_production=True,
        provenance_policy_version=PROVENANCE_POLICY_VERSION,
        known_limitations=(
            "L1-only path; native mark unavailable",
            "earliest retained WS observation 2026-04-16T23:35:16.846026Z",
            "short retained-observation overlap with last REST (~3.1 s)",
        ),
    ),
    HistoricalRegimeInventoryEntry(
        regime_id="unknown.insufficient_provenance",
        effective_start=None,
        effective_end=None,
        collector="unknown",
        ingest_type="unknown",
        transport="unknown",
        field_provenance={},
        known_semantic_differences=("classifier returned unknown_or_insufficient_provenance",),
        comparable_to=(),
        venue="unknown",
        classifier_label="unknown_or_insufficient_provenance",
        comparison_group="unknown",
        provenance_policy_version=None,
        known_limitations=("insufficient row-level acquisition metadata",),
    ),
)


def build_regime_inventory() -> Tuple[HistoricalRegimeInventoryEntry, ...]:
    return _REGIME_INVENTORY


def regime_ids() -> Tuple[str, ...]:
    return tuple(entry.regime_id for entry in _REGIME_INVENTORY)


def lookup_regime(regime_id: str) -> Optional[HistoricalRegimeInventoryEntry]:
    for entry in _REGIME_INVENTORY:
        if entry.regime_id == regime_id:
            return entry
    return None


def lookup_by_classifier(
    *,
    venue: str,
    classifier_label: str,
    ingest_type: Optional[str] = None,
) -> Optional[HistoricalRegimeInventoryEntry]:
    candidates = [
        entry
        for entry in _REGIME_INVENTORY
        if entry.venue == venue and entry.classifier_label == classifier_label
    ]
    if ingest_type:
        typed = [entry for entry in candidates if entry.ingest_type == ingest_type]
        if len(typed) == 1:
            return typed[0]
        if typed:
            production = [entry for entry in typed if entry.current_production]
            if len(production) == 1:
                return production[0]
    if len(candidates) == 1:
        return candidates[0]
    production = [entry for entry in candidates if entry.current_production]
    if len(production) == 1:
        return production[0]
    return None


def resolve_regime_from_row(row: Dict[str, object]) -> Optional[HistoricalRegimeInventoryEntry]:
    """Legacy thin resolver retained for callers; prefer assign_regime_from_row()."""
    from synapse_msi.historical_regime import classify_historical_regime

    venue = str(row.get("exchange") or row.get("venue") or "unknown")
    classifier_label = classify_historical_regime(row)
    ingest_type = str(row.get("ingest_type") or "")
    if classifier_label == "unknown_or_insufficient_provenance":
        return lookup_regime("unknown.insufficient_provenance")
    return lookup_by_classifier(
        venue=venue,
        classifier_label=classifier_label,
        ingest_type=ingest_type or None,
    )


def current_production_entries() -> Tuple[HistoricalRegimeInventoryEntry, ...]:
    return tuple(entry for entry in _REGIME_INVENTORY if entry.current_production)


def to_acquisition_regime(entry: HistoricalRegimeInventoryEntry) -> AcquisitionRegime:
    authority = next(iter(entry.field_provenance.values()), "unknown")
    authority_map = tuple(sorted(entry.field_provenance.items()))
    limitations = entry.known_limitations or entry.known_semantic_differences
    return AcquisitionRegime(
        regime_id=entry.regime_id,
        collector=entry.collector,
        collector_service_name=entry.collector,
        ingest_type=entry.ingest_type,
        transport=entry.transport,
        field_authority=authority,
        field_provenance_version=ACQUISITION_REGIME_METHODOLOGY_VERSION,
        methodology_version=ACQUISITION_REGIME_METHODOLOGY_VERSION,
        comparison_group=entry.comparison_group,
        venue=entry.venue,
        classifier_label=entry.classifier_label,
        notes=entry.known_semantic_differences,
        known_semantic_differences=entry.known_semantic_differences,
        collector_source_mode=entry.collector_source_mode,
        field_authority_map=authority_map,
        provenance_policy_version=entry.provenance_policy_version,
        known_limitations=limitations,
        effective_start=entry.effective_start,
        effective_end=entry.effective_end,
        current_production=entry.current_production,
    )


def inventory_entry_to_dict(entry: HistoricalRegimeInventoryEntry) -> Dict[str, object]:
    """Serialize an inventory entry for public consumers."""
    payload: Dict[str, object] = {
        "regime_id": entry.regime_id,
        "effective_start": entry.effective_start,
        "effective_end": entry.effective_end,
        "collector": entry.collector,
        "collector_service_name": entry.collector,
        "ingest_type": entry.ingest_type,
        "transport": entry.transport,
        "field_provenance": dict(entry.field_provenance),
        "known_semantic_differences": list(entry.known_semantic_differences),
        "comparable_to": list(entry.comparable_to),
        "venue": entry.venue,
        "classifier_label": entry.classifier_label,
        "comparison_group": entry.comparison_group,
        "current_production": entry.current_production,
        "known_limitations": list(entry.known_limitations or entry.known_semantic_differences),
        "methodology_version": ACQUISITION_REGIME_METHODOLOGY_VERSION,
    }
    if entry.provenance_policy_version is not None:
        payload["provenance_policy_version"] = entry.provenance_policy_version
    if entry.collector_source_mode is not None:
        payload["collector_source_mode"] = entry.collector_source_mode
    return payload


def validate_inventory_classifier_coverage() -> List[str]:
    errors: List[str] = []
    documented = set(HISTORICAL_REGIMES)
    inventory_labels = {entry.classifier_label for entry in _REGIME_INVENTORY}
    if "unknown_or_insufficient_provenance" not in inventory_labels:
        errors.append("missing unknown_or_insufficient_provenance inventory entry")
    for label in documented:
        if label not in inventory_labels:
            errors.append(f"no inventory entry for classifier label {label}")
    return errors
