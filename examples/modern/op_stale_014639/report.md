# Modern Bounded Temporal Freshness Reconstruction

## Summary

| Field | Value |
|-------|-------|
| Example ID | `op_stale_014639` |
| Instrument | `ETHUSDT_PERP` |
| Time window | 2026-07-21T08:51:28.079150Z → 2026-07-21T08:56:17.234571Z |
| Evidence source | Packaged multi-snapshot `observations.jsonl` / `observations.parquet` |
| Acquisition provenance status | `derived_from_preserved_lineage` |
| Comparison eligibility | `comparable_after_partition` (`mixed_regime_requires_partition`) |
| Affected venue (detector) | `binance` |
| Temporal reference venues | bybit, hyperliquid, okx |
| Packaged snapshots | 13 (bounded temporal sequence) |
| Packaged observations | 52 |

Methodology: [reconstruction-standard.md](../../../specifications/reconstruction-standard.md) · Provenance: [provenance-standard.md](../../../specifications/provenance-standard.md) · Boundaries: [reconstruction-boundaries.md](../../../docs/reconstruction-boundaries.md)

---

## Observed Evidence

Only facts retained in the packaged sequence:

* Healthy pre-entry snapshot at `2026-07-21T08:51:26.245940Z` (Binance age &lt; 60s).
* Threshold entry at `2026-07-21T08:51:28.079150Z` (Binance age ≥ 60s while usable).
* Progression to peak observation age at scan `2026-07-21T08:55:48.911654Z` (sequence `3003277`).
* Adoption of a newer Binance venue observation timestamp at `2026-07-21T08:55:50.342003Z` where applicable.
* Recovery start and five consecutive healthy recovery snapshots ending at `2026-07-21T08:56:17.234571Z`.
* Qualified episode end at that recovery completion.
* Every packaged observation retains venue, instrument, event/venue timestamp, top-level `collector_received_at`, `effective_observation_timestamp` (identical to `venue_timestamp` here), acquisition regime identity, collector identity, transport, ingest type, field provenance, and public-safe `raw_linkage.raw_row_id`.

Peak venue lag table (packaged peak snapshot):

| Venue | Temporally usable | Native-mark eligible | Age (s) | Mark |
|-------|:-----------------:|:--------------------:|--------:|------|
| binance | True | True | 321.9 | 1939.95017829 |
| bybit | True | True | 2.6 | 1939.26 |
| hyperliquid | True | False | 0.0 | 0 |
| okx | True | False | 5.2 | 0 |

Hyperliquid and OKX are usable for timestamp-based freshness reconstruction but excluded from native-mark consensus because their retained marks are zero (`missing_or_zero_mark_price`).

---

## Deterministic Detector Result

Synapse detects freshness using:

```text
age_seconds = scan_timestamp − venue observation timestamp
```

with enter threshold **60 seconds** while the venue remains usable, and recovery after **five consecutive** healthy snapshots.

Reproduction **recomputes** the following from the packaged sequence (it does not trust stored episode metadata alone):

| Field | Recomputed value |
|-------|------------------|
| Episode start | `2026-07-21T08:51:28.079150Z` |
| Episode end | `2026-07-21T08:56:17.234571Z` |
| Duration | `289.155421` seconds |
| Peak observation age | `321.933973` seconds |
| Peak scan timestamp | `2026-07-21T08:55:48.911654Z` |
| Threshold crossing | `True` (enter threshold 60.0s) |
| Recovery start | `2026-07-21T08:56:10.314291Z` |
| Recovery snapshot count | `5` |
| Recovery qualification | `True` |
| Adoption timestamp | `2026-07-21T08:55:50.342003Z` |

Peak native-mark consensus at the peak scan (independent of freshness bounds):

* Consensus mark: **1939.61**
* Disagreement score: **1.8**

These consensus and disagreement values are computed from **Binance and Bybit only**. Hyperliquid and OKX participate as temporally usable observations / temporal reference venues for freshness analysis; they do not contribute native-mark values to the median or disagreement score.

---

## Receive-path timing versus freshness age

Freshness age is derived from the effective observation timestamp (identical to `venue_timestamp` on every row in this package). Where `collector_received_at` is present, comparing collector receipt time with the venue-event timestamp provides evidence for separating age already present at receipt from delay introduced after receipt. `raw_linkage` (`linkage_status`, public-safe `raw_row_id`, `snapshot_sequence`) is provenance/reproducibility metadata for tracing packaged rows; it is not a market-state field and is not collector-health telemetry.

At the peak Binance observation (`scan_timestamp` `2026-07-21T08:55:48.911654Z`):

| Clock | Value |
|-------|-------|
| `venue_timestamp` / `effective_observation_timestamp` | `2026-07-21T08:50:26.977681+00:00` |
| `collector_received_at` | `2026-07-21T08:50:26.824724+00:00` |
| Peak observation age (`scan_timestamp − effective observation timestamp`) | `321.933973` s |
| `collector_received_at − venue_timestamp` | about `−0.15` s |

Collector receipt was essentially contemporaneous with the venue-event timestamp (within about 0.15 seconds). The large peak freshness age is therefore not explained by material collector receive-path lag on that observation; it accumulated after receipt as the same observation aged across later scans. This receive-timing comparison does **not** prove collector health, heartbeat continuity, or a single operational root cause.

---

## Operational Interpretation

`mixed/indeterminate operational cause`

The retained evidence supports detection of timestamp-based freshness degradation and deterministic recovery. Receive-path fields support separating near-receipt timing from post-receipt age accumulation. The package still does **not** establish a single operational root cause.

Do **not** describe this example simply as “Binance venue staleness.”

---

## Not Established

The packaged evidence does **not** independently establish whether the cause was:

* venue-side publication delay;
* collector delay after initial receipt;
* transport delay;
* downstream ingest delay;
* or another component.

Receive-path timing alone does not establish collector health, heartbeat continuity, or a unique operational root cause.

---

## Reconstruction Boundaries

Interpret with:

* [reconstruction-standard.md](../../../specifications/reconstruction-standard.md)
* [provenance-standard.md](../../../specifications/provenance-standard.md)
* [reconstruction-boundaries.md](../../../docs/reconstruction-boundaries.md)
* [investigation-reproducibility.md](../../../docs/investigation-reproducibility.md)

External reconstruction establishes observable timing lag and recovery relative to archived timestamps. It does not localize the delay to a single subsystem without additional evidence.

---

## Reproduction

```bash
python scripts/reproduce_investigation.py --example examples/modern/op_stale_014639
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
| investigation_id | `8ba94e2aa3607e2bfb7dbc41` |
| observation_count | 52 |
| packaged_snapshot_count | 13 |
| max_age_seconds | 321.933973 |
| linkage_status | `derived_from_preserved_lineage` |
| comparability_eligibility | `comparable_after_partition` |
