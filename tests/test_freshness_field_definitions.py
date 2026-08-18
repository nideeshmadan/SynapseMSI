"""Normative venue_staleness package field definitions (pre_entry, adoption, peak_sequence)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from synapse_msi.freshness_episode import detect_venue_staleness_episode


def _z(ts: str) -> str:
    """Match detector output normalization (drop trailing .000000)."""
    if ts.endswith(".000000Z"):
        return ts[: -len(".000000Z")] + "Z"
    return ts


def _row(
    *,
    scan: str,
    sequence: int,
    venue_ts: str,
    usable: bool = True,
    venue: str = "binance",
    raw_row_id: Optional[str] = None,
) -> Dict[str, Any]:
    rid = raw_row_id or f"{venue}-{sequence}"
    return {
        "venue": venue,
        "instrument": "ETHUSDT_PERP",
        "scan_timestamp": scan,
        "canonical_timestamp_utc": scan,
        "sequence": sequence,
        "venue_timestamp": venue_ts,
        "effective_observation_timestamp": venue_ts,
        "usable": usable,
        "mark_price": "100.0",
        "raw_linkage": {
            "linkage_status": "exact_unique",
            "raw_row_id": rid,
            "snapshot_sequence": sequence,
        },
    }


def _quad(scan: str, sequence: int, binance_ts: str, binance_usable: bool = True) -> List[Dict[str, Any]]:
    """Four-venue snapshot; only Binance ages are material for the detector."""
    rows = [
        _row(scan=scan, sequence=sequence, venue_ts=binance_ts, usable=binance_usable, venue="binance"),
    ]
    for venue in ("bybit", "hyperliquid", "okx"):
        rows.append(
            _row(
                scan=scan,
                sequence=sequence,
                venue_ts=scan,  # fresh reference venues
                usable=True,
                venue=venue,
            )
        )
    return rows


def test_pre_entry_is_last_non_stale_before_entry():
    # Ages for binance relative to scan (threshold 60s):
    # scan0: age 10 (healthy) -> pre_entry candidate
    # scan1: age 70 (entry)
    # then recover with five healthy
    obs: List[Dict[str, Any]] = []
    obs += _quad("2026-07-21T08:00:00.000000Z", 1, "2026-07-21T07:59:50.000000Z")  # age 10
    obs += _quad("2026-07-21T08:01:00.000000Z", 2, "2026-07-21T07:59:50.000000Z")  # age 70 entry
    # recovery: keep binance fresh
    for i, sec in enumerate([2, 3, 4, 5, 6], start=3):
        scan = f"2026-07-21T08:01:{sec:02d}.000000Z"
        obs += _quad(scan, i, scan)
    result = detect_venue_staleness_episode(obs, affected_venue="binance")
    assert result.pre_entry_scan_timestamp == _z("2026-07-21T08:00:00.000000Z")
    assert result.episode_start == _z("2026-07-21T08:01:00.000000Z")


def test_pre_entry_null_when_entry_on_first_scan():
    obs: List[Dict[str, Any]] = []
    # First scan already stale
    obs += _quad("2026-07-21T08:01:00.000000Z", 1, "2026-07-21T07:59:50.000000Z")  # age 70
    for i, sec in enumerate([2, 3, 4, 5, 6], start=2):
        scan = f"2026-07-21T08:01:{sec:02d}.000000Z"
        obs += _quad(scan, i, scan)
    result = detect_venue_staleness_episode(obs, affected_venue="binance")
    assert result.pre_entry_scan_timestamp is None
    assert result.episode_start == _z("2026-07-21T08:01:00.000000Z")


def test_adoption_first_in_episode_venue_timestamp_change():
    obs: List[Dict[str, Any]] = []
    # pre-entry healthy
    obs += _quad("2026-07-21T08:00:00.000000Z", 1, "2026-07-21T07:59:50.000000Z")
    # entry stale on venue_ts A
    obs += _quad("2026-07-21T08:01:00.000000Z", 2, "2026-07-21T07:59:50.000000Z")
    # still A (no adoption)
    obs += _quad("2026-07-21T08:01:10.000000Z", 3, "2026-07-21T07:59:50.000000Z")
    # first change -> adoption
    obs += _quad("2026-07-21T08:01:20.000000Z", 4, "2026-07-21T08:01:15.000000Z")
    # later change must not move adoption
    obs += _quad("2026-07-21T08:01:30.000000Z", 5, "2026-07-21T08:01:25.000000Z")
    # recover with five healthy on latest ts
    for i, sec in enumerate([40, 41, 42, 43, 44], start=6):
        scan = f"2026-07-21T08:01:{sec:02d}.000000Z"
        obs += _quad(scan, i, scan)
    result = detect_venue_staleness_episode(obs, affected_venue="binance")
    assert result.adoption_scan_timestamp == _z("2026-07-21T08:01:20.000000Z")


def test_unchanged_venue_timestamps_do_not_count_as_adoption():
    """In-episode repeats of the entry venue timestamp are not adoption.

    The first later change (here, the first recovery scan) becomes adoption; earlier
    unchanged stale scans must not.
    """
    obs: List[Dict[str, Any]] = []
    obs += _quad("2026-07-21T08:00:00.000000Z", 1, "2026-07-21T07:59:50.000000Z")
    obs += _quad("2026-07-21T08:01:00.000000Z", 2, "2026-07-21T07:59:50.000000Z")
    for i, sec in enumerate([10, 20, 30], start=3):
        obs += _quad(
            f"2026-07-21T08:01:{sec:02d}.000000Z",
            i,
            "2026-07-21T07:59:50.000000Z",
        )
    for i, sec in enumerate([40, 41, 42, 43, 44], start=6):
        scan = f"2026-07-21T08:01:{sec:02d}.000000Z"
        obs += _quad(scan, i, scan)
    result = detect_venue_staleness_episode(obs, affected_venue="binance")
    assert result.adoption_scan_timestamp == _z("2026-07-21T08:01:40.000000Z")
    assert result.adoption_scan_timestamp != _z("2026-07-21T08:01:10.000000Z")
    assert result.adoption_scan_timestamp != _z("2026-07-21T08:01:20.000000Z")
    assert result.adoption_scan_timestamp != _z("2026-07-21T08:01:30.000000Z")


def test_peak_sequence_uses_supplied_sequence_and_strict_greater_tiebreak():
    obs: List[Dict[str, Any]] = []
    obs += _quad("2026-07-21T08:00:00.000000Z", 10, "2026-07-21T07:59:50.000000Z")
    # entry age 70
    obs += _quad("2026-07-21T08:01:00.000000Z", 20, "2026-07-21T07:59:50.000000Z")
    # equal age 70 later — must NOT replace peak (strict >)
    obs += _quad("2026-07-21T08:01:10.000000Z", 21, "2026-07-21T08:00:00.000000Z")  # age 70
    # larger age 100 — replaces peak/sequence
    obs += _quad("2026-07-21T08:02:00.000000Z", 30, "2026-07-21T08:00:20.000000Z")  # age 100
    for i, sec in enumerate([10, 11, 12, 13, 14], start=31):
        scan = f"2026-07-21T08:03:{sec:02d}.000000Z"
        obs += _quad(scan, i, scan)
    result = detect_venue_staleness_episode(obs, affected_venue="binance")
    assert result.peak_sequence == 30
    assert result.peak_scan_timestamp == _z("2026-07-21T08:02:00.000000Z")
    assert result.peak_observation_age_seconds == 100.0


def test_equal_peak_ages_retain_earlier_peak_sequence():
    obs: List[Dict[str, Any]] = []
    obs += _quad("2026-07-21T08:00:00.000000Z", 1, "2026-07-21T07:59:50.000000Z")
    obs += _quad("2026-07-21T08:01:00.000000Z", 5, "2026-07-21T07:59:50.000000Z")  # age 70 peak
    obs += _quad("2026-07-21T08:01:20.000000Z", 6, "2026-07-21T08:00:10.000000Z")  # age 70 tie
    for i, sec in enumerate([30, 31, 32, 33, 34], start=7):
        scan = f"2026-07-21T08:01:{sec:02d}.000000Z"
        obs += _quad(scan, i, scan)
    result = detect_venue_staleness_episode(obs, affected_venue="binance")
    assert result.peak_sequence == 5
    assert result.peak_scan_timestamp == _z("2026-07-21T08:01:00.000000Z")
