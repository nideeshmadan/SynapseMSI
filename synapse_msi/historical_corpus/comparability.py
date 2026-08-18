"""Deterministic field-level comparability rules between acquisition regimes."""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from synapse_msi.historical_corpus.inventory import (
    build_regime_inventory,
    lookup_regime,
)
from synapse_msi.historical_corpus.models import (
    COMPARABILITY_FIELDS,
    ComparabilityLevel,
    FieldComparability,
    HistoricalRegimeInventoryEntry,
    RegimePairComparability,
)

# Ordered (left_group, right_group) → field → (level, reason_code, reason).
# Bid/ask/spread are never fully_comparable across distinct regimes: shared names
# do not prove identical timing or freshness semantics.
_GROUP_FIELD_RULES: Dict[Tuple[str, str], Dict[str, Tuple[ComparabilityLevel, str, str]]] = {
    ("rest_composed", "rest_composed"): {
        "mark_price": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "REST-composed mark may differ in endpoint composition and poll cadence",
        ),
        "funding": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "funding sampling cadence may differ across REST collectors",
        ),
        "open_interest": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "open interest REST polling cadence may differ",
        ),
        "bid": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "bid is the same economic concept but REST poll timing is unproven identical",
        ),
        "ask": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "ask is the same economic concept but REST poll timing is unproven identical",
        ),
        "spread": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "spread inherits unproven REST bid/ask timing equivalence",
        ),
    },
    ("native_mark_authoritative", "native_mark_authoritative"): {
        "mark_price": (
            "fully_comparable",
            "identical_acquisition_semantics",
            "both regimes treat native mark as authoritative",
        ),
        "funding": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "funding coverage and cadence may differ by venue path",
        ),
        "open_interest": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "open interest may be absent or separately polled",
        ),
        "bid": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "book path differs (hybrid bookTicker vs native ticker) without proven identical freshness",
        ),
        "ask": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "book path differs without proven identical freshness",
        ),
        "spread": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "spread inherits unproven cross-venue book freshness equivalence",
        ),
    },
    ("l1_midpoint_proxy", "l1_midpoint_proxy"): {
        "mark_price": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "midpoint-proxy mark is economically similar but sampling path may differ",
        ),
        "funding": (
            "not_comparable",
            "field_unavailable",
            "funding generally unavailable on L1 midpoint-proxy paths",
        ),
        "open_interest": (
            "not_comparable",
            "field_unavailable",
            "open interest generally unavailable on L1 midpoint-proxy paths",
        ),
        "bid": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "L1 bid concept matches but stream/channel timing is unproven identical",
        ),
        "ask": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "L1 ask concept matches but stream/channel timing is unproven identical",
        ),
        "spread": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "spread inherits unproven L1 timing equivalence",
        ),
    },
    ("l1_midpoint_proxy", "native_mark_authoritative"): {
        "mark_price": (
            "not_comparable",
            "changed_field_authority",
            "midpoint-proxy mark vs native authoritative mark",
        ),
        "funding": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "funding may be present on only one path",
        ),
        "open_interest": (
            "not_comparable",
            "field_unavailable",
            "open interest typically unavailable on L1 midpoint-proxy path",
        ),
        "bid": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "economic bid concept matches; acquisition freshness unproven across groups",
        ),
        "ask": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "economic ask concept matches; acquisition freshness unproven across groups",
        ),
        "spread": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "spread shares economic meaning; sampling/freshness unproven across groups",
        ),
    },
    ("native_mark_authoritative", "l1_midpoint_proxy"): {
        "mark_price": (
            "not_comparable",
            "changed_field_authority",
            "native authoritative mark vs midpoint-proxy mark",
        ),
        "funding": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "funding may be present on only one path",
        ),
        "open_interest": (
            "not_comparable",
            "field_unavailable",
            "open interest typically unavailable on L1 midpoint-proxy path",
        ),
        "bid": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "economic bid concept matches; acquisition freshness unproven across groups",
        ),
        "ask": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "economic ask concept matches; acquisition freshness unproven across groups",
        ),
        "spread": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "spread shares economic meaning; sampling/freshness unproven across groups",
        ),
    },
    ("l1_midpoint_proxy", "rest_composed"): {
        "mark_price": (
            "not_comparable",
            "changed_field_authority",
            "midpoint-proxy vs REST-composed mark authority",
        ),
        "funding": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "funding may exist on REST path with different cadence",
        ),
        "open_interest": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "open interest may exist on REST path with different cadence",
        ),
        "bid": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "bid concept matches; REST vs WS sampling unproven identical",
        ),
        "ask": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "ask concept matches; REST vs WS sampling unproven identical",
        ),
        "spread": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "spread concept matches; REST vs WS sampling unproven identical",
        ),
    },
    ("rest_composed", "l1_midpoint_proxy"): {
        "mark_price": (
            "not_comparable",
            "changed_field_authority",
            "REST-composed vs midpoint-proxy mark authority",
        ),
        "funding": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "funding may exist on REST path with different cadence",
        ),
        "open_interest": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "open interest may exist on REST path with different cadence",
        ),
        "bid": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "bid concept matches; REST vs WS sampling unproven identical",
        ),
        "ask": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "ask concept matches; REST vs WS sampling unproven identical",
        ),
        "spread": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "spread concept matches; REST vs WS sampling unproven identical",
        ),
    },
    ("native_mark_authoritative", "rest_composed"): {
        "mark_price": (
            "not_comparable",
            "changed_field_authority",
            "native authoritative vs REST-composed mark",
        ),
        "funding": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "funding cadence and authority may differ",
        ),
        "open_interest": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "open interest cadence and authority may differ",
        ),
        "bid": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "bid concept matches; hybrid/WS vs REST sampling unproven identical",
        ),
        "ask": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "ask concept matches; hybrid/WS vs REST sampling unproven identical",
        ),
        "spread": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "spread concept matches; hybrid/WS vs REST sampling unproven identical",
        ),
    },
    ("rest_composed", "native_mark_authoritative"): {
        "mark_price": (
            "not_comparable",
            "changed_field_authority",
            "REST-composed vs native authoritative mark",
        ),
        "funding": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "funding cadence and authority may differ",
        ),
        "open_interest": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "open interest cadence and authority may differ",
        ),
        "bid": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "bid concept matches; REST vs hybrid/WS sampling unproven identical",
        ),
        "ask": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "ask concept matches; REST vs hybrid/WS sampling unproven identical",
        ),
        "spread": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "spread concept matches; REST vs hybrid/WS sampling unproven identical",
        ),
    },
    ("conditional_native_mark", "l1_midpoint_proxy"): {
        "mark_price": (
            "partially_comparable",
            "conditional_native_versus_derived",
            "OKX conditional native mark vs L1 midpoint/unavailable mark",
        ),
        "funding": (
            "not_comparable",
            "field_unavailable",
            "funding generally unavailable on these WS top-of-book paths",
        ),
        "open_interest": (
            "not_comparable",
            "field_unavailable",
            "open interest generally unavailable on these WS top-of-book paths",
        ),
        "bid": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "bid concept matches; channel timing unproven identical",
        ),
        "ask": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "ask concept matches; channel timing unproven identical",
        ),
        "spread": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "spread concept matches; channel timing unproven identical",
        ),
    },
    ("l1_midpoint_proxy", "conditional_native_mark"): {
        "mark_price": (
            "partially_comparable",
            "conditional_native_versus_derived",
            "L1 midpoint/unavailable mark vs OKX conditional native mark",
        ),
        "funding": (
            "not_comparable",
            "field_unavailable",
            "funding generally unavailable on these WS top-of-book paths",
        ),
        "open_interest": (
            "not_comparable",
            "field_unavailable",
            "open interest generally unavailable on these WS top-of-book paths",
        ),
        "bid": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "bid concept matches; channel timing unproven identical",
        ),
        "ask": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "ask concept matches; channel timing unproven identical",
        ),
        "spread": (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "spread concept matches; channel timing unproven identical",
        ),
    },
}

def _timing_defaults(
    left: HistoricalRegimeInventoryEntry,
    right: HistoricalRegimeInventoryEntry,
) -> Dict[str, Tuple[ComparabilityLevel, str, str]]:
    if left.provenance_policy_version != right.provenance_policy_version:
        provenance = (
            "partially_comparable",
            "changed_provenance_policy",
            "provenance policy versions differ or one side is unpinned",
        )
    else:
        provenance = (
            "partially_comparable",
            "same_economic_concept_different_sampling_path",
            "provenance attachment path may differ even under the same policy pin",
        )
    return {
        "freshness": (
            "partially_comparable",
            "changed_freshness_semantics",
            "freshness gates and clocks are not proven identical across regimes",
        ),
        "staleness": (
            "partially_comparable",
            "changed_freshness_semantics",
            "staleness classification depends on acquisition path and clocks",
        ),
        "provenance": provenance,
        "collector_timing": (
            "partially_comparable",
            "changed_timestamp_semantics",
            "collector_observed_at semantics may differ by collector topology",
        ),
        "venue_timing": (
            "partially_comparable",
            "changed_timestamp_semantics",
            "venue_event_time population and carry-forward differ by path",
        ),
    }


def compare_fields(
    left: HistoricalRegimeInventoryEntry,
    right: HistoricalRegimeInventoryEntry,
) -> Tuple[FieldComparability, ...]:
    if left.regime_id == right.regime_id:
        return tuple(
            FieldComparability(
                field_name=field,
                level="fully_comparable",
                reason="same acquisition regime",
                reason_code="same_regime",
            )
            for field in COMPARABILITY_FIELDS
        )

    if left.comparison_group == "unknown" or right.comparison_group == "unknown":
        return tuple(
            FieldComparability(
                field_name=field,
                level="unknown",
                reason="unknown provenance regime involved",
                reason_code="unresolved_acquisition_metadata",
            )
            for field in COMPARABILITY_FIELDS
        )

    pair = (left.comparison_group, right.comparison_group)
    rules = dict(_GROUP_FIELD_RULES.get(pair, {}))
    rules.update(_timing_defaults(left, right))

    results: List[FieldComparability] = []
    for field in COMPARABILITY_FIELDS:
        if field in rules:
            level, reason_code, reason = rules[field]
        else:
            level, reason_code, reason = (
                "unknown",
                "insufficient_evidence",
                f"no proven comparability rule for {field} between "
                f"{left.comparison_group} and {right.comparison_group}",
            )
        results.append(
            FieldComparability(
                field_name=field,
                level=level,
                reason=reason,
                reason_code=reason_code,
            )
        )
    return tuple(results)


def overall_comparability(fields: Sequence[FieldComparability]) -> ComparabilityLevel:
    """
    Deterministic aggregation (fail closed):

    1. all fully_comparable → fully_comparable
    2. any unknown → unknown
    3. any not_comparable with any fully/partial → partially_comparable
    4. only not_comparable → not_comparable
    5. otherwise → partially_comparable
    """
    levels = {item.level for item in fields}
    if levels == {"fully_comparable"}:
        return "fully_comparable"
    if "unknown" in levels:
        return "unknown"
    if "not_comparable" in levels:
        if levels == {"not_comparable"}:
            return "not_comparable"
        return "partially_comparable"
    return "partially_comparable"


# Backward-compatible alias used by older call sites / tests.
_overall_level = overall_comparability


def compare_regimes(regime_a: str, regime_b: str) -> RegimePairComparability:
    left = lookup_regime(regime_a)
    right = lookup_regime(regime_b)
    if left is None or right is None:
        unknown_fields = tuple(
            FieldComparability(
                field_name=field,
                level="unknown",
                reason="regime not in inventory",
                reason_code="unknown_regime",
            )
            for field in COMPARABILITY_FIELDS
        )
        return RegimePairComparability(
            regime_a=regime_a,
            regime_b=regime_b,
            fields=unknown_fields,
            overall="unknown",
        )
    fields = compare_fields(left, right)
    return RegimePairComparability(
        regime_a=regime_a,
        regime_b=regime_b,
        fields=fields,
        overall=overall_comparability(fields),
    )


def build_comparability_matrix(
    regime_ids: Optional[Sequence[str]] = None,
) -> List[RegimePairComparability]:
    ids = tuple(regime_ids or [entry.regime_id for entry in build_regime_inventory()])
    pairs: List[RegimePairComparability] = []
    for index, regime_a in enumerate(ids):
        for regime_b in ids[index:]:
            pairs.append(compare_regimes(regime_a, regime_b))
    return pairs
