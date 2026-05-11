#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import pandas as pd

STRICT_SYNC_MS = 500
STRICT_AGE_MS = 1000


def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(path)

    if suffix == ".parquet":
        try:
            return pd.read_parquet(path)
        except Exception as exc:
            print("Warning: pandas/pyarrow failed to read parquet; retrying with DuckDB...")
            print(f"Original error: {type(exc).__name__}: {exc}")

            safe_path = str(path.resolve()).replace("'", "''")

            return duckdb.sql(
                f"SELECT * FROM read_parquet('{safe_path}')"
            ).df()

    raise ValueError("Unsupported file type. Use .csv or .parquet")


def validate(df: pd.DataFrame) -> pd.DataFrame:
    required_columns = [
        "sync_gap_ms",
    "best_pair_age_ms",
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    out = df.copy()

    out["synapse_valid"] = (
        (out["sync_gap_ms"] <= STRICT_SYNC_MS)
        &
        (out["best_pair_age_ms"] <= STRICT_AGE_MS)
    )

    return out


def write_report(path: Path, df: pd.DataFrame) -> None:
    total = len(df)

    valid = int(df["synapse_valid"].sum())

    invalid = total - valid

    invalidation_rate = invalid / total if total else 0.0

    avg_sync = df["sync_gap_ms"].mean()
    med_sync = df["sync_gap_ms"].median()

    avg_age = df["best_pair_age_ms"].mean()
    med_age = df["best_pair_age_ms"].median()

    if invalidation_rate > 0.75:
        assessment = "SEVERE temporal degradation"

    elif invalidation_rate > 0.25:
        assessment = "MATERIAL temporal degradation"

    else:
        assessment = "MODERATE/LOW temporal degradation"

    print("=" * 60)
    print("SYNAPSE MARKET-STATE INTEGRITY REPORT")
    print("=" * 60)

    print(f"File: {path}")
    print(f"Rows Analyzed: {total:,}")

    print(f"Valid States: {valid:,}")
    print(f"Invalidated States: {invalid:,}")

    print(f"Invalidation Rate: {invalidation_rate:.1%}")

    print("Temporal Metrics:")
    print(f"   Average Sync Gap: {avg_sync:,.1f}ms")
    print(f"   Median Sync Gap: {med_sync:,.1f}ms")

    print(f"   Average Best Pair Age: {avg_age:,.1f}ms")
    print(f"   Median Best Pair Age: {med_age:,.1f}ms")

    print("Strict Policy Thresholds:")
    print(f"   Sync Gap: ≤ {STRICT_SYNC_MS}ms")
    print(f"   Best Pair Age: ≤ {STRICT_AGE_MS}ms")

    print(f"Assessment: {assessment}")

    print("=" * 60)

    outputs = Path("outputs")
    outputs.mkdir(exist_ok=True)

    report = f"""# Synapse Market-State Integrity Report

## Input

- File: `{path}`
- Rows analyzed: {total:,}

## Results

- Valid states: {valid:,}
- Invalidated states: {invalid:,}
- Invalidation rate: {invalidation_rate:.1%}

## Temporal Metrics

- Average sync gap: {avg_sync:,.1f}ms
- Median sync gap: {med_sync:,.1f}ms

- Average best pair age: {avg_age:,.1f}ms
- Median best pair age: {med_age:,.1f}ms

## Strict Policy

- sync_gap_ms <= {STRICT_SYNC_MS}
- best_pair_age_ms <= {STRICT_AGE_MS}

## Assessment

{assessment}
"""

    report_path = outputs / "integrity_report.md"

    report_path.write_text(report)

    invalid_examples = df.loc[
        ~df["synapse_valid"]
    ].head(50)

    invalid_examples.to_csv(
        outputs / "invalidated_examples.csv",
        index=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate temporal coherence of "
            "cross-venue market-state datasets."
        )
    )

    parser.add_argument(
        "path",
        help="Path to .csv or .parquet dataset",
    )

    args = parser.parse_args()

    path = Path(args.path)

    print(f"Loading data from: {path}")

    df = load_data(path)

    print(f"Loaded {len(df):,} rows")

    validated = validate(df)

    write_report(path, validated)

    print("Validation complete!")


if __name__ == "__main__":
    main()
