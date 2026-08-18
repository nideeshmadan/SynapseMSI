"""JSONL/Parquet equivalence and public safety for reproducibility fixtures."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from synapse_msi.investigation_reproduction import (
    compare_freshness_episode,
    compare_published,
    load_jsonl,
    read_json,
    recompute_investigation_package,
)
from synapse_msi.public_observations import (
    BPS_DECIMAL_TYPE,
    FUNDING_DECIMAL_TYPE,
    PRICE_DECIMAL_FIELDS,
    PRICE_DECIMAL_TYPE,
    PRIVATE_OBSERVATION_FIELDS,
    load_canonical_public_observation_rows,
    public_observation_rows_equal,
    read_public_observation_parquet_rows,
    regenerate_observations_parquet_from_jsonl,
    sha256_file,
    verify_jsonl_parquet_equivalence,
    write_public_observation_parquet,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = [
    ROOT / "examples/historical/op_disagree_000244",
    ROOT / "examples/historical/op_stale_000012",
    ROOT / "examples/historical/op_consensus_000042",
    ROOT / "examples/modern/op_native_mark_000005",
    ROOT / "examples/modern/op_stale_014639",
]

DISALLOWED_MARKERS = (
    b"/Users/",
    b"/root/",
    b"s3://",
    b"aws_",
    b"postgres",
    b"archive_cache",
    b"source_object_keys",
    b'"source_snapshot_path"',  # observation-row locator field
    b"prod-v1",
    b"production-project-slug",
    b"CryptoSight",
)


def _assert_no_disallowed(raw: bytes) -> None:
    for marker in DISALLOWED_MARKERS:
        assert marker not in raw, f"disallowed marker present: {marker!r}"


@pytest.mark.parametrize("example_dir", EXAMPLES, ids=lambda p: p.name)
def test_jsonl_parquet_semantic_equivalence(example_dir: Path):
    result = verify_jsonl_parquet_equivalence(example_dir)
    assert result["equivalent"] is True
    assert result["row_count"] > 0
    jsonl_rows = load_canonical_public_observation_rows(example_dir / "observations.jsonl")
    parquet_rows = read_public_observation_parquet_rows(example_dir / "observations.parquet")
    assert len(jsonl_rows) == len(parquet_rows)
    assert public_observation_rows_equal(jsonl_rows, parquet_rows) == []
    for row in jsonl_rows:
        assert PRIVATE_OBSERVATION_FIELDS.isdisjoint(row.keys())
    for row in parquet_rows:
        assert PRIVATE_OBSERVATION_FIELDS.isdisjoint(row.keys())


@pytest.mark.parametrize("example_dir", EXAMPLES, ids=lambda p: p.name)
def test_parquet_schema_metadata_is_public_only(example_dir: Path):
    table = pq.read_table(example_dir / "observations.parquet")
    metadata = table.schema.metadata or {}
    assert metadata.get(b"schema_name") == b"synapse_msi_public_observations"
    assert metadata.get(b"schema_version") == b"synapse_public_observations_v2"
    assert metadata.get(b"artifact_role") == b"observations_parquet"
    assert metadata.get(b"price_decimal") == b"decimal128(38,18)"
    assert metadata.get(b"price_quantum_scale") == b"12"
    assert metadata.get(b"funding_decimal") == b"decimal128(38,8)"
    assert metadata.get(b"bps_decimal") == b"decimal128(38,1)"
    for field in table.schema:
        if field.name in PRICE_DECIMAL_FIELDS:
            assert field.type == PRICE_DECIMAL_TYPE
        elif field.name == "funding_rate":
            assert field.type == FUNDING_DECIMAL_TYPE
        elif field.name in {"spread_bps", "archived_disagreement_score"}:
            assert field.type == BPS_DECIMAL_TYPE
        assert not (
            field.name
            in PRICE_DECIMAL_FIELDS
            | {"funding_rate", "spread_bps", "archived_disagreement_score"}
            and (
                pa.types.is_string(field.type)
                or pa.types.is_floating(field.type)
            )
        )
    for key, value in metadata.items():
        blob = key + b"=" + value
        _assert_no_disallowed(blob)
    _assert_no_disallowed(Path(example_dir / "observations.parquet").read_bytes())
    _assert_no_disallowed(Path(example_dir / "observations.jsonl").read_bytes())


@pytest.mark.parametrize("example_dir", EXAMPLES, ids=lambda p: p.name)
def test_investigation_reproducible_from_jsonl_and_parquet_rows(example_dir: Path):
    published = read_json(example_dir / "investigation.json")
    episode_id = str((published.get("source") or {}).get("episode_id"))
    jsonl_rows = load_jsonl(example_dir / "observations.jsonl")
    parquet_rows = read_public_observation_parquet_rows(example_dir / "observations.parquet")

    from_jsonl, freshness_jsonl = recompute_investigation_package(
        jsonl_rows,
        published=published,
        episode_id=episode_id,
        example_dir=example_dir,
    )
    from_parquet, freshness_parquet = recompute_investigation_package(
        parquet_rows,
        published=published,
        episode_id=episode_id,
        example_dir=example_dir,
    )
    assert compare_published(published, from_jsonl) == []
    assert compare_published(published, from_parquet) == []
    if published.get("freshness_episode"):
        assert freshness_jsonl is not None and freshness_parquet is not None
        assert compare_freshness_episode(published, freshness_jsonl) == []
        assert compare_freshness_episode(published, freshness_parquet) == []
    assert from_jsonl.consensus_mark == from_parquet.consensus_mark
    assert from_jsonl.disagreement_score == from_parquet.disagreement_score


@pytest.mark.parametrize("example_dir", EXAMPLES, ids=lambda p: p.name)
def test_repeat_generation_is_semantically_stable(example_dir: Path, tmp_path: Path):
    rows = load_canonical_public_observation_rows(example_dir / "observations.jsonl")
    first = tmp_path / "a.parquet"
    second = tmp_path / "b.parquet"
    write_public_observation_parquet(rows, first)
    write_public_observation_parquet(rows, second)
    assert (
        public_observation_rows_equal(
            read_public_observation_parquet_rows(first),
            read_public_observation_parquet_rows(second),
        )
        == []
    )


@pytest.mark.parametrize("example_dir", EXAMPLES, ids=lambda p: p.name)
def test_input_manifest_lists_parquet_and_hashes(example_dir: Path):
    manifest = read_json(example_dir / "input_manifest.json")
    assert manifest["observations_sha256"] == sha256_file(example_dir / "observations.jsonl")
    assert manifest["observations_parquet_sha256"] == sha256_file(
        example_dir / "observations.parquet"
    )
    assert manifest["observations_parquet_path"] == "observations.parquet"
    assert manifest["observations_row_count"] == len(
        load_canonical_public_observation_rows(example_dir / "observations.jsonl")
    )
    assert manifest["investigation_sha256"] == sha256_file(example_dir / "investigation.json")


def test_bundle_public_artifacts_have_no_disallowed_markers():
    for example_dir in EXAMPLES:
        for name in (
            "observations.jsonl",
            "observations.parquet",
            "investigation.json",
            "provenance.json",
            "input_manifest.json",
        ):
            path = example_dir / name
            assert path.exists(), path
            _assert_no_disallowed(path.read_bytes())


def test_regenerate_script_round_trip(tmp_path: Path):
    # Regenerate into a temp copy so bundled JSONL fixtures stay untouched.
    source = EXAMPLES[0]
    work = tmp_path / source.name
    work.mkdir()
    for name in ("observations.jsonl", "observations.parquet"):
        (work / name).write_bytes((source / name).read_bytes())
    before = load_canonical_public_observation_rows(work / "observations.jsonl")
    before_jsonl_sha = sha256_file(work / "observations.jsonl")
    summary = regenerate_observations_parquet_from_jsonl(work, rewrite_jsonl=False)
    after = load_canonical_public_observation_rows(work / "observations.jsonl")
    assert sha256_file(work / "observations.jsonl") == before_jsonl_sha
    assert summary["row_count"] == len(before)
    assert public_observation_rows_equal(before, after) == []
    assert verify_jsonl_parquet_equivalence(work)["equivalent"] is True
