# Historical Acquisition Regimes

**Conservative classification of archived `external_raw_ingest` observations without rewriting historical evidence.**

This document describes the known acquisition regimes represented in the historical corpus. Unlike the repository's normative specifications, it records observed historical acquisition behavior and the evidentiary limits of that record.

Authoritative sources in this repository:

* Classifier definitions: `synapse_msi/historical_regime.py` (`HISTORICAL_REGIMES`, `classify_historical_regime()`)
* Public regime inventory: `synapse_msi/historical_corpus/inventory.py` (`_REGIME_INVENTORY`)

Field semantics and current sourcing are defined in the [Canonical Field Specification](../specifications/canonical-field-specification.md#3-current-authoritative-field-sourcing). The provenance model is defined in [Provenance](../specifications/provenance-standard.md#6-acquisition-regimes).

Historical archives are not uniformly WebSocket-derived or semantically uniform. Interpretation is governed by each observation's recorded `ingest_type`, `transport`, payload shape, and `field_provenance`.

Unknown bounds remain unknown unless surviving evidence supports a more precise value.

## Boundary Semantics

Unless a regime explicitly states otherwise:

- `effective_start` is the earliest retained archived observation assigned to the regime.
- `effective_end` is the latest retained archived observation assigned to the regime.
- Both timestamps are inclusive observation bounds.
- Bounds describe the retained archive, not necessarily the exact collector deployment or shutdown time.
- Gaps and overlaps between regimes are preserved rather than normalized away.

Some modern production regimes use documented authoritative cutover times rather than earliest-retained observations. Those exceptions are identified explicitly in the public inventory.

---

## Classifier Labels

These are the complete classifier labels defined by `HISTORICAL_REGIMES` and exposed through the public inventory.

| Classifier label                     | Observable evidence                                                                               |
| ------------------------------------ | ------------------------------------------------------------------------------------------------- |
| `pure_rest`                          | `ingest_type=canonical_v1` or `rest_metadata`, or `transport=rest`                                |
| `ws_top_of_book_midpoint`            | WebSocket book or merged-ticker acquisition where midpoint may be represented under `mark_price`  |
| `ws_top_of_book_conditional_native`  | OKX `ingest_type=ws_top_of_book`; native mark only when `markPx` evidence is present              |
| `hybrid_ws_book_rest_reference`      | `ingest_type=hybrid_book_reference` or mixed WebSocket book and REST reference acquisition        |
| `native_ws_ticker`                   | `ingest_type=ws_ticker` with native mark captured                                                 |
| `unknown_or_insufficient_provenance` | Missing or insufficient `ingest_type`, `transport`, payload-shape, or `field_provenance` evidence |

Classification is performed by `classify_historical_regime()` at read time.

---

## Public Regime Inventory

The following entries are reproduced from `synapse_msi/historical_corpus/inventory.py`.

| regime_id | venue | classifier_label | ingest_type | transport | effective_start | effective_end | current_production |
|-----------|-------|------------------|-------------|---------|-----------------|---------------|--------------------|
| `binance.pure_rest.canonical_v1` | binance | `pure_rest` | `canonical_v1` | `rest` | `2026-04-13T00:00:00Z` | `2026-07-13T23:59:59Z` | false |
| `binance.ws_top_of_book.midpoint_proxy` | binance | `ws_top_of_book_midpoint` | `ws_top_of_book` | `websocket` | `2026-04-16T00:00:00Z` | `2026-07-14T16:15:00Z` | false |
| `binance.ws_merged_ticker.midpoint_proxy` | binance | `ws_top_of_book_midpoint` | `ws_merged_ticker` | `websocket` | unknown | `2026-07-14T16:15:00Z` | false |
| `binance.hybrid_book_reference.native_mark` | binance | `hybrid_ws_book_rest_reference` | `hybrid_book_reference` | `hybrid` | `2026-07-14T15:57:00Z` | open | true |
| `bybit.pure_rest.canonical_v1` | bybit | `pure_rest` | `canonical_v1` | `rest` | `2026-04-13T00:00:00Z` | `2026-07-13T23:59:59Z` | false |
| `bybit.ws_top_of_book.midpoint_proxy` | bybit | `ws_top_of_book_midpoint` | `ws_top_of_book` | `websocket` | `2026-05-19T00:00:00Z` | `2026-07-14T01:22:00Z` | false |
| `bybit.native_ws_ticker.markPrice` | bybit | `native_ws_ticker` | `ws_ticker` | `websocket` | `2026-07-14T20:00:00Z` | open | true |
| `okx.pure_rest.canonical_v1` | okx | `pure_rest` | `canonical_v1` | `rest` | `2026-04-13T00:00:00Z` | `2026-04-16T22:58:38.155839Z` | false |
| `okx.ws_top_of_book.conditional_native_mark` | okx | `ws_top_of_book_conditional_native` | `ws_top_of_book` | `websocket` | `2026-04-16T23:06:13.935233Z` | open | true |
| `hyperliquid.pure_rest.canonical_v1` | hyperliquid | `pure_rest` | `canonical_v1` | `rest` | `2026-04-13T00:00:00Z` | `2026-04-16T23:35:19.963617Z` | false |
| `hyperliquid.ws_top_of_book.l1_only` | hyperliquid | `ws_top_of_book_midpoint` | `ws_top_of_book` | `websocket` | `2026-04-16T23:35:16.846026Z` | open | true |
| `unknown.insufficient_provenance` | unknown | `unknown_or_insufficient_provenance` | `unknown` | `unknown` | unknown | unknown | false |

---

## Venue-Specific Regimes

The inventory above is authoritative.

The venue summaries below reorganize the same inventory by venue and explain how each historical acquisition regime should be interpreted when reconstructing `mark_price`.

Additional narrative is included only where the retained historical archive contains transition characteristics requiring interpretation. Binance and Bybit are fully described by the published inventory, whereas OKX and Hyperliquid include retained transition artifacts (a gap and an overlap, respectively) that are relevant to interpreting the historical corpus.

### Binance

| regime_id                                   | classifier_label                | ingest_type             | transport   | Mark interpretation                                                              |
| ------------------------------------------- | ------------------------------- | ----------------------- | ----------- | -------------------------------------------------------------------------------- |
| `binance.pure_rest.canonical_v1`            | `pure_rest`                     | `canonical_v1`          | `rest`      | Native mark obtained from the REST `premiumIndex` response                       |
| `binance.ws_top_of_book.midpoint_proxy`     | `ws_top_of_book_midpoint`       | `ws_top_of_book`        | `websocket` | Top-of-book midpoint proxy; not native mark                                      |
| `binance.ws_merged_ticker.midpoint_proxy`   | `ws_top_of_book_midpoint`       | `ws_merged_ticker`      | `websocket` | Legacy merged-path classification; no retained row uses this exact `ingest_type` |
| `binance.hybrid_book_reference.native_mark` | `hybrid_ws_book_rest_reference` | `hybrid_book_reference` | `hybrid`    | WebSocket book combined with native REST reference mark                          |

### Bybit

| regime_id                             | classifier_label          | ingest_type      | transport   | Mark interpretation                                             |
| ------------------------------------- | ------------------------- | ---------------- | ----------- | --------------------------------------------------------------- |
| `bybit.pure_rest.canonical_v1`        | `pure_rest`               | `canonical_v1`   | `rest`      | REST-composed canonical payload                                 |
| `bybit.ws_top_of_book.midpoint_proxy` | `ws_top_of_book_midpoint` | `ws_top_of_book` | `websocket` | Top-of-book midpoint-era acquisition; superseded by `ws_ticker` |
| `bybit.native_ws_ticker.markPrice`    | `native_ws_ticker`        | `ws_ticker`      | `websocket` | Native `markPrice` from the WebSocket tickers channel           |

### OKX

| regime_id                                    | classifier_label                    | ingest_type      | transport   | Mark interpretation                                               |
| -------------------------------------------- | ----------------------------------- | ---------------- | ----------- | ----------------------------------------------------------------- |
| `okx.pure_rest.canonical_v1`                 | `pure_rest`                         | `canonical_v1`   | `rest`      | REST-composed canonical observation                               |
| `okx.ws_top_of_book.conditional_native_mark` | `ws_top_of_book_conditional_native` | `ws_top_of_book` | `websocket` | Native mark only when `markPx` is present in the observed message |

The last retained OKX REST observation occurred at `2026-04-16T22:58:38.155839Z`. The first retained OKX WebSocket observation occurred at `2026-04-16T23:06:13.935233Z`.

### Hyperliquid

| regime_id                            | classifier_label          | ingest_type      | transport   | Mark interpretation                                |
| ------------------------------------ | ------------------------- | ---------------- | ----------- | -------------------------------------------------- |
| `hyperliquid.pure_rest.canonical_v1` | `pure_rest`               | `canonical_v1`   | `rest`      | REST metadata plus mids composition                |
| `hyperliquid.ws_top_of_book.l1_only` | `ws_top_of_book_midpoint` | `ws_top_of_book` | `websocket` | L1-only acquisition; native venue mark unavailable |

The first retained Hyperliquid WebSocket observation occurred at `2026-04-16T23:35:16.846026Z`. The final retained REST observation occurred approximately 3.1 seconds later, at `2026-04-16T23:35:19.963617Z`.

---

## Era Summary

This summary is derived from inventory bounds and `current_production` flags. Historical periods may overlap, and row-level metadata remains authoritative.

| Era                    | Binance                         | Bybit                     | OKX                                 | Hyperliquid               |
| ---------------------- | ------------------------------- | ------------------------- | ----------------------------------- | ------------------------- |
| REST-composed          | `pure_rest`                     | `pure_rest`               | `pure_rest`                         | `pure_rest`               |
| Transitional WebSocket | `ws_top_of_book_midpoint`       | `ws_top_of_book_midpoint` | `ws_top_of_book_conditional_native` | `ws_top_of_book_midpoint` |
| Current production     | `hybrid_ws_book_rest_reference` | `native_ws_ticker`        | `ws_top_of_book_conditional_native` | `ws_top_of_book_midpoint` |

This table summarizes the historical acquisition eras represented in the retained public corpus. Exact interpretation remains governed by the inventory bounds and row-level provenance. The retained corpus preserves historical gaps and overlaps rather than rewriting transition history.

---

## Investigation Exposure

Published investigation artifacts expose acquisition regime through:

* `historical_regime`, when sufficient row-level evidence is available;
* the Field-Level Provenance section for current snapshots;
* the Legacy Consensus Compatibility section for historical mixed semantics.

Historical observations, reports, and Parquet archives are not rewritten when classification rules or inventory bounds are refined.

A later classification may improve the interpretation of an archived observation without altering the archived observation itself.

---

## Limitations

* Classification is conservative; ambiguous observations are classified as `unknown_or_insufficient_provenance`.
* Observation bounds describe the retained archive and do not necessarily establish exact collector deployment or shutdown times.
* OKX native mark depends on `markPx` evidence in each message and must not be inferred from venue identity alone.
* No retained archived observation uses Binance `ingest_type=ws_merged_ticker`; its first observed production use remains unknown.
* Gaps and overlaps between acquisition regimes are preserved when present in the archive.
* Not all monitoring-time signals are retained in public investigation bundles.
* Historical midpoint values must not be interpreted as native venue marks.
* The historical corpus must not be treated as uniformly WebSocket-native or semantically uniform.

Further provenance limitations are described in [Provenance](../specifications/provenance-standard.md#7-provenance-limitations). Evidence boundaries are defined in [Reconstruction Boundaries](reconstruction-boundaries.md).

## Related References

* [Canonical Field Specification](../specifications/canonical-field-specification.md)
* [Methodology](../specifications/reconstruction-standard.md)
* [Provenance](../specifications/provenance-standard.md)
* [Reconstruction Boundaries](reconstruction-boundaries.md)
