# Synapse Market-State Integrity Findings

## Executive Summary

Synapse reconstructed 2,329,481 BTC/ETH perpetual futures market states across Binance, Bybit, OKX, and Hyperliquid using deterministic reconstruction and temporal alignment, venue freshness validation, and strict market-state integrity policies.

The core finding is that observed cross-venue top-of-book spreads are not uniformly reliable. Across the current research-preview dataset, 1,277,377 spreads were invalidated under strict temporal-coherence rules, producing a 47.72% average market-state invalidation rate.

This is not an alpha claim, execution recommendation, or allegation of venue misconduct. It is a market-data integrity result: many apparent cross-venue states fail synchronization and freshness validation once reconstructed deterministically.

## Dataset Scale

- 2,329,481 reconstructed market-state snapshots
- 15 daily integrity releases
- Instruments: BTCUSDT_PERP, ETHUSDT_PERP
- Venues: Binance, Bybit, OKX, Hyperliquid
- 1,277,377 invalidated spreads
- 47.72% average market-state invalidation rate

## Core Finding

Observed cross-venue spreads can materially degrade when tested against temporal-coherence constraints.

In degraded regimes, invalidation exceeded 90%:
- BTCUSDT_PERP on 2026-04-09: 96.00% invalidation
- ETHUSDT_PERP on 2026-04-09: 93.94% invalidation

In normalized regimes, invalidation stabilized closer to 23–31%.

This suggests that cross-venue market-state reliability is regime dependent. A spread observed from fragmented venues may not represent a simultaneously coherent state unless venue timestamps, quote age, and synchronization gaps are validated.

## Interpretation

A naive cross-venue comparison asks:

> What is the best bid and best ask across venues?

Synapse asks a stricter question:

> Did those prices coexist within a defensible temporal window?

Under the current strict policy:
- sync gap must be <= 500ms
- quote age must be <= 1000ms

If a market state fails these constraints, Synapse does not claim the price is fake. It marks the state as temporally invalid for strict reconstruction purposes.

Temporal invalidation does not imply unusable market data. It indicates that the observed state fails the current strict reconstruction policy for synchronized replay-oriented analysis.

## Institutional Relevance

This matters for:

- backtesting reliability
- cross-venue execution simulation
- market-making research
- venue routing logic
- signal integrity
- market-data QA
- replay validation
- stale liquidity detection

The practical issue is not whether a spread appeared in raw data. The issue is whether the spread survived deterministic reconstruction with timestamp provenance and freshness controls.

## Current Status

This is a research-preview dataset. Additional daily releases, venue-pair breakdowns, and phantom arbitrage case studies are being added.

The current evidence is sufficient to demonstrate that temporal market-state integrity is measurable, regime dependent, and commercially relevant to desks that rely on cross-venue crypto data.
