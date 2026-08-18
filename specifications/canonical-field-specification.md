# Canonical Field Specification

## 1. Purpose

This document defines the authoritative public semantics of the fields used in SynapseMSI External Reconstruction.

This specification describes **current production behavior** and the **fields required to interpret public investigation outputs**. It does not replace the full consensus and episode algorithms; those are documented in [reconstruction-standard.md](reconstruction-standard.md).

Published field meanings apply to their declared version pins (see §11). Current production changes MUST NOT silently modify the meaning of an already published version.

---

## 2. Field terminology

| Term | Definition |
|---|---|
| **Venue-native** | A value reported directly by the venue API or WebSocket payload before Synapse normalization. |
| **Normalized** | A per-venue value after symbol mapping, unit handling, sanity gates, and authoritative mark resolution. |
| **Derived** | A value computed deterministically from other fields (for example, midpoint from bid and ask). |
| **Alias** | A field that carries the same economic value as another field under an explicit alias rule documented below. |
| **Metadata** | Classification, identity, or structural information that describes an observation or artifact. |
| **Timing** | A timestamp or age measurement tied to a specific clock or event. |
| **Provenance** | Information describing how, when, and through which transport a field was obtained. |
| **Quality / classification** | A pass/fail, trust, or eligibility label applied during normalization or consensus. |
| **Presentation** | A report or registry field name that aliases a persisted field without changing its value. |
| **Authoritative source** | The upstream market-data object that defines the economic meaning of a field for a given venue. |
| **Transport** | The mechanism used to obtain the authoritative source (REST poll, WebSocket stream, hybrid merge of components, or internal derivation). |
| **Canonical observation** | One venue-instrument market-state record accepted by the acquisition layer for a point in time, including provenance and timing. |
| **Canonical snapshot** | A multi-venue assembled record containing normalized venue rows, consensus outputs, L1 metrics, and snapshot metadata for one instrument at one scan time. |

Field authority is defined independently of acquisition transport. A single observation may contain fields acquired through different transports.

**Artifact layers:**

| Layer | Description |
|---|---|
| Raw observation | Venue payload as ingested, with envelope metadata. |
| Canonical snapshot | *(defined above)* — persisted for reconstruction. |
| Consensus | Cross-venue aggregates and disagreement metrics on a snapshot. |
| Operational episode | A time-bounded interval derived from archived snapshots. |
| Investigation artifact | Report, manifest, and optional flattened snapshot export for an episode. |

### Alias registry

| Alias field | Canonical field | Direction | Where used |
|---|---|---|---|
| `mark_price` | `native_mark_price` | `mark_price` := `native_mark_price` when authoritative-mark alias rules apply | `normalized[]`; legacy consensus |
| `peak_disagreement_score` | `max_disagreement_score` | `peak_disagreement_score` := `max_disagreement_score` | Investigation report and registry JSON |
| `mid_price` | `top_of_book_mid` | `mid_price` := `top_of_book_mid` | Flattened investigation snapshot parquet export |
| `venue_event_time` | `venue_timestamp` | Same economic role; `venue_event_time` is the envelope/provenance name | Raw ingest and `field_provenance` |

`component_timestamp_skew_seconds` is an alternate serialization of `component_skew_ms` on Binance hybrid payloads. Only `component_skew_ms` is normative.

---

## 3. Current authoritative field sourcing

Current production acquisition model. Values apply to the primary market-state observation selected for each venue when building canonical snapshots.

| Field | Binance | Bybit | OKX | Hyperliquid | Field class |
|---|---|---|---|---|---|
| `bid_price` | WS `bookTicker` best bid | WS `tickers` `bid1Price` | WS `tickers` `bidPx` | WS `l2Book` best bid px | venue-native |
| `ask_price` | WS `bookTicker` best ask | WS `tickers` `ask1Price` | WS `tickers` `askPx` | WS `l2Book` best ask px | venue-native |
| `bid_size` | WS `bookTicker` bid size | WS `tickers` `bid1Size` | WS `tickers` `bidSz` (defaults to `0` if absent) | WS `l2Book` best bid sz | venue-native |
| `ask_size` | WS `bookTicker` ask size | WS `tickers` `ask1Size` | WS `tickers` `askSz` (defaults to `0` if absent) | WS `l2Book` best ask sz | venue-native |
| `top_of_book_mid` | derived `(bid+ask)/2` | derived | derived | derived | derived |
| `native_mark_price` | REST Premium Index `markPrice` | WS `tickers` `markPrice` (required positive) | WS `tickers` `markPx` when key is truthy | absent | venue-native / absent |
| `mark_price` | alias of `native_mark_price` | alias of `native_mark_price` | alias of `native_mark_price` when `markPx` truthy; omitted when `markPx` absent | absent; normalizes to `"0"` | alias / placeholder |
| `index_price` | REST Premium Index `indexPrice` | WS `tickers` `indexPrice` | WS `tickers` `idxPx` when present | absent | venue-native / absent |
| `funding_rate` | REST Premium Index `lastFundingRate` | WS `tickers` `fundingRate` | WS `tickers` `fundingRate` (nullable) | absent | venue-native / absent |
| `next_funding_time` | REST Premium Index `nextFundingTime` | WS `tickers` `nextFundingTime` | not in primary observation | absent | venue-native / absent |
| `open_interest_contracts` | not in hybrid primary observation | WS `tickers` `openInterest` (same event) | not in primary observation | absent | venue-native / absent |
| `open_interest_usd` | not in hybrid primary observation | WS `tickers` `openInterestValue` (same event) | not in primary observation | absent | venue-native / absent |
| `venue_timestamp` | `min(book_ts, ref_ts)` from hybrid components | WS envelope `ts` | WS `tickers` `ts` when parseable; else `null` | WS `l2Book` `time` when parseable; else `null` | timing |
| `collector_observed_at` | collector receive time (UTC) | collector receive time | collector receive time | collector receive time | timing |

**Ingest types:** Binance `hybrid_book_reference`; Bybit `ws_ticker`; OKX and Hyperliquid `ws_top_of_book`.

### Venue acceptance rules (current production)

**Binance (`hybrid_book_reference`):** Book fields from `bookTicker` WebSocket. Native mark, index, funding, and next funding time from Premium Index REST. `top_of_book_mid` derived from accepted bid and ask. Observation **rejected** when a required book or reference component is missing, symbols mismatch, either component exceeds freshness limits, or book–reference timestamp skew exceeds the configured threshold.

Open interest is acquired through a separate REST metadata ingest and is **not** included in the hybrid primary market-state observation. Primary canonical snapshots do not carry Binance open interest from the hybrid merge path.

**Bybit (`ws_ticker`):** All listed fields come from the same `tickers.{symbol}` WebSocket stream (`snapshot` or `delta`). Observation **rejected** when the topic is not a ticker, message type is not `snapshot` or `delta`, `data` is invalid, or `markPrice` is missing, empty, non-numeric, or not positive. Bid, ask, funding, and open interest are optional at the message level; `markPrice` is mandatory for acceptance.

**OKX (`ws_top_of_book`, channel `tickers`):** Bid, ask, sizes, and midpoint from tickers WebSocket. `native_mark_price` and `mark_price` are set only when `markPx` is truthy (including string `"0"`, which parses to zero and is then excluded from consensus as zero). When `markPx` is absent or falsy, native mark and mark alias fields are omitted; normalization resolves `mark_price` to `"0"` and sets `usable=false` via the zero-mark gate. `fundingRate` and `idxPx` are included when present. Open interest and next funding time are not in the primary observation. Unparseable `ts` rejects the observation; absent `ts` emits with `venue_timestamp=null`.

**Hyperliquid (`ws_top_of_book`, channel `l2Book`):** Bid, ask, sizes, and midpoint from L2 book WebSocket. Native mark, index, funding, open interest, and next funding time are absent. Collector does not supply `mark_price`; normalization resolves it to `"0"`. L1 disagreement uses `top_of_book_mid`, not a native mark. Unparseable `time` rejects the observation; absent `time` emits with `venue_timestamp=null`.

> Archived observations retain acquisition and methodology provenance applicable to the observation period.  Not every archived row exposes full regime metadata; when `ingest_type`, `transport`, or `field_provenance` are present, use them to interpret the observation.

Field definitions: §4–§8. Internal-only fields excluded: [Appendix A](#appendix-a-internal-only-fields-excluded).

---

## 4. Canonical market-state fields

Authoritative definitions for per-venue normalized fields and cross-venue L1 metrics. Consensus fields: §5. Timing and provenance fields: §6.

| Field | Definition | Class | Unit | Derivation or source rule | Consumed by | Public persistence | Supports | Does not support |
|---|---|---|---|---|---|---|---|---|
| `bid_price` | Best displayed bid price at L1 | venue-native | USD | Venue top-of-book bid (§3) | `top_of_book_mid`, spread, L1 metrics | `normalized[]`; investigation export | Displayed best bid at L1 | Executable depth, queue position, hidden liquidity |
| `ask_price` | Best displayed ask price at L1 | venue-native | USD | Venue top-of-book ask (§3) | `top_of_book_mid`, spread, L1 metrics | Same | Displayed best ask at L1 | Same as `bid_price` |
| `bid_size` | Displayed size at best bid | venue-native | contracts | Venue L1 bid size when captured (§3) | Snapshot export | `normalized[]` when present; investigation export | Displayed L1 bid size when captured | Consensus, disagreement, executable depth |
| `ask_size` | Displayed size at best ask | venue-native | contracts | Venue L1 ask size when captured (§3) | Snapshot export | Same | Displayed L1 ask size when captured | Same as `bid_size` |
| `top_of_book_mid` | Arithmetic midpoint of bid and ask | derived | USD | `(bid_price + ask_price) / 2` | `l1_midpoint_disagreement` (§5) | `normalized[]`; export as `mid_price` | Cross-venue L1 midpoint comparison | Native mark, volume-weighted mid, fair value |
| `native_mark_price` | Venue-supplied mark independent of bid/ask midpoint | venue-native | USD | §3 sourcing by venue | `native_mark_disagreement` (§5) | `normalized[]` when captured | Native mark cross-venue comparison when captured | Midpoint proxy, Hyperliquid L1 path, OKX when `markPx` absent |
| `mark_price` | Per-venue mark used for **legacy** mark consensus | normalized / alias | USD | Aliases `native_mark_price` when configured; Hyperliquid WS resolves to `"0"`; OKX absent `markPx` resolves to `"0"` | Legacy `mark_price_consensus`, `disagreement_score` (§5) | `normalized[]` | Legacy median mark consensus and `consensus_quality` episodes | Semantic `native_mark_disagreement`; economic truth independent of archive |
| `index_price` | Venue index or oracle price | venue-native | USD | §3 sourcing when captured | Context only | `normalized[]` when captured | Index/oracle reference when captured | Consensus or disagreement input |
| `funding_rate` | Current funding rate as venue reports | venue-native | decimal rate | §3 sourcing when captured | `funding_rate_consensus`, `funding_spread` (§5) | `normalized[]`; consensus | Funding level and cross-venue funding spread when captured | Funding-rate disagreement episodes (not implemented in MSI v1) |
| `open_interest_contracts` | Open interest in venue-native contracts | venue-native | contracts | Bybit WS `openInterest` (§3) | OI normalization gate | `normalized[]` / `oi_native` when captured | Contract-denominated OI when captured | USD consensus without trustworthy conversion |
| `open_interest_usd` | USD notional open interest when trustworthy | derived | USD | Venue USD OI field or conversion; `oi_usd_trustworthy` gate | `oi_total_usd` (§5) | `normalized[]`; consensus | Median OI consensus when trustworthy | Binance hybrid primary path (absent); sum across venues |
| `oi_usd_trustworthy` | Flag that `open_interest_usd` is eligible for consensus OI | quality | boolean / string | Set when conversion method is trustworthy | `oi_total_usd` median selection | `normalized[]` | Trust eligibility for OI consensus | Economic correctness of OI by itself |
| `spread_bps` | Bid–ask spread relative to mid | derived | basis points | Cross-venue median in `l1_metrics`: `(ask−bid)/mid×10000` | L1 analytics, pilot export | `l1_metrics.spread_bps`; pilot export | Observable L1 spread dispersion | Per-venue row value in pilot export (uses cross-venue metric) |
| `max_price_deviation` | Maximum usable-venue mark deviation from median consensus | derived | basis points | Cross-venue L1 metric from usable venue `mark_price` values | L1 analytics, pilot export | `l1_metrics`; pilot export | Legacy mark deviation summary | Native-mark disagreement; native mark input |
| `funding_spread` | Range of funding rates across usable venues | derived | decimal rate | `max(funding) − min(funding)` across usable venues (requires ≥2) | L1 analytics, pilot export | `l1_metrics`; pilot export | Funding dispersion when ≥2 usable values | Value when fewer than two usable funding values (null) |
| `usable` | Venue row passes normalization sanity gates and staleness limit | quality | boolean | Gates on mark, bid/ask consistency, funding bounds, OI bounds, staleness | Episode usable counts, L1 metrics, `venue_staleness` entry | `normalized[]` | Venue eligibility for staleness and L1 metrics | Filtering before legacy consensus median (not applied) |
| `quality` | Snapshot-level consensus quality by venue count | quality | enum | `good` (≥2 venues), `degraded` (1), `unusable` (0) | `consensus_quality` episodes, reports | `consensus.quality`; pilot export as `consensus_quality` | Input-venue-count classification | Economic correctness of consensus |
| `staleness_ms` | Age of venue timestamp vs normalization clock | derived | milliseconds | `(normalize_time − venue_timestamp)×1000` on live path | `usable` gate, staleness interpretation | `normalized[]` | Relative freshness of venue timestamp | Collector-dead vs venue-frozen attribution alone |

**Basis fields:** Mark-to-index basis percentage (`basis_pct`) is not persisted in canonical snapshots or public investigation artifacts. Cross-venue price dispersion is expressed through `disagreement_score`, `field_disagreement_metrics`, and L1 metrics (`spread_bps`, `max_price_deviation`).

---

## 5. Consensus and disagreement fields

Computed at snapshot write time and stored in the archived canonical snapshot. Investigations read stored values; they do not recompute consensus at report time. Input fields: §4. Algorithms: [reconstruction-standard.md](reconstruction-standard.md).

| Field | Definition | Class | Unit | Consumed by | Public persistence | Supports | Does not support |
|---|---|---|---|---|---|---|
| `mark_price_consensus` | Median of non-null, non-zero per-venue `mark_price` values | derived | USD (2 dp) | Legacy disagreement, reports, pilot export | `consensus`; pilot export | Legacy cross-venue mark reference | Native-mark consensus; depth-weighted consensus |
| `funding_rate_consensus` | Median of non-null, non-zero per-venue `funding_rate` values | derived | decimal rate (8 dp) | Reports, pilot export | `consensus`; pilot export | Cross-venue funding reference when values exist | Funding disagreement episodes |
| `oi_total_usd` | Median of trustworthy per-venue USD open-interest estimates | derived | USD (2 dp) | Reports, pilot export | `consensus`; nullable | Central OI estimate when trustworthy venues exist | Sum across venues; Binance on hybrid primary path |
| `disagreement_score` | Maximum absolute deviation of valid `mark_price` values from their median, in basis points | derived | basis points (1 dp) | `consensus_quality` episodes, reports | `consensus` | Legacy cross-venue mark dispersion | Native-mark or L1-midpoint semantic disagreement |
| `field_disagreement_metrics` | List of semantic disagreement metric objects on the snapshot | derived | JSON list | Semantic episode detection, report provenance sections | `consensus` in archived snapshots | Reproduction of semantic episode scores | Pilot export schema; report-only reproduction without archives |
| `native_mark_disagreement` | Cross-venue disagreement on `native_mark_price` among eligible venues | derived | basis points | `native_mark_disagreement` episodes | Inside `field_disagreement_metrics` | Semantic native-mark dispersion | Midpoint-only venues; venues without native mark |
| `l1_midpoint_disagreement` | Cross-venue disagreement on `top_of_book_mid` among eligible venues | derived | basis points | `l1_midpoint_disagreement` episodes | Inside `field_disagreement_metrics` | Semantic L1 midpoint dispersion | Native mark comparison; depth beyond L1 |
| `max_disagreement_score` | Maximum per-snapshot disagreement score over an operational episode window | derived | basis points | Episode parquet; investigation summary input | Operational episode parquet | Episode-level peak disagreement (stored name) | Full per-snapshot time series without archived snapshots |
| `peak_disagreement_score` | Presentation alias for `max_disagreement_score` | presentation | basis points | Investigation reports and registry adapters | Investigation JSON / report summary | Same numeric peak as `max_disagreement_score` | Distinct metric; episode parquet column name |
| `max_age_seconds` | Maximum per-venue age in seconds during a `venue_staleness` episode | derived | seconds | `venue_staleness` episodes, reports | Operational episode parquet | Primary staleness episode metric | Price disagreement by itself |
| `venues_count` | Number of venues in the consensus input list | metadata | integer | Quality classification, reports | `consensus`; pilot export | Input venue count | Usable-only count (`venues_usable`) |
| `venues_used` | Sorted names of all venues in consensus input | metadata | string list | Reports | `consensus` | Consensus input venue set | Per-metric semantic exclusion set |
| `venues_usable` | Sorted names of venues with `usable=true` at normalization | metadata | string list | Episode usable-count logic | `consensus` | Usable venue set at snapshot time | Legacy consensus median filtering (not applied) |
| `excluded_venues` | Venues excluded from a semantic disagreement metric with reasons | metadata | string list + reason map | Semantic episode `evidence_summary` | Episode `evidence_summary` JSON | Per-metric exclusion audit | Legacy consensus venue lists |

**`funding_disagreement`:** Not implemented. No detector or `field_disagreement_metrics` entry exists for funding-rate cross-venue disagreement.

### `max_disagreement_score` source by `episode_type`

| `episode_type` | Score accumulated into `max_disagreement_score` |
|---|---|
| `consensus_quality` | Legacy `consensus.disagreement_score` |
| `native_mark_disagreement` | `native_mark_disagreement` metric `disagreement_score` |
| `l1_midpoint_disagreement` | `l1_midpoint_disagreement` metric `disagreement_score` |
| `venue_staleness` | Legacy `disagreement_score` updated on each stale snapshot; primary episode metric is `max_age_seconds` |

An episode parquet aggregate alone does **not** reproduce the full per-snapshot time series. Reproduction requires archived canonical snapshots for the episode window, the applicable `methodology_version`, and stored `field_disagreement_metrics` per snapshot for semantic episodes.

**Episode entry thresholds:** semantic and legacy disagreement entry at **10 basis points**; `venue_staleness` entry at **60 seconds** venue age while `usable`; recovery after **5 consecutive** healthy snapshots.

**Not emitted:** `market_disagreement` episode type is disabled.

---

## 6. Temporal and provenance fields

Authoritative definitions for timing and provenance fields relevant to public reconstruction. Market-state timing on normalized rows: `venue_timestamp`, `staleness_ms` (§4).

| Field | Definition | Class | Assigned at | Public persistence | Supports | Does not support |
|---|---|---|---|---|---|---|
| `venue_timestamp` | Venue-assigned event time on the observation | timing | Collector parse | `normalized[].timestamp`; export; public package observations when published | Staleness, episode age, relative freshness | Collector-dead vs venue-frozen attribution alone |
| `scan_timestamp` | Wall-clock time when canonical snapshot assembled | timing | Snapshot builder | `meta.scan_timestamp`; export | Episode age (`scan_timestamp − venue_timestamp`) | Venue event time |
| `collector_received_at` | Collector wall-clock time at which the observation was received, where captured by the modern acquisition/package path | timing | Collector / modern public export | Top-level public package observation field when published (for example modern freshness packages); **omitted** from historical packages and from modern packages that do not publish the field | Receive-path timing; comparison against venue-event / effective observation time; investigating whether observation age was already present near receipt or accumulated after receipt | Collector health, heartbeat, or process diagnostics; proof that a collector was healthy or unhealthy |
| `effective_observation_timestamp` | Resolved observation timestamp used as the venue-event timing surface on modern packaged observations that publish the field. On the currently published freshness package path it is identical to `venue_timestamp` on every retained row. Public freshness reconstruction prefers `venue_timestamp`, then `timestamp`, then `effective_observation_timestamp` when computing age | timing | Modern public export / package materialization | Top-level public package observation field when published; **omitted** from historical packages and from modern packages that do not publish the field | Freshness age when selected by the published reconstruction preference order; alignment with `venue_timestamp` on the published freshness path | Inventing a distinct clock when the field is absent; implying a fallback other than the published preference order |
| `raw_linkage` | Provenance/reproducibility object linking a packaged observation to preserved raw evidence. Public subfields on the published freshness package path: `linkage_status`, `raw_row_id`, `snapshot_sequence`. `raw_row_id` is treated as a public-safe linkage identifier in this repository’s modern freshness packages and uniqueness checks | provenance | Modern public export / package materialization | Top-level public package observation object when published; **omitted** from historical packages and from modern packages that do not publish the object | Tracing a package observation to preserved raw evidence for reproducibility auditing; enforcing unique `(sequence, venue)` linkage when required | Market-state prices or economic meaning; private storage locators or internal-only infrastructure identifiers |
| `collector_observed_at` | Wall-clock time when collector processed the message | timing | Collector | `field_provenance`; source metadata on archived observations | Observation receive-path timing | Proof of venue-side halt without other signals |
| `collector_service_name` | Collector service or implementation associated with an acquisition regime or observation stream. Public acquisition / operational provenance metadata; not a canonical market-state value and not venue-native evidence. | provenance | Collector / inventory | Public regime inventory serialization; observation `acquisition` when captured | Identification of which collector service produced or is assigned to a stream or regime | Inferring venue behavior or venue-side failure |
| `transport` | Acquisition transport: `websocket`, `rest`, `hybrid`, `http` | provenance | Collector / envelope | `source_provenance`; raw payload when archived | Regime and path classification | Economic meaning of prices |
| `ingest_type` | Acquisition regime classifier (`hybrid_book_reference`, `ws_ticker`, `ws_top_of_book`) | provenance | Collector | Raw payload; `source_provenance` when present | Historical mark-semantics interpretation | Automatic mark semantics without field inspection |
| `field_provenance` | Per-field map: source transport, channel, event time, degradation | provenance | Collector | Archived snapshot when persisted | Semantic metric eligibility; report provenance sections | Depth beyond L1; sink or archive lag |
| `observation_provenance` | Observation-level merge metadata including component skew | provenance | Binance hybrid merge | Hybrid payload when archived | Binance native-mark temporal eligibility | Non-hybrid venues |
| `canonical_source_mode` | Merge mode for hybrid observations (`component_merged`) | provenance | Binance hybrid merge | Hybrid payload | Binance hybrid identification | Non-Binance venues |
| `component_sources` | Named components contributing to a hybrid observation | provenance | Binance hybrid merge | Hybrid payload | Book vs reference component identification | Field-level economic values |
| `book_component_age_seconds` | Age of book component at merge time | timing | Binance hybrid merge | Hybrid payload when archived | Binance freshness rejection audit | Non-Binance staleness |
| `reference_component_age_seconds` | Age of REST reference component at merge time | timing | Binance hybrid merge | Hybrid payload when archived | Binance freshness rejection audit | Non-Binance staleness |
| `component_skew_ms` | Absolute timestamp difference between book and reference components | timing | Binance hybrid merge | Hybrid payload; `observation_provenance` | Binance skew rejection; native-mark eligibility | Identification of which clock is wrong |

> A stale venue timestamp alone does not prove venue-side failure. When `collector_received_at` is present, receive-path timing can be compared with venue-event / effective observation time to separate age near receipt from age accumulated after receipt. That comparison is preserved observation provenance; it is not collector-health or heartbeat telemetry and does not by itself establish a single operational root cause. Absent receive-path fields MUST NOT be filled in or inferred.

Staleness interpretation from investigations relies on archived `venue_timestamp`, `scan_timestamp`, `staleness_ms`, and provenance fields when present on loaded snapshots. Where published, `effective_observation_timestamp` and `collector_received_at` further support age and receive-path timing interpretation.

Envelope alias `venue_event_time` (§2) carries the same role as `venue_timestamp` on raw observations.

---

## 7. Operational episode fields

Operational episodes are derived artifacts. Episode identifiers label reconstructed intervals; they are not venue-native event IDs. Disagreement and age metrics: §5.

| Field | Definition | Public persistence | Supports | Does not support |
|---|---|---|---|---|
| `episode_id` | Stable identifier for one operational episode | Episode parquet; investigation manifest | Reference to one derived episode interval | Venue-native event identity |
| `episode_type` | Episode classifier | Episode parquet; manifest | Selection of disagreement vs staleness logic (§5 table) | Underlying venue mechanism |
| `instrument` | Canonical instrument (for example `BTCUSDT_PERP`) | Episode parquet; manifest | Instrument scope of episode | Venue symbol mapping internals |
| `venue` | Affected venue name, `multi_venue`, or `consensus` | Episode parquet | Venue scope of episode | Per-venue routing or execution |
| `start_timestamp` | `scan_timestamp` of first snapshot in episode | Episode parquet; manifest `window_start` | Episode window start | Venue event start time |
| `end_timestamp` | `scan_timestamp` of last snapshot in episode | Episode parquet; manifest `window_end` | Episode window end | Venue event end time |
| `duration_seconds` | `end_timestamp − start_timestamp` in seconds | Episode parquet | Episode duration | Causal duration of venue outage |
| `snapshot_count` | Number of canonical snapshots in episode | Episode parquet; manifest | Archive coverage within window | Completeness of all venue feeds |
| `max_disagreement_score` | Running maximum disagreement score over episode | Episode parquet | Episode peak disagreement (see §5) | Time series without archived snapshots |
| `max_age_seconds` | Maximum venue age seconds during `venue_staleness` episodes | Episode parquet | Episode peak staleness (see §5) | Root-cause attribution of staleness |
| `evidence_summary` | JSON string of entry, close, and metric evidence | Episode parquet | Semantic episode reproduction metadata; includes `methodology_version` for semantic types | Full snapshot payload |

Investigation presentation alias `peak_disagreement_score` (§2, §5) maps to `max_disagreement_score` in episode parquet.

---

## 8. Investigation artifact fields

Public investigation bundles: markdown report, manifest JSON, and optional flattened snapshot parquet export.

| Field | Definition | Public persistence | Supports | Does not support |
|---|---|---|---|---|
| `investigation_id` | Stable identifier for the investigation package. For published reproducibility packages, derived exactly as in [reconstruction-standard.md §9](reconstruction-standard.md#9-independent-reproduction-requirements) with `cluster_id` = published `episode_id` | Investigation registry / package JSON | Registry lookup, replay, and published-package exact equality | Venue-native event ID |
| `findings` | Structured list of investigation conclusions and limitations | `result.findings` | Declared conclusions with evidence references | Independent reproduction without archived snapshots |
| `metadata` | Investigation context object | `result.metadata` | Episode references, `reconstruction_confidence`, materialization source | Raw per-field provenance for every field |
| `semantics_version` | Investigation evidence schema version (`investigation_evidence_v1`) | `result.semantics_version` | Evidence schema compatibility | Consensus methodology version |
| `reconstruction_confidence` | Archive coverage and continuity classification (`status`, `limitations`) | `result.metadata.reconstruction_confidence` | Archive completeness assessment | Mark correctness or liquidity |
| `reconstruction_semantics_version` | Version pin for reconstruction confidence (`reconstruction_confidence_v1`) | Investigation manifest | Confidence semantics compatibility | Field economic meaning |
| `methodology_version` | Consensus methodology pin (`canonical_snapshot_consensus_v1`) | Investigation manifest; semantic `evidence_summary` | Consensus/episodes semantics for replay | Investigation evidence schema |
| `reconstruction_version` | Reconstruction layer pin (`l1_canonical_v1`) | Investigation manifest | L1 reconstruction scope | Depth beyond L1 |
| `detection_version` | Episode detection pin (`operational_episode_v1`) | Investigation manifest | Episode detection semantics | Consensus computation |
| `source_snapshot_paths` | Archive references to canonical snapshots used | Investigation manifest | Independent replay of investigation window | Automatic download or validation |
| `window_start` / `window_end` | Episode time window (ISO UTC) | Investigation manifest | Investigation time bounds | Venue clock authority |
| `snapshot_count` | Snapshots loaded for investigation window | Investigation manifest | Loaded snapshot cardinality | Guaranteed gap-free archive |
| `timeline` | Time-ordered snapshot events in report | Markdown report body | Temporal narrative from archives | Causal ordering of venue events |
| `data_limitations` | Declared limitations of the reconstruction scope | Investigation manifest | Explicit scope limits | Implicit completeness |
| `reconstruction_establishes` / `reconstruction_does_not_establish` | Explicit scope statements | Investigation manifest | Declared evidentiary scope (§10) | Claims beyond §10 |

**Not a canonical persisted field:** `reconstruction_completeness` is narrative text in report generation only, not a structured investigation JSON field.

**Flattened snapshot export:** `timestamp`, `venue`, `bid_price`, `ask_price`, `mid_price` (alias §2), `mark_price`, `native_mark_price`, `funding_rate`, `usable`, `staleness_ms`, and related L1 fields per [architecture.md](../docs/architecture.md).

---

## 9. Field dependencies

Concise dependency chains. Legacy mark consensus and semantic disagreement paths are **separate**.

```
bid_price + ask_price
  → top_of_book_mid (§4)
    → l1_midpoint_disagreement (§5)
      → max_disagreement_score (§5, episode_type=l1_midpoint_disagreement)
        → peak_disagreement_score (§2, investigation presentation)
```

```
native_mark_price (§4, when captured)
  → native_mark_disagreement (§5)
    → max_disagreement_score (§5, episode_type=native_mark_disagreement)
      → peak_disagreement_score (§2)
```

```
mark_price (§4, legacy)
  → mark_price_consensus (§5)
    → disagreement_score (§5)
      → max_disagreement_score (§5, episode_type=consensus_quality)
        → peak_disagreement_score (§2)
```

```
venue_timestamp + scan_timestamp (§4, §6)
  → staleness_ms / age_seconds
    → venue_staleness episode (usable AND age ≥ 60 s)
      → max_age_seconds (§5)
```

```
field_provenance + ingest_type + transport (§6)
  → semantic metric eligibility
    → field_disagreement_metrics (§5)
      → evidence_summary (§7)
```

```
source_snapshot_paths (§8) + archived canonical snapshots
  → investigation replay window
    → findings, timeline, reconstruction_confidence
```

---

## 10. Evidence boundaries

### What these fields support

- Best bid and best ask at displayed L1
- Displayed L1 size when the venue path captures size on the normalized row
- Top-of-book midpoint (`top_of_book_mid`)
- Native mark and index/reference values when captured for the venue path
- Funding rate when captured
- Open interest when captured and trustworthy (Bybit primary path; absent on Binance hybrid primary path)
- Timestamp freshness and relative age between venue time and snapshot scan time
- Acquisition and field provenance to the extent persisted on archived observations (`ingest_type`, `transport`, `field_provenance`, hybrid component metadata)

### What these fields do not support

- Depth beyond displayed L1
- Queue position
- Hidden liquidity
- Iceberg orders
- Executable depth beyond displayed L1 size
- Expected fill price
- Fill probability
- Market impact
- Depth-weighted consensus
- Internal routing or execution behavior
- Attribution of stale timestamps to venue failure versus collector failure without additional health evidence

> A divergent L1 quote can reflect thin displayed liquidity. L1-only evidence cannot determine whether deeper liquidity would eliminate or materially reduce the observed disagreement.

See also [reconstruction-boundaries.md](../docs/reconstruction-boundaries.md).

---

## 11. Versioning

- Field semantics are versioned with the methodology. The current consensus and episode methodology pin is `canonical_snapshot_consensus_v1`.
- Investigation evidence semantics are versioned separately as `investigation_evidence_v1`.
- Reconstruction confidence semantics are versioned as `reconstruction_confidence_v1`.
- A change to the economic meaning of a field requires a methodology or semantics-version change. A change to report wording alone does not alter field meaning.
- Archived artifacts retain the version identifiers present when they were generated.
- Later methodology changes MUST NOT silently reinterpret prior artifacts. Readers MUST use the version pins embedded in the artifact being analyzed. Current production changes MUST NOT silently modify the meaning of an already published version.

| Version field | Current value | Appears in |
|---|---|---|
| `methodology_version` | `canonical_snapshot_consensus_v1` | Manifest; semantic episode `evidence_summary` |
| `reconstruction_version` | `l1_canonical_v1` | Manifest |
| `detection_version` | `operational_episode_v1` | Manifest |
| `semantics_version` | `investigation_evidence_v1` | Investigation JSON |
| `reconstruction_semantics_version` | `reconstruction_confidence_v1` | Manifest |

---

## Appendix A. Internal-only fields (excluded)

The following fields exist in production or archive pipelines but are **not** part of this public normative specification. They are not required to interpret public investigation artifacts.

| Field | Reason for exclusion |
|---|---|
| `archive_timestamp` | Archive worker write time; not in investigation bundles |
| `ts_venue`, `ts_ingest`, `sink_received_at` | Ingest database columns; not in investigation bundles |
| `raw_ingest_ids` | Snapshot database lineage metadata |
| `collector_fetch_time` | Collector envelope diagnostic |
| `collector_instance_id`, `collector_source_region` | Deployment identity |
| `state_degraded` | Legacy soft-merge flag; current hybrid path rejects instead |
| `quality_class` | Incremental corpus path only; not standard backfill episode schema |
| `last_price` | Not on primary venue paths used for investigations |
| `mark_price_alias_of`, `mark_price_source` | Raw-envelope alias metadata; alias rule documented in §2 and §4 |
| `latency_ms` | Optional diagnostic; null on external ingest path |
| `min_usable_venues`, `max_excluded_venues`, `recovery_snapshot_count` | Episode parquet analytics columns; not required for investigation interpretation |
| `component_timestamp_skew_seconds` | Duplicate serialization of `component_skew_ms` |
| `engines`, `traces`, `bid_levels`, `ask_levels` | Non-reconstruction snapshot payload |
| `basis_pct`, `funding_rate_annualized` | Not persisted in public artifacts |
| `reconstruction_completeness` | Report-generator narrative only |
| `funding_disagreement` | Not implemented |
| `market_disagreement` | Episode type disabled |

---

## Related documents

- [reconstruction-standard.md](reconstruction-standard.md) — consensus and episode algorithms
- [provenance-standard.md](provenance-standard.md) — acquisition and archive overview
- [reconstruction-boundaries.md](../docs/reconstruction-boundaries.md) — L1 evidence scope
- [schemas/canonical_snapshot.md](../schemas/canonical_snapshot.md) — snapshot JSON shape
- [architecture.md](../docs/architecture.md) — investigation bundle layout
