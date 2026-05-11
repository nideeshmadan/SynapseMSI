# Synapse Market-State Integrity (MSI)

**Temporal coherence validation for cross-venue cryptocurrency market data**

Synapse MSI validates whether observed cross-venue spreads represent temporally coherent market states or result from asynchronous timestamp misalignment across exchanges.

## Core Research Question

**Do observed cross-venue spreads reflect genuine pricing inefficiency or temporal measurement artifacts?**

Cross-venue arbitrage opportunities may be phantom if venues report quotes at materially different times. Synapse applies strict temporal coherence constraints to distinguish real spread states from measurement noise.

---

## Local Quickstart (No VPS Required)

Validate market-state integrity using included sample data. **No API keys, VPS, or exchange access required.**

### Normalized Baseline Regime
```bash
pip3 install -r requirements.txt
python3 synapse_validate.py sample_data/btc_apr23_normalized_sample.csv
```

**Sample Output (Normalized Conditions):**
```
SYNAPSE MARKET-STATE INTEGRITY REPORT
File: sample_data/btc_apr23_normalized_sample.csv
Rows Analyzed: 10,000
Valid States: 7,524
Invalidated States: 2,476
Invalidation Rate: 24.8%
Assessment: MODERATE/LOW temporal degradation
```

### Stress Regime Comparison
```bash
python3 synapse_validate.py sample_data/btc_apr09_degraded_sample.csv
```

**Sample Output (Stress Conditions):**
```
SYNAPSE MARKET-STATE INTEGRITY REPORT  
File: sample_data/btc_apr09_degraded_sample.csv
Rows Analyzed: 10,000
Valid States: 18
Invalidated States: 9,982
Invalidation Rate: 99.8%
Assessment: SEVERE temporal degradation
```

**Key Insight:** Temporal coherence quality varies dramatically by regime. The **normalized sample** (24.8% invalidation) shows typical baseline behavior, while the **stress sample** (99.8% invalidation) demonstrates extreme temporal breakdown.

**Available Sample Regimes:**
- **Normalized**: `btc_apr23_normalized_sample.csv` - Baseline conditions (~25% invalidation)
- **Degraded**: `btc_apr09_degraded_sample.csv` - Stress conditions (~99% invalidation)  
- **Legacy**: Original samples (`btc_apr09_sample.csv`, `eth_apr09_sample.csv`)
- **Live Demo**: Optional REST workflow (may require VPS)

See [`sample_data/README.md`](sample_data/README.md) for detailed regime explanations.

---

## Optional Live Public Demo

**Note: May require VPS or non-restricted region** - Binance/Bybit public APIs can return HTTP 451/403 from some locations.

This workflow demonstrates real-time collection and validation but uses collection-time timestamps where venue event timestamps are limited. **The local sample data provides higher-fidelity analysis without network requirements.**

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
- Replay and execution-simulation input validation
- Backtest replay
- Risk analysis
- Performance attribution

---

## Methodology Note

**Local Sample Data** uses institutional research data with preserved venue-side timestamps from Synapse canonical reconstruction archive. This provides deterministic replay-oriented reconstruction and high-fidelity temporal analysis.

- **Stress regime samples**: Demonstrate extreme temporal breakdown (>99% invalidation)
- **Normalized baseline samples**: Show typical temporal behavior (~25-30% invalidation)  
- **No network access required**: Complete validation workflow works offline

**Live Public Demo** uses public REST polling with collection-time timestamps where venue event timestamps are limited. This is a workflow demonstration showing MSI validation capabilities, **not a replacement for canonical websocket/event-driven reconstruction**.

Key differences:
- **Sample Data**: WebSocket events, high-resolution venue-side timestamps, deterministic replay, no VPS needed
- **Live Demo**: REST polling, collection-time fallbacks, limited precision, may require VPS/unrestricted region

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

Analysis of 943,102 cross-venue market states reveals **regime-dependent temporal coherence**:

- **24.6%** invalidation under normalized baseline conditions
- **95.0%** invalidation during degraded temporal stress regimes  
- **35.9%** median persistence contraction under strict coherence validation
- **$192 phantom spread episodes** observed during extreme misalignment periods

**Key insight**: Temporal coherence quality varies dramatically by regime. The included samples demonstrate both stress-case behavior (99.8% invalidation) and the research baseline range.

See [`reports/FINDINGS.md`](reports/FINDINGS.md) for detailed empirical analysis.

---

## What Synapse MSI is NOT

- **Trading signal** - Validates data quality, does not generate signals
- **Investment advice** - Research tool for infrastructure assessment  
- **PnL model** - Does not estimate returns or performance
- **Execution engine** - Does not place trades or manage orders
- **Market-making system** - Does not provide liquidity or pricing

## What Synapse MSI IS

- **Data quality validator** - Assesses temporal coherence in market data
- **Research framework** - Quantifies cross-venue synchronization performance  
- **Replay integrity tool** - Validates backtest data temporal assumptions
- **Infrastructure diagnostic** - Identifies systematic timing issues

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