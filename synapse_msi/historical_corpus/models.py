"""Typed models for historical acquisition-regime interpretation.

This package describes *data acquisition* regimes (collector/ingest/transport
semantics). It is unrelated to market/volatility regimes in
market/volatility regime engines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple

ACQUISITION_REGIME_METHODOLOGY_VERSION = "acquisition_regime_v2026_07"
FIELD_SEMANTICS_VERSION = "field_semantics_v2026_07"
PROVENANCE_POLICY_VERSION = "provenance_policy_v2026_07"

ComparabilityLevel = Literal[
    "fully_comparable",
    "partially_comparable",
    "not_comparable",
    "unknown",
]

AssignmentMethod = Literal[
    "explicit",
    "row_metadata",
    "row_metadata_with_payload",
    "inventory_supported",
    "temporal_provisional",
    "unknown",
]

AssignmentStatus = Literal[
    "definitive",
    "provisional",
    "unknown",
]

MarkEvidence = Literal[
    "native_present",
    "midpoint_derived",
    "unavailable",
    "insufficient",
    "not_applicable",
]

COMPARABILITY_FIELDS: Tuple[str, ...] = (
    "mark_price",
    "funding",
    "open_interest",
    "bid",
    "ask",
    "spread",
    "freshness",
    "staleness",
    "provenance",
    "collector_timing",
    "venue_timing",
)

# Stable machine-readable comparability reason codes.
COMPARABILITY_REASON_CODES: frozenset[str] = frozenset(
    {
        "identical_acquisition_semantics",
        "same_economic_concept_different_sampling_path",
        "changed_field_authority",
        "changed_provenance_policy",
        "changed_freshness_semantics",
        "changed_timestamp_semantics",
        "field_unavailable",
        "insufficient_evidence",
        "conditional_native_versus_derived",
        "unresolved_acquisition_metadata",
        "same_regime",
        "unknown_regime",
    }
)


@dataclass(frozen=True)
class AcquisitionRegime:
    """Canonical historical interpretation layer for acquisition semantics."""

    regime_id: str
    collector: str
    ingest_type: str
    transport: str
    field_authority: str
    field_provenance_version: str
    methodology_version: str
    comparison_group: str
    venue: str
    classifier_label: str
    notes: Tuple[str, ...] = ()
    known_semantic_differences: Tuple[str, ...] = ()
    # Additive Phase-1 fields (optional for backward-compatible construction).
    collector_service_name: Optional[str] = None
    collector_source_mode: Optional[str] = None
    field_authority_map: Tuple[Tuple[str, str], ...] = ()
    provenance_policy_version: Optional[str] = None
    known_limitations: Tuple[str, ...] = ()
    effective_start: Optional[str] = None
    effective_end: Optional[str] = None
    current_production: bool = False

    def resolved_collector_service_name(self) -> str:
        return self.collector_service_name or self.collector

    def to_dict(self) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "regime_id": self.regime_id,
            "collector": self.collector,
            "collector_service_name": self.resolved_collector_service_name(),
            "ingest_type": self.ingest_type,
            "transport": self.transport,
            "field_authority": self.field_authority,
            "field_provenance_version": self.field_provenance_version,
            "methodology_version": self.methodology_version,
            "comparison_group": self.comparison_group,
            "venue": self.venue,
            "classifier_label": self.classifier_label,
            "notes": list(self.notes),
            "known_semantic_differences": list(self.known_semantic_differences),
            "field_authority_map": {key: value for key, value in self.field_authority_map},
            "known_limitations": list(self.known_limitations or self.known_semantic_differences),
            "effective_start": self.effective_start,
            "effective_end": self.effective_end,
            "current_production": self.current_production,
        }
        if self.collector_source_mode is not None:
            payload["collector_source_mode"] = self.collector_source_mode
        if self.provenance_policy_version is not None:
            payload["provenance_policy_version"] = self.provenance_policy_version
        return payload


@dataclass(frozen=True)
class HistoricalRegimeInventoryEntry:
    """Inventory row with proven effective bounds where documented."""

    regime_id: str
    effective_start: Optional[str]
    effective_end: Optional[str]
    collector: str
    ingest_type: str
    transport: str
    field_provenance: Dict[str, str]
    known_semantic_differences: Tuple[str, ...]
    comparable_to: Tuple[str, ...]
    venue: str
    classifier_label: str
    comparison_group: str
    current_production: bool = False
    provenance_policy_version: Optional[str] = None
    collector_source_mode: Optional[str] = None
    known_limitations: Tuple[str, ...] = ()


@dataclass(frozen=True)
class FieldComparability:
    field_name: str
    level: ComparabilityLevel
    reason: str
    reason_code: str = "insufficient_evidence"

    def to_dict(self) -> Dict[str, object]:
        return {
            "field": self.field_name,
            "level": self.level,
            "reason": self.reason,
            "reason_code": self.reason_code,
        }


@dataclass
class RegimePairComparability:
    regime_a: str
    regime_b: str
    fields: Tuple[FieldComparability, ...]
    overall: ComparabilityLevel = "unknown"

    def to_dict(self) -> Dict[str, object]:
        return {
            "regime_a": self.regime_a,
            "regime_b": self.regime_b,
            "overall": self.overall,
            "fields": [item.to_dict() for item in self.fields],
        }


@dataclass(frozen=True)
class RegimeAssignment:
    """Structured, evidence-first row→regime assignment result."""

    acquisition_regime_id: str
    assignment_method: AssignmentMethod
    assignment_status: AssignmentStatus
    evidence_fields: Tuple[str, ...]
    warnings: Tuple[str, ...] = ()
    unresolved_reason: Optional[str] = None
    unresolved_reason_detail: Optional[Dict[str, Any]] = None
    classifier_label: Optional[str] = None
    comparison_group: Optional[str] = None
    mark_evidence: MarkEvidence = "not_applicable"
    methodology_version: str = ACQUISITION_REGIME_METHODOLOGY_VERSION
    provenance_policy_version: Optional[str] = PROVENANCE_POLICY_VERSION
    field_semantics_version: str = FIELD_SEMANTICS_VERSION

    def to_dict(self) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "acquisition_regime_id": self.acquisition_regime_id,
            "assignment_method": self.assignment_method,
            "assignment_status": self.assignment_status,
            "evidence_fields": list(self.evidence_fields),
            "warnings": list(self.warnings),
            "unresolved_reason": self.unresolved_reason,
            "classifier_label": self.classifier_label,
            "comparison_group": self.comparison_group,
            "mark_evidence": self.mark_evidence,
            "methodology_version": self.methodology_version,
            "field_semantics_version": self.field_semantics_version,
        }
        if self.unresolved_reason_detail is not None:
            payload["unresolved_reason_detail"] = dict(self.unresolved_reason_detail)
        if self.provenance_policy_version is not None:
            payload["provenance_policy_version"] = self.provenance_policy_version
        return payload


@dataclass(frozen=True)
class InvestigationHistoricalLinkage:
    """Additive investigation metadata referencing acquisition regimes."""

    acquisition_regime_id: str
    comparison_group: str
    field_semantics_version: str
    comparability: Dict[str, ComparabilityLevel]
    linked_regime_ids: Tuple[str, ...] = ()
    provenance_policy_version: Optional[str] = None
    assignment_method: Optional[AssignmentMethod] = None
    assignment_status: Optional[AssignmentStatus] = None

    def to_dict(self) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "acquisition_regime_id": self.acquisition_regime_id,
            "comparison_group": self.comparison_group,
            "field_semantics_version": self.field_semantics_version,
            "comparability": dict(self.comparability),
            "linked_regime_ids": list(self.linked_regime_ids),
        }
        if self.provenance_policy_version is not None:
            payload["provenance_policy_version"] = self.provenance_policy_version
        if self.assignment_method is not None:
            payload["assignment_method"] = self.assignment_method
        if self.assignment_status is not None:
            payload["assignment_status"] = self.assignment_status
        return payload


@dataclass(frozen=True)
class InvestigationRegimeContext:
    """Investigation-level acquisition-regime context derived from row assignments."""

    primary_regime_id: Optional[str]
    linked_regime_ids: Tuple[str, ...]
    assignment_method: AssignmentMethod
    assignment_status: AssignmentStatus
    assignment_evidence: Tuple[str, ...]
    assignment_warnings: Tuple[str, ...]
    unresolved_reason: Optional[str]
    methodology_version: str
    field_semantics_version: str
    provenance_policy_version: Optional[str]
    spans_multiple_regimes: bool
    cross_regime_compatibility: Optional[Dict[str, object]] = None
    known_limitations: Tuple[str, ...] = ()
    comparison_group: Optional[str] = None
    # Legacy anchor for InvestigationHistoricalLinkage.acquisition_regime_id.
    # Equals primary when singular; otherwise lexicographic first resolved ID
    # with an explicit warning that it is not a semantic primary.
    acquisition_regime_id: Optional[str] = None
    mark_evidence_summary: Tuple[str, ...] = ()
    row_assignment_count: int = 0
    unknown_row_count: int = 0
    unresolved_reason_detail: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "primary_regime_id": self.primary_regime_id,
            "acquisition_regime_id": self.acquisition_regime_id or self.primary_regime_id
            or "unknown.insufficient_provenance",
            "linked_regime_ids": list(self.linked_regime_ids),
            "assignment_method": self.assignment_method,
            "assignment_status": self.assignment_status,
            "assignment_evidence": list(self.assignment_evidence),
            "assignment_warnings": list(self.assignment_warnings),
            "unresolved_reason": self.unresolved_reason,
            "methodology_version": self.methodology_version,
            "field_semantics_version": self.field_semantics_version,
            "spans_multiple_regimes": self.spans_multiple_regimes,
            "comparison_group": self.comparison_group,
            "known_limitations": list(self.known_limitations),
            "mark_evidence_summary": list(self.mark_evidence_summary),
            "row_assignment_count": self.row_assignment_count,
            "unknown_row_count": self.unknown_row_count,
        }
        if self.unresolved_reason_detail is not None:
            payload["unresolved_reason_detail"] = dict(self.unresolved_reason_detail)
        if self.provenance_policy_version is not None:
            payload["provenance_policy_version"] = self.provenance_policy_version
        if self.cross_regime_compatibility is not None:
            payload["cross_regime_compatibility"] = dict(self.cross_regime_compatibility)
        return payload

    def to_linkage(self) -> InvestigationHistoricalLinkage:
        """Project into the existing linkage type for shared validation paths."""
        regime_id = (
            self.acquisition_regime_id
            or self.primary_regime_id
            or "unknown.insufficient_provenance"
        )
        comparability: Dict[str, ComparabilityLevel] = {}
        if self.cross_regime_compatibility:
            field_levels = self.cross_regime_compatibility.get("field_levels") or {}
            if isinstance(field_levels, dict):
                comparability = {
                    str(key): value  # type: ignore[misc]
                    for key, value in field_levels.items()
                }
        return InvestigationHistoricalLinkage(
            acquisition_regime_id=regime_id,
            comparison_group=self.comparison_group or "unknown",
            field_semantics_version=self.field_semantics_version,
            comparability=comparability,
            linked_regime_ids=self.linked_regime_ids,
            provenance_policy_version=self.provenance_policy_version,
            assignment_method=self.assignment_method,
            assignment_status=self.assignment_status,
        )
