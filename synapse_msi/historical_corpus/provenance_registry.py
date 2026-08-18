"""Centralized working provenance registry (audit-derived, pre-normative).

Authority roles:
  * This module — registry authority (values, scopes, reason-code behavior).
  * eligibility.py — authoritative eligibility evaluator.
  * sidecar_publication_validation.py — publication validator.
  * assignment.py / sidecar_generator.py / investigation_context.py — producers.
  * models.py / sidecar_models.py — serializers.
  * reports / evidence renderers — display only.

WORKING_PROVENANCE_REGISTRY_VERSION is a working identifier only; it is not the
final public normative PROVENANCE_REGISTRY_VERSION.

Public modern fixture reproduction uses the package-pinned frozen evidence
artifact ``acquisition_regime_fixture_registry_v1`` (see
``synapse_msi.historical_corpus.frozen_registry`` and provenance-standard §9).
This working module remains available for non-fixture / operational workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Mapping, Optional, Sequence, Tuple

from synapse_msi.historical_corpus.models import (
    ACQUISITION_REGIME_METHODOLOGY_VERSION,
    COMPARABILITY_FIELDS,
    FIELD_SEMANTICS_VERSION,
    PROVENANCE_POLICY_VERSION,
)
# Schema version constants inlined from sidecar_models (reproduction does not
# need sidecar builders).
EPISODE_SIDECAR_SCHEMA_VERSION = "acquisition_regime_episode_sidecar_v1"
INVESTIGATION_SIDECAR_SCHEMA_VERSION = "acquisition_regime_investigation_sidecar_v1"
SNAPSHOT_LINEAGE_SCHEMA_VERSION = "acquisition_regime_snapshot_lineage_v1"
LINKAGE_GENERATOR_VERSION = "acquisition_regime_linkage_v2026_07"
WINDOW_DIAGNOSTIC_SCHEMA_VERSION = "acquisition_regime_window_diagnostic_v1"

# Working (non-normative) registry pin — do not treat as public freeze version.
WORKING_PROVENANCE_REGISTRY_VERSION = "acquisition_provenance_working_registry_v1"

# ---------------------------------------------------------------------------
# assignment_status
# ---------------------------------------------------------------------------
ACTIVE_ASSIGNMENT_STATUSES: FrozenSet[str] = frozenset(
    {"definitive", "provisional", "unknown"}
)

# ---------------------------------------------------------------------------
# assignment_method
# ---------------------------------------------------------------------------
ACTIVE_ASSIGNMENT_METHODS: FrozenSet[str] = frozenset(
    {
        "explicit",
        "row_metadata",
        "row_metadata_with_payload",
        "unknown",
    }
)
RESERVED_ASSIGNMENT_METHODS: FrozenSet[str] = frozenset(
    {
        "inventory_supported",
        "temporal_provisional",
    }
)
# Accepted by readers for historical compatibility inspection only; always fail-closed.
HISTORICAL_COMPAT_ASSIGNMENT_METHODS: FrozenSet[str] = RESERVED_ASSIGNMENT_METHODS

# ---------------------------------------------------------------------------
# linkage_status / linkage_method
# ---------------------------------------------------------------------------
ACTIVE_LINKAGE_STATUSES: FrozenSet[str] = frozenset(
    {
        "exact",
        "derived_from_preserved_lineage",
        "qualified",
        "unknown",
        "conflict",
        "insufficient_raw_lineage",
    }
)
ACTIVE_LINKAGE_METHODS: FrozenSet[str] = frozenset(
    {
        "exact_raw_id",
        "snapshot_raw_index",
        "historical_lineage_unavailable",
        "episode_sidecar_aggregation",
    }
)
RESERVED_LINKAGE_METHODS: FrozenSet[str] = frozenset(
    {
        "none",
        "window_diagnostic_only",
    }
)

# ---------------------------------------------------------------------------
# unresolved_reason (closed)
# ---------------------------------------------------------------------------
ACTIVE_UNRESOLVED_REASONS: FrozenSet[str] = frozenset(
    {
        "timestamp_only_assignment_forbidden",
        "missing_acquisition_metadata",
        "unresolved_classifier_or_inventory",
        "no_source_rows",
        "all_rows_unknown",
        "mixed_resolved_and_unknown_rows",
        "multi_regime_investigation",
        "multi_regime_with_unknown_rows",
        "explicit_linkage_conflict",
        "missing_snapshot_to_raw_lineage",
        "explicit_regime_unknown",
    }
)
EXPLICIT_REGIME_UNKNOWN = "explicit_regime_unknown"
EXPLICIT_REGIME_UNKNOWN_PREFIX = "explicit_regime_unknown:"

# ---------------------------------------------------------------------------
# comparison_group / eligibility / scopes
# ---------------------------------------------------------------------------
ACTIVE_COMPARISON_GROUPS: FrozenSet[str] = frozenset(
    {
        "rest_composed",
        "l1_midpoint_proxy",
        "native_mark_authoritative",
        "conditional_native_mark",
        "unknown",
        "mixed",
    }
)
ACTIVE_COMPARABILITY_ELIGIBILITIES: FrozenSet[str] = frozenset(
    {
        "comparable",
        "comparable_after_partition",
        "not_comparable",
        "excluded_fail_closed",
    }
)

# Scopes matching the field-level comparability engine (COMPARABILITY_FIELDS).
ACTIVE_COMPARISON_SCOPES: FrozenSet[str] = frozenset(
    {
        "artifact",
        "mark_price",
        "funding",
        "full_supported_field_set",
    }
)
DEFAULT_SIDECAR_COMPARISON_SCOPE = "artifact"
DEFAULT_PAIR_COMPARISON_SCOPE = "artifact"

# Normative required fields for artifact-wide acquisition-sensitive comparison.
# Explicit policy: mark_price is required for artifact scope (not an implicit
# promotion from an unscoped pair evaluator).
ARTIFACT_REQUIRED_FIELDS: Tuple[str, ...] = ("mark_price",)

COMPARISON_SCOPE_REQUIRED_FIELDS: Mapping[str, Tuple[str, ...]] = {
    "artifact": ARTIFACT_REQUIRED_FIELDS,
    "mark_price": ("mark_price",),
    "funding": ("funding",),
    "full_supported_field_set": tuple(COMPARABILITY_FIELDS),
}

# ---------------------------------------------------------------------------
# Schema / version authorities (re-exported)
# ---------------------------------------------------------------------------
SUPPORTED_SCHEMA_VERSIONS: FrozenSet[str] = frozenset(
    {
        EPISODE_SIDECAR_SCHEMA_VERSION,
        INVESTIGATION_SIDECAR_SCHEMA_VERSION,
        SNAPSHOT_LINEAGE_SCHEMA_VERSION,
        WINDOW_DIAGNOSTIC_SCHEMA_VERSION,
    }
)
SUPPORTED_METHODOLOGY_VERSIONS: FrozenSet[str] = frozenset(
    {ACQUISITION_REGIME_METHODOLOGY_VERSION}
)
SUPPORTED_FIELD_SEMANTICS_VERSIONS: FrozenSet[str] = frozenset({FIELD_SEMANTICS_VERSION})
SUPPORTED_PROVENANCE_POLICY_VERSIONS: FrozenSet[str] = frozenset(
    {PROVENANCE_POLICY_VERSION}
)
SUPPORTED_GENERATOR_VERSIONS: FrozenSet[str] = frozenset({LINKAGE_GENERATOR_VERSION})

# ---------------------------------------------------------------------------
# Conflict publication rule (centralized)
# ---------------------------------------------------------------------------
# Conflict artifacts are structurally valid and publishable, but always
# excluded_fail_closed for comparison/aggregation (preserve contradictory evidence).
CONFLICT_ARTIFACTS_ARE_PUBLISHABLE = True

# ---------------------------------------------------------------------------
# Eligibility reason codes + behavior classification
# ---------------------------------------------------------------------------
REASON_BEHAVIOR_COMPARISON_ALLOWED = "comparison_allowed"
REASON_BEHAVIOR_PARTITION_REQUIRED = "partition_required"
REASON_BEHAVIOR_VALID_NOT_COMPARABLE = "valid_not_comparable"
REASON_BEHAVIOR_PUBLISH_REJECTING = "publish_rejecting_fail_closed"
REASON_BEHAVIOR_PUBLISHABLE_EXCLUDED = "publishable_historical_excluded"

ELIGIBILITY_REASON_CODE_BEHAVIOR: Mapping[str, str] = {
    "same_regime_semantics": REASON_BEHAVIOR_COMPARISON_ALLOWED,
    "mixed_regime_requires_partition": REASON_BEHAVIOR_PARTITION_REQUIRED,
    "pair_requires_partition": REASON_BEHAVIOR_PARTITION_REQUIRED,
    "methodology_forbids_comparison": REASON_BEHAVIOR_VALID_NOT_COMPARABLE,
    "unknown_assignment": REASON_BEHAVIOR_PUBLISHABLE_EXCLUDED,
    "insufficient_provenance": REASON_BEHAVIOR_PUBLISHABLE_EXCLUDED,
    "conflicting_assignment": REASON_BEHAVIOR_PUBLISHABLE_EXCLUDED,
    "pair_excluded": REASON_BEHAVIOR_PUBLISHABLE_EXCLUDED,
    "unsupported_assignment_status": REASON_BEHAVIOR_PUBLISH_REJECTING,
    "unsupported_assignment_method": REASON_BEHAVIOR_PUBLISH_REJECTING,
    "reserved_assignment_method": REASON_BEHAVIOR_PUBLISH_REJECTING,
    "unsupported_linkage_status": REASON_BEHAVIOR_PUBLISH_REJECTING,
    "unsupported_linkage_method": REASON_BEHAVIOR_PUBLISH_REJECTING,
    "reserved_linkage_method": REASON_BEHAVIOR_PUBLISH_REJECTING,
    "unsupported_unresolved_reason": REASON_BEHAVIOR_PUBLISH_REJECTING,
    "unsupported_comparison_group": REASON_BEHAVIOR_PUBLISH_REJECTING,
    "unsupported_comparison_scope": REASON_BEHAVIOR_PUBLISH_REJECTING,
    "unsupported_schema": REASON_BEHAVIOR_PUBLISH_REJECTING,
    "unsupported_regime_id": REASON_BEHAVIOR_PUBLISH_REJECTING,
    "contradictory_provenance": REASON_BEHAVIOR_PUBLISH_REJECTING,
    "malformed_provenance": REASON_BEHAVIOR_PUBLISH_REJECTING,
}

ELIGIBILITY_REASON_CODES: FrozenSet[str] = frozenset(ELIGIBILITY_REASON_CODE_BEHAVIOR)
PUBLISH_REJECTING_REASON_CODES: FrozenSet[str] = frozenset(
    code
    for code, behavior in ELIGIBILITY_REASON_CODE_BEHAVIOR.items()
    if behavior == REASON_BEHAVIOR_PUBLISH_REJECTING
)

# Back-compat aliases used by eligibility / publication imports.
SUPPORTED_ASSIGNMENT_STATUSES = ACTIVE_ASSIGNMENT_STATUSES
SUPPORTED_ASSIGNMENT_METHODS = ACTIVE_ASSIGNMENT_METHODS | RESERVED_ASSIGNMENT_METHODS
SUPPORTED_LINKAGE_STATUSES = ACTIVE_LINKAGE_STATUSES
SUPPORTED_LINKAGE_METHODS = ACTIVE_LINKAGE_METHODS | RESERVED_LINKAGE_METHODS
SUPPORTED_COMPARISON_GROUPS = ACTIVE_COMPARISON_GROUPS
SUPPORTED_COMPARABILITY_ELIGIBILITIES = ACTIVE_COMPARABILITY_ELIGIBILITIES
SUPPORTED_COMPARISON_SCOPES = ACTIVE_COMPARISON_SCOPES
SUPPORTED_UNRESOLVED_REASONS = ACTIVE_UNRESOLVED_REASONS


@dataclass(frozen=True)
class ParsedUnresolvedReason:
    """Normalized unresolved_reason parse result."""

    ok: bool
    code: Optional[str]
    detail: Dict[str, Any]
    raw: Optional[str]
    legacy_serialized: bool = False

    @property
    def is_supported(self) -> bool:
        return self.ok and (self.code is None or self.code in ACTIVE_UNRESOLVED_REASONS)


def parse_unresolved_reason(value: Any) -> ParsedUnresolvedReason:
    """Parse closed unresolved_reason codes and permitted structured forms.

    Permitted forms:
      * None
      * exact active code
      * legacy ``explicit_regime_unknown:<regime_id>`` (deterministic parser)
      * semicolon-joined sequence of the above (aggregated historical form),
        normalized to ``all_rows_unknown`` with constituent detail
    """
    if value is None:
        return ParsedUnresolvedReason(ok=True, code=None, detail={}, raw=None)
    if not isinstance(value, str):
        return ParsedUnresolvedReason(
            ok=False,
            code=None,
            detail={"malformation": "unresolved_reason_not_string"},
            raw=repr(value),
        )
    if value == "":
        return ParsedUnresolvedReason(
            ok=False,
            code=None,
            detail={"malformation": "unresolved_reason_empty"},
            raw=value,
        )
    if ";" in value:
        parts = value.split(";")
        constituents: list[Dict[str, Any]] = []
        for part in parts:
            parsed = _parse_unresolved_atom(part)
            if not parsed.ok or parsed.code is None:
                return ParsedUnresolvedReason(
                    ok=False,
                    code=None,
                    detail={
                        "malformation": "unresolved_reason_aggregate_contains_unsupported",
                        "bad_part": part,
                        "part_detail": dict(parsed.detail),
                    },
                    raw=value,
                )
            entry: Dict[str, Any] = {"unresolved_reason": parsed.code}
            if parsed.detail:
                entry["unresolved_reason_detail"] = dict(parsed.detail)
            constituents.append(entry)
        codes = [item["unresolved_reason"] for item in constituents]
        if len(set(codes)) == 1 and len(constituents) == 1:
            only = constituents[0]
            return ParsedUnresolvedReason(
                ok=True,
                code=str(only["unresolved_reason"]),
                detail=dict(only.get("unresolved_reason_detail") or {}),
                raw=value,
                legacy_serialized=True,
            )
        return ParsedUnresolvedReason(
            ok=True,
            code="all_rows_unknown",
            detail={"constituent_reasons": constituents},
            raw=value,
            legacy_serialized=True,
        )
    return _parse_unresolved_atom(value)


def _parse_unresolved_atom(value: str) -> ParsedUnresolvedReason:
    if value in ACTIVE_UNRESOLVED_REASONS:
        return ParsedUnresolvedReason(ok=True, code=value, detail={}, raw=value)
    if value.startswith(EXPLICIT_REGIME_UNKNOWN_PREFIX):
        regime_id = value[len(EXPLICIT_REGIME_UNKNOWN_PREFIX) :]
        if not regime_id or regime_id.startswith(":") or ";" in regime_id:
            return ParsedUnresolvedReason(
                ok=False,
                code=None,
                detail={"malformation": "explicit_regime_unknown_invalid_regime_id"},
                raw=value,
            )
        return ParsedUnresolvedReason(
            ok=True,
            code=EXPLICIT_REGIME_UNKNOWN,
            detail={"regime_id": regime_id},
            raw=value,
            legacy_serialized=True,
        )
    return ParsedUnresolvedReason(
        ok=False,
        code=None,
        detail={"malformation": "unsupported_unresolved_reason"},
        raw=value,
    )


def format_explicit_regime_unknown_legacy(regime_id: str) -> str:
    """Legacy serialized form retained for temporary compatibility."""
    return f"{EXPLICIT_REGIME_UNKNOWN_PREFIX}{regime_id}"


def normalize_reason_detail(detail: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Deterministic JSON-comparable normalization of reason detail."""
    return _normalize_jsonish(detail if detail is not None else {})


def _normalize_jsonish(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _normalize_jsonish(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    if isinstance(value, (list, tuple)):
        return [_normalize_jsonish(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def required_fields_for_scope(comparison_scope: str) -> Tuple[str, ...]:
    if comparison_scope not in ACTIVE_COMPARISON_SCOPES:
        raise ValueError(f"unsupported comparison_scope: {comparison_scope!r}")
    return COMPARISON_SCOPE_REQUIRED_FIELDS[comparison_scope]


def is_active_assignment_method(method: str) -> bool:
    return method in ACTIVE_ASSIGNMENT_METHODS


def is_active_linkage_method(method: str) -> bool:
    return method in ACTIVE_LINKAGE_METHODS


def assert_writer_assignment_method(method: str) -> None:
    if method not in ACTIVE_ASSIGNMENT_METHODS:
        raise AssertionError(
            f"writers must not emit non-active assignment_method={method!r}"
        )


def assert_writer_linkage_method(method: str) -> None:
    if method not in ACTIVE_LINKAGE_METHODS:
        raise AssertionError(
            f"writers must not emit non-active linkage_method={method!r}"
        )


def reason_behavior(reason_code: str) -> str:
    try:
        return ELIGIBILITY_REASON_CODE_BEHAVIOR[reason_code]
    except KeyError as exc:
        raise ValueError(f"unknown eligibility reason code: {reason_code}") from exc


def is_publish_rejecting_reason(reason_code: str) -> bool:
    return reason_code in PUBLISH_REJECTING_REASON_CODES
