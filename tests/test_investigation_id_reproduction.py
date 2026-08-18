"""Published-package investigation_id reproduction (cluster_id = episode_id)."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from synapse_msi.ids import stable_investigation_id

ROOT = Path(__file__).resolve().parents[1]

FIXTURES = [
    "examples/modern/op_native_mark_000005",
    "examples/modern/op_stale_014639",
    "examples/historical/op_disagree_000244",
    "examples/historical/op_stale_000012",
    "examples/historical/op_consensus_000042",
]


def _published_episode_id(inv: dict, manifest: dict) -> str:
    source = inv.get("source") or {}
    return str(
        source.get("episode_id")
        or inv.get("episode_id")
        or manifest.get("episode_id")
    )


def _manual_id(instrument: str, start: str, end: str, cluster_id: str) -> str:
    payload = f"{instrument}|{start}|{end}|{cluster_id}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


@pytest.mark.parametrize("rel", FIXTURES)
def test_fixture_investigation_id_uses_episode_id_as_cluster_id(rel: str):
    example = ROOT / rel
    inv = json.loads((example / "investigation.json").read_text(encoding="utf-8"))
    manifest = json.loads((example / "input_manifest.json").read_text(encoding="utf-8"))
    episode_id = _published_episode_id(inv, manifest)
    expected = inv["investigation_id"]

    recomputed = stable_investigation_id(
        inv["instrument"],
        inv["window_start"],
        inv["window_end"],
        episode_id,
    )
    manual = _manual_id(
        inv["instrument"],
        inv["window_start"],
        inv["window_end"],
        episode_id,
    )
    assert recomputed == expected
    assert manual == expected
    assert re.fullmatch(r"[0-9a-f]{24}", expected)


def test_separator_order_and_encoding():
    instrument = "ETHUSDT_PERP"
    start = "2026-07-24T07:10:27.161814Z"
    end = "2026-07-24T07:11:03.966942Z"
    cluster = "op_native_mark_000005"
    payload = f"{instrument}|{start}|{end}|{cluster}"
    assert payload.count("|") == 3
    assert payload.encode("utf-8") == (
        b"ETHUSDT_PERP|2026-07-24T07:10:27.161814Z|"
        b"2026-07-24T07:11:03.966942Z|op_native_mark_000005"
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    assert digest == digest.lower()
    assert stable_investigation_id(instrument, start, end, cluster) == digest[:24]


def test_instrument_or_timestamp_mutation_changes_id():
    base = stable_investigation_id(
        "ETHUSDT_PERP",
        "2026-07-24T07:10:27.161814Z",
        "2026-07-24T07:11:03.966942Z",
        "op_native_mark_000005",
    )
    assert (
        stable_investigation_id(
            "ethusdt_perp",
            "2026-07-24T07:10:27.161814Z",
            "2026-07-24T07:11:03.966942Z",
            "op_native_mark_000005",
        )
        != base
    )
    assert (
        stable_investigation_id(
            "ETHUSDT_PERP",
            "2026-07-24T07:10:27.161815Z",
            "2026-07-24T07:11:03.966942Z",
            "op_native_mark_000005",
        )
        != base
    )
    assert (
        stable_investigation_id(
            "ETHUSDT_PERP",
            "2026-07-24T07:10:27.161814Z",
            "2026-07-24T07:11:03.966942Z",
            "different_episode",
        )
        != base
    )
