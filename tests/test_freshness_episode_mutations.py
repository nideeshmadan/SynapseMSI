"""Negative mutation tests for bounded freshness temporal reproduction."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from synapse_msi.freshness_episode import detect_venue_staleness_episode
from synapse_msi.investigation_reproduction import (
    compare_freshness_episode,
    load_jsonl,
    read_json,
    recompute_investigation_package,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/modern/op_stale_014639"


@pytest.fixture(scope="module")
def package():
    observations = load_jsonl(EXAMPLE / "observations.jsonl")
    published = read_json(EXAMPLE / "investigation.json")
    return observations, published


def test_baseline_freshness_reproduces(package):
    observations, published = package
    recomputed, freshness = recompute_investigation_package(
        observations,
        published=published,
        episode_id="op_stale_014639",
        example_dir=EXAMPLE,
    )
    assert freshness is not None
    assert compare_freshness_episode(published, freshness) == []
    assert recomputed.consensus_mark == str(published["consensus_mark"])
    assert recomputed.disagreement_score == str(published["disagreement_score"])


def test_removing_entry_snapshot_fails(package):
    observations, published = package
    entry = published["freshness_episode"]["episode_start"]
    mutated = [
        row for row in observations if str(row.get("scan_timestamp")) != entry
    ]
    _, freshness = recompute_investigation_package(
        mutated,
        published=published,
        episode_id="op_stale_014639",
        example_dir=EXAMPLE,
    )
    assert freshness is not None
    diffs = compare_freshness_episode(published, freshness)
    assert any("episode_start" in d for d in diffs)


def test_reordering_timestamps_fails_match(package):
    observations, published = package
    mutated = copy.deepcopy(observations)
    # Swap two distinct scan timestamps while keeping sequences.
    scans = sorted({row["scan_timestamp"] for row in mutated})
    a, b = scans[0], scans[-1]
    for row in mutated:
        if row["scan_timestamp"] == a:
            row["scan_timestamp"] = b
            row["canonical_timestamp_utc"] = b
        elif row["scan_timestamp"] == b:
            row["scan_timestamp"] = a
            row["canonical_timestamp_utc"] = a
    try:
        _, freshness = recompute_investigation_package(
            mutated,
            published=published,
            episode_id="op_stale_014639",
            example_dir=EXAMPLE,
        )
    except ValueError:
        return
    assert freshness is not None
    diffs = compare_freshness_episode(published, freshness)
    assert diffs, "reordered timestamps must not match published freshness bounds"


def test_altering_peak_observation_timestamp_fails(package):
    observations, published = package
    peak_scan = published["freshness_episode"]["peak_scan_timestamp"]
    mutated = copy.deepcopy(observations)
    for row in mutated:
        if (
            row.get("scan_timestamp") == peak_scan
            and row.get("venue") == "binance"
        ):
            row["venue_timestamp"] = "2026-07-21T08:55:48.911654+00:00"
            row["effective_observation_timestamp"] = row["venue_timestamp"]
    _, freshness = recompute_investigation_package(
        mutated,
        published=published,
        episode_id="op_stale_014639",
        example_dir=EXAMPLE,
    )
    assert freshness is not None
    diffs = compare_freshness_episode(published, freshness)
    assert any("peak_observation_age_seconds" in d for d in diffs)


def test_altering_peak_age_input_via_scan_fails(package):
    observations, published = package
    peak_scan = published["freshness_episode"]["peak_scan_timestamp"]
    mutated = copy.deepcopy(observations)
    for row in mutated:
        if row.get("scan_timestamp") == peak_scan:
            row["scan_timestamp"] = "2026-07-21T08:56:00.000000Z"
            row["canonical_timestamp_utc"] = "2026-07-21T08:56:00.000000Z"
    _, freshness = recompute_investigation_package(
        mutated,
        published=published,
        episode_id="op_stale_014639",
        example_dir=EXAMPLE,
    )
    assert freshness is not None
    diffs = compare_freshness_episode(published, freshness)
    assert any("peak" in d for d in diffs)


def test_removing_recovery_observation_fails(package):
    observations, published = package
    recovery_start = published["freshness_episode"]["recovery_start"]
    mutated = [
        row
        for row in observations
        if not (
            str(row.get("scan_timestamp")) == recovery_start
            and row.get("venue") == "binance"
        )
    ]
    # Removing one recovery healthy snap leaves only four consecutive healthies.
    with pytest.raises(ValueError, match="missing affected venue|closed venue_staleness|do not contain"):
        detect_venue_staleness_episode(mutated, affected_venue="binance")


def test_only_four_healthy_recovery_snapshots_fails(package):
    observations, published = package
    end = published["freshness_episode"]["episode_end"]
    mutated = [
        row for row in observations if str(row.get("scan_timestamp")) != end
    ]
    with pytest.raises(ValueError, match="closed venue_staleness|do not contain"):
        detect_venue_staleness_episode(mutated, affected_venue="binance")


def test_duplicate_raw_linkage_fails(package):
    observations, _published = package
    mutated = copy.deepcopy(observations)
    # Duplicate an entire (sequence, venue) row.
    mutated.append(copy.deepcopy(mutated[0]))
    with pytest.raises(ValueError, match="duplicate_snapshot_venue_linkage"):
        detect_venue_staleness_episode(mutated, affected_venue="binance")


def test_missing_raw_row_id_fails(package):
    observations, _published = package
    mutated = copy.deepcopy(observations)
    for row in mutated:
        if row.get("venue") == "binance":
            row["raw_linkage"] = {
                "linkage_status": "exact_unique",
                "snapshot_sequence": row.get("sequence"),
            }
            if isinstance(row.get("acquisition"), dict):
                row["acquisition"].pop("raw_row_id", None)
            break
    with pytest.raises(ValueError, match="missing_raw_row_id"):
        detect_venue_staleness_episode(mutated, affected_venue="binance")


def test_temporal_usability_vs_native_mark_eligibility(package):
    """Freshness may use temporally usable venues that are native-mark ineligible."""
    observations, published = package
    recomputed, freshness = recompute_investigation_package(
        observations,
        published=published,
        episode_id="op_stale_014639",
        example_dir=EXAMPLE,
    )
    assert freshness is not None
    assert compare_freshness_episode(published, freshness) == []

    affected = published["freshness_episode"]["affected_venue"]
    assert affected == "binance"

    peak_scan = published["freshness_episode"]["peak_scan_timestamp"]
    peak_rows = [
        row
        for row in observations
        if str(row.get("scan_timestamp", "")).replace("+00:00", "Z").startswith(
            peak_scan.replace("+00:00", "Z")
        )
    ]
    assert {row["venue"] for row in peak_rows} == {
        "binance",
        "bybit",
        "hyperliquid",
        "okx",
    }
    # Temporal usability for freshness: all four peak rows are usable.
    assert all(bool(row.get("usable", True)) for row in peak_rows)
    temporal_reference_venues = sorted(
        row["venue"] for row in peak_rows if row["venue"] != affected
    )
    assert temporal_reference_venues == ["bybit", "hyperliquid", "okx"]

    # Native-mark consensus/disagreement: Binance and Bybit only.
    assert list(recomputed.included_venues) == ["binance", "bybit"]
    assert recomputed.excluded_venues == {
        "hyperliquid": "missing_or_zero_mark_price",
        "okx": "missing_or_zero_mark_price",
    }
    by_venue = {row.venue: row for row in recomputed.venue_table}
    assert by_venue["binance"].included is True
    assert by_venue["bybit"].included is True
    assert by_venue["hyperliquid"].included is False
    assert by_venue["okx"].included is False
    assert by_venue["hyperliquid"].exclusion_reason == "missing_or_zero_mark_price"
    assert by_venue["okx"].exclusion_reason == "missing_or_zero_mark_price"
    assert by_venue["hyperliquid"].consensus_input_value is None
    assert by_venue["okx"].consensus_input_value is None

    assert recomputed.consensus_mark == str(published["consensus_mark"])
    assert recomputed.disagreement_score == str(published["disagreement_score"])
    assert recomputed.consensus_mark == "1939.61"
    assert recomputed.disagreement_score == "1.8"
