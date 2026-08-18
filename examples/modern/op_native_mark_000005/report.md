# Modern Native-Mark Field Comparability

## Summary

| Field | Value |
|-------|-------|
| Example ID | `op_native_mark_000005` |
| Instrument | `ETHUSDT_PERP` |
| Time window | 2026-07-24T07:10:27.161814Z → 2026-07-24T07:11:03.966942Z |
| Evidence source | Packaged `observations.jsonl` / `observations.parquet` (from archived production snapshots) |
| Acquisition provenance status | `derived_from_preserved_lineage` |
| Comparison eligibility | `comparable_after_partition` (`mixed_regime_requires_partition`) |
| Included venues (native-mark input) | binance, bybit |
| Excluded venues | hyperliquid (`missing_or_zero_mark_price`), okx (`missing_or_zero_mark_price`) |
| Peak scan timestamp | 2026-07-24T07:10:40.254317Z |

Methodology: [reconstruction-standard.md](../../../specifications/reconstruction-standard.md) · Provenance: [provenance-standard.md](../../../specifications/provenance-standard.md) · Fields: [canonical-field-specification.md](../../../specifications/canonical-field-specification.md)

---

## Observed Evidence

Facts retained in the packaged observations:

* Four venue rows are present at the peak scan for `ETHUSDT_PERP`.
* Every retained venue observation carries explicit modern acquisition regime identity (see `provenance.json` and per-row acquisition metadata).
* Binance and Bybit retain nonzero native mark values used as consensus input.
* Hyperliquid retains `mark_price` of `0` with acquisition regime `hyperliquid.ws_top_of_book.l1_only` (L1 bid/ask path; no comparable native mark on this stream).
* OKX retains `mark_price` of `0` with acquisition regime `okx.ws_top_of_book.conditional_native_mark` (retained tick has no usable native mark).
* Exact zero is treated as unavailable for the narrowly specified canonical mark fields; zeros are preserved in the public JSONL/Parquet, not rewritten.

Authoritative provenance sidecar: `provenance.json` (`acquisition_regime_investigation_sidecar_v1`, investigation `6b4444214bf6d9fff3c43ece`).

---

## Deterministic Reconstruction

Recomputed from packaged observations under `canonical_snapshot_consensus_v1`:

| Output | Value |
|--------|------:|
| Consensus mark (peak) | 1898.42 |
| Disagreement score (peak) | 24.1 |

| Venue | Included | Mark | Deviation (bps) | Acquisition regime |
|-------|:--------:|------:|----------------:|--------------------|
| binance | True | 1893.85 | 24.1 | `binance.hybrid_book_reference.native_mark` |
| bybit | True | 1902.99 | 24.1 | `bybit.native_ws_ticker.markPrice` |
| hyperliquid | False | 0 | — | `hyperliquid.ws_top_of_book.l1_only` |
| okx | False | 0 | — | `okx.ws_top_of_book.conditional_native_mark` |

What is deterministically reproduced: peak consensus mark, disagreement score, per-venue inclusion/exclusion, and mark deviations for included venues.

---

## Field Comparability

This is a **field-level native-mark** comparison, not a generic four-venue market-state equality claim.

* No midpoint, oracle, index, last trade, or derived substitute is inserted for missing native marks.
* Comparability eligibility is `comparable_after_partition` because regimes differ and native-mark input is partitioned to venues with usable native marks.
* Result: a **partitioned two-venue** native-mark comparison (Binance–Bybit), not a four-venue native-mark comparison.

### Binance acquisition note

Binance market-data transport for the book may be WebSocket. The **native mark** field is sourced through the documented **reference** component of the hybrid acquisition regime `binance.hybrid_book_reference.native_mark`. This report does **not** claim that the native mark itself was necessarily emitted by the L1 WebSocket stream.

### Bybit

Bybit native mark is sourced from the documented WebSocket ticker field `markPrice` under `bybit.native_ws_ticker.markPrice`.

---

## Included and Excluded Venues

| Venue | Native-mark role | Reason |
|-------|------------------|--------|
| binance | Included | Eligible nonzero native mark under hybrid reference component |
| bybit | Included | Eligible nonzero native mark under WS ticker `markPrice` |
| hyperliquid | Excluded | Retained acquisition regime is L1-only; no comparable native mark (`missing_or_zero_mark_price`) |
| okx | Excluded | Retained observation has no usable native mark (`missing_or_zero_mark_price`) |

---

## Operational Interpretation

The packaged evidence supports a reproducible partitioned native-mark disagreement between Binance and Bybit at the peak scan, with Hyperliquid and OKX excluded fail-closed from native-mark input.

---

## Not Established

This package does **not** establish:

* a four-venue native-mark consensus;
* economic “correct” mark or fair value;
* root cause of the Binance–Bybit mark divergence;
* that Hyperliquid or OKX lacked marks on every possible venue channel outside the retained acquisition paths;
* attribution requiring proprietary internal evidence.

---

## Reproduction

```bash
python scripts/reproduce_investigation.py --example examples/modern/op_native_mark_000005
```

Expected: `REPRODUCTION VERIFIED` with `Exact match: true`.

---

## Appendix

| Field | Value |
|-------|-------|
| report_schema_version | `synapse_investigation_report_v1` |
| methodology_version | `canonical_snapshot_consensus_v1` |
| detection_version | `operational_episode_v1` |
| reconstruction_version | `l1_canonical_v1` |
| investigation_id | `6b4444214bf6d9fff3c43ece` |
| observation_count | 4 |
| linked_regime_ids | `binance.hybrid_book_reference.native_mark`, `bybit.native_ws_ticker.markPrice`, `hyperliquid.ws_top_of_book.l1_only`, `okx.ws_top_of_book.conditional_native_mark` |
