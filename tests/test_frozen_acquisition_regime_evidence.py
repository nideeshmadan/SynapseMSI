"""Frozen acquisition-regime evidence integrity and classification policy."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from synapse_msi.historical_corpus.eligibility import (
    evaluate_artifact_comparability_eligibility,
)
from synapse_msi.historical_corpus.frozen_registry import (
    FROZEN_REGISTRY_CONTENT_VERSION,
    FROZEN_REGISTRY_ID,
    FrozenRegistryError,
    assign_regime_from_frozen_registry,
    load_frozen_registry_file,
    load_frozen_registry_from_example,
    verify_manifest_pin,
)
from synapse_msi.historical_corpus.investigation_context import (
    aggregate_regime_assignments,
)
from synapse_msi.historical_corpus.models import RegimeAssignment
from synapse_msi.investigation_reproduction import (
    acquisition_row_from_observation,
    compare_published,
    load_jsonl,
    read_json,
    recompute_investigation_package,
)

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "evidence/acquisition_regime_fixture_registry_v1.json"
MODERN = [
    ROOT / "examples/modern/op_native_mark_000005",
    ROOT / "examples/modern/op_stale_014639",
]
HISTORICAL = [
    ROOT / "examples/historical/op_disagree_000244",
    ROOT / "examples/historical/op_stale_000012",
    ROOT / "examples/historical/op_consensus_000042",
]


def _pin(example: Path) -> dict:
    return read_json(example / "input_manifest.json")["acquisition_regime_evidence"]


def test_artifact_digest_and_identity():
    raw = ARTIFACT.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    registry = load_frozen_registry_file(ARTIFACT)
    assert registry.registry_id == FROZEN_REGISTRY_ID
    assert registry.registry_content_version == FROZEN_REGISTRY_CONTENT_VERSION
    assert registry.sha256 == digest
    assert len(registry.assignments) == 4


@pytest.mark.parametrize("example", MODERN, ids=lambda p: p.name)
def test_modern_pin_passes(example: Path):
    registry = load_frozen_registry_from_example(example)
    assert registry is not None
    assert registry.sha256 == _pin(example)["sha256"]


@pytest.mark.parametrize("example", MODERN, ids=lambda p: p.name)
def test_modified_artifact_fails(example: Path, tmp_path: Path):
    pin = dict(_pin(example))
    mutated = tmp_path / "mutated.json"
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    payload["assignments"][0]["collector_service_name"] = "mutated-collector"
    mutated.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pin["path"] = os.path.relpath(str(mutated), str(example))
    with pytest.raises(FrozenRegistryError, match="sha256 mismatch"):
        verify_manifest_pin(example_dir=example, pin=pin)


@pytest.mark.parametrize("example", MODERN, ids=lambda p: p.name)
def test_missing_artifact_fails(example: Path, tmp_path: Path):
    pin = dict(_pin(example))
    missing = tmp_path / "missing.json"
    pin["path"] = os.path.relpath(str(missing), str(example))
    with pytest.raises(FrozenRegistryError, match="missing"):
        verify_manifest_pin(example_dir=example, pin=pin)


@pytest.mark.parametrize("example", MODERN, ids=lambda p: p.name)
def test_wrong_identifier_fails(example: Path):
    pin = dict(_pin(example))
    pin["registry_id"] = "not_the_frozen_registry"
    with pytest.raises(FrozenRegistryError, match="registry_id"):
        verify_manifest_pin(example_dir=example, pin=pin)


@pytest.mark.parametrize("example", MODERN, ids=lambda p: p.name)
def test_wrong_version_fails(example: Path):
    pin = dict(_pin(example))
    pin["registry_content_version"] = "not-a-real-version"
    with pytest.raises(FrozenRegistryError, match="registry_content_version"):
        verify_manifest_pin(example_dir=example, pin=pin)


def test_one_matching_regime_is_definitive():
    registry = load_frozen_registry_file(ARTIFACT)
    assignment = assign_regime_from_frozen_registry(
        {
            "venue": "binance",
            "ingest_type": "hybrid_book_reference",
            "transport": "hybrid",
            "collector_service_name": "synapse-collector-binance-ws",
            "payload": {"native_mark_price": 1.0},
        },
        registry,
    )
    assert assignment.assignment_status == "definitive"
    assert assignment.acquisition_regime_id == "binance.hybrid_book_reference.native_mark"
    assert assignment.comparison_group == "native_mark_authoritative"


def test_no_match_fails_closed():
    registry = load_frozen_registry_file(ARTIFACT)
    assignment = assign_regime_from_frozen_registry(
        {
            "venue": "binance",
            "ingest_type": "canonical_v1",
            "transport": "rest",
        },
        registry,
    )
    assert assignment.assignment_status == "unknown"
    assert assignment.acquisition_regime_id == "unknown.insufficient_provenance"


def test_transport_mismatch_fails_closed():
    registry = load_frozen_registry_file(ARTIFACT)
    assignment = assign_regime_from_frozen_registry(
        {
            "venue": "bybit",
            "ingest_type": "ws_ticker",
            "transport": "rest",
            "payload": {"native_mark_price": 1.0},
        },
        registry,
    )
    assert assignment.assignment_status == "unknown"


def test_ingest_type_mismatch_fails_closed():
    registry = load_frozen_registry_file(ARTIFACT)
    assignment = assign_regime_from_frozen_registry(
        {
            "venue": "okx",
            "ingest_type": "ws_ticker",
            "transport": "websocket",
        },
        registry,
    )
    assert assignment.assignment_status == "unknown"


def test_collector_mismatch_warns_but_assigns():
    registry = load_frozen_registry_file(ARTIFACT)
    assignment = assign_regime_from_frozen_registry(
        {
            "venue": "hyperliquid",
            "ingest_type": "ws_top_of_book",
            "transport": "websocket",
            "collector_service_name": "different-collector",
            "payload": {},
        },
        registry,
    )
    assert assignment.assignment_status == "definitive"
    assert assignment.acquisition_regime_id == "hyperliquid.ws_top_of_book.l1_only"
    assert any("differs from frozen collector" in w for w in assignment.warnings)


def test_overlapping_matches_prefer_current_production(tmp_path: Path):
    from synapse_msi.historical_corpus import frozen_registry as fr

    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    base = dict(payload["assignments"][0])
    base["regime_id"] = "binance.hybrid_book_reference.native_mark.alt"
    base["acquisition_regime"] = base["regime_id"]
    base["current_production"] = False
    payload["assignments"].append(base)
    path = tmp_path / "overlap.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    data = json.loads(path.read_text(encoding="utf-8"))
    records = tuple(fr._record_from_mapping(item) for item in data["assignments"])
    registry = fr.FrozenAcquisitionRegistry(
        artifact_format_version=data["artifact_format_version"],
        registry_id=data["registry_id"],
        registry_content_version=data["registry_content_version"],
        evidence_status=data["evidence_status"],
        boundary_semantics=data["boundary_semantics"],
        assignments=records,
        source_path=path,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )
    assignment = assign_regime_from_frozen_registry(
        {
            "venue": "binance",
            "ingest_type": "hybrid_book_reference",
            "transport": "hybrid",
            "payload": {"native_mark_price": 1.0},
        },
        registry,
    )
    assert assignment.acquisition_regime_id == "binance.hybrid_book_reference.native_mark"


def test_time_bounds_advisory_by_default():
    registry = load_frozen_registry_file(ARTIFACT)
    # Far before valid_from for binance hybrid
    assignment = assign_regime_from_frozen_registry(
        {
            "venue": "binance",
            "ingest_type": "hybrid_book_reference",
            "transport": "hybrid",
            "payload": {"native_mark_price": 1.0},
            "venue_timestamp": "2020-01-01T00:00:00Z",
        },
        registry,
    )
    assert assignment.assignment_status == "definitive"
    assert any("precedes valid_from" in w for w in assignment.warnings)


def test_time_bounds_enforced_when_requested():
    registry = load_frozen_registry_file(ARTIFACT)
    assignment = assign_regime_from_frozen_registry(
        {
            "venue": "binance",
            "ingest_type": "hybrid_book_reference",
            "transport": "hybrid",
            "payload": {"native_mark_price": 1.0},
            "venue_timestamp": "2020-01-01T00:00:00Z",
        },
        registry,
        enforce_time_bounds=True,
    )
    assert assignment.assignment_status == "unknown"


def test_multi_regime_aggregation_and_eligibility():
    registry = load_frozen_registry_file(ARTIFACT)
    rows = [
        {
            "venue": "binance",
            "ingest_type": "hybrid_book_reference",
            "transport": "hybrid",
            "payload": {"native_mark_price": 1.0},
        },
        {
            "venue": "bybit",
            "ingest_type": "ws_ticker",
            "transport": "websocket",
            "payload": {"native_mark_price": 1.0},
        },
        {
            "venue": "hyperliquid",
            "ingest_type": "ws_top_of_book",
            "transport": "websocket",
            "payload": {},
        },
        {
            "venue": "okx",
            "ingest_type": "ws_top_of_book",
            "transport": "websocket",
            "payload": {},
        },
    ]
    assignments = [assign_regime_from_frozen_registry(row, registry) for row in rows]
    context = aggregate_regime_assignments(assignments)
    assert context.assignment_status == "provisional"
    assert context.primary_regime_id is None
    assert context.spans_multiple_regimes is True
    assert context.comparison_group == "mixed"
    decision = evaluate_artifact_comparability_eligibility(
        {
            **context.to_dict(),
            "linkage_status": "derived_from_preserved_lineage",
            "linkage_method": "episode_sidecar_aggregation",
        },
        known_regime_ids=registry.regime_ids,
    )
    assert decision.comparability_eligibility == "comparable_after_partition"
    assert decision.comparability_reason_code == "mixed_regime_requires_partition"


def test_single_regime_aggregation():
    registry = load_frozen_registry_file(ARTIFACT)
    assignment = assign_regime_from_frozen_registry(
        {
            "venue": "bybit",
            "ingest_type": "ws_ticker",
            "transport": "websocket",
            "payload": {"native_mark_price": 1.0},
        },
        registry,
    )
    context = aggregate_regime_assignments([assignment])
    assert context.assignment_status == "definitive"
    assert context.primary_regime_id == "bybit.native_ws_ticker.markPrice"
    assert context.spans_multiple_regimes is False
    assert context.comparison_group == "native_mark_authoritative"


def test_historical_unknown_aggregation_fail_closed():
    unknown = RegimeAssignment(
        acquisition_regime_id="unknown.insufficient_provenance",
        assignment_method="unknown",
        assignment_status="unknown",
        evidence_fields=("archived_observation_without_acquisition_metadata",),
        unresolved_reason="missing_acquisition_metadata",
        comparison_group="unknown",
        provenance_policy_version=None,
    )
    context = aggregate_regime_assignments([unknown, unknown, unknown, unknown])
    assert context.assignment_status == "unknown"
    decision = evaluate_artifact_comparability_eligibility(
        {
            **context.to_dict(),
            "linkage_status": "insufficient_raw_lineage",
            "linkage_method": "historical_lineage_unavailable",
        }
    )
    assert decision.comparability_eligibility == "excluded_fail_closed"
    assert decision.comparability_reason_code == "unknown_assignment"


@pytest.mark.parametrize("example", MODERN, ids=lambda p: p.name)
def test_modern_fixture_provenance_equality(example: Path):
    published = read_json(example / "investigation.json")
    observations = load_jsonl(example / "observations.jsonl")
    episode_id = str((published.get("source") or {}).get("episode_id"))
    recomputed, _ = recompute_investigation_package(
        observations,
        published=published,
        episode_id=episode_id,
        example_dir=example,
    )
    assert compare_published(published, recomputed) == []
    assert recomputed.provenance_classification["assignment_status"] == "provisional"
    assert recomputed.provenance_classification["primary_regime_id"] is None
    assert recomputed.provenance_classification["spans_multiple_regimes"] is True
    assert recomputed.provenance_classification["comparison_group"] == "mixed"
    assert recomputed.comparability_eligibility == "comparable_after_partition"
    assert recomputed.comparability_reason_code == "mixed_regime_requires_partition"


@pytest.mark.parametrize("example", HISTORICAL, ids=lambda p: p.name)
def test_historical_fixture_fail_closed_unchanged(example: Path):
    published = read_json(example / "investigation.json")
    observations = load_jsonl(example / "observations.jsonl")
    episode_id = str((published.get("source") or {}).get("episode_id"))
    recomputed, _ = recompute_investigation_package(
        observations,
        published=published,
        episode_id=episode_id,
        example_dir=example,
    )
    assert compare_published(published, recomputed) == []
    assert recomputed.provenance_classification["assignment_status"] == "unknown"
    assert recomputed.comparability_eligibility == "excluded_fail_closed"
    assert recomputed.comparability_reason_code == "unknown_assignment"
    assert "acquisition_regime_evidence" not in read_json(example / "input_manifest.json")


@pytest.mark.parametrize(
    "field,value",
    [
        ("regime_id", "binance.does_not_exist"),
        ("transport", "rest"),
        ("ingest_type", "canonical_v1"),
        ("collector_service_name", "mutated-collector"),
    ],
)
def test_asserted_evidence_mutations(field: str, value: str):
    registry = load_frozen_registry_file(ARTIFACT)
    row = {
        "venue": "binance",
        "ingest_type": "hybrid_book_reference",
        "transport": "hybrid",
        "collector_service_name": "synapse-collector-binance-ws",
        "payload": {"native_mark_price": 1.0},
    }
    if field == "regime_id":
        row["acquisition_regime_id"] = value
        assignment = assign_regime_from_frozen_registry(row, registry)
        assert assignment.assignment_status == "unknown"
        return
    row[field] = value
    assignment = assign_regime_from_frozen_registry(row, registry)
    if field == "collector_service_name":
        assert assignment.assignment_status == "definitive"
        assert any("differs from frozen collector" in w for w in assignment.warnings)
    else:
        assert assignment.assignment_status == "unknown"


def test_validity_interval_mutation_changes_enforced_assignment():
    registry = load_frozen_registry_file(ARTIFACT)
    # Mutate observation time outside bounds with enforcement
    assignment = assign_regime_from_frozen_registry(
        {
            "venue": "bybit",
            "ingest_type": "ws_ticker",
            "transport": "websocket",
            "payload": {"native_mark_price": 1.0},
            "venue_timestamp": "2020-01-01T00:00:00Z",
        },
        registry,
        enforce_time_bounds=True,
    )
    assert assignment.assignment_status == "unknown"


def test_digest_mutation_fails_modern_package(tmp_path: Path):
    example = MODERN[0]
    pin = dict(_pin(example))
    pin["sha256"] = "0" * 64
    with pytest.raises(FrozenRegistryError, match="sha256 mismatch"):
        verify_manifest_pin(example_dir=example, pin=pin)


def test_modern_assignment_uses_frozen_not_working_inventory_path():
    """Peak modern rows assign via frozen registry when example_dir is provided."""
    example = MODERN[0]
    registry = load_frozen_registry_from_example(example)
    assert registry is not None
    observations = load_jsonl(example / "observations.jsonl")
    for row in observations:
        acq = acquisition_row_from_observation(row)
        frozen = assign_regime_from_frozen_registry(acq, registry)
        assert frozen.assignment_status == "definitive"
        assert frozen.acquisition_regime_id in registry.regime_ids
