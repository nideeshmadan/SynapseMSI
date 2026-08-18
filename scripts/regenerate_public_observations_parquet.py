#!/usr/bin/env python3
"""Regenerate observations.parquet from normative observations.jsonl fixtures.

Does not modify investigation semantics, provenance, or JSONL evidence contents.
Only rewrites observations.parquet and updates observation hash fields in
input_manifest.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from synapse_msi.public_observations import (  # noqa: E402
    regenerate_observations_parquet_from_jsonl,
    update_input_manifest_observation_hashes,
)

EXAMPLES = (
    ROOT / "examples/historical/op_disagree_000244",
    ROOT / "examples/historical/op_stale_000012",
    ROOT / "examples/historical/op_consensus_000042",
    ROOT / "examples/modern/op_native_mark_000005",
    ROOT / "examples/modern/op_stale_014639",
)


def main() -> int:
    summaries: List[Dict[str, Any]] = []
    for example_dir in EXAMPLES:
        if not example_dir.is_dir():
            raise SystemExit(f"missing example directory: {example_dir}")
        summary = regenerate_observations_parquet_from_jsonl(
            example_dir,
            rewrite_jsonl=False,
        )
        manifest_update = update_input_manifest_observation_hashes(example_dir)
        summary.update(manifest_update)
        summaries.append(summary)
        print(
            f"OK {example_dir.name}: rows={summary['row_count']} "
            f"parquet_sha256={summary['observations_parquet_sha256']}"
        )
    print(json.dumps({"examples": summaries}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
