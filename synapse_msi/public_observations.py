"""Public observation JSONL ↔ Parquet conversion for Synapse MSI fixtures.

``observations.jsonl`` is the normative evidence source.
``observations.parquet`` is a deterministic analytical mirror of those rows.

Exact market quantities use fixed-precision Arrow ``decimal128`` types so
analytical readers receive numeric decimals rather than strings or binary
floats. Private storage locators and production infrastructure identifiers
are never emitted in the Parquet artifact.
"""

from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import pyarrow as pa
import pyarrow.parquet as pq

PUBLIC_OBSERVATIONS_SCHEMA_NAME = "synapse_msi_public_observations"
PUBLIC_OBSERVATIONS_SCHEMA_VERSION = "synapse_public_observations_v2"
ARTIFACT_ROLE = "observations_parquet"

# Stable column order for deterministic schemas (extras appended sorted).
CANONICAL_FIELD_ORDER: Tuple[str, ...] = (
    "acquisition",
    "archived_consensus_mark",
    "archived_disagreement_score",
    "ask_price",
    "bid_price",
    "canonical_timestamp_utc",
    "collector_received_at",
    "effective_observation_timestamp",
    "funding_rate",
    "instrument",
    "mark_price",
    "mid_price",
    "native_mark_price",
    "raw_linkage",
    "scan_timestamp",
    "sequence",
    "spread_bps",
    "staleness_ms",
    "usable",
    "venue",
    "venue_timestamp",
)

# Nested JSON objects stored as canonical JSON text in Parquet.
JSON_TEXT_FIELDS = frozenset({"acquisition", "raw_linkage"})

# Private-only locator / infrastructure fields — never emit in public Parquet.
PRIVATE_OBSERVATION_FIELDS = frozenset(
    {
        "source_snapshot_path",
        "source_snapshot_paths",
        "source_object_keys",
        "archive_cache",
    }
)

# ---------------------------------------------------------------------------
# Public decimal128 schema (precision, scale)
#
# Derived from the public canonical numeric rules in synapse_msi.decimals and
# methodology / ingest quantization — not from per-fixture digit mining:
#
#   * Price / USD quantities: public ingest quantum is Decimal("1e-12")
#     (12 fractional digits). Parquet storage uses scale 18 so exact
#     Decimal values from normative JSONL are preserved without Python float
#     and without requantizing evidence (requantize-to-1e-12 would alter
#     historical mid/mark strings and published investigation metrics).
#     Scale 18 is a fixed schema constant ≥ the 12-digit public quantum.
#   * Funding rates: methodology quantize_funding_rate → scale 8
#   * BPS / disagreement scores: methodology quantize_bps → scale 1
#   * Precision 38: full Arrow/Parquet decimal128 capacity (stable ceiling)
#
# Values are parsed via decimal.Decimal only. Trailing zeros are not
# semantically meaningful during equivalence checks.
# ---------------------------------------------------------------------------
DECIMAL128_PRECISION = 38
PRICE_DECIMAL_SCALE = 18
FUNDING_DECIMAL_SCALE = 8
BPS_DECIMAL_SCALE = 1
PUBLIC_PRICE_QUANTUM_SCALE = 12  # Decimal("1e-12") ingest / consensus width

PRICE_DECIMAL_TYPE = pa.decimal128(DECIMAL128_PRECISION, PRICE_DECIMAL_SCALE)
FUNDING_DECIMAL_TYPE = pa.decimal128(DECIMAL128_PRECISION, FUNDING_DECIMAL_SCALE)
BPS_DECIMAL_TYPE = pa.decimal128(DECIMAL128_PRECISION, BPS_DECIMAL_SCALE)

# Exact decimal market / archive fields exposed in public observations.
PRICE_DECIMAL_FIELDS = frozenset(
    {
        "bid_price",
        "ask_price",
        "mid_price",
        "mark_price",
        "native_mark_price",
        "archived_consensus_mark",
    }
)
FUNDING_DECIMAL_FIELDS = frozenset({"funding_rate"})
BPS_DECIMAL_FIELDS = frozenset({"spread_bps", "archived_disagreement_score"})
DECIMAL_FIELDS = PRICE_DECIMAL_FIELDS | FUNDING_DECIMAL_FIELDS | BPS_DECIMAL_FIELDS

_DISALLOWED_VALUE_PATTERNS = (
    re.compile(r"/Users/"),
    re.compile(r"/root/"),
    re.compile(r"s3://", re.IGNORECASE),
    re.compile(r"production-project-slug", re.IGNORECASE),
    re.compile(r"\bprod-v1\b"),
    re.compile(r"archive_cache"),
    re.compile(r"railway", re.IGNORECASE),
    re.compile(r"postgres(ql)?://", re.IGNORECASE),
    re.compile(r"\baws_", re.IGNORECASE),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strip_private_observation_fields(row: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in row.items() if key not in PRIVATE_OBSERVATION_FIELDS}


def observation_sort_key(row: Mapping[str, Any]) -> Tuple[str, int, str]:
    sequence = row.get("sequence")
    try:
        seq_key = int(sequence) if sequence is not None else -1
    except (TypeError, ValueError):
        seq_key = -1
    return (
        str(row.get("scan_timestamp") or ""),
        seq_key,
        str(row.get("venue") or ""),
    )


def canonical_field_names(rows: Sequence[Mapping[str, Any]]) -> List[str]:
    present = {key for row in rows for key in row.keys()}
    ordered = [name for name in CANONICAL_FIELD_ORDER if name in present]
    extras = sorted(present.difference(CANONICAL_FIELD_ORDER))
    return ordered + extras


def decimal_type_for_field(field: str) -> Optional[pa.DataType]:
    if field in PRICE_DECIMAL_FIELDS:
        return PRICE_DECIMAL_TYPE
    if field in FUNDING_DECIMAL_FIELDS:
        return FUNDING_DECIMAL_TYPE
    if field in BPS_DECIMAL_FIELDS:
        return BPS_DECIMAL_TYPE
    return None


def decimal_scale_for_field(field: str) -> Optional[int]:
    if field in PRICE_DECIMAL_FIELDS:
        return PRICE_DECIMAL_SCALE
    if field in FUNDING_DECIMAL_FIELDS:
        return FUNDING_DECIMAL_SCALE
    if field in BPS_DECIMAL_FIELDS:
        return BPS_DECIMAL_SCALE
    return None


def parse_exact_decimal(value: Any) -> Decimal:
    """Parse a public numeric value as Decimal without Python float."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise InvalidOperation("boolean is not a decimal market value")
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise InvalidOperation("empty decimal string")
        return Decimal(text)
    raise InvalidOperation(
        f"refusing non-decimal exact numeric input of type {type(value).__name__}"
    )


def to_schema_decimal(field: str, value: Any) -> Optional[Decimal]:
    """
    Convert a JSONL cell to the field's public decimal128 scale.

    Nulls are preserved. Values are parsed via Decimal only. The value must
    equal its representation at the field's canonical scale (padding allowed;
    rounding that changes the exact decimal value is rejected).
    """
    if value is None:
        return None
    scale = decimal_scale_for_field(field)
    if scale is None:
        raise ValueError(f"{field}: not a decimal-typed public field")
    parsed = parse_exact_decimal(value)
    quantizer = Decimal(10) ** -scale
    scaled = parsed.quantize(quantizer)
    if scaled != parsed:
        raise ValueError(
            f"{field}: value {parsed!s} is not exactly representable at "
            f"decimal128({DECIMAL128_PRECISION},{scale}) without changing the "
            f"exact decimal (quantized={scaled!s}). JSONL remains normative; "
            f"fix the evidence string or widen the public scale."
        )
    return scaled


def normalize_decimal_value(field: str, value: Any) -> Optional[Decimal]:
    """Normalize a JSONL or Parquet cell to an exact Decimal for comparison."""
    if value is None:
        return None
    if field in DECIMAL_FIELDS:
        return parse_exact_decimal(value)
    raise ValueError(f"{field}: not a decimal-typed public field")


def _assert_public_value(field: str, value: Any, *, context: str) -> None:
    if value is None:
        return
    if field in PRIVATE_OBSERVATION_FIELDS:
        raise ValueError(f"{context}: private field not allowed: {field}")
    if isinstance(value, Mapping):
        for nested_key, nested_value in value.items():
            _assert_public_value(str(nested_key), nested_value, context=f"{context}.{field}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _assert_public_value(field, item, context=f"{context}.{field}[{index}]")
        return
    if isinstance(value, str):
        for pattern in _DISALLOWED_VALUE_PATTERNS:
            if pattern.search(value):
                raise ValueError(
                    f"{context}: disallowed infrastructure value in field "
                    f"{field!r}: {value!r}"
                )


def load_canonical_public_observation_rows(jsonl_path: Path) -> List[Dict[str, Any]]:
    """Load normative JSONL rows and project to sanitized public observation rows."""
    rows: List[Dict[str, Any]] = []
    for line_no, line in enumerate(
        Path(jsonl_path).read_text(encoding="utf-8").splitlines(), start=1
    ):
        text = line.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{jsonl_path}:{line_no}: invalid JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"{jsonl_path}:{line_no}: observation row must be an object")
        public_row = strip_private_observation_fields(payload)
        for key, value in public_row.items():
            _assert_public_value(key, value, context=f"{jsonl_path}:{line_no}")
        rows.append(public_row)
    rows.sort(key=observation_sort_key)
    return rows


def write_public_observation_jsonl(rows: Sequence[Mapping[str, Any]], path: Path) -> Path:
    path = Path(path)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            payload = strip_private_observation_fields(row)
            handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
    return path


def _parquet_cell(field: str, value: Any) -> Any:
    if value is None:
        return None
    if field in DECIMAL_FIELDS:
        return to_schema_decimal(field, value)
    if field in JSON_TEXT_FIELDS:
        if isinstance(value, str):
            parsed = json.loads(value)
            return json.dumps(parsed, sort_keys=True, separators=(",", ":"))
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return value


def _arrow_type_for_field(field: str) -> pa.DataType:
    decimal_type = decimal_type_for_field(field)
    if decimal_type is not None:
        return decimal_type
    if field in JSON_TEXT_FIELDS:
        return pa.string()
    if field == "sequence":
        return pa.int64()
    if field == "usable":
        return pa.bool_()
    if field == "staleness_ms":
        # Duration metric from JSON number; not an exact market decimal.
        return pa.float64()
    return pa.string()


def build_public_observation_arrow_table(rows: Sequence[Mapping[str, Any]]) -> pa.Table:
    """
    Build a deterministic Arrow table from canonical public observation rows.

    Exact market quantities use fixed ``decimal128`` types. Nested
    ``acquisition`` is stored as canonical JSON text. ``staleness_ms`` remains
    float64 when JSONL stores a JSON number.
    """
    metadata = {
        b"schema_name": PUBLIC_OBSERVATIONS_SCHEMA_NAME.encode("utf-8"),
        b"schema_version": PUBLIC_OBSERVATIONS_SCHEMA_VERSION.encode("utf-8"),
        b"artifact_role": ARTIFACT_ROLE.encode("utf-8"),
        b"price_decimal": f"decimal128({DECIMAL128_PRECISION},{PRICE_DECIMAL_SCALE})".encode(
            "utf-8"
        ),
        b"price_quantum_scale": str(PUBLIC_PRICE_QUANTUM_SCALE).encode("utf-8"),
        b"funding_decimal": (
            f"decimal128({DECIMAL128_PRECISION},{FUNDING_DECIMAL_SCALE})".encode("utf-8")
        ),
        b"bps_decimal": f"decimal128({DECIMAL128_PRECISION},{BPS_DECIMAL_SCALE})".encode(
            "utf-8"
        ),
    }
    if not rows:
        return pa.Table.from_arrays([], schema=pa.schema([], metadata=metadata))

    field_names = canonical_field_names(rows)
    for banned in PRIVATE_OBSERVATION_FIELDS:
        if banned in field_names:
            raise ValueError(f"private field leaked into public rows: {banned}")

    arrays = []
    fields = []
    for name in field_names:
        raw_values = [row.get(name) for row in rows]
        cells = [_parquet_cell(name, value) for value in raw_values]
        for cell in cells:
            if isinstance(cell, str):
                _assert_public_value(name, cell, context="parquet-cell")
        arrow_type = _arrow_type_for_field(name)
        fields.append(pa.field(name, arrow_type, nullable=True))
        arrays.append(pa.array(cells, type=arrow_type))

    return pa.Table.from_arrays(arrays, schema=pa.schema(fields, metadata=metadata))


def write_public_observation_parquet(rows: Sequence[Mapping[str, Any]], path: Path) -> Path:
    path = Path(path)
    table = build_public_observation_arrow_table(rows)
    pq.write_table(
        table,
        where=str(path),
        compression="snappy",
        write_statistics=True,
        store_schema=True,
    )
    return path


def read_public_observation_parquet_rows(path: Path) -> List[Dict[str, Any]]:
    table = pq.read_table(path)
    rows = table.to_pylist()
    normalized: List[Dict[str, Any]] = []
    for row in rows:
        item = strip_private_observation_fields(row)
        for json_field in JSON_TEXT_FIELDS:
            cell = item.get(json_field)
            if isinstance(cell, str):
                item[json_field] = json.loads(cell)
        # Omit null-only keys so Parquet null padding does not invent fields.
        item = {key: value for key, value in item.items() if value is not None}
        normalized.append(item)
    normalized.sort(key=observation_sort_key)
    return normalized


def _normalize_acquisition(value: Any) -> Any:
    if isinstance(value, str):
        return json.loads(value)
    return value


def public_observation_rows_equal(
    left: Sequence[Mapping[str, Any]],
    right: Sequence[Mapping[str, Any]],
) -> List[str]:
    """Return human-readable diffs; empty means semantic equality."""
    diffs: List[str] = []
    if len(left) != len(right):
        diffs.append(f"row_count: left={len(left)} right={len(right)}")
        return diffs
    for index, (a, b) in enumerate(zip(left, right)):
        a_public = {
            key: value
            for key, value in strip_private_observation_fields(a).items()
            if value is not None
        }
        b_public = {
            key: value
            for key, value in strip_private_observation_fields(b).items()
            if value is not None
        }
        keys = sorted(set(a_public) | set(b_public))
        for key in keys:
            left_value = a_public.get(key)
            right_value = b_public.get(key)
            if key in JSON_TEXT_FIELDS:
                left_value = _normalize_acquisition(left_value)
                right_value = _normalize_acquisition(right_value)
            elif key in DECIMAL_FIELDS:
                try:
                    left_value = normalize_decimal_value(key, left_value)
                    right_value = normalize_decimal_value(key, right_value)
                except (InvalidOperation, ValueError) as exc:
                    diffs.append(f"row[{index}].{key}: decimal normalize error: {exc}")
                    continue
            if left_value != right_value:
                diffs.append(
                    f"row[{index}].{key}: left={left_value!r} right={right_value!r}"
                )
    return diffs


def verify_jsonl_parquet_equivalence(example_dir: Path) -> Dict[str, Any]:
    """
    Fail loudly if observations.jsonl and observations.parquet differ logically.

    JSONL remains the normative source; Parquet must mirror it.
    Decimal fields are compared as normalized exact Decimal values.
    """
    example_dir = Path(example_dir)
    jsonl_path = example_dir / "observations.jsonl"
    parquet_path = example_dir / "observations.parquet"
    if not jsonl_path.exists():
        raise FileNotFoundError(jsonl_path)
    if not parquet_path.exists():
        raise FileNotFoundError(parquet_path)

    jsonl_rows = load_canonical_public_observation_rows(jsonl_path)
    parquet_rows = read_public_observation_parquet_rows(parquet_path)
    diffs = public_observation_rows_equal(jsonl_rows, parquet_rows)
    if diffs:
        raise RuntimeError(
            f"JSONL ⇔ Parquet mismatch in {example_dir}:\n" + "\n".join(diffs)
        )

    table = pq.read_table(parquet_path)
    for field in table.schema:
        expected = decimal_type_for_field(field.name)
        if expected is not None and field.type != expected:
            raise RuntimeError(
                f"{parquet_path}: column {field.name!r} has type {field.type}, "
                f"expected {expected}"
            )
        if field.name in DECIMAL_FIELDS and not pa.types.is_decimal(field.type):
            raise RuntimeError(
                f"{parquet_path}: column {field.name!r} must be decimal, got {field.type}"
            )
        if field.name in DECIMAL_FIELDS and pa.types.is_floating(field.type):
            raise RuntimeError(
                f"{parquet_path}: column {field.name!r} must not be binary float"
            )

    # Binary / metadata hygiene for the Parquet artifact.
    raw = parquet_path.read_bytes()
    for marker in (
        b"/Users/",
        b"/root/",
        b"s3://",
        b"production-project-slug",
        b"prod-v1",
        b"archive_cache",
        b'"source_snapshot_path"',
    ):
        if marker in raw:
            raise RuntimeError(
                f"disallowed marker {marker!r} present in {parquet_path}"
            )

    metadata = table.schema.metadata or {}
    for key, value in metadata.items():
        blob = key + b"=" + value
        for marker in (b"/Users/", b"/root/", b"s3://", b"archive_cache"):
            if marker in blob:
                raise RuntimeError(
                    f"disallowed marker {marker!r} in Parquet metadata of {parquet_path}"
                )

    return {
        "example_dir": str(example_dir),
        "row_count": len(jsonl_rows),
        "fields": canonical_field_names(jsonl_rows),
        "equivalent": True,
        "observations_jsonl_sha256": sha256_file(jsonl_path),
        "observations_parquet_sha256": sha256_file(parquet_path),
        "price_decimal": f"decimal128({DECIMAL128_PRECISION},{PRICE_DECIMAL_SCALE})",
        "funding_decimal": f"decimal128({DECIMAL128_PRECISION},{FUNDING_DECIMAL_SCALE})",
        "bps_decimal": f"decimal128({DECIMAL128_PRECISION},{BPS_DECIMAL_SCALE})",
    }


def regenerate_observations_parquet_from_jsonl(
    example_dir: Path,
    *,
    rewrite_jsonl: bool = False,
) -> Dict[str, Any]:
    """
    Canonical conversion path:

    observations.jsonl (normative) -> sanitized public rows -> observations.parquet

    By default the JSONL file is left untouched.
    """
    example_dir = Path(example_dir)
    jsonl_path = example_dir / "observations.jsonl"
    parquet_path = example_dir / "observations.parquet"
    if not jsonl_path.exists():
        raise FileNotFoundError(jsonl_path)

    rows = load_canonical_public_observation_rows(jsonl_path)
    if rewrite_jsonl:
        write_public_observation_jsonl(rows, jsonl_path)
    write_public_observation_parquet(rows, parquet_path)
    return verify_jsonl_parquet_equivalence(example_dir)


def update_input_manifest_observation_hashes(example_dir: Path) -> Dict[str, Any]:
    """Update observation Parquet path/hash/row_count fields in input_manifest.json."""
    example_dir = Path(example_dir)
    manifest_path = example_dir / "input_manifest.json"
    manifest: Dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    jsonl_path = example_dir / "observations.jsonl"
    parquet_path = example_dir / "observations.parquet"
    rows = load_canonical_public_observation_rows(jsonl_path)

    manifest["observations_path"] = "observations.jsonl"
    manifest["observations_sha256"] = sha256_file(jsonl_path)
    manifest["observations_parquet_path"] = "observations.parquet"
    manifest["observations_parquet_sha256"] = sha256_file(parquet_path)
    manifest["observations_row_count"] = len(rows)

    # Keep other existing hashes in sync if those files are present.
    if (example_dir / "investigation.json").exists():
        manifest["published_investigation_path"] = manifest.get(
            "published_investigation_path", "investigation.json"
        )
        manifest["investigation_sha256"] = sha256_file(example_dir / "investigation.json")
    if (example_dir / "provenance.json").exists():
        manifest["provenance_sidecar_path"] = manifest.get(
            "provenance_sidecar_path", "provenance.json"
        )
        manifest["provenance_sha256"] = sha256_file(example_dir / "provenance.json")

    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "observations_parquet_path": manifest["observations_parquet_path"],
        "observations_parquet_sha256": manifest["observations_parquet_sha256"],
        "observations_row_count": manifest["observations_row_count"],
    }
