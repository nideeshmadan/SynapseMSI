"""Helpers for independent investigation reproduction from archived observations.

Role: thin orchestration over consensus, assignment, and eligibility.
Derived from the internal reconstruction implementation for standalone
Synapse MSI reproduction.
Does not invent methodology or provenance.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from synapse_msi.canonical_absence import (
    canonical_nonzero_decimal,
    is_exact_zero,
    mark_price_available,
)
from synapse_msi.consensus import (
    CANONICAL_CONSENSUS_METHODOLOGY_VERSION,
    build_consensus,
)
from synapse_msi.decimals import quantize_bps
from synapse_msi.freshness_episode import (
    detect_venue_staleness_episode,
    observations_for_scan,
)
from synapse_msi.historical_corpus.assignment import assign_regime_from_row
from synapse_msi.historical_corpus.eligibility import (
    evaluate_artifact_comparability_eligibility,
)
from synapse_msi.historical_corpus.frozen_registry import (
    FrozenAcquisitionRegistry,
    assert_registry_covers_observations,
    assign_regime_from_frozen_registry,
    load_frozen_registry_from_example,
)
from synapse_msi.historical_corpus.investigation_context import (
    aggregate_regime_assignments,
)
from synapse_msi.historical_corpus.models import RegimeAssignment
from synapse_msi.historical_corpus.provenance_registry import (
    DEFAULT_SIDECAR_COMPARISON_SCOPE,
    WORKING_PROVENANCE_REGISTRY_VERSION,
)
from synapse_msi.ids import stable_investigation_id
from synapse_msi.methodology_versions import (
    DETECTION_VERSION,
    METHODOLOGY_VERSION,
    RECONSTRUCTION_VERSION,
)
from synapse_msi.types import NormalizedVenueData


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_ts(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    text = str(value).strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def observation_to_normalized(row: Mapping[str, Any]) -> NormalizedVenueData:
    """Project an archived observation row into NormalizedVenueData."""
    instrument = str(row.get("instrument") or row.get("instrument_canonical") or "")
    mark = row.get("mark_price")
    if mark is not None:
        # Exact zero (including Parquet 0E-18) normalizes to the canonical absent sentinel.
        mark = "0" if is_exact_zero(mark) else str(mark)
    funding = row.get("funding_rate")
    # Funding uses the same zero-unavailable rule; absent funding gets the
    # historical reproduction default fill used by NormalizedVenueData paths.
    if funding in (None, "", 0) or is_exact_zero(funding):
        funding = "0.0001"
    return NormalizedVenueData(
        venue=str(row["venue"]),
        instrument_canonical=instrument,
        timestamp=_parse_ts(
            row.get("venue_timestamp") or row.get("timestamp") or row.get("scan_timestamp")
        ),
        mark_price=str(mark),
        bid_price=None if row.get("bid_price") is None else str(row.get("bid_price")),
        ask_price=None if row.get("ask_price") is None else str(row.get("ask_price")),
        funding_rate=str(funding),
        oi_usd=str(row.get("oi_usd") or "0"),
        volume_24h_usd=str(row.get("volume_24h_usd") or "0"),
        spread_bps=str(row.get("spread_bps") or "0"),
        price_change_24h_bps=str(row.get("price_change_24h_bps") or "0"),
        staleness_ms=float(row.get("staleness_ms") or 0.0),
        usable=bool(row.get("usable", True)),
        provenance_id=str(row.get("provenance_id") or f"archive:{row['venue']}"),
        normalization_rules_applied=list(row.get("normalization_rules_applied") or []),
        source_provenance=dict(row["source_provenance"])
        if isinstance(row.get("source_provenance"), Mapping)
        else None,
        field_provenance=dict(row["field_provenance"])
        if isinstance(row.get("field_provenance"), Mapping)
        else None,
        native_mark_price=None
        if row.get("native_mark_price") is None
        else str(row.get("native_mark_price")),
    )


def acquisition_row_from_observation(row: Mapping[str, Any]) -> Dict[str, Any]:
    """Build an assignment input row from archived observation acquisition evidence."""
    acq = row.get("acquisition") or {}
    if not isinstance(acq, Mapping):
        acq = {}
    payload = dict(acq.get("payload") or {})
    if row.get("native_mark_price") is not None and "native_mark_price" not in payload:
        payload["native_mark_price"] = row["native_mark_price"]
    out: Dict[str, Any] = {
        "exchange": acq.get("exchange") or row.get("venue"),
        "venue": acq.get("venue") or row.get("venue"),
        "ingest_type": acq.get("ingest_type"),
        "transport": acq.get("transport"),
        "payload": payload,
    }
    if acq.get("acquisition_regime_id"):
        out["acquisition_regime_id"] = acq["acquisition_regime_id"]
    if acq.get("collector_service_name"):
        out["collector_service_name"] = acq["collector_service_name"]
    return out


@dataclass(frozen=True)
class VenueReproductionRow:
    venue: str
    source_observation_timestamp: str
    canonical_timestamp: str
    included: bool
    exclusion_reason: Optional[str]
    canonical_value: Optional[str]
    acquisition_status: str
    acquisition_regime_id: str
    consensus_input_value: Optional[str]
    disagreement_bps: Optional[str]
    order_position: int


@dataclass(frozen=True)
class ReproductionResult:
    investigation_id: str
    instrument: str
    window_start: str
    window_end: str
    included_venues: Tuple[str, ...]
    excluded_venues: Dict[str, str]
    consensus_mark: str
    disagreement_score: str
    methodology_version: str
    detection_version: str
    reconstruction_version: str
    provenance_classification: Dict[str, Any]
    comparability_eligibility: str
    comparability_reason_code: str
    comparison_scope: str
    venue_table: Tuple[VenueReproductionRow, ...]
    consensus_venues_used: Tuple[str, ...]

    def to_published_dict(self) -> Dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "instrument": self.instrument,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "included_venues": list(self.included_venues),
            "excluded_venues": dict(self.excluded_venues),
            "consensus_mark": self.consensus_mark,
            "disagreement_score": self.disagreement_score,
            "methodology_version": self.methodology_version,
            "detection_version": self.detection_version,
            "reconstruction_version": self.reconstruction_version,
            "canonical_consensus_methodology_version": CANONICAL_CONSENSUS_METHODOLOGY_VERSION,
            "working_provenance_registry_version": WORKING_PROVENANCE_REGISTRY_VERSION,
            "provenance_classification": dict(self.provenance_classification),
            "comparison_scope": self.comparison_scope,
            "comparability_eligibility": self.comparability_eligibility,
            "comparability_reason_code": self.comparability_reason_code,
            "consensus_venues_used": list(self.consensus_venues_used),
            "venue_table": [
                {
                    "venue": row.venue,
                    "source_observation_timestamp": row.source_observation_timestamp,
                    "canonical_timestamp": row.canonical_timestamp,
                    "included": row.included,
                    "exclusion_reason": row.exclusion_reason,
                    "canonical_value": row.canonical_value,
                    "acquisition_status": row.acquisition_status,
                    "acquisition_regime_id": row.acquisition_regime_id,
                    "consensus_input_value": row.consensus_input_value,
                    "disagreement_bps": row.disagreement_bps,
                    "order_position": row.order_position,
                }
                for row in self.venue_table
            ],
        }


def recompute_from_observations(
    observations: Sequence[Mapping[str, Any]],
    *,
    episode_id: str,
    instrument: str,
    window_start: str,
    window_end: str,
    comparison_scope: str = DEFAULT_SIDECAR_COMPARISON_SCOPE,
    frozen_registry: Optional[FrozenAcquisitionRegistry] = None,
) -> ReproductionResult:
    """Independently reconstruct consensus/disagreement/provenance from observations.

    When ``frozen_registry`` is supplied (modern package pin), observation
    assignment and regime-id support MUST use that artifact — not the working
    operational registry — for provenance/comparability equality fields.
    """
    if not observations:
        raise ValueError("observations are required")

    sorted_obs = sorted(
        observations,
        key=lambda row: (str(row.get("venue") or ""), str(row.get("scan_timestamp") or "")),
    )
    normalized = [observation_to_normalized(row) for row in sorted_obs]
    consensus = build_consensus(normalized, instrument)

    if frozen_registry is not None:
        assert_registry_covers_observations(
            frozen_registry,
            sorted_obs,
            acquisition_row_builder=acquisition_row_from_observation,
        )

    assignments: List[RegimeAssignment] = []
    for row in sorted_obs:
        acq_row = acquisition_row_from_observation(row)
        if acq_row.get("ingest_type") or acq_row.get("acquisition_regime_id") or (
            frozen_registry is not None and acq_row.get("transport")
        ):
            if frozen_registry is not None:
                assignments.append(
                    assign_regime_from_frozen_registry(acq_row, frozen_registry)
                )
            else:
                assignments.append(assign_regime_from_row(acq_row))
        else:
            assignments.append(
                RegimeAssignment(
                    acquisition_regime_id="unknown.insufficient_provenance",
                    assignment_method="unknown",
                    assignment_status="unknown",
                    evidence_fields=("archived_observation_without_acquisition_metadata",),
                    unresolved_reason="missing_acquisition_metadata",
                    comparison_group="unknown",
                    provenance_policy_version=None,
                )
            )

    context = aggregate_regime_assignments(assignments)
    known_ids = frozen_registry.regime_ids if frozen_registry is not None else None
    eligibility = evaluate_artifact_comparability_eligibility(
        {
            **context.to_dict(),
            "linkage_status": (
                "insufficient_raw_lineage"
                if context.assignment_status == "unknown"
                else "derived_from_preserved_lineage"
            ),
            "linkage_method": (
                "historical_lineage_unavailable"
                if context.assignment_status == "unknown"
                else "episode_sidecar_aggregation"
            ),
        },
        comparison_scope=comparison_scope,
        known_regime_ids=known_ids,
    )

    consensus_dec = Decimal(consensus.mark_price_consensus)
    table: List[VenueReproductionRow] = []
    excluded: Dict[str, str] = {}
    included: List[str] = []
    for position, (row, assignment) in enumerate(
        sorted(zip(sorted_obs, assignments), key=lambda item: str(item[0]["venue"])),
        start=1,
    ):
        venue = str(row["venue"])
        mark = row.get("mark_price")
        included_flag = True
        reason = None
        consensus_input = None
        disagreement = None
        mark_dec: Optional[Decimal] = None
        if mark in (None, ""):
            included_flag = False
            reason = "missing_or_zero_mark_price"
            excluded[venue] = reason
        elif not mark_price_available(mark):
            # Exact zero (including Parquet decimal128 zeros such as 0E-18)
            # is unavailable for native-mark consensus input.
            included_flag = False
            reason = "missing_or_zero_mark_price"
            excluded[venue] = reason
        else:
            mark_dec = canonical_nonzero_decimal("mark_price", mark)
            if mark_dec is None:
                included_flag = False
                reason = "mark_price_parse_failure"
                excluded[venue] = reason
            else:
                consensus_input = str(mark)
                included.append(venue)
                if consensus_dec > 0:
                    disagreement = quantize_bps(
                        abs(mark_dec - consensus_dec)
                        / consensus_dec
                        * Decimal("10000")
                    )
        table.append(
            VenueReproductionRow(
                venue=venue,
                source_observation_timestamp=str(
                    row.get("venue_timestamp") or row.get("timestamp") or ""
                ),
                canonical_timestamp=str(
                    row.get("scan_timestamp") or row.get("canonical_timestamp_utc") or ""
                ),
                included=included_flag,
                exclusion_reason=reason,
                canonical_value=None if mark is None else str(mark),
                acquisition_status=assignment.assignment_status,
                acquisition_regime_id=assignment.acquisition_regime_id,
                consensus_input_value=consensus_input,
                disagreement_bps=disagreement,
                order_position=position,
            )
        )

    investigation_id = stable_investigation_id(
        instrument, window_start, window_end, episode_id
    )
    return ReproductionResult(
        investigation_id=investigation_id,
        instrument=instrument,
        window_start=window_start,
        window_end=window_end,
        included_venues=tuple(sorted(included)),
        excluded_venues=excluded,
        consensus_mark=str(consensus.mark_price_consensus),
        disagreement_score=str(consensus.disagreement_score),
        methodology_version=METHODOLOGY_VERSION,
        detection_version=DETECTION_VERSION,
        reconstruction_version=RECONSTRUCTION_VERSION,
        provenance_classification={
            "assignment_status": context.assignment_status,
            "assignment_method": context.assignment_method,
            "primary_regime_id": context.primary_regime_id,
            "linked_regime_ids": list(context.linked_regime_ids),
            "spans_multiple_regimes": context.spans_multiple_regimes,
            "comparison_group": context.comparison_group,
            "unresolved_reason": context.unresolved_reason,
            "acquisition_regime_id": context.acquisition_regime_id,
        },
        comparability_eligibility=eligibility.comparability_eligibility,
        comparability_reason_code=eligibility.comparability_reason_code,
        comparison_scope=eligibility.comparison_scope,
        venue_table=tuple(table),
        consensus_venues_used=tuple(consensus.venues_used),
    )


def compare_published(
    published: Mapping[str, Any],
    recomputed: ReproductionResult,
) -> List[str]:
    """Return human-readable diffs; empty means exact required match."""
    diffs: List[str] = []

    def _check(key: str, expected: Any, actual: Any) -> None:
        if expected != actual:
            diffs.append(f"{key}: published={expected!r} recomputed={actual!r}")

    _check("investigation_id", published.get("investigation_id"), recomputed.investigation_id)
    _check("instrument", published.get("instrument"), recomputed.instrument)
    _check("window_start", published.get("window_start"), recomputed.window_start)
    _check("window_end", published.get("window_end"), recomputed.window_end)
    _check(
        "included_venues",
        list(published.get("included_venues") or []),
        list(recomputed.included_venues),
    )
    _check(
        "excluded_venues",
        dict(published.get("excluded_venues") or {}),
        dict(recomputed.excluded_venues),
    )
    _check(
        "consensus_mark",
        str(published.get("consensus_mark")),
        str(recomputed.consensus_mark),
    )
    _check(
        "disagreement_score",
        str(published.get("disagreement_score")),
        str(recomputed.disagreement_score),
    )
    _check(
        "methodology_version",
        published.get("methodology_version"),
        recomputed.methodology_version,
    )
    pub_prov = published.get("provenance_classification") or {}
    for key in (
        "assignment_status",
        "primary_regime_id",
        "spans_multiple_regimes",
        "comparison_group",
    ):
        _check(
            f"provenance_classification.{key}",
            pub_prov.get(key),
            recomputed.provenance_classification.get(key),
        )
    _check(
        "comparability_eligibility",
        published.get("comparability_eligibility"),
        recomputed.comparability_eligibility,
    )
    _check(
        "comparability_reason_code",
        published.get("comparability_reason_code"),
        recomputed.comparability_reason_code,
    )
    return diffs


def _float_close(a: Any, b: Any, *, places: int = 6) -> bool:
    try:
        return round(float(a), places) == round(float(b), places)
    except (TypeError, ValueError):
        return False


def compare_freshness_episode(
    published: Mapping[str, Any],
    freshness: Mapping[str, Any],
) -> List[str]:
    """Compare published freshness_episode fields to a recomputed detector result."""
    diffs: List[str] = []
    expected = published.get("freshness_episode") or {}
    if not expected:
        diffs.append("published.freshness_episode missing")
        return diffs

    def _check(key: str, exp: Any, act: Any) -> None:
        if exp != act:
            diffs.append(f"freshness_episode.{key}: published={exp!r} recomputed={act!r}")

    for key in (
        "affected_venue",
        "episode_start",
        "episode_end",
        "peak_scan_timestamp",
        "peak_sequence",
        "recovery_start",
        "recovery_snapshot_count",
        "recovery_qualified",
        "threshold_crossed",
        "pre_entry_scan_timestamp",
        "adoption_scan_timestamp",
    ):
        _check(key, expected.get(key), freshness.get(key))

    if not _float_close(expected.get("duration_seconds"), freshness.get("duration_seconds")):
        _check(
            "duration_seconds",
            expected.get("duration_seconds"),
            freshness.get("duration_seconds"),
        )
    if not _float_close(
        expected.get("peak_observation_age_seconds"),
        freshness.get("peak_observation_age_seconds"),
    ):
        _check(
            "peak_observation_age_seconds",
            expected.get("peak_observation_age_seconds"),
            freshness.get("peak_observation_age_seconds"),
        )
    return diffs


def recompute_investigation_package(
    observations: Sequence[Mapping[str, Any]],
    *,
    published: Mapping[str, Any],
    episode_id: str,
    example_dir: Optional[Path] = None,
    frozen_registry: Optional[FrozenAcquisitionRegistry] = None,
) -> Tuple[ReproductionResult, Optional[Dict[str, Any]]]:
    """Reproduce consensus (and freshness when applicable) from packaged rows.

    For ``venue_staleness`` packages, freshness is recomputed from the full
    observation sequence; peak consensus uses only the peak-scan rows.

    When ``example_dir`` is provided, any package-pinned frozen acquisition-regime
    evidence is loaded and used for modern provenance/comparability equality.
    """
    instrument = str(published["instrument"])
    window_start = str(published["window_start"])
    window_end = str(published["window_end"])
    source = published.get("source") or {}
    comparison_scope = str(
        published.get("comparison_scope")
        or DEFAULT_SIDECAR_COMPARISON_SCOPE
    )

    if frozen_registry is None and example_dir is not None:
        frozen_registry = load_frozen_registry_from_example(example_dir)

    freshness_dict: Optional[Dict[str, Any]] = None
    consensus_rows: Sequence[Mapping[str, Any]] = observations

    # Only modern bounded freshness packages publish freshness_episode and
    # require sequence-level detector recompute. Historical venue_staleness
    # peak fixtures remain consensus-only reproductions.
    if published.get("freshness_episode"):
        affected = str(
            (published.get("freshness_episode") or {}).get("affected_venue")
            or source.get("affected_venue")
            or "binance"
        )
        freshness = detect_venue_staleness_episode(
            observations, affected_venue=affected
        )
        freshness_dict = freshness.to_dict()
        peak_rows = observations_for_scan(
            observations, freshness.peak_scan_timestamp
        )
        if not peak_rows:
            raise ValueError(
                f"no observations at peak scan {freshness.peak_scan_timestamp}"
            )
        consensus_rows = peak_rows
        # Episode bounds are authoritative for freshness packages.
        window_start = freshness.episode_start
        window_end = freshness.episode_end

    recomputed = recompute_from_observations(
        consensus_rows,
        episode_id=episode_id,
        instrument=instrument,
        window_start=window_start,
        window_end=window_end,
        comparison_scope=comparison_scope,
        frozen_registry=frozen_registry,
    )
    return recomputed, freshness_dict


def format_venue_table(rows: Sequence[VenueReproductionRow]) -> str:
    headers = [
        "venue",
        "source_ts",
        "canonical_ts",
        "included",
        "exclusion",
        "mark",
        "acq_status",
        "regime",
        "disagreement_bps",
        "order",
    ]
    lines = [" | ".join(headers), " | ".join("---" for _ in headers)]
    for row in rows:
        lines.append(
            " | ".join(
                [
                    row.venue,
                    row.source_observation_timestamp,
                    row.canonical_timestamp,
                    str(row.included),
                    row.exclusion_reason or "",
                    row.canonical_value or "",
                    row.acquisition_status,
                    row.acquisition_regime_id,
                    row.disagreement_bps or "",
                    str(row.order_position),
                ]
            )
        )
    return "\n".join(lines)
