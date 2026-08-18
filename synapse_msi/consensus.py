"""Canonical snapshot consensus used by investigation reproduction.

Authoritative algorithm documented in specifications/reconstruction-standard.md.
Derived from the internal reconstruction implementation; mark-price
median and disagreement_score behavior preserved exactly.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from statistics import median
from typing import List

from synapse_msi.canonical_absence import canonical_nonzero_decimal
from synapse_msi.decimals import quantize_bps, quantize_funding_rate, quantize_price
from synapse_msi.types import ConsensusData, NormalizedVenueData

CANONICAL_CONSENSUS_METHODOLOGY_VERSION = "canonical_snapshot_consensus_v1"
CONSENSUS_MAX_DISAGREEMENT_BPS = 50


def build_consensus(normalized: List[NormalizedVenueData], instrument: str) -> ConsensusData:
    if not normalized:
        raise ValueError("Cannot build consensus with no data")

    usable = normalized
    venues_used = sorted([n.venue for n in normalized])
    venues_usable = sorted([n.venue for n in usable])
    venues_excluded: dict = {}
    venues_degraded: dict = {}

    if len(usable) >= 2:
        quality = "good"
    elif len(usable) == 1:
        quality = "degraded"
    else:
        quality = "unusable"

    if usable:
        valid_prices = []
        valid_funding_rates = []
        for n in usable:
            mark = canonical_nonzero_decimal("mark_price", n.mark_price)
            if mark is not None:
                valid_prices.append(mark)
            funding = canonical_nonzero_decimal("funding_rate", n.funding_rate)
            if funding is not None:
                valid_funding_rates.append(funding)

        if valid_prices:
            mark_price_consensus = quantize_price(median(valid_prices))
        else:
            mark_price_consensus = "0.000000000000"

        if valid_funding_rates:
            funding_rate_consensus = quantize_funding_rate(median(valid_funding_rates))
        else:
            funding_rate_consensus = "0.000000000000"

        if valid_prices:
            price_median = Decimal(mark_price_consensus)
            if price_median > 0:
                max_deviation_bps = max(
                    abs((p - price_median) / price_median * 10000) for p in valid_prices
                )
                disagreement_score = quantize_bps(max_deviation_bps)
            else:
                disagreement_score = quantize_bps("0.0")
        else:
            disagreement_score = quantize_bps("0.0")

        disagreement_flags = []
        if Decimal(disagreement_score) > CONSENSUS_MAX_DISAGREEMENT_BPS:
            disagreement_flags.append("MARK_PRICE_DIVERGENCE_HIGH")
        if len(usable) == 1:
            disagreement_flags.append("CONSENSUS_SINGLE_VENUE_ONLY")
        if not valid_prices:
            disagreement_flags.append("NO_VALID_MARK_PRICES_FOR_CONSENSUS")
        if not valid_funding_rates:
            disagreement_flags.append("NO_VALID_FUNDING_RATES_FOR_CONSENSUS")
    else:
        mark_price_consensus = "0.000000000000"
        funding_rate_consensus = "0.000000000000"
        disagreement_score = quantize_bps("0.0")
        disagreement_flags = ["ALL_VENUES_UNUSABLE"]

    return ConsensusData(
        instrument=instrument,
        timestamp=datetime.now(timezone.utc),
        mark_price_consensus=mark_price_consensus,
        funding_rate_consensus=funding_rate_consensus,
        oi_total_usd=None,
        venues_count=len(normalized),
        venues_used=venues_used,
        venues_usable=venues_usable,
        venues_excluded=sorted(venues_excluded.keys()) if venues_excluded else [],
        venues_degraded=sorted(venues_degraded.keys()) if venues_degraded else [],
        venue_exclusion_reasons=dict(venues_excluded, **venues_degraded)
        if (venues_excluded or venues_degraded)
        else {},
        disagreement_flags=disagreement_flags,
        disagreement_score=disagreement_score,
        quality=quality,  # type: ignore[arg-type]
        consensus_provenance_ids=sorted(
            {n.provenance_id for n in normalized if n.provenance_id}
        ),
    )
