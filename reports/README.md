# Synapse Dataset Preview v1

This package is a lightweight preview of Synapse market-state integrity data.

It is intended for:
- replay validation
- market-data QA
- temporal coherence research
- execution simulation infrastructure review

It is not:
- an alpha dataset
- a PnL model
- an investment signal
- a trading recommendation

## Contents

- `sample_data/` — small BTC/ETH April 9 parquet samples
- `schema/schema.md` — field definitions
- `methodology/METHODOLOGY.md` — reconstruction and validation methodology
- `charts/` — selected institutional analysis charts
- `reports/` — market-state integrity report

## Strict Temporal Policy

A spread state is considered temporally coherent only if:

- `sync_gap_ms <= 500`
- `best_pair_age_ms <= 1000`

The goal is to evaluate replay sensitivity under strict coexistence constraints, not to estimate live trading performance.
