"""Authoritative acquisition-regime comparability eligibility.

Production consumers must use this module (or validation helpers that wrap it)
to decide whether artifacts may participate in regime-sensitive comparison or
aggregation. Raw provenance fields are inputs only.

Role: eligibility evaluator (imports value authority from provenance_registry).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import (
    AbstractSet,
    Any,
    Dict,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from synapse_msi.historical_corpus.comparability import compare_regimes
from synapse_msi.historical_corpus.inventory import lookup_regime
from synapse_msi.historical_corpus.models import (
    InvestigationRegimeContext,
    RegimeAssignment,
)
from synapse_msi.historical_corpus.provenance_registry import (
    ACTIVE_ASSIGNMENT_METHODS,
    ACTIVE_ASSIGNMENT_STATUSES,
    ACTIVE_COMPARABILITY_ELIGIBILITIES,
    ACTIVE_COMPARISON_GROUPS,
    ACTIVE_COMPARISON_SCOPES,
    ACTIVE_LINKAGE_METHODS,
    ACTIVE_LINKAGE_STATUSES,
    DEFAULT_PAIR_COMPARISON_SCOPE,
    DEFAULT_SIDECAR_COMPARISON_SCOPE,
    ELIGIBILITY_REASON_CODES,
    PUBLISH_REJECTING_REASON_CODES,
    RESERVED_ASSIGNMENT_METHODS,
    RESERVED_LINKAGE_METHODS,
    SUPPORTED_SCHEMA_VERSIONS,
    is_publish_rejecting_reason,
    normalize_reason_detail,
    parse_unresolved_reason,
    required_fields_for_scope,
)

# Re-export registry sets for callers that historically imported from here.
SUPPORTED_ASSIGNMENT_STATUSES = ACTIVE_ASSIGNMENT_STATUSES
SUPPORTED_ASSIGNMENT_METHODS = ACTIVE_ASSIGNMENT_METHODS | RESERVED_ASSIGNMENT_METHODS
SUPPORTED_LINKAGE_STATUSES = ACTIVE_LINKAGE_STATUSES
SUPPORTED_LINKAGE_METHODS = ACTIVE_LINKAGE_METHODS | RESERVED_LINKAGE_METHODS
SUPPORTED_COMPARISON_GROUPS = ACTIVE_COMPARISON_GROUPS
SUPPORTED_COMPARABILITY_ELIGIBILITIES = ACTIVE_COMPARABILITY_ELIGIBILITIES
SUPPORTED_COMPARISON_SCOPES = ACTIVE_COMPARISON_SCOPES

ComparabilityEligibility = Literal[
    "comparable",
    "comparable_after_partition",
    "not_comparable",
    "excluded_fail_closed",
]

UNKNOWN_REGIME_ID = "unknown.insufficient_provenance"

ProvenanceInput = Union[
    Mapping[str, Any],
    InvestigationRegimeContext,
    RegimeAssignment,
]


@dataclass(frozen=True)
class ComparabilityDecision:
    """Authoritative coarse eligibility plus forensic diagnostics."""

    comparability_eligibility: ComparabilityEligibility
    comparability_reason_code: str
    comparability_reason_detail: Dict[str, Any] = field(default_factory=dict)
    comparison_scope: str = DEFAULT_SIDECAR_COMPARISON_SCOPE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comparison_scope": self.comparison_scope,
            "comparability_eligibility": self.comparability_eligibility,
            "comparability_reason_code": self.comparability_reason_code,
            "comparability_reason_detail": dict(self.comparability_reason_detail),
        }

    def allows_global_comparison(self) -> bool:
        return self.comparability_eligibility == "comparable"

    def allows_partitioned_comparison(self) -> bool:
        return self.comparability_eligibility in {
            "comparable",
            "comparable_after_partition",
        }

    def is_excluded(self) -> bool:
        return self.comparability_eligibility == "excluded_fail_closed"


def _decision(
    eligibility: ComparabilityEligibility,
    reason_code: str,
    *,
    comparison_scope: str,
    **detail: Any,
) -> ComparabilityDecision:
    if reason_code not in ELIGIBILITY_REASON_CODES:
        raise ValueError(f"unknown eligibility reason code: {reason_code}")
    if eligibility not in ACTIVE_COMPARABILITY_ELIGIBILITIES:
        raise ValueError(f"unknown comparability_eligibility: {eligibility}")
    return ComparabilityDecision(
        comparability_eligibility=eligibility,
        comparability_reason_code=reason_code,
        comparability_reason_detail=dict(detail),
        comparison_scope=comparison_scope,
    )


def normalize_provenance_view(source: ProvenanceInput) -> Dict[str, Any]:
    """Project heterogeneous provenance carriers into a stable dict (raw preserved)."""
    if isinstance(source, InvestigationRegimeContext):
        view = source.to_dict()
    elif isinstance(source, RegimeAssignment):
        view = source.to_dict()
        view.setdefault("primary_regime_id", None)
        view.setdefault("linked_regime_ids", [source.acquisition_regime_id])
        view.setdefault("spans_multiple_regimes", False)
    elif isinstance(source, Mapping):
        view = dict(source)
        nested = view.get("acquisition_regime_context")
        if isinstance(nested, Mapping) and "assignment_status" not in view:
            merged = dict(nested)
            for key in (
                "schema_version",
                "linkage_status",
                "linkage_method",
                "coverage",
                "comparison_scope",
                "comparability_eligibility",
                "comparability_reason_code",
                "comparability_reason_detail",
            ):
                if key in view and key not in merged:
                    merged[key] = view[key]
            view = merged
            # Preserve top-level linkage/schema when nested.
            for key in (
                "schema_version",
                "linkage_status",
                "linkage_method",
                "coverage",
            ):
                if key in source and key not in view:
                    view[key] = source[key]
    else:
        raise TypeError(f"unsupported provenance input type: {type(source)!r}")

    linked = view.get("linked_regime_ids")
    if linked is None:
        linked_list: List[Any] = []
    elif isinstance(linked, (list, tuple)):
        linked_list = list(linked)
    else:
        linked_list = [linked]
    view["linked_regime_ids"] = linked_list
    return view


def _resolved_regime_ids(view: Mapping[str, Any]) -> Tuple[str, ...]:
    linked = [str(item) for item in (view.get("linked_regime_ids") or []) if item]
    primary = view.get("primary_regime_id")
    acquisition = view.get("acquisition_regime_id")
    candidates: List[str] = []
    for item in linked:
        if item and item != UNKNOWN_REGIME_ID and item not in candidates:
            candidates.append(item)
    for item in (primary, acquisition):
        if item and str(item) != UNKNOWN_REGIME_ID and str(item) not in candidates:
            candidates.append(str(item))
    return tuple(candidates)


def _malformed_linked(view: Mapping[str, Any]) -> Optional[str]:
    linked = view.get("linked_regime_ids")
    if linked is None:
        return None
    if not isinstance(linked, (list, tuple)):
        return "linked_regime_ids_not_sequence"
    for item in linked:
        if item is None:
            return "linked_regime_ids_contains_null"
        if not isinstance(item, str):
            return "linked_regime_ids_non_string"
        if item == "":
            return "linked_regime_ids_empty_string"
    return None


def _contradiction(view: Mapping[str, Any], resolved: Sequence[str]) -> Optional[str]:
    spans = view.get("spans_multiple_regimes")
    if spans is not None and not isinstance(spans, bool):
        return "spans_multiple_regimes_not_bool"

    if spans is True and len(resolved) < 2:
        return "spans_multiple_true_but_fewer_than_two_resolved_regimes"
    if spans is False and len(resolved) > 1:
        return "spans_multiple_false_but_multiple_resolved_regimes"

    primary = view.get("primary_regime_id")
    if len(resolved) == 1:
        if spans is True:
            return "single_resolved_with_spans_multiple_true"
        if primary is not None and str(primary) != resolved[0]:
            return "primary_regime_id_mismatch_with_singleton_linked_set"

    if len(resolved) > 1 and primary is not None:
        return "primary_regime_id_set_for_multi_regime"

    status = view.get("assignment_status")
    method = view.get("assignment_method")
    if status in {"definitive", "provisional"} and method == "unknown":
        return "known_assignment_status_with_unknown_method"

    return None


def evaluate_artifact_comparability_eligibility(
    source: ProvenanceInput,
    *,
    schema_version: Optional[str] = None,
    comparison_scope: str = DEFAULT_SIDECAR_COMPARISON_SCOPE,
    known_regime_ids: Optional[AbstractSet[str]] = None,
) -> ComparabilityDecision:
    """Decide whether one artifact may participate in regime-sensitive comparison.

    When ``known_regime_ids`` is provided (package-pinned frozen evidence),
    regime-id support is validated against that set instead of the working inventory.
    """
    scope = comparison_scope
    if scope not in ACTIVE_COMPARISON_SCOPES:
        return _decision(
            "excluded_fail_closed",
            "unsupported_comparison_scope",
            comparison_scope=str(scope),
            observed_comparison_scope=scope,
            supported_comparison_scopes=sorted(ACTIVE_COMPARISON_SCOPES),
        )

    view = normalize_provenance_view(source)
    raw_snapshot = {
        "assignment_status": view.get("assignment_status"),
        "assignment_method": view.get("assignment_method"),
        "linkage_status": view.get("linkage_status"),
        "linkage_method": view.get("linkage_method"),
        "comparison_group": view.get("comparison_group"),
        "acquisition_regime_id": view.get("acquisition_regime_id"),
        "primary_regime_id": view.get("primary_regime_id"),
        "linked_regime_ids": list(view.get("linked_regime_ids") or []),
        "spans_multiple_regimes": view.get("spans_multiple_regimes"),
        "unresolved_reason": view.get("unresolved_reason"),
        "unresolved_reason_detail": view.get("unresolved_reason_detail"),
        "schema_version": schema_version or view.get("schema_version"),
    }

    schema = schema_version or view.get("schema_version")
    if schema is not None and schema not in SUPPORTED_SCHEMA_VERSIONS:
        return _decision(
            "excluded_fail_closed",
            "unsupported_schema",
            comparison_scope=scope,
            raw=raw_snapshot,
            observed_schema_version=schema,
            supported_schema_versions=sorted(SUPPORTED_SCHEMA_VERSIONS),
        )

    malformed = _malformed_linked(view)
    if malformed is not None:
        return _decision(
            "excluded_fail_closed",
            "malformed_provenance",
            comparison_scope=scope,
            raw=raw_snapshot,
            malformation=malformed,
        )

    status = view.get("assignment_status")
    if status is not None and status not in ACTIVE_ASSIGNMENT_STATUSES:
        return _decision(
            "excluded_fail_closed",
            "unsupported_assignment_status",
            comparison_scope=scope,
            raw=raw_snapshot,
            observed_assignment_status=status,
        )

    method = view.get("assignment_method")
    if method is not None and method in RESERVED_ASSIGNMENT_METHODS:
        return _decision(
            "excluded_fail_closed",
            "reserved_assignment_method",
            comparison_scope=scope,
            raw=raw_snapshot,
            observed_assignment_method=method,
        )
    if method is not None and method not in ACTIVE_ASSIGNMENT_METHODS:
        return _decision(
            "excluded_fail_closed",
            "unsupported_assignment_method",
            comparison_scope=scope,
            raw=raw_snapshot,
            observed_assignment_method=method,
        )

    linkage = view.get("linkage_status")
    if linkage is not None and linkage not in ACTIVE_LINKAGE_STATUSES:
        return _decision(
            "excluded_fail_closed",
            "unsupported_linkage_status",
            comparison_scope=scope,
            raw=raw_snapshot,
            observed_linkage_status=linkage,
        )

    linkage_method = view.get("linkage_method")
    if linkage_method is not None and linkage_method in RESERVED_LINKAGE_METHODS:
        return _decision(
            "excluded_fail_closed",
            "reserved_linkage_method",
            comparison_scope=scope,
            raw=raw_snapshot,
            observed_linkage_method=linkage_method,
        )
    if linkage_method is not None and linkage_method not in ACTIVE_LINKAGE_METHODS:
        return _decision(
            "excluded_fail_closed",
            "unsupported_linkage_method",
            comparison_scope=scope,
            raw=raw_snapshot,
            observed_linkage_method=linkage_method,
        )

    group = view.get("comparison_group")
    if group is not None and group not in ACTIVE_COMPARISON_GROUPS:
        return _decision(
            "excluded_fail_closed",
            "unsupported_comparison_group",
            comparison_scope=scope,
            raw=raw_snapshot,
            observed_comparison_group=group,
        )

    unresolved_raw = view.get("unresolved_reason")
    if unresolved_raw is not None:
        parsed = parse_unresolved_reason(unresolved_raw)
        if not parsed.is_supported:
            return _decision(
                "excluded_fail_closed",
                "unsupported_unresolved_reason",
                comparison_scope=scope,
                raw=raw_snapshot,
                observed_unresolved_reason=unresolved_raw,
                parse_detail=dict(parsed.detail),
            )

    resolved = _resolved_regime_ids(view)
    for regime_id in resolved:
        if known_regime_ids is not None:
            known = regime_id in known_regime_ids
        else:
            known = lookup_regime(regime_id) is not None
        if not known:
            return _decision(
                "excluded_fail_closed",
                "unsupported_regime_id",
                comparison_scope=scope,
                raw=raw_snapshot,
                observed_regime_id=regime_id,
            )

    contradiction = _contradiction(view, resolved)
    if contradiction is not None:
        return _decision(
            "excluded_fail_closed",
            "contradictory_provenance",
            comparison_scope=scope,
            raw=raw_snapshot,
            contradiction=contradiction,
            resolved_regime_ids=list(resolved),
        )

    unresolved_for_conflict = view.get("unresolved_reason")
    parsed_conflict = (
        parse_unresolved_reason(unresolved_for_conflict)
        if unresolved_for_conflict is not None
        else None
    )
    if linkage == "conflict" or (
        parsed_conflict is not None and parsed_conflict.code == "explicit_linkage_conflict"
    ):
        return _decision(
            "excluded_fail_closed",
            "conflicting_assignment",
            comparison_scope=scope,
            raw=raw_snapshot,
            resolved_regime_ids=list(resolved),
            conflict_artifacts_are_publishable=True,
        )

    if status is None and not resolved:
        return _decision(
            "excluded_fail_closed",
            "malformed_provenance",
            comparison_scope=scope,
            raw=raw_snapshot,
            malformation="missing_assignment_status_and_regimes",
        )

    if status == "unknown" or not resolved:
        return _decision(
            "excluded_fail_closed",
            "unknown_assignment" if status == "unknown" else "insufficient_provenance",
            comparison_scope=scope,
            raw=raw_snapshot,
            resolved_regime_ids=list(resolved),
        )

    if view.get("spans_multiple_regimes") or len(resolved) > 1:
        cross = view.get("cross_regime_compatibility")
        return _decision(
            "comparable_after_partition",
            "mixed_regime_requires_partition",
            comparison_scope=scope,
            raw=raw_snapshot,
            resolved_regime_ids=list(resolved),
            comparison_group=group,
            cross_regime_compatibility=dict(cross) if isinstance(cross, Mapping) else cross,
        )

    return _decision(
        "comparable",
        "same_regime_semantics",
        comparison_scope=scope,
        raw=raw_snapshot,
        resolved_regime_ids=list(resolved),
        primary_regime_id=view.get("primary_regime_id") or resolved[0],
        comparison_group=group,
    )


def _field_level(
    pair_fields: Sequence[Any], field_name: str
) -> Optional[str]:
    for item in pair_fields:
        if getattr(item, "field_name", None) == field_name:
            return getattr(item, "level", None)
    return None


def _pair_scope_decision(
    *,
    comparison_scope: str,
    pair: Any,
    left_decision: ComparabilityDecision,
    right_decision: ComparabilityDecision,
) -> ComparabilityDecision:
    detail = {
        "left": left_decision.to_dict(),
        "right": right_decision.to_dict(),
        "regime_a": pair.regime_a,
        "regime_b": pair.regime_b,
        "overall": pair.overall,
        "fields": [item.to_dict() for item in pair.fields],
        "required_fields": list(required_fields_for_scope(comparison_scope)),
    }

    if comparison_scope == "full_supported_field_set":
        if pair.overall == "not_comparable":
            return _decision(
                "not_comparable",
                "methodology_forbids_comparison",
                comparison_scope=comparison_scope,
                **detail,
            )
        if pair.overall == "unknown":
            return _decision(
                "excluded_fail_closed",
                "insufficient_provenance",
                comparison_scope=comparison_scope,
                **detail,
            )
        return _decision(
            "comparable",
            "same_regime_semantics",
            comparison_scope=comparison_scope,
            **detail,
        )

    required = required_fields_for_scope(comparison_scope)
    levels = {name: _field_level(pair.fields, name) for name in required}
    detail["field_levels"] = levels
    if any(level == "not_comparable" for level in levels.values()):
        return _decision(
            "not_comparable",
            "methodology_forbids_comparison",
            comparison_scope=comparison_scope,
            mark_price_level=levels.get("mark_price"),
            **detail,
        )
    if any(level is None or level == "unknown" for level in levels.values()):
        return _decision(
            "excluded_fail_closed",
            "insufficient_provenance",
            comparison_scope=comparison_scope,
            mark_price_level=levels.get("mark_price"),
            **detail,
        )
    return _decision(
        "comparable",
        "same_regime_semantics",
        comparison_scope=comparison_scope,
        mark_price_level=levels.get("mark_price"),
        **detail,
    )


def evaluate_pair_comparability_eligibility(
    left: ProvenanceInput,
    right: ProvenanceInput,
    *,
    comparison_scope: str = DEFAULT_PAIR_COMPARISON_SCOPE,
    left_schema_version: Optional[str] = None,
    right_schema_version: Optional[str] = None,
) -> ComparabilityDecision:
    """Decide whether two artifacts may be compared for an explicit scope."""
    if comparison_scope not in ACTIVE_COMPARISON_SCOPES:
        return _decision(
            "excluded_fail_closed",
            "unsupported_comparison_scope",
            comparison_scope=str(comparison_scope),
            observed_comparison_scope=comparison_scope,
            supported_comparison_scopes=sorted(ACTIVE_COMPARISON_SCOPES),
        )

    left_decision = evaluate_artifact_comparability_eligibility(
        left,
        schema_version=left_schema_version,
        comparison_scope=comparison_scope,
    )
    right_decision = evaluate_artifact_comparability_eligibility(
        right,
        schema_version=right_schema_version,
        comparison_scope=comparison_scope,
    )

    if left_decision.is_excluded() or right_decision.is_excluded():
        return _decision(
            "excluded_fail_closed",
            "pair_excluded",
            comparison_scope=comparison_scope,
            left=left_decision.to_dict(),
            right=right_decision.to_dict(),
        )

    if (
        left_decision.comparability_eligibility == "comparable_after_partition"
        or right_decision.comparability_eligibility == "comparable_after_partition"
    ):
        return _decision(
            "comparable_after_partition",
            "pair_requires_partition",
            comparison_scope=comparison_scope,
            left=left_decision.to_dict(),
            right=right_decision.to_dict(),
        )

    left_view = normalize_provenance_view(left)
    right_view = normalize_provenance_view(right)
    left_ids = _resolved_regime_ids(left_view)
    right_ids = _resolved_regime_ids(right_view)
    if not left_ids or not right_ids:
        return _decision(
            "excluded_fail_closed",
            "insufficient_provenance",
            comparison_scope=comparison_scope,
            left=left_decision.to_dict(),
            right=right_decision.to_dict(),
        )

    pair = compare_regimes(left_ids[0], right_ids[0])
    return _pair_scope_decision(
        comparison_scope=comparison_scope,
        pair=pair,
        left_decision=left_decision,
        right_decision=right_decision,
    )


def allows_regime_sensitive_use(decision: ComparabilityDecision) -> bool:
    """True when provenance is known enough for forward linkage / non-excluded use."""
    return decision.comparability_eligibility in {
        "comparable",
        "comparable_after_partition",
        "not_comparable",
    }


def recommend_forward_linkage_status(decision: ComparabilityDecision) -> Optional[str]:
    """Map eligibility to forward investigation linkage_status, or None to skip write."""
    if decision.is_excluded():
        return None
    if decision.comparability_eligibility == "comparable":
        status = (decision.comparability_reason_detail.get("raw") or {}).get(
            "assignment_status"
        )
        if status == "definitive":
            return "exact"
        return "qualified"
    if decision.comparability_eligibility in {
        "comparable_after_partition",
        "not_comparable",
    }:
        return "qualified"
    return None


def attach_comparability_decision(
    payload: Mapping[str, Any],
    *,
    schema_version: Optional[str] = None,
    comparison_scope: str = DEFAULT_SIDECAR_COMPARISON_SCOPE,
) -> Dict[str, Any]:
    """Copy payload and attach the authoritative eligibility decision (additive)."""
    out = dict(payload)
    decision = evaluate_artifact_comparability_eligibility(
        out,
        schema_version=schema_version,
        comparison_scope=comparison_scope,
    )
    out.update(decision.to_dict())
    return out


def decisions_match_stamp(
    stamped: Mapping[str, Any],
    recomputed: ComparabilityDecision,
) -> List[str]:
    """Return mismatch messages between stamped sidecar fields and recomputation."""
    errors: List[str] = []
    if stamped.get("comparison_scope") != recomputed.comparison_scope:
        errors.append(
            f"comparison_scope stamped={stamped.get('comparison_scope')!r} "
            f"recomputed={recomputed.comparison_scope!r}"
        )
    if stamped.get("comparability_eligibility") != recomputed.comparability_eligibility:
        errors.append(
            f"comparability_eligibility stamped={stamped.get('comparability_eligibility')!r} "
            f"recomputed={recomputed.comparability_eligibility!r}"
        )
    if stamped.get("comparability_reason_code") != recomputed.comparability_reason_code:
        errors.append(
            f"comparability_reason_code stamped={stamped.get('comparability_reason_code')!r} "
            f"recomputed={recomputed.comparability_reason_code!r}"
        )
    stamped_detail = stamped.get("comparability_reason_detail")
    if normalize_reason_detail(
        stamped_detail if isinstance(stamped_detail, Mapping) else {}
    ) != normalize_reason_detail(recomputed.comparability_reason_detail):
        errors.append("comparability_reason_detail mismatch after normalization")
    return errors


__all__ = [
    "ComparabilityDecision",
    "ComparabilityEligibility",
    "ELIGIBILITY_REASON_CODES",
    "PUBLISH_REJECTING_REASON_CODES",
    "SUPPORTED_ASSIGNMENT_METHODS",
    "SUPPORTED_ASSIGNMENT_STATUSES",
    "SUPPORTED_COMPARABILITY_ELIGIBILITIES",
    "SUPPORTED_COMPARISON_GROUPS",
    "SUPPORTED_COMPARISON_SCOPES",
    "SUPPORTED_LINKAGE_METHODS",
    "SUPPORTED_LINKAGE_STATUSES",
    "SUPPORTED_SCHEMA_VERSIONS",
    "UNKNOWN_REGIME_ID",
    "allows_regime_sensitive_use",
    "attach_comparability_decision",
    "decisions_match_stamp",
    "evaluate_artifact_comparability_eligibility",
    "evaluate_pair_comparability_eligibility",
    "is_publish_rejecting_reason",
    "normalize_provenance_view",
    "recommend_forward_linkage_status",
]
