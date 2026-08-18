# Reconstruction Methodology

**Status:** Normative
**Applies to:** Synapse MSI External Reconstruction
**Methodology version:** MSI v1
**Last updated:** 2026-07-30

> If another public document conflicts with this specification regarding reconstruction algorithms or derived metrics, this specification is authoritative.

### Normative methodology versus public reference package scope

This document defines the normative reconstruction methodology for Synapse MSI External Reconstruction.

The presence of an algorithm in this normative standard does not by itself mean that the public `synapse_msi/` reference package implements it. Public reference implementation coverage is identified explicitly. A package conformance claim covers only the algorithms, fields, and version pins declared by that package.

The public `synapse_msi/` reference package currently verifies, for the committed reproducibility packages:

* package observation loading and canonical absence handling;
* legacy published mark consensus and disagreement reproduction;
* published package mark exclusion reasons on the equality surface (§4);
* acquisition-regime assignment and fail-closed comparability eligibility;
* provenance sidecar consistency;
* venue-staleness / freshness episode reconstruction where a freshness episode is published;
* manifest/hash integrity and JSONL/Parquet parity where applicable;
* the exact published equality surfaces in [conformance.md](conformance.md).

It does **not** currently ship every broader semantic metric or detector defined in this methodology (including all native-mark, midpoint, open-interest, and semantic episode engine paths). Those algorithms remain normatively specified. A system that claims implementation of a particular semantic metric or detector MUST implement the corresponding normative algorithm; it MUST NOT claim implementation merely because the algorithm appears in this specification.

The public reference package is not authoritative over the normative methodology. Where it claims to implement a normative algorithm, its behavior MUST conform to that algorithm.

Related: [canonical-field-specification.md](canonical-field-specification.md) · [provenance-standard.md](provenance-standard.md) · [reconstruction-boundaries.md](../docs/reconstruction-boundaries.md) · [historical-acquisition-regimes.md](../docs/historical-acquisition-regimes.md)

---

## 1. Purpose

This document defines how reconstructed observations become canonical snapshots and investigation artifacts. It specifies the algorithms that produce consensus values, disagreement metrics, operational episodes, and investigation aggregates.

Field meanings, provenance lineage, and evidentiary limits are defined elsewhere:

| Document | Governs |
|---|---|
| [canonical-field-specification.md](canonical-field-specification.md) | Field semantics, sourcing, aliases, persistence |
| [provenance-standard.md](provenance-standard.md) | Evidence lineage |
| [reconstruction-boundaries.md](../docs/reconstruction-boundaries.md) | Evidentiary limits |

---

## 2. Reconstruction inputs

Reconstruction requires the following inputs per instrument scan:

| Input | Role |
|---|---|
| **Normalized canonical observations** | One row per venue in `normalized[]` with market-state fields defined in [canonical-field-specification.md](canonical-field-specification.md) |
| **Provenance metadata** | `field_provenance`, `source_provenance`, and `observation_provenance` when present on archived rows; lineage rules in [provenance-standard.md](provenance-standard.md) |
| **Timestamps** | `meta.scan_timestamp` (snapshot assembly time) and per-venue `normalized[].timestamp` (venue event time) |
| **Observation eligibility** | Per-venue `usable` flag and metric-specific eligibility rules that determine which rows and field values participate in each algorithm |

Consensus and semantic disagreement metrics are computed at snapshot write time and stored on the archived snapshot. Episode detection and investigation generation consume stored snapshot values; they do not recompute consensus at read time.

---

## 3. Canonical observation selection

### One observation per venue

Each canonical snapshot contains at most one normalized row per venue. Field sourcing and alias resolution are defined in [canonical-field-specification.md](canonical-field-specification.md); this section states only reconstruction assumptions.

### Timestamp ordering

Episode detection orders archived snapshots deterministically:

```text
sort key = (0, sequence, scan_timestamp)  when sequence is present
sort key = (1, 0, scan_timestamp)         when sequence is absent
```

`scan_timestamp` is compared as an ISO-8601 UTC string.

Per-venue age for staleness detection:

```text
age_seconds = max(0, scan_timestamp − normalized[].timestamp)
```

### Normalization assumptions

- Unusable rows (`usable=false`) remain in `normalized[]`; they are not removed before persistence.
- Legacy consensus does not filter on `usable` before median aggregation.
- Semantic metrics apply metric-specific eligibility rules independent of the legacy `.usable` gate alone.

### Observation eligibility

| Context | Eligibility rule |
|---|---|
| Legacy mark consensus | Truthy `mark_price` not equal to `"0"` that parses to `Decimal`, on each row in `normalized[]` |
| Legacy funding consensus | Truthy `funding_rate` not equal to `"0"` that parses to `Decimal`, on each row in `normalized[]` |
| Open-interest consensus | Trustworthy OI per venue rules in §4 |
| Semantic metrics | Field-specific rules in §5 |
| Episode `usable_venue_count` | Count of rows where `usable=true` |
| L1 cross-venue metrics | Rows where `usable=true` with valid bid/ask or funding data per metric |

---

## 4. Consensus methodology

All venues in the `normalized[]` list are included. **`.usable` is not filtered** before mark or funding median aggregation.

Quantization uses `ROUND_HALF_UP`. Median is the unweighted median of eligible values; when the eligible count is even, the median is the arithmetic mean of the two middle values after sorting.

### Mark-price consensus

| Property | Rule |
|---|---|
| **Input field** | `normalized[].mark_price` |
| **Eligible inputs** | Values that are truthy, not equal to `"0"`, and parse to `Decimal` |
| **Excluded inputs** | Null, empty, `"0"`, and values that fail `Decimal` parsing |
| **Mathematical method** | Unweighted median of eligible values |
| **Tie handling** | Mean of the two middle values when the eligible count is even |
| **Missing-value handling** | Missing venues are ignored; they do not contribute to the median |
| **Output units** | Price string |
| **Quantization** | 2 decimal places (`ROUND_HALF_UP`) |
| **Fallback** | `"0.000000000000"` when no eligible values exist |
| **Deterministic ordering** | `venues_used` and `venues_usable` are sorted alphabetically by venue name |

### Published package mark exclusion reasons (equality surface)

When reproducing a published investigation package under the public reference package path — recomputing legacy mark consensus and disagreement from packaged observations — the published `excluded_venues` map on the equality surface ([conformance.md](conformance.md) §2) MUST use exactly these serialized reason codes:

| Serialized reason code | When used |
|---|---|
| `missing_or_zero_mark_price` | The package observation does not contain a usable positive mark value for this reconstruction path |
| `mark_price_parse_failure` | A published mark value is present but cannot be parsed into the numeric form required by the reconstruction algorithm |

#### `missing_or_zero_mark_price`

Use when the package observation does not contain a usable positive mark value for the reconstruction path, including:

* missing value;
* explicit `null`;
* zero;
* a value that normalizes to zero.

This reason reflects unavailable usable **package evidence**. It MUST NOT be interpreted as a claim that the venue itself lacked a mark price outside the preserved evidence.

#### `mark_price_parse_failure`

Use when a published mark value is present but cannot be parsed into the numeric form required by the reconstruction algorithm.

This is an evidence-parsing exclusion. It MUST NOT be interpreted as a statement about venue economic behavior.

Midpoint, oracle, index, or last-trade values MUST NOT be substituted for an unavailable native mark. A derived midpoint MUST NOT be redefined as a native mark.

These serialized package codes are distinct from conceptual semantic-methodology eligibility language such as `no_native_mark_price` in §5. For the published equality surface field `excluded_venues`, independent implementations MUST emit the exact package codes above. They MUST NOT substitute `no_native_mark_price` (or other conceptual labels) for `missing_or_zero_mark_price` on that surface.

A package’s `source.episode_type` (or equivalent label) MAY record the original detection vocabulary (for example `native_mark_disagreement`). Peak-package reproduction of `consensus_mark`, `disagreement_score`, `included_venues`, and `excluded_venues` under this public reference path still uses the **legacy mark consensus** rules in this section after applying the exclusion reasons above, unless the package explicitly declares and ships a different recomputation path.

### Funding-rate consensus

| Property | Rule |
|---|---|
| **Input field** | `normalized[].funding_rate` |
| **Eligible inputs** | Values that are truthy, not equal to `"0"`, and parse to `Decimal` |
| **Excluded inputs** | Null, empty, `"0"`, and values that fail `Decimal` parsing |
| **Mathematical method** | Unweighted median of eligible values |
| **Tie handling** | Same as mark consensus |
| **Missing-value handling** | Missing venues are ignored |
| **Output units** | Decimal funding rate string |
| **Quantization** | 8 decimal places (`ROUND_HALF_UP`) |
| **Fallback** | `"0.000000000000"` when no eligible values exist |

### Open-interest consensus (`oi_total_usd`)

| Property | Rule |
|---|---|
| **Eligible inputs** | Per venue: `oi_usd_trustworthy` when set; otherwise Bybit with `oi_calc_method == "direct_usd_field"` using `oi_usd` |
| **Excluded inputs** | All other venues' `oi_usd`; values where `oi_value ≤ 0` or `oi_value > 200,000,000,000`; values that fail `Decimal` parsing |
| **Mathematical method** | Unweighted median of eligible OI values (**not a sum**) |
| **Tie handling** | Same as mark consensus |
| **Missing-value handling** | `null` when no venue qualifies (**not zero**) |
| **Output units** | USD string or `null` |
| **Quantization** | 2 decimal places (`ROUND_HALF_UP`) |
| **Deterministic ordering** | `oi_source_venues` sorted and deduplicated alphabetically |

### Venue count and quality classification

| Field | Rule |
|---|---|
| **`venues_count`** | `len(normalized[])` — count of rows passed to consensus |
| **`consensus.quality`** | `good` when `len(normalized[]) ≥ 2`; `degraded` when `len(normalized[]) == 1`; `unusable` when `len(normalized[]) == 0` |

Quality is based on input row count, not on the count of rows with `usable=true`.

### Disagreement inputs (legacy consensus)

Legacy `consensus.disagreement_score` is derived from the same eligible mark prices used for mark consensus:

| Property | Rule |
|---|---|
| **Input field** | `normalized[].mark_price` |
| **Eligible inputs** | Same set as mark-price consensus |
| **Excluded inputs** | Same exclusions as mark-price consensus |
| **Semantic note** | `mark_price` carries regime-dependent semantics in historical archives; see [historical-acquisition-regimes.md](../docs/historical-acquisition-regimes.md) |

The disagreement formula, per-venue breakdown, semantic metrics, and episode thresholds are specified in §5.

### Divergence flag

| Flag | Condition |
|---|---|
| `MARK_PRICE_DIVERGENCE_HIGH` | `disagreement_score > 50` basis points (`CONSENSUS_MAX_DISAGREEMENT_BPS`) |

---

## 5. Disagreement methodology

### Legacy consensus disagreement (`consensus.disagreement_score`)

| Property | Rule |
|---|---|
| **Mathematical method** | `median_mark = median(eligible mark prices)`; `deviation_bps_i = abs(mark_price_i − median_mark) / median_mark × 10,000`; `disagreement_score = max(deviation_bps_i)` |
| **Eligible inputs** | Eligible mark prices from §4 |
| **Excluded inputs** | Same exclusions as mark consensus |
| **Tie handling** | `max()` selects one maximum deviation when multiple venues tie |
| **Missing-value handling** | `"0.0"` basis points (1 decimal place, `ROUND_HALF_UP`) when no eligible mark prices or when `median_mark ≤ 0` |
| **Output units** | Basis points |
| **Quantization** | 1 decimal place (`ROUND_HALF_UP`) |
| **Outlier removal** | None |

### Per-venue disagreement breakdown (`consensus.disagreement_breakdown`)

Computed when `len(normalized[]) ≥ 2` and both valid mark prices and valid funding rates exist with at least two venue names.

Per field (`mark_price`, `funding_rate`):

```text
deviation_pct_i = abs(value_i − consensus_value) / abs(consensus_value) × 100
spread_bps       = abs(max(values) − min(values)) / abs(consensus_value) × 10,000
outliers         = venues where deviation_pct_i > 5.0
```

| Property | Rule |
|---|---|
| **Output units** | Percent and basis points (basis points quantized to 1 decimal place, `ROUND_HALF_UP`) |
| **Outlier threshold** | **5.0** percent deviation |

### Semantic field disagreement metrics

Stored in `consensus.field_disagreement_metrics`.

| Metric | Input field | Status |
|---|---|---|
| `native_mark_disagreement` | `native_mark_price` | Normatively specified; not implemented by this public reference package |
| `l1_midpoint_disagreement` | `top_of_book_mid` | Normatively specified; not implemented by this public reference package |
| `funding_disagreement` | — | **Not implemented** |

Shared formula per semantic metric:

```text
eligible_values  = field values passing metric eligibility (§5.3)
consensus_value  = median(eligible_values), quantized to 2 dp
deviation_bps_i  = abs(value_i − consensus_value) / consensus_value × 10,000
disagreement_score = max(deviation_bps_i), quantized to 1 dp bps
```

| Property | Rule |
|---|---|
| **Minimum eligible venues** | **2** (`MIN_SEMANTIC_ELIGIBLE_VENUES`); metric is inactive below this count |
| **Eligible value exclusion** | Null, `"0"`, values `≤ 0`, and values that fail `Decimal` parsing |
| **Missing-value handling** | `consensus_value = null`, `disagreement_score = "0.0"` basis points (1 decimal place, `ROUND_HALF_UP`) when no eligible values |
| **Deterministic ordering** | `eligible_venues` and `excluded_venues` sorted alphabetically |

#### `native_mark_disagreement` eligibility

A venue is excluded when:

- `native_mark_price` is absent and field provenance does not indicate a native mark → conceptual condition `no_native_mark_price` (semantic-methodology eligibility language only; **not** a serialized reason code on the published package equality surface — see §4 published package mark exclusion reasons)
- Binance temporal exclusion applies (§5.3.1)
- Value is null, `"0"`, `≤ 0`, or invalid

#### `l1_midpoint_disagreement` eligibility

A venue is excluded when:

- `top_of_book_mid` is absent and neither field provenance nor the observation payload indicates a top-of-book midpoint → `no_top_of_book_mid`
- Value is null, `"0"`, `≤ 0`, or invalid
- Native mark fields are not substituted for midpoint

#### Binance native-mark temporal exclusion

For Binance rows, a venue is excluded from `native_mark_disagreement` when any of the following holds (checked in order):

| Condition | Exclusion reason |
|---|---|
| `field_provenance.native_mark_price.degraded` with reason in `reference_stale`, `component_skew_exceeded`, `cadence_incompatible`, `episode_persistence_below_reference_cadence`, `stale_reference_component` | That reason string |
| `field_provenance.native_mark_price.degraded` with any other reason | `reference_stale` |
| `observation_provenance.degraded` with a `degradation_reason` | That reason string |
| `reference_component_age_seconds > BINANCE_COMPONENT_MAX_AGE_SECONDS` | `reference_stale` |
| `component_timestamp_skew_seconds > BINANCE_COMPONENT_MAX_SKEW_SECONDS` | `component_skew_exceeded` |
| `reference_component_age_seconds > BINANCE_REFERENCE_POLL_INTERVAL_SECONDS × 2` | `cadence_incompatible` |
| `episode_duration_seconds < BINANCE_REFERENCE_POLL_INTERVAL_SECONDS` (when provided) | `episode_persistence_below_reference_cadence` |

Current documented defaults:

| Constant | Default |
|---|---|
| `BINANCE_COMPONENT_MAX_AGE_SECONDS` | 30 |
| `BINANCE_COMPONENT_MAX_SKEW_SECONDS` | 5 |
| `BINANCE_REFERENCE_POLL_INTERVAL_SECONDS` | 5 |

These values are current documented defaults and may be overridden at deployment. Historical reproduction requires the effective values active for the observation period. Where those values are not persisted or covered by a dated configuration-regime record, exact temporal-eligibility reproduction cannot be independently established from the public artifact alone.

### Per-venue disagreement (semantic episodes)

For semantic episode affected-venue attribution:

1. If `per_field.outliers` is non-empty, affected venues are those outliers (sorted).
2. Otherwise, for each normalized row, compute deviation from the metric `consensus_value`; a venue is affected when `deviation_bps ≥ 10.0` or when its comparison value is null or `≤ 0`.

Comparison values: `native_mark_price` for native-mark episodes; `top_of_book_mid` (or `(bid_price + ask_price) / 2` when midpoint absent) for L1 episodes.

### Per-venue disagreement (L1 snapshot metrics)

Computed at snapshot write time and stored in `l1_metrics`. These metrics filter on `usable=true`.

#### `max_price_deviation`

| Property | Rule |
|---|---|
| **Eligible inputs** | Usable venues with parseable `mark_price > 0`, or valid `bid_price` and `ask_price` both `> 0` (midpoint fallback) |
| **Excluded inputs** | Non-usable venues; venues without valid price |
| **Mathematical method** | `deviation_bps_i = abs(venue_price − mark_price_consensus) / mark_price_consensus × 10,000`; return `max(deviation_bps_i)` |
| **Missing-value handling** | `null` when `mark_price_consensus ≤ 0` or no valid venues |
| **Output units** | Basis points (float, not quantized on storage) |
| **Minimum venues** | **1** valid usable venue |

#### `funding_spread`

| Property | Rule |
|---|---|
| **Eligible inputs** | Usable venues with truthy, parseable `funding_rate` |
| **Excluded inputs** | Non-usable venues; invalid funding values |
| **Mathematical method** | `max(funding_rates) − min(funding_rates)` |
| **Missing-value handling** | `null` when fewer than **2** valid funding rates |
| **Output units** | Funding rate delta (decimal, not basis points) |

#### `spread_bps`

| Property | Rule |
|---|---|
| **Eligible inputs** | Usable venues with `bid_price > 0`, `ask_price > 0`, and `ask_price ≥ bid_price` |
| **Mathematical method** | Per venue: `(ask_price − bid_price) / mark_price_consensus × 10,000`; return **median** of per-venue spreads |
| **Missing-value handling** | `null` when `mark_price_consensus ≤ 0` or no valid spreads |
| **Output units** | Basis points (float) |

### Episode disagreement thresholds

| Constant | Value |
|---|---|
| `DISAGREEMENT_ENTER` (`SEMANTIC_DISAGREEMENT_ENTER_BPS`) | **10.0** bps |
| `MIN_USABLE_ENTER` | **2** |
| `STALE_ENTER_SECONDS` | **60.0** s |
| `RECOVERY_SNAPSHOTS` | **5** |

### Peak disagreement (`max_disagreement_score`)

During an open episode, on each snapshot:

```text
max_disagreement_score = max(previous max_disagreement_score, current snapshot score)
```

| Episode type | Score source |
|---|---|
| `consensus_quality` | Legacy `consensus.disagreement_score` |
| `native_mark_disagreement` | `native_mark_disagreement.disagreement_score` |
| `l1_midpoint_disagreement` | `l1_midpoint_disagreement.disagreement_score` |
| `venue_staleness` | Legacy `consensus.disagreement_score` (secondary); primary aggregate is `max_age_seconds` |

`peak_disagreement_score` in investigation presentation is an alias for `max_disagreement_score`; it is not a separate calculation.

### Persistence and recovery

Recovery requires **5 consecutive** snapshots satisfying the healthy condition for the episode type. The consecutive counter resets to 0 on any non-healthy snapshot. Open episodes at end of input close with reason `end_of_input`.

| Episode type | Healthy condition |
|---|---|
| `consensus_quality` | `disagreement_score < 10.0` **and** `usable_venue_count > 2` |
| `native_mark_disagreement` | Semantic metric `disagreement_score < 10.0` |
| `l1_midpoint_disagreement` | Semantic metric `disagreement_score < 10.0` |
| `venue_staleness` | Same venue `usable=true` **and** `age_seconds < 60.0` |

### Episode entry

| Episode type | Entry condition |
|---|---|
| `consensus_quality` | `disagreement_score ≥ 10.0` **and** (`normalized[]` empty **or** `usable_venue_count ≤ 2`) |
| `native_mark_disagreement` | `len(eligible_venues) ≥ 2` **and** semantic `disagreement_score ≥ 10.0` |
| `l1_midpoint_disagreement` | `len(eligible_venues) ≥ 2` **and** semantic `disagreement_score ≥ 10.0` |
| `venue_staleness` | Per venue: `usable=true` **and** `age_seconds ≥ 60.0` |

| Episode type | Status |
|---|---|
| `market_disagreement` | **Disabled** |
| `funding_disagreement` | **Not implemented** |

---

## 6. Operational episode methodology

### Snapshot evaluation

For each archived snapshot in deterministic order (§3):

1. Parse `normalized[]`, `consensus`, and `meta.scan_timestamp`.
2. Extract legacy `disagreement_score` and semantic metrics from stored `consensus.field_disagreement_metrics`.
3. Compute `usable_venue_count`, per-venue `age_seconds`, and `excluded_venue_count`.
4. Apply entry, continuation, and recovery rules for each active episode type (§5).

Episode detection reads stored consensus and semantic metrics; it does not recompute them.

### Entry conditions

See §5 episode entry table. On entry, the detector records `entry_evidence` including entry scores, eligible/excluded venues (semantic types), and entry age (staleness type).

### Continuation

While an episode is open, each subsequent snapshot:

- Updates `end_timestamp` to the current `scan_timestamp`
- Increments `snapshot_count`
- Updates running aggregates: `max_disagreement_score`, `min_usable_venues`, `max_excluded_venues`, `max_age_seconds` (staleness), `max_affected_venues` (semantic)

### Recovery

See §5 persistence table. On recovery, the episode closes with `close_reason = "recovered"` and `recovery_snapshot_count = 5`.

### Aggregation

Closed episodes emit one row per episode with:

| Column | Derivation |
|---|---|
| `duration_seconds` | `max(0, end_timestamp − start_timestamp)` in seconds |
| `max_disagreement_score` | Running maximum per §5 |
| `min_usable_venues` | Minimum `usable_venue_count` observed during episode |
| `max_excluded_venues` | Maximum `excluded_venue_count` observed during episode |
| `max_age_seconds` | Maximum per-venue `age_seconds` during `venue_staleness` episodes |
| `evidence_summary` | JSON of entry evidence and close reason, keys sorted |

### Published `venue_staleness` package fields

When a published reproducibility package includes a `freshness_episode` object for a `venue_staleness` detector result, the following fields are derived from the reconstructed affected-venue scan sequence (one observation per scan for the affected venue, ordered by §3). They are required on the published equality surface ([conformance.md](conformance.md) §2).

Scan domain: packaged observations for the declared instrument and affected venue, grouped into scans and ordered deterministically per §3. Timestamp source for ages is the venue observation timestamp preference in [canonical-field-specification.md §6](canonical-field-specification.md#6-temporal-and-provenance-fields) (`venue_timestamp`, then `timestamp`, then `effective_observation_timestamp`). Field values below are **scan timestamps** (`scan_timestamp`) or the scan’s supplied integer `sequence`, not newly generated indices.

#### `pre_entry_scan_timestamp`

* The `scan_timestamp` of the last non-stale scan for the affected venue immediately preceding episode entry.
* Non-stale means the healthy condition for `venue_staleness` in §5 (`usable=true` and `age_seconds < 60.0`).
* Ordering is within the reconstructed affected-venue / instrument scan sequence.
* The value is that scan’s `scan_timestamp`, not the venue observation timestamp.
* The value is `null` when the episode begins on the first available scan in the packaged sequence (no preceding non-stale scan).

#### `adoption_scan_timestamp`

* Evaluated only after episode entry.
* Let `entry_venue_observation_timestamp` be the selected venue observation timestamp on the entry scan.
* `adoption_scan_timestamp` is the `scan_timestamp` of the first in-episode scan whose selected venue observation timestamp differs from `entry_venue_observation_timestamp`.
* It records when the affected venue first adopts a newer observation during the open stale episode.
* Peak-age updates do **not** reset or replace `entry_venue_observation_timestamp`.
* Repeated in-episode scans that keep the same venue observation timestamp do not qualify as adoption.
* Later additional venue-timestamp changes do not move the adoption scan; the first qualifying scan is retained.
* The value is `null` if no qualifying in-episode scan exists.
* The value is a scan timestamp (supplied/normalized `scan_timestamp`), not a generated index.

#### `peak_sequence`

* The integer `sequence` attached to the scan selected as the episode peak.
* During an open episode, the peak scan is updated only when the current scan’s `age_seconds` is **strictly greater** than the current peak age.
* Equal peak ages therefore retain the earliest already-selected peak and its `sequence`.
* A later scan with a strictly larger age replaces both the peak scan and `peak_sequence`.
* `peak_sequence` is the scan’s **supplied** sequence value from the packaged observations; it is not a newly generated zero-based or one-based index over episode scans.

### Investigation generation

Investigation artifacts are derived from closed operational episodes and the archived snapshots referenced by the investigation window:

1. Episode rows supply window bounds, episode type, and aggregates.
2. Archived snapshots supply per-snapshot evidence for the window.
3. Investigation materialization combines episode summaries with snapshot references; version pins are embedded per §7.

Investigation reports are presentation artifacts. An episode aggregate alone does not preserve the per-snapshot time series. Evidentiary limits: [reconstruction-boundaries.md](../docs/reconstruction-boundaries.md).

---

## 7. Deterministic reproducibility

Identical archived evidence, processed under identical methodology and field-specification versions, produces identical reconstructed consensus values, semantic metrics, episode windows, and episode aggregates.

### Required inputs for reproduction

| Input | Purpose |
|---|---|
| Archived canonical snapshots for the reconstruction window | `normalized[]`, stored `consensus`, `l1_metrics`, `meta` |
| **Methodology version** | Algorithm compatibility |
| **Canonical field specification** | Field semantics and alias rules at analysis time |
| **Provenance** | Regime interpretation per [provenance-standard.md](provenance-standard.md) |
| **Reconstruction window** | Start and end bounds for snapshot selection |

### Version pins (current MSI v1)

| Pin | Value |
|---|---|
| `methodology_version` | `canonical_snapshot_consensus_v1` |
| `detection_version` | `operational_episode_v1` |
| `reconstruction_version` | `l1_canonical_v1` |
| `semantics_version` | `investigation_evidence_v1` |
| `reconstruction_semantics_version` | `reconstruction_confidence_v1` |

Artifacts retain the version pins present at generation. Later methodology changes must not silently reinterpret prior artifacts.

### Reproduction scope

Reproducibility applies to metrics, episode windows, and aggregates computed from archived snapshots. It does not extend beyond archived evidence: live observations, collector health, or infrastructure state outside the archive are not reproducible from archived snapshots alone.

---

## 8. Historical methodology compatibility

Historical acquisition transport may differ across archive rows. Historical field semantics are interpreted using historical provenance and regime classification, not current-production sourcing assumptions alone.

Historical methodology must not reinterpret archived evidence using newer field semantics. When `mark_price` semantics differ by regime, legacy consensus inherits that variability; semantic metrics (`native_mark_disagreement`, `l1_midpoint_disagreement`) compare fields with explicit semantic eligibility.

Regime definitions and venue-specific historical modes: [historical-acquisition-regimes.md](../docs/historical-acquisition-regimes.md). Provenance interpretation: [provenance-standard.md](provenance-standard.md).

Historical investigations may contain episode types that are no longer produced by the current methodology. Those reports should be interpreted using the methodology version recorded in the investigation, not the current episode-type vocabulary.

---

## 9. Independent reproduction requirements

### Required artifacts

An external reviewer requires:

| Artifact | Purpose |
|---|---|
| Archived canonical observations / snapshots for the investigation window | Per-snapshot `normalized[]`, `consensus`, `l1_metrics`, `meta.scan_timestamp` |
| **Methodology version** (`canonical_snapshot_consensus_v1`) | Consensus and semantic metric algorithms |
| **Detection version** (`operational_episode_v1`) | Episode entry, continuation, recovery |
| **Field specification version** at analysis time | [canonical-field-specification.md](canonical-field-specification.md) |
| **Provenance** on archived rows | Regime and field-source interpretation |
| **Investigation window** | Start and end timestamps bounding snapshot selection |
| Threshold constants from §5 | Entry and recovery logic |

### Reproduction procedure

```text
1. Load archived canonical snapshots for the investigation window.
2. Order snapshots by §3 sort key.
3. Recompute consensus and semantic metrics from normalized[] using §4–§5.
4. Walk snapshots in order; apply episode rules from §5–§6.
5. Recompute episode aggregates: max_disagreement_score, max_age_seconds, min_usable_venues.
6. Compare recomputed values to stored episode and snapshot fields.
```

### Insufficient for independent reproduction

Without archived snapshots for the window, the following cannot be independently reproduced:

- Per-snapshot consensus and semantic metric time series
- Episode window boundaries and running aggregates
- Investigation report narrative and summary fields (including `peak_disagreement_score`) without underlying snapshots

Investigation manifests that include `source_snapshot_paths` and window bounds locate required snapshot evidence but do not substitute for it.

### Identifier reproduction

`investigation_id` and `episode_id` are stable derived identifiers.

#### Published-package `investigation_id` (exact equality)

For published reproducibility packages, exact `investigation_id` equality is required ([conformance.md](conformance.md) §2). For those packages:

```text
cluster_id = published episode_id
```

The published `episode_id` is the package’s episode identifier as serialized on the package (for example `investigation.json` `source.episode_id` or the equivalent published episode id field / manifest `episode_id`).

```text
investigation_id = lowercase_hex( SHA-256( utf8(
    instrument + "|" + window_start + "|" + window_end + "|" + cluster_id
) ) )[0:24]
```

Serialization rules for published-package reproduction:

| Input | Rule |
|---|---|
| `instrument` | Exact canonical serialized package string; casing preserved |
| `window_start` | Exact canonical serialized package timestamp string |
| `window_end` | Exact canonical serialized package timestamp string |
| `cluster_id` | Exact published `episode_id` string |
| Separator | Literal ASCII `\|` between the four fields, in the order above |
| Encoding | UTF-8 |
| Hash | SHA-256 |
| Output | Lowercase hexadecimal digest; first **24** hexadecimal characters |

Under these rules, recomputed `investigation_id` MUST match the published package value exactly.

#### Independent detection runs (may differ)

When an implementer runs episode detection independently over a broader archive, rather than reproducing a committed package `episode_id` / clustering may use detection-run counters or different episode boundaries. In that setting, regenerated `investigation_id` strings MAY differ because `cluster_id` or window bounds differ. That possibility does **not** relax exact `investigation_id` equality for published-package conformance.
