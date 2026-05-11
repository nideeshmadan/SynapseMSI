-- Count rows
SELECT COUNT(*) AS rows
FROM read_parquet('sample_data/btc_apr09_sample.parquet');

-- Compute temporal invalidation rate
SELECT
  AVG(CASE WHEN spread_invalidated THEN 1 ELSE 0 END) AS invalidation_rate
FROM read_parquet('sample_data/btc_apr09_sample.parquet');

-- Filter temporally coherent states
SELECT *
FROM read_parquet('sample_data/btc_apr09_sample.parquet')
WHERE pair_valid_under_strict_policy = true
LIMIT 20;

-- Inspect high sync-gap states
SELECT
  timestamp,
  instrument,
  best_bid_venue,
  best_ask_venue,
  observed_cross_venue_spread_bps,
  sync_gap_ms,
  best_pair_age_ms,
  market_state_validity_score
FROM read_parquet('sample_data/btc_apr09_sample.parquet')
ORDER BY sync_gap_ms DESC
LIMIT 20;

-- Compare observed vs temporally coherent state counts
SELECT
  COUNT(*) AS observed_states,
  COUNT(*) FILTER (WHERE pair_valid_under_strict_policy = true) AS temporally_coherent_states
FROM read_parquet('sample_data/btc_apr09_sample.parquet');
