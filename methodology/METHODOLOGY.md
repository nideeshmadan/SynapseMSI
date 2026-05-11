# Methodology

Synapse reconstructs cross-venue perpetual futures market states from fragmented venue observations.

The preview dataset focuses on BTCUSDT_PERP and ETHUSDT_PERP across Binance, Bybit, OKX, and Hyperliquid.

## Core Concepts

An observed spread state is constructed from the best available cross-venue bid and ask.

A temporally coherent state is an observed spread state that passes strict synchronization and freshness constraints.

## Strict Policy

- `sync_gap_ms <= 500`
- `best_pair_age_ms <= 1000`

This policy is intentionally conservative. It is designed for replay environments where sub-second synchronization materially affects market-state construction assumptions.

The framework evaluates replay sensitivity under strict coexistence constraints. It does not estimate alpha, PnL, or investment performance.

## Intended Use

- market-data integrity review
- replay validation
- venue synchronization research
- execution simulation preprocessing
- temporal quality monitoring
