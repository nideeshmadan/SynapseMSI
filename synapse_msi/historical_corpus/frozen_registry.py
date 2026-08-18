"""Package-pinned frozen acquisition-regime evidence for public fixtures.

Layer A (this module's artifact): asserted empirical assignment records.
Layer B (assignment/aggregation/eligibility): deterministic classification policy.

The working operational registry remains non-normative for fixture reproduction.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from synapse_msi.historical_corpus.models import (
    PROVENANCE_POLICY_VERSION,
    RegimeAssignment,
)

ARTIFACT_FORMAT_VERSION = "acquisition_regime_fixture_evidence_v1"
FROZEN_REGISTRY_ID = "acquisition_regime_fixture_registry_v1"
FROZEN_REGISTRY_CONTENT_VERSION = "2026-07-30.modern_fixtures.v1"

_REQUIRED_PIN_KEYS = (
    "registry_id",
    "registry_content_version",
    "path",
    "sha256",
)


@dataclass(frozen=True)
class FrozenAssignmentRecord:
    venue: str
    instrument_scope: str
    regime_id: str
    acquisition_regime: str
    transport: str
    ingest_type: str
    collector_service_name: str
    valid_from: Optional[str]
    valid_to: Optional[str]
    comparison_group: str
    current_production: bool
    evidence_status: str


@dataclass(frozen=True)
class FrozenAcquisitionRegistry:
    artifact_format_version: str
    registry_id: str
    registry_content_version: str
    evidence_status: str
    boundary_semantics: Mapping[str, Any]
    assignments: Tuple[FrozenAssignmentRecord, ...]
    source_path: Path
    sha256: str

    @property
    def regime_ids(self) -> frozenset[str]:
        return frozenset(item.regime_id for item in self.assignments)


class FrozenRegistryError(ValueError):
    """Raised when a package-pinned frozen registry cannot be used."""


def _parse_iso(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _record_from_mapping(raw: Mapping[str, Any]) -> FrozenAssignmentRecord:
    required = (
        "venue",
        "instrument_scope",
        "regime_id",
        "acquisition_regime",
        "transport",
        "ingest_type",
        "collector_service_name",
        "comparison_group",
        "evidence_status",
    )
    missing = [key for key in required if key not in raw]
    if missing:
        raise FrozenRegistryError(f"assignment record missing keys: {missing}")
    return FrozenAssignmentRecord(
        venue=str(raw["venue"]).lower(),
        instrument_scope=str(raw["instrument_scope"]),
        regime_id=str(raw["regime_id"]),
        acquisition_regime=str(raw["acquisition_regime"]),
        transport=str(raw["transport"]),
        ingest_type=str(raw["ingest_type"]),
        collector_service_name=str(raw["collector_service_name"]),
        valid_from=None if raw.get("valid_from") is None else str(raw["valid_from"]),
        valid_to=None if raw.get("valid_to") is None else str(raw["valid_to"]),
        comparison_group=str(raw["comparison_group"]),
        current_production=bool(raw.get("current_production", False)),
        evidence_status=str(raw["evidence_status"]),
    )


def load_frozen_registry_file(path: Path) -> FrozenAcquisitionRegistry:
    raw_bytes = path.read_bytes()
    digest = sha256_bytes(raw_bytes)
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise FrozenRegistryError(f"invalid frozen registry JSON: {path}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise FrozenRegistryError("frozen registry root must be an object")

    if payload.get("artifact_format_version") != ARTIFACT_FORMAT_VERSION:
        raise FrozenRegistryError(
            "unsupported artifact_format_version: "
            f"{payload.get('artifact_format_version')!r}"
        )
    if payload.get("registry_id") != FROZEN_REGISTRY_ID:
        raise FrozenRegistryError(
            f"unexpected registry_id: {payload.get('registry_id')!r}"
        )
    if payload.get("registry_content_version") != FROZEN_REGISTRY_CONTENT_VERSION:
        raise FrozenRegistryError(
            "unexpected registry_content_version: "
            f"{payload.get('registry_content_version')!r}"
        )

    assignments_raw = payload.get("assignments")
    if not isinstance(assignments_raw, list) or not assignments_raw:
        raise FrozenRegistryError("frozen registry assignments must be a non-empty list")
    assignments = tuple(_record_from_mapping(item) for item in assignments_raw)
    boundary = payload.get("boundary_semantics") or {}
    if not isinstance(boundary, Mapping):
        raise FrozenRegistryError("boundary_semantics must be an object")

    return FrozenAcquisitionRegistry(
        artifact_format_version=str(payload["artifact_format_version"]),
        registry_id=str(payload["registry_id"]),
        registry_content_version=str(payload["registry_content_version"]),
        evidence_status=str(payload.get("evidence_status") or ""),
        boundary_semantics=dict(boundary),
        assignments=assignments,
        source_path=path.resolve(),
        sha256=digest,
    )


def verify_manifest_pin(
    *,
    example_dir: Path,
    pin: Mapping[str, Any],
) -> FrozenAcquisitionRegistry:
    """Load and verify a package-pinned frozen registry reference."""
    missing = [key for key in _REQUIRED_PIN_KEYS if key not in pin]
    if missing:
        raise FrozenRegistryError(
            f"acquisition_regime_evidence pin missing keys: {missing}"
        )

    if pin.get("registry_id") != FROZEN_REGISTRY_ID:
        raise FrozenRegistryError(
            f"pin registry_id mismatch: {pin.get('registry_id')!r}"
        )
    if pin.get("registry_content_version") != FROZEN_REGISTRY_CONTENT_VERSION:
        raise FrozenRegistryError(
            "pin registry_content_version mismatch: "
            f"{pin.get('registry_content_version')!r}"
        )

    relative = Path(str(pin["path"]))
    path = (example_dir / relative).resolve()
    if not path.is_file():
        raise FrozenRegistryError(f"frozen registry artifact missing: {path}")

    actual = sha256_file(path)
    expected = str(pin["sha256"]).lower()
    if actual != expected:
        raise FrozenRegistryError(
            f"frozen registry sha256 mismatch: expected={expected} actual={actual}"
        )

    registry = load_frozen_registry_file(path)
    if registry.sha256 != expected:
        raise FrozenRegistryError("loaded registry digest does not match pin")
    return registry


def load_frozen_registry_from_example(example_dir: Path) -> Optional[FrozenAcquisitionRegistry]:
    manifest_path = example_dir / "input_manifest.json"
    if not manifest_path.is_file():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pin = manifest.get("acquisition_regime_evidence")
    if not pin:
        return None
    if not isinstance(pin, Mapping):
        raise FrozenRegistryError("acquisition_regime_evidence must be an object")
    return verify_manifest_pin(example_dir=example_dir, pin=pin)


def _instrument_matches(scope: str, instrument: Optional[str]) -> bool:
    if scope == "*":
        return True
    if instrument is None:
        return False
    return scope == instrument


def _within_bounds(record: FrozenAssignmentRecord, ts: Optional[datetime]) -> bool:
    """Inclusive bounds; null end is open-ended. Missing ts skips the filter."""
    if ts is None:
        return True
    start = _parse_iso(record.valid_from)
    end = _parse_iso(record.valid_to)
    if start is not None and ts < start:
        return False
    if end is not None and ts > end:
        return False
    return True


def _bounds_warning(record: FrozenAssignmentRecord, ts: Optional[datetime]) -> Optional[str]:
    """Advisory warning text when a timestamp falls outside asserted bounds."""
    if ts is None:
        return None
    start = _parse_iso(record.valid_from)
    end = _parse_iso(record.valid_to)
    if start is not None and ts < start:
        return (
            f"row timestamp {ts.isoformat()} precedes valid_from "
            f"{record.valid_from} for {record.regime_id}"
        )
    if end is not None and ts > end:
        return (
            f"row timestamp {ts.isoformat()} after valid_to "
            f"{record.valid_to} for {record.regime_id}"
        )
    return None


def _observation_time(row: Mapping[str, Any]) -> Optional[datetime]:
    for key in (
        "sink_received_at",
        "collector_observed_at",
        "venue_event_time",
        "venue_timestamp",
        "effective_observation_timestamp",
        "scan_timestamp",
    ):
        parsed = _parse_iso(row.get(key))
        if parsed is not None:
            return parsed
    return None


def _unknown(
    *,
    method: str = "unknown",
    reason: str,
    evidence: Tuple[str, ...] = (),
    warnings: Tuple[str, ...] = (),
) -> RegimeAssignment:
    return RegimeAssignment(
        acquisition_regime_id="unknown.insufficient_provenance",
        assignment_method=method,  # type: ignore[arg-type]
        assignment_status="unknown",
        evidence_fields=evidence,
        warnings=warnings,
        unresolved_reason=reason,
        classifier_label="unknown_or_insufficient_provenance",
        comparison_group="unknown",
        mark_evidence="not_applicable",
        provenance_policy_version=None,
    )


def assign_regime_from_frozen_registry(
    row: Mapping[str, Any],
    registry: FrozenAcquisitionRegistry,
    *,
    enforce_time_bounds: bool = False,
) -> RegimeAssignment:
    """Deterministic observation → regime assignment against frozen evidence.

    Matching key: venue + ingest_type + transport (+ instrument_scope).
    Collector mismatch warns but does not block (existing producer behavior).
    Time-bound mismatch is advisory unless enforce_time_bounds=True.
    """
    warnings: List[str] = []
    evidence: List[str] = []

    ingest_type = str(row.get("ingest_type") or "")
    transport = str(row.get("transport") or "")
    venue = str(row.get("exchange") or row.get("venue") or "").lower()
    instrument = row.get("instrument") or row.get("instrument_canonical")
    instrument_s = None if instrument is None else str(instrument)
    explicit = row.get("acquisition_regime_id") or row.get("regime_id")
    ts = _observation_time(row)

    if not explicit and not (ingest_type or transport):
        return _unknown(reason="missing_acquisition_metadata")

    if explicit:
        evidence.append("acquisition_regime_id")
        matches = [item for item in registry.assignments if item.regime_id == str(explicit)]
        if len(matches) != 1:
            return _unknown(
                method="explicit",
                reason="explicit_regime_unknown",
                evidence=tuple(evidence),
            )
        record = matches[0]
        bound_warning = _bounds_warning(record, ts)
        if bound_warning:
            warnings.append(bound_warning)
            if enforce_time_bounds:
                return _unknown(
                    method="explicit",
                    reason="unresolved_classifier_or_inventory",
                    evidence=tuple(evidence),
                    warnings=tuple(warnings),
                )
        return RegimeAssignment(
            acquisition_regime_id=record.regime_id,
            assignment_method="explicit",
            assignment_status="definitive",
            evidence_fields=tuple(evidence),
            warnings=tuple(warnings),
            comparison_group=record.comparison_group,
            provenance_policy_version=PROVENANCE_POLICY_VERSION,
        )

    if ingest_type:
        evidence.append("ingest_type")
    if transport:
        evidence.append("transport")
    if venue:
        evidence.append("venue")

    candidates = [
        item
        for item in registry.assignments
        if item.venue == venue
        and item.ingest_type == ingest_type
        and item.transport == transport
        and _instrument_matches(item.instrument_scope, instrument_s)
    ]
    if enforce_time_bounds:
        candidates = [item for item in candidates if _within_bounds(item, ts)]

    if not candidates:
        return _unknown(
            method="row_metadata",
            reason="unresolved_classifier_or_inventory",
            evidence=tuple(dict.fromkeys(evidence)),
        )

    if len(candidates) > 1:
        production = [item for item in candidates if item.current_production]
        if len(production) == 1:
            candidates = production
        else:
            return _unknown(
                method="row_metadata",
                reason="unresolved_classifier_or_inventory",
                evidence=tuple(dict.fromkeys(evidence)),
                warnings=("multiple_frozen_assignment_matches",),
            )

    record = candidates[0]
    bound_warning = _bounds_warning(record, ts)
    if bound_warning:
        warnings.append(bound_warning)

    collector = str(row.get("collector_service_name") or "")
    if collector:
        evidence.append("collector_service_name")
        if collector != record.collector_service_name:
            warnings.append(
                f"collector_service_name={collector} differs from frozen "
                f"collector={record.collector_service_name}; "
                "row ingest metadata takes precedence"
            )

    payload = row.get("payload")
    method = "row_metadata_with_payload" if payload else "row_metadata"
    if payload:
        evidence.append("payload")

    return RegimeAssignment(
        acquisition_regime_id=record.regime_id,
        assignment_method=method,  # type: ignore[arg-type]
        assignment_status="definitive",
        evidence_fields=tuple(dict.fromkeys(evidence)),
        warnings=tuple(warnings),
        comparison_group=record.comparison_group,
        provenance_policy_version=PROVENANCE_POLICY_VERSION,
    )


def assert_registry_covers_observations(
    registry: FrozenAcquisitionRegistry,
    observations: Sequence[Mapping[str, Any]],
    *,
    acquisition_row_builder,
) -> None:
    """Fail closed when any observation with acquisition metadata cannot be assigned."""
    for row in observations:
        acq = acquisition_row_builder(row)
        if not (acq.get("ingest_type") or acq.get("acquisition_regime_id") or acq.get("transport")):
            continue
        assignment = assign_regime_from_frozen_registry(acq, registry)
        if assignment.assignment_status == "unknown":
            raise FrozenRegistryError(
                "frozen registry lacks coverage for observation venue="
                f"{acq.get('venue') or acq.get('exchange')} "
                f"ingest_type={acq.get('ingest_type')} transport={acq.get('transport')}"
            )
