"""Investigation- and episode-level aggregation of Phase-1 regime assignments."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from synapse_msi.historical_corpus.comparability import (
    compare_regimes,
    overall_comparability,
)
from synapse_msi.historical_corpus.inventory import lookup_regime
from synapse_msi.historical_corpus.models import (
    ACQUISITION_REGIME_METHODOLOGY_VERSION,
    FIELD_SEMANTICS_VERSION,
    PROVENANCE_POLICY_VERSION,
    AssignmentMethod,
    AssignmentStatus,
    ComparabilityLevel,
    InvestigationRegimeContext,
    RegimeAssignment,
)

UNKNOWN_REGIME_ID = "unknown.insufficient_provenance"

_ACQUISITION_ROW_KEYS = (
    "acquisition_regime_id",
    "regime_id",
    "ingest_type",
    "transport",
    "exchange",
    "venue",
    "collector_service_name",
    "payload",
    "payload_jsonb",
    "sink_received_at",
    "collector_observed_at",
    "venue_event_time",
)


def _is_unknown(assignment: RegimeAssignment) -> bool:
    return (
        assignment.assignment_status == "unknown"
        or assignment.acquisition_regime_id == UNKNOWN_REGIME_ID
    )


def _unique_sorted(values: Iterable[str]) -> Tuple[str, ...]:
    return tuple(sorted({value for value in values if value}))


def _method_priority(method: AssignmentMethod) -> int:
    order = {
        "explicit": 0,
        "row_metadata_with_payload": 1,
        "row_metadata": 2,
        "inventory_supported": 3,
        "temporal_provisional": 4,
        "unknown": 5,
    }
    return order.get(method, 99)


def _select_aggregate_method(assignments: Sequence[RegimeAssignment]) -> AssignmentMethod:
    if not assignments:
        return "unknown"
    return min((item.assignment_method for item in assignments), key=_method_priority)


def _collect_limitations(regime_ids: Sequence[str]) -> Tuple[str, ...]:
    limitations: List[str] = []
    for regime_id in regime_ids:
        entry = lookup_regime(regime_id)
        if entry is None:
            continue
        for item in entry.known_limitations or entry.known_semantic_differences:
            if item not in limitations:
                limitations.append(item)
    return tuple(limitations)


def _pair_compatibility(regime_ids: Sequence[str]) -> Optional[Dict[str, object]]:
    resolved = [regime_id for regime_id in regime_ids if regime_id != UNKNOWN_REGIME_ID]
    if len(resolved) < 2:
        return None

    pair_summaries: List[Dict[str, object]] = []
    field_levels: Dict[str, ComparabilityLevel] = {}
    overall_fields = []

    for index, left_id in enumerate(resolved):
        for right_id in resolved[index + 1 :]:
            pair = compare_regimes(left_id, right_id)
            pair_summaries.append(
                {
                    "regime_a": pair.regime_a,
                    "regime_b": pair.regime_b,
                    "overall": pair.overall,
                    "fields": [item.to_dict() for item in pair.fields],
                }
            )
            overall_fields.extend(pair.fields)
            for field in pair.fields:
                existing = field_levels.get(field.field_name)
                if existing is None or field.level == "not_comparable":
                    field_levels[field.field_name] = field.level
                elif existing == "fully_comparable" and field.level != "fully_comparable":
                    field_levels[field.field_name] = field.level

    aggregated = overall_comparability(overall_fields) if overall_fields else "unknown"
    return {
        "overall": aggregated,
        "field_levels": dict(sorted(field_levels.items())),
        "pairs": pair_summaries,
    }


def aggregate_regime_assignments(
    assignments: Sequence[RegimeAssignment],
) -> InvestigationRegimeContext:
    """
    Deterministic investigation-level aggregation.

    Rules:
    - one resolved regime → primary set, spans_multiple_regimes=false
    - multiple resolved → spans_multiple_regimes=true, primary=None
      (legacy acquisition_regime_id uses lexicographic anchor + warning)
    - unknowns preserved; mixed resolved+unknown → provisional status
    - all unknown → explicit unknown context (section always present for new artifacts)
    """
    if not assignments:
        return InvestigationRegimeContext(
            primary_regime_id=None,
            linked_regime_ids=(UNKNOWN_REGIME_ID,),
            assignment_method="unknown",
            assignment_status="unknown",
            assignment_evidence=(),
            assignment_warnings=("no_source_rows_for_regime_assignment",),
            unresolved_reason="no_source_rows",
            methodology_version=ACQUISITION_REGIME_METHODOLOGY_VERSION,
            field_semantics_version=FIELD_SEMANTICS_VERSION,
            provenance_policy_version=None,
            spans_multiple_regimes=False,
            comparison_group="unknown",
            acquisition_regime_id=UNKNOWN_REGIME_ID,
            row_assignment_count=0,
            unknown_row_count=0,
        )

    resolved = [item for item in assignments if not _is_unknown(item)]
    unknowns = [item for item in assignments if _is_unknown(item)]
    resolved_ids = _unique_sorted(item.acquisition_regime_id for item in resolved)

    evidence = _unique_sorted(
        field for item in assignments for field in item.evidence_fields
    )
    warnings: List[str] = []
    for item in assignments:
        warnings.extend(item.warnings)
    mark_evidence = _unique_sorted(
        item.mark_evidence for item in assignments if item.mark_evidence != "not_applicable"
    )

    if unknowns:
        warnings.append(
            f"unresolved_acquisition_rows={len(unknowns)}; fail-closed for claims relying on them"
        )

    if not resolved_ids:
        from synapse_msi.historical_corpus.provenance_registry import (
            parse_unresolved_reason,
        )

        constituent: List[Dict[str, Any]] = []
        codes: List[str] = []
        for item in unknowns:
            raw_reason = item.unresolved_reason or "all_rows_unknown"
            parsed = parse_unresolved_reason(raw_reason)
            code = parsed.code if parsed.ok and parsed.code else "all_rows_unknown"
            entry: Dict[str, Any] = {"unresolved_reason": code}
            detail = dict(item.unresolved_reason_detail or {})
            if parsed.detail:
                detail = {**parsed.detail, **detail}
            if detail:
                entry["unresolved_reason_detail"] = detail
            constituent.append(entry)
            codes.append(code)
        unique_codes = _unique_sorted(codes)
        if len(unique_codes) == 1 and len(constituent) == 1:
            unresolved_reason = unique_codes[0]
            unresolved_reason_detail = constituent[0].get("unresolved_reason_detail")
        elif len(unique_codes) == 1:
            unresolved_reason = unique_codes[0]
            unresolved_reason_detail = {"constituent_reasons": constituent}
        else:
            unresolved_reason = "all_rows_unknown"
            unresolved_reason_detail = {"constituent_reasons": constituent}
        return InvestigationRegimeContext(
            primary_regime_id=None,
            linked_regime_ids=(UNKNOWN_REGIME_ID,),
            assignment_method=_select_aggregate_method(assignments),
            assignment_status="unknown",
            assignment_evidence=evidence,
            assignment_warnings=tuple(dict.fromkeys(warnings)),
            unresolved_reason=unresolved_reason,
            unresolved_reason_detail=unresolved_reason_detail,
            methodology_version=ACQUISITION_REGIME_METHODOLOGY_VERSION,
            field_semantics_version=FIELD_SEMANTICS_VERSION,
            provenance_policy_version=None,
            spans_multiple_regimes=False,
            comparison_group="unknown",
            acquisition_regime_id=UNKNOWN_REGIME_ID,
            mark_evidence_summary=mark_evidence,
            known_limitations=("insufficient row-level acquisition metadata",),
            row_assignment_count=len(assignments),
            unknown_row_count=len(unknowns),
        )

    linked = list(resolved_ids)
    if unknowns and UNKNOWN_REGIME_ID not in linked:
        linked.append(UNKNOWN_REGIME_ID)
    linked_ids = tuple(linked)

    spans = len(resolved_ids) > 1
    compatibility = _pair_compatibility(resolved_ids) if spans else None

    def _group_for(regime_id: str) -> str:
        for item in resolved:
            if item.acquisition_regime_id == regime_id and item.comparison_group:
                return item.comparison_group
        entry = lookup_regime(regime_id)
        return entry.comparison_group if entry else "unknown"

    if len(resolved_ids) == 1:
        primary = resolved_ids[0]
        status: AssignmentStatus = "provisional" if unknowns else "definitive"
        method = _select_aggregate_method(resolved if not unknowns else assignments)
        policies = {
            item.provenance_policy_version
            for item in resolved
            if item.provenance_policy_version
        }
        policy = next(iter(policies)) if len(policies) == 1 else (
            PROVENANCE_POLICY_VERSION if policies else None
        )
        if unknowns:
            warnings.append("mixed_resolved_and_unknown_rows")
        return InvestigationRegimeContext(
            primary_regime_id=primary,
            linked_regime_ids=linked_ids,
            assignment_method=method,
            assignment_status=status,
            assignment_evidence=evidence,
            assignment_warnings=tuple(dict.fromkeys(warnings)),
            unresolved_reason="mixed_resolved_and_unknown_rows" if unknowns else None,
            methodology_version=ACQUISITION_REGIME_METHODOLOGY_VERSION,
            field_semantics_version=FIELD_SEMANTICS_VERSION,
            provenance_policy_version=policy,
            spans_multiple_regimes=False,
            cross_regime_compatibility=None,
            known_limitations=_collect_limitations(resolved_ids),
            comparison_group=_group_for(primary),
            acquisition_regime_id=primary,
            mark_evidence_summary=mark_evidence,
            row_assignment_count=len(assignments),
            unknown_row_count=len(unknowns),
        )

    # Multiple resolved regimes — do not invent a semantic primary.
    anchor = resolved_ids[0]
    warnings.append(
        "multi_regime_no_semantic_primary; "
        f"legacy acquisition_regime_id anchor={anchor}"
    )
    if unknowns:
        warnings.append("mixed_resolved_and_unknown_rows")
    status = "provisional"
    groups = {_group_for(regime_id) for regime_id in resolved_ids}
    comparison_group = next(iter(groups)) if len(groups) == 1 else "mixed"

    # Eligibility is authoritative for comparison posture; warnings mirror it.
    from synapse_msi.historical_corpus.eligibility import (
        evaluate_artifact_comparability_eligibility,
    )

    eligibility = evaluate_artifact_comparability_eligibility(
        {
            "assignment_status": status,
            "assignment_method": _select_aggregate_method(resolved),
            "primary_regime_id": None,
            "linked_regime_ids": linked_ids,
            "spans_multiple_regimes": True,
            "comparison_group": comparison_group,
            "acquisition_regime_id": anchor,
            "unresolved_reason": (
                "multi_regime_investigation" if not unknowns else "multi_regime_with_unknown_rows"
            ),
            "cross_regime_compatibility": compatibility,
        }
    )
    if eligibility.comparability_eligibility == "comparable_after_partition":
        overall = (compatibility or {}).get("overall")
        if overall == "not_comparable":
            warnings.append("multi_regime_not_comparable")
        elif overall == "partially_comparable":
            warnings.append("multi_regime_partially_comparable")
        warnings.append("comparability_eligibility=comparable_after_partition")
    elif eligibility.is_excluded():
        warnings.append(
            f"comparability_eligibility=excluded_fail_closed;"
            f"reason={eligibility.comparability_reason_code}"
        )

    return InvestigationRegimeContext(
        primary_regime_id=None,
        linked_regime_ids=linked_ids,
        assignment_method=_select_aggregate_method(resolved),
        assignment_status=status,
        assignment_evidence=evidence,
        assignment_warnings=tuple(dict.fromkeys(warnings)),
        unresolved_reason="multi_regime_investigation" if not unknowns else "multi_regime_with_unknown_rows",
        methodology_version=ACQUISITION_REGIME_METHODOLOGY_VERSION,
        field_semantics_version=FIELD_SEMANTICS_VERSION,
        provenance_policy_version=PROVENANCE_POLICY_VERSION,
        spans_multiple_regimes=True,
        cross_regime_compatibility=compatibility,
        known_limitations=_collect_limitations(resolved_ids),
        comparison_group=comparison_group,
        acquisition_regime_id=anchor,
        mark_evidence_summary=mark_evidence,
        row_assignment_count=len(assignments),
        unknown_row_count=len(unknowns),
    )
