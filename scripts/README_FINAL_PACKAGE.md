# Synapse Market-State Integrity Research Package

## Overview

This package contains empirical research on cross-venue market-state temporal coherence in cryptocurrency perpetual futures markets. The analysis examines the validity of observed cross-venue spread calculations when venue data timestamps lack synchronization guarantees.

## Core Thesis

Observed cross-venue spreads do not necessarily represent temporally coherent market states. Price observations from different venues may reflect different points in time, potentially invalidating spread calculations and derived market-state inferences.

## Recommended Reading Order

1. **INSTITUTIONAL_REPORT.md** - Executive summary and key findings
2. **FINDINGS.md** - Detailed empirical results and statistical analysis  
3. **METHODOLOGY.md** - Research methodology and validation framework
4. **schema/schema.md** - Data schema and field definitions

## Package Structure

```
├── sample_data/           # Parquet samples for validation
├── charts/               # Empirical analysis visualizations
├── reports/              # Generated analysis reports
├── methodology/          # Research methodology documentation
├── schema/               # Data schema specifications
└── sample_queries/       # SQL queries for data exploration
```

## Included Visualizations

- **invalidation_by_regime.png** - Spread invalidation rates across market regimes
- **spread_state_timeline.png** - Temporal evolution of spread validity
- **sync_gap_distribution.png** - Distribution of cross-venue synchronization gaps
- **persistence_decay.png** - Decay analysis of valid spread state persistence

## Strict Policy Parameters

The temporal coherence validation framework employs:

- **Synchronization gap threshold**: ≤ 500ms
- **Best pair age threshold**: ≤ 1000ms

These parameters define the maximum acceptable temporal deviation for valid cross-venue market-state calculations.

## Intended Use

This research package is designed for:

- Replay validation and backtesting accuracy assessment
- Market-data quality assurance protocols
- Execution simulation research with temporal fidelity requirements
- Cross-venue temporal coherence analysis

## Important Disclaimer

**This package is NOT:**
- A trading signal or strategy recommendation
- Investment advice or alpha generation methodology  
- A predictive model for market movements
- A commercial trading system

## Reproducibility

The package includes representative parquet data samples and corresponding SQL queries to enable independent validation of findings. Sample queries demonstrate key analytical techniques and can be executed against the provided datasets.

---

*This research was conducted using production market-data infrastructure with microsecond-precision timestamping and cross-venue synchronization monitoring.*