# Schema

| Field | Definition |
|---|---|
| `timestamp` | Canonical reconstructed market-state timestamp. |
| `instrument` | Canonical instrument identifier. |
| `source_snapshot_sequence` | Source canonical snapshot sequence. |
| `frame_hash` | Hash of current reconstructed frame. |
| `prev_frame_hash` | Hash of previous reconstructed frame. |
| `date` | Partition date. |
| `best_bid` | Best observed bid across venues. |
| `best_bid_venue` | Venue contributing best bid. |
| `best_bid_timestamp` | Timestamp of best bid observation. |
| `best_ask` | Best observed ask across venues. |
| `best_ask_venue` | Venue contributing best ask. |
| `best_ask_timestamp` | Timestamp of best ask observation. |
| `best_bid_age_ms` | Age of best bid observation in milliseconds. |
| `best_ask_age_ms` | Age of best ask observation in milliseconds. |
| `observed_cross_venue_spread_bps` | Observed cross-venue spread in basis points. |
| `sync_gap_ms` | Absolute timestamp difference between best bid and best ask observations. |
| `best_pair_age_ms` | Maximum age across the selected best bid / best ask pair. |
| `venue_coverage_ratio` | Fraction of venues represented in reconstructed state. |
| `coverage_class` | Venue coverage category. |
| `market_state_validity_score` | Composite temporal-coherence score. |
| `state_reconstruction_status` | Reconstruction quality class. |
| `invalidation_severity` | Severity bucket for temporal invalidation. |
| `spread_invalidated` | Whether spread state failed temporal validity checks. |
| `pair_valid_under_strict_policy` | Whether state satisfies strict sync/freshness policy. |
| `policy_name` | Validation policy name. |
| `policy_version` | Validation policy version. |
