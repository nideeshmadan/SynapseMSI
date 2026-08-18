"""Evidence-first deterministic row → acquisition-regime assignment."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Tuple

# Producer: emits assignment_status/method; must not invent eligibility.

from synapse_msi.historical_corpus.inventory import (
    lookup_regime,
    lookup_by_classifier,
    resolve_regime_from_row,
)
from synapse_msi.historical_corpus.models import (
    PROVENANCE_POLICY_VERSION,
    RegimeAssignment,
)
from synapse_msi.historical_regime import (
    classify_historical_regime,
    classify_okx_mark_evidence,
)


def _payload(row: Mapping[str, Any]) -> Dict[str, Any]:
    payload = row.get("payload") or row.get("payload_jsonb") or {}
    return payload if isinstance(payload, dict) else {}


def _explicit_regime_id(row: Mapping[str, Any]) -> Optional[str]:
    for key in ("acquisition_regime_id", "regime_id"):
        value = row.get(key)
        if value:
            return str(value)
    metadata = row.get("metadata")
    if isinstance(metadata, dict):
        historical = metadata.get("historical_corpus") or metadata.get("historical_linkage") or {}
        if isinstance(historical, dict) and historical.get("acquisition_regime_id"):
            return str(historical["acquisition_regime_id"])
    return None


def _parse_iso(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
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
    return parsed


def _bounds_conflict(entry, row: Mapping[str, Any]) -> Optional[str]:
    """Advisory only: inventory bounds never sole assignment evidence."""
    ts = (
        _parse_iso(row.get("sink_received_at"))
        or _parse_iso(row.get("collector_observed_at"))
        or _parse_iso(row.get("venue_event_time"))
    )
    if ts is None:
        return None
    start = _parse_iso(entry.effective_start)
    end = _parse_iso(entry.effective_end)
    if start is not None and ts < start:
        return (
            f"row timestamp {ts.isoformat()} precedes inventory effective_start "
            f"{entry.effective_start} for {entry.regime_id}"
        )
    if end is not None and ts > end:
        return (
            f"row timestamp {ts.isoformat()} after inventory effective_end "
            f"{entry.effective_end} for {entry.regime_id}"
        )
    return None


def _mark_evidence_for_row(row: Mapping[str, Any], *, venue: str, classifier_label: str) -> str:
    if venue == "okx" and classifier_label == "ws_top_of_book_conditional_native":
        return classify_okx_mark_evidence(row)
    if venue == "hyperliquid" and classifier_label == "ws_top_of_book_midpoint":
        return "unavailable"
    return "not_applicable"


def _unknown_assignment(
    *,
    method: str = "unknown",
    reason: str,
    evidence: Tuple[str, ...] = (),
    warnings: Tuple[str, ...] = (),
    mark_evidence: str = "not_applicable",
    classifier_label: Optional[str] = "unknown_or_insufficient_provenance",
    unresolved_reason_detail: Optional[Dict[str, Any]] = None,
) -> RegimeAssignment:
    from synapse_msi.historical_corpus.provenance_registry import (
        assert_writer_assignment_method,
    )

    assert_writer_assignment_method(method)
    return RegimeAssignment(
        acquisition_regime_id="unknown.insufficient_provenance",
        assignment_method=method,  # type: ignore[arg-type]
        assignment_status="unknown",
        evidence_fields=evidence,
        warnings=warnings,
        unresolved_reason=reason,
        unresolved_reason_detail=unresolved_reason_detail,
        classifier_label=classifier_label,
        comparison_group="unknown",
        mark_evidence=mark_evidence,  # type: ignore[arg-type]
        provenance_policy_version=None,
    )


def assign_regime_from_row(row: Mapping[str, Any]) -> RegimeAssignment:
    """
    Canonical evidence-first assignment.

    Precedence:
      1. explicit acquisition_regime_id
      2. venue + ingest_type + transport (+ payload markers when required)
      3. collector identity as supporting evidence / conflict warning only
      4. inventory bounds as validation warnings only
      5. unknown — never timestamp-only definitive assignment
    """
    warnings: List[str] = []
    evidence: List[str] = []

    ingest_type = str(row.get("ingest_type") or "")
    transport = str(row.get("transport") or "")
    venue = str(row.get("exchange") or row.get("venue") or "").lower()
    has_row_acquisition_meta = bool(ingest_type or transport)
    has_explicit = _explicit_regime_id(row) is not None

    if not has_explicit and not has_row_acquisition_meta:
        ts_keys = [
            key
            for key in ("sink_received_at", "collector_observed_at", "venue_event_time")
            if row.get(key)
        ]
        if ts_keys:
            return _unknown_assignment(
                reason="timestamp_only_assignment_forbidden",
                evidence=tuple(ts_keys),
                warnings=("wall-clock time alone is not definitive acquisition evidence",),
            )
        return _unknown_assignment(reason="missing_acquisition_metadata")

    explicit_id = _explicit_regime_id(row)
    if explicit_id:
        evidence.append("acquisition_regime_id")
        entry = lookup_regime(explicit_id)
        if entry is None:
            return _unknown_assignment(
                method="explicit",
                reason="explicit_regime_unknown",
                unresolved_reason_detail={"regime_id": explicit_id},
                evidence=tuple(evidence),
            )
        conflict = _bounds_conflict(entry, row)
        if conflict:
            warnings.append(conflict)
        return RegimeAssignment(
            acquisition_regime_id=entry.regime_id,
            assignment_method="explicit",
            assignment_status="definitive",
            evidence_fields=tuple(evidence),
            warnings=tuple(warnings),
            classifier_label=entry.classifier_label,
            comparison_group=entry.comparison_group,
            mark_evidence=_mark_evidence_for_row(  # type: ignore[arg-type]
                row, venue=entry.venue, classifier_label=entry.classifier_label
            ),
            provenance_policy_version=entry.provenance_policy_version or PROVENANCE_POLICY_VERSION,
        )

    if ingest_type:
        evidence.append("ingest_type")
    if transport:
        evidence.append("transport")
    if venue:
        evidence.append("venue")

    payload = _payload(row)
    used_payload = False
    classifier_label = classify_historical_regime(dict(row))
    evidence.append("classifier_label")

    if venue == "okx" and ingest_type == "ws_top_of_book":
        used_payload = True
        evidence.append("payload_mark_evidence")
    elif ingest_type in ("ws_ticker", "ws_merged_ticker", "ws_top_of_book") and payload:
        used_payload = True
        evidence.append("payload")

    entry = None
    if classifier_label != "unknown_or_insufficient_provenance":
        entry = lookup_by_classifier(
            venue=venue or "unknown",
            classifier_label=classifier_label,
            ingest_type=ingest_type or None,
        )
    if entry is None:
        entry = resolve_regime_from_row(dict(row))

    collector = str(
        row.get("collector_service_name")
        or (payload.get("collector_service_name") if payload else None)
        or ""
    )
    if collector:
        evidence.append("collector_service_name")
        if entry is not None and entry.collector and collector != entry.collector:
            warnings.append(
                f"collector_service_name={collector} differs from inventory collector={entry.collector}; "
                "row ingest metadata takes precedence"
            )

    if entry is None or entry.regime_id == "unknown.insufficient_provenance":
        return _unknown_assignment(
            method="row_metadata_with_payload" if used_payload else "row_metadata",
            reason="unresolved_classifier_or_inventory",
            evidence=tuple(dict.fromkeys(evidence)),
            warnings=tuple(warnings),
            mark_evidence=_mark_evidence_for_row(
                row, venue=venue, classifier_label=classifier_label
            ),
            classifier_label=classifier_label,
        )

    conflict = _bounds_conflict(entry, row)
    if conflict:
        warnings.append(conflict)

    method = "row_metadata_with_payload" if used_payload else "row_metadata"
    mark_evidence = _mark_evidence_for_row(
        row, venue=entry.venue, classifier_label=entry.classifier_label
    )
    return RegimeAssignment(
        acquisition_regime_id=entry.regime_id,
        assignment_method=method,  # type: ignore[arg-type]
        assignment_status="definitive",
        evidence_fields=tuple(dict.fromkeys(evidence)),
        warnings=tuple(warnings),
        classifier_label=entry.classifier_label,
        comparison_group=entry.comparison_group,
        mark_evidence=mark_evidence,  # type: ignore[arg-type]
        provenance_policy_version=entry.provenance_policy_version or PROVENANCE_POLICY_VERSION,
    )
