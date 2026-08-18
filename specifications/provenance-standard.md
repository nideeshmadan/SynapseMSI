# Provenance Model

**Status:** Normative
**Applies to:** Synapse MSI External Reconstruction
**Last updated:** 2026-07-14

> If another public document conflicts with this specification regarding provenance or evidence lineage, this document is authoritative.

Related: [canonical-field-specification.md](canonical-field-specification.md) · [reconstruction-standard.md](reconstruction-standard.md) · [reconstruction-boundaries.md](../docs/reconstruction-boundaries.md) · [historical-acquisition-regimes.md](../docs/historical-acquisition-regimes.md)

---

## 1. Purpose

This document defines what evidence Synapse MSI preserves, what provenance accompanies reconstructed observations, what provenance supports, and what provenance cannot establish.

It defines the lineage of reconstructed evidence from archived observations through canonical snapshots into operational episodes and investigation artifacts. It does not redefine field semantics or reconstruction algorithms.

| Document | Governs |
|---|---|
| [canonical-field-specification.md](canonical-field-specification.md) | Field definitions, sourcing, persistence, evidence limits |
| [reconstruction-standard.md](reconstruction-standard.md) | Consensus, disagreement, episode detection, reproduction |
| This document | Evidence hierarchy and provenance lineage |

---

## 2. Evidence hierarchy

```
Archived raw observations
  ↓
Normalized canonical observations
  ↓
Canonical snapshots
  ↓
Operational episodes
  ↓
Investigation reports
```

| Layer | Evidence class | Role |
|---|---|---|
| Archived raw observation | **Primary evidence** | Venue payload as captured, with envelope timing and provenance when present |
| Normalized canonical observation | **Reconstructed evidence** | One venue-instrument market-state row after normalization |
| Canonical snapshot | **Reconstructed evidence** | Multi-venue market state at one scan time, including stored consensus |
| Operational episode | **Derived evidence** | Time-bounded interval identified from stored snapshot metrics |
| Investigation report | **Presentation artifact** | Report, manifest, and optional export derived from episodes and snapshots |

Archived observations and canonical snapshots are evidentiary inputs. Investigation reports summarize derived conclusions; they are not primary evidence and are not sufficient for independent reconstruction without archived snapshots.

---

## 3. Canonical observation provenance

Each normalized canonical observation carries lineage metadata that identifies where field values originated. Provenance records acquisition path and timing; it does not establish economic correctness.

Field definitions and persistence rules: [canonical-field-specification.md §3–§6](canonical-field-specification.md).

### Provenance elements

| Element | Purpose |
|---|---|
| `venue` | Venue identity for the observation row |
| Observation timestamp | Venue-assigned event time (`venue_timestamp`; alias `venue_event_time` on raw envelopes) |
| Canonical timestamp | Snapshot assembly time (`scan_timestamp`) is separate from observation timestamp |
| Authoritative source | Upstream object defining the economic meaning of each field (field-specific and venue-specific) |
| `transport` | Acquisition mechanism: `websocket`, `rest`, `hybrid`, or `http` |
| `ingest_type` | Acquisition regime classifier (`hybrid_book_reference`, `ws_ticker`, `ws_top_of_book`) |
| `field_provenance` | Per-field map: source transport, channel, event time, derivation flag, degradation when present |
| `observation_provenance` | Observation-level metadata, including hybrid component skew and merge context when present |

### What observation provenance supports

- Identification of which upstream source supplied each captured field
- Distinction between venue event time and snapshot scan time
- Classification of acquisition regime for historical interpretation
- Binance hybrid separation of book and reference components when archived
- Semantic metric eligibility when field-level provenance is present

### What observation provenance does not support

- Proof that a captured value is economically correct
- Depth beyond displayed L1
- Root-cause attribution of stale timestamps
- Automatic mark-semantics resolution without inspecting field provenance and `ingest_type`

**Authoritative source is independent of transport.** A hybrid observation uses WebSocket for the book and REST for the reference mark; each field's authoritative source is stated separately from transport.

---

## 4. Snapshot provenance

A canonical snapshot assembles one normalized observation per eligible venue for an instrument at one scan cycle.

### Snapshot composition

| Property | Rule |
|---|---|
| Venue rows | One normalized row per venue selected for the snapshot cycle |
| Unusable rows | Rows with `usable=false` remain in `normalized[]`; they are not removed before persistence |
| Snapshot timestamp | `meta.scan_timestamp` records when the snapshot was assembled |
| Observation references | Normalized rows retain provenance linkage to source ingest records when available |
| Stored outputs | `consensus`, `l1_metrics`, and snapshot metadata are persisted with the snapshot |

### Provenance carried into snapshots

When present on archived observations, the following are preserved on or with the snapshot:

| Provenance | Typical location |
|---|---|
| `field_provenance` | Normalized venue row and/or archived raw payload |
| `observation_provenance` | Hybrid observation payload |
| `ingest_type`, `transport`, `source_provenance` | Raw payload and/or normalized source metadata |
| `canonical_source_mode`, `component_sources` | Binance hybrid payload |
| `book_component_age_seconds`, `reference_component_age_seconds`, `component_skew_ms` | Binance hybrid payload when archived |

Collector-health or heartbeat diagnostics are **not** part of the canonical snapshot.

### Snapshot ordering

Snapshots are ordered by instrument and `scan_timestamp` (and sequence metadata when present). Snapshot provenance supports reconstruction of the evidence chain from archived observations through normalized rows to stored consensus outputs.

Reconstruction algorithms: [reconstruction-standard.md §3](reconstruction-standard.md#3-canonical-observation-selection).

---

## 5. Investigation provenance

Investigation artifacts reference the snapshot evidence used to produce episode conclusions. They do not replace archived snapshots.

### Investigation references

| Reference | Purpose |
|---|---|
| `source_snapshot_paths` | Archive locations of canonical snapshots loaded for the investigation window |
| `window_start` / `window_end` | Episode time bounds (ISO UTC) |
| `snapshot_count` | Number of snapshots loaded for the window |
| `methodology_version` | Consensus and episode methodology pin |
| `detection_version` | Episode detection methodology pin |
| `reconstruction_version` | L1 reconstruction scope pin |
| `semantics_version` | Investigation evidence schema version |
| `reconstruction_semantics_version` | Reconstruction-confidence semantics pin |
| `data_limitations` | Declared reconstruction scope limits |
| `reconstruction_establishes` / `reconstruction_does_not_establish` | Explicit evidentiary scope statements |
| `evidence_summary` (episode) | Entry, close, and metric evidence for semantic episodes |
| Report timeline and findings | Derived presentation from loaded snapshots |

### Affected observations

Investigation reports surface episode windows, affected venues, and field-provenance context when present on loaded snapshots. Semantic episodes record eligible and excluded venues in `evidence_summary` when archived.

### Reproducibility boundary

Investigation artifacts remain reproducible **only together with** the archived canonical snapshots referenced by the investigation manifest. A report or episode aggregate alone does not preserve the full per-snapshot time series.

Reproduction requirements: [reconstruction-standard.md §9](reconstruction-standard.md#9-independent-reproduction-requirements).

---

## 6. Acquisition regimes

Supported venues: `binance`, `bybit`, `okx`, `hyperliquid`.

The authoritative source of a field is **independent of transport**. Transport records how data arrived; authoritative source records what each value means.

### Current production regimes

| Venue | `ingest_type` | Transport | Role |
|---|---|---|---|
| Binance | `hybrid_book_reference` | `hybrid` | WS book + REST reference merge |
| Bybit | `ws_ticker` | `websocket` | Unified tickers stream |
| OKX | `ws_top_of_book` | `websocket` | Tickers channel (L1 + conditional native mark) |
| Hyperliquid | `ws_top_of_book` | `websocket` | L2 book channel (L1 only) |

### Current authoritative sourcing

| Venue | Field | Authoritative source | Transport | Notes |
|---|---|---|---|---|
| Binance | `bid_price`, `ask_price`, sizes | WS `bookTicker` | `websocket` (book component) | Hybrid merge; observation rejected on missing/stale/skewed components |
| Binance | `native_mark_price`, `index_price`, `funding_rate`, `next_funding_time` | REST Premium Index | `rest` (reference component) | Same hybrid observation |
| Binance | `top_of_book_mid` | derived from accepted bid and ask | internal derivation | |
| Binance | `open_interest_*` | not in hybrid primary observation | separate REST metadata path | Not on primary canonical snapshot path |
| Binance | `venue_timestamp` | `min(book_ts, ref_ts)` | hybrid | |
| Bybit | `bid_price`, `ask_price`, sizes, `native_mark_price`, `index_price`, `funding_rate`, `next_funding_time`, `open_interest_*` | WS `tickers.{symbol}` | `websocket` | Same ticker event; `markPrice` required positive for acceptance |
| Bybit | `venue_timestamp` | WS envelope `ts` | `websocket` | |
| OKX | `bid_price`, `ask_price`, sizes | WS `tickers` | `websocket` | Channel `tickers` |
| OKX | `native_mark_price` | WS `markPx` when key is truthy | `websocket` | Absent when `markPx` absent or falsy |
| OKX | `funding_rate`, `index_price` | WS `tickers` when present | `websocket` | |
| OKX | `open_interest_*`, `next_funding_time` | absent | — | Not in primary observation |
| OKX | `venue_timestamp` | WS `ts` when parseable | `websocket` | Unparseable `ts` rejects observation |
| Hyperliquid | `bid_price`, `ask_price`, sizes | WS `l2Book` L1 | `websocket` | |
| Hyperliquid | `top_of_book_mid` | derived from bid and ask | internal derivation | |
| Hyperliquid | `native_mark_price`, `index_price`, `funding_rate`, `open_interest_*` | absent | — | `mark_price` normalizes to `"0"` |
| Hyperliquid | `venue_timestamp` | WS `time` when parseable | `websocket` | Unparseable `time` rejects observation |

Full field semantics: [canonical-field-specification.md §3](canonical-field-specification.md#3-current-authoritative-field-sourcing).

### Historical regimes

Archived corpus periods can differ in `ingest_type` and `transport` while preserving comparable field semantics when provenance metadata is present.

| Regime | `ingest_type` | Typical mark semantics | Status |
|---|---|---|---|
| REST-composed | `canonical_v1` | Native mark from REST reference | Historical |
| Legacy WS top-of-book | `ws_top_of_book`, `ws_merged_ticker` | Midpoint or mixed semantics possible | Historical |
| Hybrid book + reference | `hybrid_book_reference` | Native mark from REST reference; book from WS | Current (Binance) |
| WS ticker | `ws_ticker` | Native mark from WS ticker | Current (Bybit) |
| WS top-of-book | `ws_top_of_book` | Venue-dependent: conditional native mark (OKX) or L1 only (Hyperliquid) | Current (OKX, Hyperliquid) |

When `ingest_type`, `transport`, or `field_provenance` are absent on an archived row, regime classification is incomplete and semantic metric eligibility is conservative.

Rejected primary ingest types for current production selection include `canonical_v1` and legacy WS types used as primary paths for Binance and Bybit.

---

## 7. Provenance limitations

### Timestamp limitations

Venue timestamps support **age measurement** relative to `scan_timestamp` and staleness interpretation.

Venue timestamps do **not** establish whether stale observations were caused by:

- exchange inactivity;
- collector interruption;
- network interruption.

A stale venue timestamp alone does not prove venue-side failure. Without independent operational telemetry in the same artifact, venue-side inactivity and collector-side stalling cannot be conclusively separated.

### Causality and quality

| Limitation | Detail |
|---|---|
| Lineage vs causality | Provenance documents evidence lineage, not causality |
| Transport vs quality | Transport does not imply evidence quality |
| Investigation scope | Investigation bundles do not include collector heartbeat diagnostics |
| Receive-path timing | Historical packages may omit receive-path timing. The modern acquisition/package path records `collector_received_at` when captured and preserves it alongside venue-event / `effective_observation_timestamp` so investigators can compare receive-path delay with venue-event age ([canonical-field-specification.md §6](canonical-field-specification.md#6-temporal-and-provenance-fields)). Absence of `collector_received_at` MUST NOT be filled in or inferred. A receive timestamp is preserved observation provenance; it is **not** equivalent to collector-health or heartbeat telemetry |
| Missing provenance | Absent `field_provenance` reduces interpretability; it does not invalidate unrelated fields |
| Historical variability | `mark_price` can carry mixed semantics in legacy archives; use `ingest_type` and `field_provenance` to interpret |

### Binance hybrid limitations

Hybrid provenance supports identification of book and reference components, component ages, and timestamp skew when archived. It supports native-mark temporal eligibility decisions. It does not identify which clock is wrong when skew is observed.

---

## 8. Independent evidence review

An external reviewer validating an investigation needs:

| Input | Purpose |
|---|---|
| Archived canonical snapshots for the investigation window | Primary per-snapshot evidence |
| `source_snapshot_paths` and window bounds from the investigation manifest | Locate and bound the evidence set |
| `methodology_version`, `detection_version`, and applicable semantics pins | Algorithm and threshold compatibility |
| [canonical-field-specification.md](canonical-field-specification.md) | Field definitions, aliases, and evidence limits |
| [reconstruction-standard.md](reconstruction-standard.md) | Consensus, semantic metrics, episode rules, reproduction procedure |
| Provenance metadata on loaded snapshots | `ingest_type`, `transport`, `field_provenance`, hybrid component metadata when present |

### What provenance enables

- Determination of where reconstructed values originated
- Verification that like-for-like fields were compared in semantic metrics
- Assessment of timestamp freshness relative to snapshot scan time
- Identification of acquisition regime for historical rows

### What provenance does not enable

- Explanation of why an external observation was absent from the archive
- Root-cause attribution of staleness or disagreement
- Proof of economic mechanism behind observed divergence
- Independent reconstruction from the investigation report alone

Reproduction procedure: [reconstruction-standard.md §9](reconstruction-standard.md#9-independent-reproduction-requirements).

Evidence scope limits: [reconstruction-boundaries.md](../docs/reconstruction-boundaries.md) and [canonical-field-specification.md §10](canonical-field-specification.md#10-evidence-boundaries).

---

## 9. Published-package acquisition-regime classification (normative)

This section defines the **deterministic classification policy** used for published-package exact equality of provenance and comparability fields. It separates two layers:

| Layer | Role | Examples |
|---|---|---|
| **A — asserted empirical evidence** | Package-pinned facts about the acquisition path | `venue`, `transport`, `ingest_type`, `collector_service_name`, frozen `regime_id` assignment records, validity bounds |
| **B — derived classification outputs** | Deterministic results of the rules below | `assignment_status`, `primary_regime_id`, `spans_multiple_regimes`, `comparison_group`, `comparability_eligibility`, `comparability_reason_code` |

Conformance validates Layer A integrity (pin, digest, coverage, consistency) and requires exact equality of Layer B outputs derived from Layer A plus packaged observations. Conformance does **not** require rediscovering private production history. It does require reproducing classifications from the frozen evidence supplied by the package.

### 9.1 Fixture-pinned frozen evidence artifact

Modern published packages that claim resolved acquisition regimes MUST pin a frozen evidence artifact in `input_manifest.json` under `acquisition_regime_evidence`:

```text
registry_id
registry_content_version
path                 # repository-relative path from the example directory
sha256               # lowercase hex digest of the exact committed artifact bytes
```

Current public pin:

| Field | Value |
|---|---|
| `registry_id` | `acquisition_regime_fixture_registry_v1` |
| `registry_content_version` | `2026-07-30.modern_fixtures.v1` |
| Artifact path | [`evidence/acquisition_regime_fixture_registry_v1.json`](../evidence/acquisition_regime_fixture_registry_v1.json) |
| Schema | [`schemas/acquisition-regime-fixture-registry.md`](../schemas/acquisition-regime-fixture-registry.md) |

That artifact contains **only** the empirical assignment records required by the committed modern fixtures. It is not a freeze of the live operational registry. The working identifier `acquisition_provenance_working_registry_v1` remains a non-normative implementation aid and MUST NOT be treated as the package evidence pin.

Published-package reproduction MUST fail when the pin is present and any of the following hold:

* the artifact file is missing;
* the SHA-256 digest differs;
* `registry_id` or `registry_content_version` differs from the pin;
* an observation with acquisition metadata cannot be assigned under §9.2;
* observation acquisition metadata contradicts the matched frozen record’s venue / ingest_type / transport match key (no assignment).

Historical packages without sufficient acquisition lineage MUST NOT be retroactively assigned modern regimes. They remain fail-closed under §9.4.

### 9.2 Observation-to-regime assignment

Inputs for each packaged observation:

1. acquisition metadata from the observation (`venue`/`exchange`, `transport`, `ingest_type`, optional `collector_service_name`, optional explicit `acquisition_regime_id` / `regime_id`, optional payload);
2. the package-pinned frozen assignment records.

Observation time used for advisory bound checks (first present): `sink_received_at`, `collector_observed_at`, `venue_event_time`, `venue_timestamp`, `effective_observation_timestamp`, `scan_timestamp`.

Validity interval semantics on frozen records:

* `valid_from` inclusive when present; null means unbounded past;
* `valid_to` inclusive when present; null means open-ended;
* a timestamp outside the interval produces an **advisory warning** and does **not** by itself change the assignment when a unique venue/ingest_type/transport match exists (bounds are asserted archive coverage hints, not sole assignment evidence).

Matching rules (in order):

1. If neither explicit regime id nor (`ingest_type` or `transport`) is present → `assignment_status=unknown`, `acquisition_regime_id=unknown.insufficient_provenance`, reason `missing_acquisition_metadata`.
2. If an explicit `acquisition_regime_id` / `regime_id` is present → select the unique frozen record with that `regime_id`. Zero or multiple matches → unknown with reason `explicit_regime_unknown`. One match → `assignment_status=definitive`, method `explicit`.
3. Otherwise select frozen records where all of the following hold:
   * `venue` equals the observation venue (case-insensitive);
   * `ingest_type` equals the observation ingest type;
   * `transport` equals the observation transport;
   * `instrument_scope` is `*` or equals the observation instrument.
4. Candidate resolution:
   * exactly one candidate → that record;
   * multiple candidates and exactly one has `current_production=true` → that record;
   * otherwise → unknown with reason `unresolved_classifier_or_inventory`.
5. Collector-service comparison: if the observation supplies `collector_service_name` and it differs from the matched record, emit a warning; the assignment still proceeds (row acquisition metadata takes precedence for matching; collector is supporting evidence).
6. Successful non-explicit match → `assignment_status=definitive`, method `row_metadata_with_payload` when a payload object is present, else `row_metadata`. Carry `comparison_group` from the matched frozen record.

Transport, ingest type, and venue MUST agree with the matched frozen record under rule 3. There is no separate “override” that assigns a different regime when those fields disagree; disagreement yields no match → unknown.

### 9.3 Package-level aggregation

Aggregate per-observation assignments into package provenance fields:

Let **resolved** be assignments whose status is not `unknown` and whose `acquisition_regime_id` is not `unknown.insufficient_provenance`. Let **resolved_ids** be the sorted unique set of those regime ids.

| Condition | `assignment_status` | `primary_regime_id` | `spans_multiple_regimes` | `comparison_group` |
|---|---|---|---|---|
| No assignments / no resolved ids (all unknown) | `unknown` | `null` | `false` | `unknown` |
| Exactly one resolved id, no unknown rows | `definitive` | that regime id | `false` | the regime’s frozen/inventory `comparison_group` |
| Exactly one resolved id, some unknown rows | `provisional` | that regime id | `false` | the regime’s `comparison_group` |
| Two or more resolved ids | `provisional` | `null` | `true` | single shared group if all resolved groups equal; otherwise `mixed` |

Additional aggregation facts used by current packages:

* Multi-regime packages set unresolved reason `multi_regime_investigation` when no unknown rows remain among inputs used for aggregation.
* Legacy anchor `acquisition_regime_id` for multi-regime packages is the lexicographically first resolved id (presentation/anchor only; not a semantic primary).
* `comparison_group` values used by committed fixtures include `native_mark_authoritative`, `conditional_native_mark`, `l1_midpoint_proxy`, `mixed`, and `unknown`.

### 9.4 Comparability eligibility

From the aggregated provenance view (and linkage fields used by package reproduction):

| Condition | `comparability_eligibility` | `comparability_reason_code` |
|---|---|---|
| `assignment_status=unknown` or no resolved regime ids | `excluded_fail_closed` | `unknown_assignment` (or `insufficient_provenance` when status is not unknown but no regimes resolved) |
| `spans_multiple_regimes=true` or more than one resolved regime id | `comparable_after_partition` | `mixed_regime_requires_partition` |
| Exactly one resolved regime and status definitive/provisional | `comparable` | `same_regime_semantics` |

Package reproduction for historical fixtures uses linkage `insufficient_raw_lineage` with unknown assignment and MUST remain `excluded_fail_closed` / `unknown_assignment`.

Modern committed fixtures currently resolve four regimes and therefore MUST derive:

```text
assignment_status = provisional
primary_regime_id = null
spans_multiple_regimes = true
comparison_group = mixed
comparability_eligibility = comparable_after_partition
comparability_reason_code = mixed_regime_requires_partition
```

Unsupported status/method/group/regime-id values fail closed with the corresponding reason codes used by the reference evaluator; published fixtures MUST NOT require inventing new eligibility categories.
