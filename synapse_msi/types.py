"""Minimal venue/consensus carriers for deterministic reproduction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional


@dataclass(frozen=True)
class NormalizedVenueData:
    venue: str
    instrument_canonical: str
    timestamp: datetime
    mark_price: str
    funding_rate: str
    oi_usd: str
    volume_24h_usd: str
    spread_bps: str
    price_change_24h_bps: str
    staleness_ms: float
    usable: bool
    provenance_id: str
    normalization_rules_applied: List[str]
    bid_price: Optional[str] = None
    ask_price: Optional[str] = None
    oi_usd_trustworthy: Optional[str] = None
    oi_calc_method: Optional[str] = None
    exclusion_reasons: Optional[Dict[str, str]] = None
    trust_level: Optional[str] = None
    source_provenance: Optional[Dict[str, Any]] = None
    field_provenance: Optional[Dict[str, Any]] = None
    native_mark_price: Optional[str] = None


@dataclass(frozen=True)
class ConsensusData:
    instrument: str
    timestamp: datetime
    mark_price_consensus: str
    funding_rate_consensus: str
    oi_total_usd: Optional[str]
    venues_count: int
    venues_used: List[str]
    venues_usable: List[str]
    disagreement_flags: List[str]
    disagreement_score: str
    quality: Literal["good", "degraded", "unusable"]
    consensus_provenance_ids: List[str]
    venues_excluded: Optional[List[str]] = None
    venues_degraded: Optional[List[str]] = None
    venue_exclusion_reasons: Optional[Dict[str, str]] = None
    disagreement_breakdown: Optional[Dict[str, Any]] = None
    field_disagreement_metrics: Optional[List[Dict[str, Any]]] = None
    legacy_analysis_metadata: Optional[Dict[str, Any]] = None
    oi_source_venues: Optional[List[str]] = None
