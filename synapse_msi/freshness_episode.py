"""Deterministic venue-freshness episode detection from packaged observations.

Mirrors the public ``venue_staleness`` rules documented in specifications/reconstruction-standard.md:
enter when usable venue age ≥ 60s; recover after 5 consecutive healthy snapshots.
Age is ``scan_timestamp − venue observation timestamp`` (never read from metadata).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

STALE_ENTER_SECONDS = 60.0
RECOVERY_SNAPSHOTS = 5


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


def _to_z(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class SnapshotVenueAge:
    venue: str
    usable: bool
    age_seconds: float
    venue_timestamp: str
    scan_timestamp: str
    sequence: int
    raw_row_id: Optional[str]


@dataclass(frozen=True)
class FreshnessEpisodeResult:
    affected_venue: str
    enter_threshold_seconds: float
    recovery_snapshots_required: int
    episode_start: str
    episode_end: str
    duration_seconds: float
    peak_observation_age_seconds: float
    peak_scan_timestamp: str
    peak_sequence: int
    recovery_start: str
    recovery_snapshot_count: int
    recovery_qualified: bool
    threshold_crossed: bool
    packaged_snapshot_count: int
    pre_entry_scan_timestamp: Optional[str]
    adoption_scan_timestamp: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "affected_venue": self.affected_venue,
            "enter_threshold_seconds": self.enter_threshold_seconds,
            "recovery_snapshots_required": self.recovery_snapshots_required,
            "episode_start": self.episode_start,
            "episode_end": self.episode_end,
            "duration_seconds": self.duration_seconds,
            "peak_observation_age_seconds": self.peak_observation_age_seconds,
            "peak_scan_timestamp": self.peak_scan_timestamp,
            "peak_sequence": self.peak_sequence,
            "recovery_start": self.recovery_start,
            "recovery_snapshot_count": self.recovery_snapshot_count,
            "recovery_qualified": self.recovery_qualified,
            "threshold_crossed": self.threshold_crossed,
            "packaged_snapshot_count": self.packaged_snapshot_count,
            "pre_entry_scan_timestamp": self.pre_entry_scan_timestamp,
            "adoption_scan_timestamp": self.adoption_scan_timestamp,
        }


def _raw_row_id(row: Mapping[str, Any]) -> Optional[str]:
    linkage = row.get("raw_linkage")
    if isinstance(linkage, Mapping) and linkage.get("raw_row_id") is not None:
        return str(linkage["raw_row_id"])
    acq = row.get("acquisition") if isinstance(row.get("acquisition"), Mapping) else {}
    if acq.get("raw_row_id") is not None:
        return str(acq["raw_row_id"])
    return None


def group_observations_by_snapshot(
    observations: Sequence[Mapping[str, Any]],
) -> List[Tuple[str, int, List[Mapping[str, Any]]]]:
    """Group rows by (scan_timestamp, sequence), ordered chronologically."""
    buckets: Dict[Tuple[str, int], List[Mapping[str, Any]]] = {}
    for row in observations:
        scan = str(row.get("scan_timestamp") or row.get("canonical_timestamp_utc") or "")
        try:
            sequence = int(row.get("sequence"))
        except (TypeError, ValueError):
            sequence = -1
        buckets.setdefault((scan, sequence), []).append(row)
    ordered = sorted(buckets.items(), key=lambda item: (_parse_ts(item[0][0]), item[0][1]))
    return [(scan, sequence, rows) for (scan, sequence), rows in ordered]


def venue_age_for_snapshot(
    *,
    venue: str,
    scan_timestamp: str,
    sequence: int,
    rows: Sequence[Mapping[str, Any]],
) -> Optional[SnapshotVenueAge]:
    match = next(
        (row for row in rows if str(row.get("venue") or "").lower() == venue.lower()),
        None,
    )
    if match is None:
        return None
    venue_ts = str(
        match.get("venue_timestamp")
        or match.get("timestamp")
        or match.get("effective_observation_timestamp")
        or ""
    )
    if not venue_ts:
        return None
    age = max(0.0, (_parse_ts(scan_timestamp) - _parse_ts(venue_ts)).total_seconds())
    return SnapshotVenueAge(
        venue=venue.lower(),
        usable=bool(match.get("usable", True)),
        age_seconds=age,
        venue_timestamp=venue_ts,
        scan_timestamp=scan_timestamp,
        sequence=sequence,
        raw_row_id=_raw_row_id(match),
    )


def validate_raw_linkage_uniqueness(
    observations: Sequence[Mapping[str, Any]],
) -> List[str]:
    """Return errors when packaged (sequence, venue) linkage is not unique."""
    errors: List[str] = []
    seen: Dict[Tuple[int, str], str] = {}
    for row in observations:
        venue = str(row.get("venue") or "")
        try:
            sequence = int(row.get("sequence"))
        except (TypeError, ValueError):
            errors.append(f"missing_or_invalid_sequence for venue={venue}")
            continue
        key = (sequence, venue)
        ref = _raw_row_id(row) or ""
        if key in seen:
            errors.append(
                f"duplicate_snapshot_venue_linkage sequence={sequence} venue={venue}"
            )
        else:
            seen[key] = ref
        if not ref:
            errors.append(f"missing_raw_row_id sequence={sequence} venue={venue}")
    return errors


def detect_venue_staleness_episode(
    observations: Sequence[Mapping[str, Any]],
    *,
    affected_venue: str,
    enter_threshold_seconds: float = STALE_ENTER_SECONDS,
    recovery_snapshots_required: int = RECOVERY_SNAPSHOTS,
) -> FreshnessEpisodeResult:
    """Recompute a closed venue_staleness episode from packaged observations."""
    linkage_errors = validate_raw_linkage_uniqueness(observations)
    if linkage_errors:
        raise ValueError("; ".join(linkage_errors))

    venue = affected_venue.lower()
    snapshots = group_observations_by_snapshot(observations)
    if not snapshots:
        raise ValueError("no snapshots in observations")

    ages: List[SnapshotVenueAge] = []
    for scan, sequence, rows in snapshots:
        age = venue_age_for_snapshot(
            venue=venue, scan_timestamp=scan, sequence=sequence, rows=rows
        )
        if age is None:
            raise ValueError(f"missing affected venue {venue} at sequence={sequence}")
        ages.append(age)

    open_ep: Optional[Dict[str, Any]] = None
    closed: Optional[Dict[str, Any]] = None
    pre_entry: Optional[SnapshotVenueAge] = None
    adoption: Optional[SnapshotVenueAge] = None
    peak_et_before_adoption: Optional[str] = None

    for age in ages:
        stale = age.usable and age.age_seconds >= enter_threshold_seconds
        healthy = age.usable and age.age_seconds < enter_threshold_seconds
        if open_ep is None:
            if stale:
                open_ep = {
                    "start": age,
                    "peak": age,
                    "consecutive_healthy": 0,
                    "recovery_start": None,
                }
                peak_et_before_adoption = age.venue_timestamp
            else:
                pre_entry = age
            continue

        if age.age_seconds > open_ep["peak"].age_seconds:
            open_ep["peak"] = age

        if (
            peak_et_before_adoption is not None
            and adoption is None
            and age.venue_timestamp != peak_et_before_adoption
        ):
            adoption = age

        if healthy:
            open_ep["consecutive_healthy"] += 1
            if open_ep["recovery_start"] is None:
                open_ep["recovery_start"] = age
            if open_ep["consecutive_healthy"] >= recovery_snapshots_required:
                closed = open_ep
                closed["end"] = age
                break
        else:
            open_ep["consecutive_healthy"] = 0
            open_ep["recovery_start"] = None

    if closed is None:
        raise ValueError(
            "packaged observations do not contain a closed venue_staleness episode "
            f"for {venue}"
        )

    start: SnapshotVenueAge = closed["start"]
    end: SnapshotVenueAge = closed["end"]
    peak: SnapshotVenueAge = closed["peak"]
    recovery_start: SnapshotVenueAge = closed["recovery_start"]
    duration = (_parse_ts(end.scan_timestamp) - _parse_ts(start.scan_timestamp)).total_seconds()

    return FreshnessEpisodeResult(
        affected_venue=venue,
        enter_threshold_seconds=enter_threshold_seconds,
        recovery_snapshots_required=recovery_snapshots_required,
        episode_start=_to_z(_parse_ts(start.scan_timestamp)),
        episode_end=_to_z(_parse_ts(end.scan_timestamp)),
        duration_seconds=duration,
        peak_observation_age_seconds=peak.age_seconds,
        peak_scan_timestamp=_to_z(_parse_ts(peak.scan_timestamp)),
        peak_sequence=peak.sequence,
        recovery_start=_to_z(_parse_ts(recovery_start.scan_timestamp)),
        recovery_snapshot_count=recovery_snapshots_required,
        recovery_qualified=True,
        threshold_crossed=True,
        packaged_snapshot_count=len(snapshots),
        pre_entry_scan_timestamp=(
            None if pre_entry is None else _to_z(_parse_ts(pre_entry.scan_timestamp))
        ),
        adoption_scan_timestamp=(
            None if adoption is None else _to_z(_parse_ts(adoption.scan_timestamp))
        ),
    )


def observations_for_scan(
    observations: Sequence[Mapping[str, Any]],
    scan_timestamp: str,
) -> List[Mapping[str, Any]]:
    target = _to_z(_parse_ts(scan_timestamp))
    return [
        row
        for row in observations
        if _to_z(_parse_ts(row.get("scan_timestamp") or row.get("canonical_timestamp_utc")))
        == target
    ]
