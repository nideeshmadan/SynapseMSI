# Synapse MSI Sample Data

This directory contains institutional research datasets demonstrating different temporal coherence regimes in cross-venue cryptocurrency markets.

## Sample Regimes

### Degraded Stress Samples
- **`btc_apr09_sample.csv`** - BTCUSDT perpetual states from April 9, 2026
- **`eth_apr09_sample.csv`** - ETHUSDT perpetual states from April 9, 2026

These samples represent **stress-regime behavior** with severe temporal degradation:
- ~99.8% invalidation rates under strict policy constraints
- Large sync gaps (median ~4,800ms) 
- Substantial quote age violations
- Demonstrates worst-case temporal misalignment scenarios

**Use case**: Understanding how cross-venue market states behave during extreme temporal stress periods.

### Normalized Baseline Samples
*Coming soon: Additional samples from normalized temporal regimes showing ~25-30% invalidation rates typical of baseline conditions.*

## Data Format

All samples use consistent schema:
```
timestamp,instrument,sync_gap_ms,best_pair_age_ms,[additional fields]
```

- **timestamp**: Market-state reconstruction timestamp (ISO format)
- **instrument**: Trading pair (e.g., BTCUSDT_PERP) 
- **sync_gap_ms**: Cross-venue timestamp synchronization gap
- **best_pair_age_ms**: Quote freshness from collection time
- **Additional fields**: Venue sources, spreads, validation flags

## Usage

### Local Validation (No VPS Required)
```bash
# Validate stress-regime behavior
python3 synapse_validate.py sample_data/btc_apr09_sample.csv

# Expected output: ~99.8% invalidation (severe temporal degradation)
```

### File Formats
- **`.csv`** - Human-readable, compatible with spreadsheets
- **`.parquet`** - Compressed binary format, faster loading

Both formats contain identical data. Use CSV for inspection, Parquet for performance.

## Comparison with Live Demo

**Sample Data (No Network Required):**
- ✅ Institutional research quality with preserved venue-side timestamps
- ✅ Deterministic replay-oriented reconstruction
- ✅ High-fidelity temporal analysis
- ✅ No VPS or exchange API access needed

**Live Public Demo (May Require VPS):**
- ⚠️ REST polling with collection-time timestamp fallbacks  
- ⚠️ Limited temporal precision for demonstration purposes
- ⚠️ Binance/Bybit APIs may return HTTP 451/403 from restricted regions
- ⚠️ Not a replacement for canonical reconstruction

## Research Context

These samples support the core research finding: **Cross-venue market-state temporal coherence is regime-dependent.**

- **Stress regimes**: >90% invalidation, widespread temporal breakdown
- **Normalized regimes**: ~25-30% invalidation, manageable temporal gaps
- **Policy sensitivity**: Strict constraints reveal systematic timing issues

The included stress samples demonstrate the upper bound of temporal degradation observed in institutional research datasets.