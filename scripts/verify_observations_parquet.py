#!/usr/bin/env python3
"""Verify observations.jsonl ⇔ observations.parquet equivalence for all examples.

Fails with a non-zero exit code and explicit diffs on any mismatch.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from synapse_msi.public_observations import verify_jsonl_parquet_equivalence  # noqa: E402

EXAMPLES = (
    ROOT / "examples/historical/op_disagree_000244",
    ROOT / "examples/historical/op_stale_000012",
    ROOT / "examples/historical/op_consensus_000042",
    ROOT / "examples/modern/op_native_mark_000005",
    ROOT / "examples/modern/op_stale_014639",
)


def main() -> int:
    results: List[Dict[str, Any]] = []
    failures: List[str] = []
    for example_dir in EXAMPLES:
        try:
            result = verify_jsonl_parquet_equivalence(example_dir)
            results.append(result)
            print(f"OK {example_dir.name}: rows={result['row_count']} equivalent=true")
        except Exception as exc:  # noqa: BLE001 — surface all verification failures
            failures.append(f"{example_dir.name}: {exc}")
            print(f"FAIL {example_dir.name}: {exc}", file=sys.stderr)

    print(json.dumps({"verified": results, "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
