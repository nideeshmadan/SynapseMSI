# Synapse Market-State Integrity (MSI)

**Temporal coherence validation for cross-venue cryptocurrency market data**

Synapse MSI validates whether observed cross-venue spreads represent temporally coherent market states or result from asynchronous timestamp misalignment across exchanges.

## Core Research Question

**Do observed cross-venue spreads reflect genuine pricing inefficiency or temporal measurement artifacts?**

Cross-venue arbitrage opportunities may be phantom if venues report quotes at materially different times. Synapse applies strict temporal coherence constraints to distinguish real spread states from measurement noise.

---

## Local Quickstart (No VPS Required)

Validate market-state integrity using included sample data:

```bash
pip3 install -r requirements.txt
python3 synapse_validate.py sample_data/btc_apr09_sample.csv
```

**Sample Output:**
```
📊 SYNAPSE MARKET-STATE INTEGRITY REPORT
📁 File: sample_data/btc_apr09_sample.csv
📈 Rows Analyzed: 10,000
✅ Valid States: 18
❌ Invalidated States: 9,982
📉 Invalidation Rate: 99.8%
🎯 Assessment: SEVERE temporal degradation
```

This validates 10,000 reconstructed BTCUSDT perpetual market states from April 2026 across Binance, Bybit, OKX, and Hyperliquid.

---

## Optional Live Public Demo

**⚠️ May require VPS or non-restricted region** - Binance/Bybit public APIs can return HTTP 451/403 from some locations.

### Step 1: Collect Live Data
```bash
python3 collect_public_binance_bybit.py --symbol BTCUSDT --seconds 60 --out public_data/btc_binance_bybit_live.csv
```

### Step 2: Build Cross-Venue States  
```bash
python3 build_public_crossvenue_states.py --input public_data/btc_binance_bybit_live.csv --out public_data/btc_binance_bybit_states.csv
```

### Step 3: Validate Temporal Coherence
```bash
python3 synapse_validate.py public_data/btc_binance_bybit_states.csv
```

---

## Temporal Coherence Policy

Synapse applies strict constraints for cross-venue state validity:

- **`sync_gap_ms ≤ 500`** - Cross-venue timestamp synchronization
- **`best_pair_age_ms ≤ 1000`** - Quote freshness from collection time

States violating either constraint are marked as **temporally invalidated** and unsuitable for:
- Execution simulation
- Backtest replay
- Risk analysis
- Performance attribution

---

## Methodology Note

**Local Quickstart** uses institutional research data with preserved venue-side timestamps from Synapse canonical reconstruction archive. This provides deterministic replay semantics and precise temporal analysis.

**Live Public Demo** uses public REST polling with collection-time timestamps where venue event timestamps are limited. This is a workflow demonstration showing MSI validation capabilities, **not a replacement for canonical websocket/event-driven reconstruction**.

Key differences:
- **Canonical**: WebSocket events, venue-side timestamps, microsecond precision, deterministic replay
- **Public REST**: Polling tickers, collection-time fallbacks, limited temporal precision, demonstration purposes

---

## Repository Structure

```
├── synapse_validate.py          # Core temporal coherence validator  
├── collect_public_binance_bybit.py  # Live data collection demo
├── build_public_crossvenue_states.py  # Cross-venue state reconstruction
├── sample_data/                 # Research datasets (CSV/Parquet)
├── charts/                      # Integrity analysis visualizations  
├── reports/                     # Research findings and methodology
├── methodology/                 # Technical documentation
├── schema/                      # Data schema specifications
├── queries/                     # Sample analysis queries
└── outputs/                     # Generated reports (ignored)
```

---

## Research Findings

Analysis of 943,102 cross-venue market states reveals:

- **24.6%** invalidation under normalized conditions
- **95.0%** invalidation during degraded temporal regimes  
- **35.9%** median persistence contraction under strict coherence validation
- **$192 basis point** phantom spreads observed during extreme misalignment

See [`reports/FINDINGS.md`](reports/FINDINGS.md) for detailed empirical analysis.

---

## What Synapse MSI is NOT

- ❌ **Trading signal** - Validates data quality, does not generate signals
- ❌ **Investment advice** - Research tool for infrastructure assessment  
- ❌ **PnL model** - Does not estimate returns or performance
- ❌ **Execution engine** - Does not place trades or manage orders
- ❌ **Market-making system** - Does not provide liquidity or pricing

## What Synapse MSI IS

- ✅ **Data quality validator** - Assesses temporal coherence in market data
- ✅ **Research framework** - Quantifies cross-venue synchronization performance  
- ✅ **Replay integrity tool** - Validates backtest data temporal assumptions
- ✅ **Infrastructure diagnostic** - Identifies systematic timing issues

---

## Dependencies

```
pandas      # Data manipulation
pyarrow     # Parquet support  
duckdb      # Fallback data engine
requests    # HTTP client for live demo
```

---

## Academic Citation

If using Synapse MSI in research:

```
Synapse Market-State Integrity Framework (2026)
"Cross-Venue Temporal Coherence Assessment in Cryptocurrency Perpetual Futures Markets"  
Research Preview v1.0
```

---

## License & Disclaimer

This research software is provided for **educational and research purposes only**. 

**No warranty of any kind.** Market data contains errors. Temporal analysis has limitations. Past performance does not predict future results. Cryptocurrency markets are volatile and speculative.

**Use at your own risk.** The authors assume no liability for any trading losses, data errors, or infrastructure failures resulting from use of this software.