#!/usr/bin/env python3
"""Independently reproduce a published investigation from archived observations.

Uses only repository code, committed fixtures, and published methodology.
Exits 0 only on exact match of required fields.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from synapse_msi.historical_corpus.eligibility import (  # noqa: E402
    evaluate_artifact_comparability_eligibility,
)
from synapse_msi.historical_corpus.frozen_registry import (  # noqa: E402
    FrozenRegistryError,
    load_frozen_registry_from_example,
)
from synapse_msi.investigation_reproduction import (  # noqa: E402
    compare_freshness_episode,
    compare_published,
    format_venue_table,
    load_jsonl,
    read_json,
    recompute_investigation_package,
    sha256_file,
)


def _print(msg: str = "") -> None:
    print(msg, flush=True)


def reproduce(
    *,
    observations_path: Path,
    published_path: Path,
    provenance_path: Path,
    episode_id: Optional[str] = None,
    example_dir: Optional[Path] = None,
) -> int:
    observations = load_jsonl(observations_path)
    published = read_json(published_path)
    provenance = read_json(provenance_path)

    episode_id = episode_id or str(
        (published.get("source") or {}).get("episode_id")
        or published.get("episode_id")
        or "unknown_episode"
    )
    instrument = str(published["instrument"])
    window_start = str(published["window_start"])
    window_end = str(published["window_end"])

    _print("=== Investigation reproduction ===")
    _print(f"observations: {observations_path} sha256={sha256_file(observations_path)}")
    _print(f"published:    {published_path} sha256={sha256_file(published_path)}")
    _print(f"provenance:   {provenance_path} sha256={sha256_file(provenance_path)}")
    _print(f"episode_id:   {episode_id}")
    _print(f"instrument:   {instrument}")
    _print(f"window:       {window_start} -> {window_end}")
    _print()
    _print("Methodology references:")
    _print("  specifications/reconstruction-standard.md §3 Canonical observation selection")
    _print("  specifications/reconstruction-standard.md §4 Consensus methodology")
    _print("  specifications/reconstruction-standard.md §5 Disagreement methodology")
    _print("  specifications/reconstruction-standard.md §7 Deterministic reproducibility")
    _print("  specifications/reconstruction-standard.md §9 Independent reproduction requirements")
    _print("  specifications/provenance-standard.md §9 Published-package acquisition-regime classification")

    frozen = None
    if example_dir is not None:
        try:
            frozen = load_frozen_registry_from_example(example_dir)
        except FrozenRegistryError as exc:
            _print(f"REPRODUCTION FAILED: {exc}")
            return 1
    if frozen is not None:
        _print(
            "  Frozen acquisition-regime evidence: "
            f"{frozen.registry_id} / {frozen.registry_content_version} "
            f"sha256={frozen.sha256}"
        )
    else:
        _print(
            "  Working provenance registry: acquisition_provenance_working_registry_v1 "
            "(not a frozen normative registry; historical fail-closed path)"
        )
    _print()

    try:
        recomputed, freshness = recompute_investigation_package(
            observations,
            published=published,
            episode_id=episode_id,
            example_dir=example_dir,
            frozen_registry=frozen,
        )
    except (ValueError, FrozenRegistryError) as exc:
        _print(f"REPRODUCTION FAILED: {exc}")
        return 1

    _print("Venue reconstruction table:")
    _print(format_venue_table(recomputed.venue_table))
    _print()
    _print(f"Recomputed consensus mark:     {recomputed.consensus_mark}")
    _print(f"Recomputed disagreement:       {recomputed.disagreement_score}")
    _print(f"Published consensus mark:      {published.get('consensus_mark')}")
    _print(f"Published disagreement:        {published.get('disagreement_score')}")
    if freshness is not None:
        _print()
        _print("Freshness episode (recomputed from packaged sequence):")
        _print(f"  start:      {freshness.get('episode_start')}")
        _print(f"  end:        {freshness.get('episode_end')}")
        _print(f"  duration_s: {freshness.get('duration_seconds')}")
        _print(f"  peak_age_s: {freshness.get('peak_observation_age_seconds')}")
        _print(f"  peak_scan:  {freshness.get('peak_scan_timestamp')}")
        _print(f"  recovery_n: {freshness.get('recovery_snapshot_count')}")
        _print(f"  recovery_q: {freshness.get('recovery_qualified')}")
    _print(
        "Provenance assignment_status:  "
        f"{recomputed.provenance_classification.get('assignment_status')}"
    )
    _print(
        "Comparability eligibility:     "
        f"{recomputed.comparability_eligibility} "
        f"({recomputed.comparability_reason_code})"
    )
    _print()

    sidecar_decision = evaluate_artifact_comparability_eligibility(
        provenance,
        known_regime_ids=frozen.regime_ids if frozen is not None else None,
    )
    _print(
        "Sidecar eligibility recompute: "
        f"{sidecar_decision.comparability_eligibility} "
        f"({sidecar_decision.comparability_reason_code})"
    )
    if (
        sidecar_decision.comparability_eligibility
        != provenance.get("comparability_eligibility")
        or sidecar_decision.comparability_reason_code
        != provenance.get("comparability_reason_code")
    ):
        _print("ERROR: provenance sidecar stamp does not match evaluator recompute")
        return 2

    diffs = compare_published(published, recomputed)
    if freshness is not None:
        diffs.extend(compare_freshness_episode(published, freshness))
    # Also require sidecar eligibility fields match published investigation.
    if published.get("comparability_eligibility") != provenance.get(
        "comparability_eligibility"
    ):
        diffs.append(
            "published.comparability_eligibility != provenance.comparability_eligibility"
        )
    if published.get("comparability_reason_code") != provenance.get(
        "comparability_reason_code"
    ):
        diffs.append(
            "published.comparability_reason_code != provenance.comparability_reason_code"
        )

    if diffs:
        _print("REPRODUCTION FAILED")
        for item in diffs:
            _print(f"  DIFF {item}")
        return 1

    _print("REPRODUCTION VERIFIED")
    _print(f"Published consensus: {published.get('consensus_mark')}")
    _print(f"Recomputed consensus: {recomputed.consensus_mark}")
    _print(f"Published disagreement: {published.get('disagreement_score')}")
    _print(f"Recomputed disagreement: {recomputed.disagreement_score}")
    _print("Exact match: true")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--observations",
        type=Path,
        default=None,
        help="Archived observations JSONL",
    )
    parser.add_argument(
        "--published-investigation",
        type=Path,
        default=None,
        help="Published investigation JSON",
    )
    parser.add_argument(
        "--provenance-sidecar",
        type=Path,
        default=None,
        help="Acquisition-regime investigation provenance sidecar JSON",
    )
    parser.add_argument(
        "--episode-id",
        type=str,
        default=None,
        help="Episode id used for stable investigation_id (optional)",
    )
    parser.add_argument(
        "--example",
        type=Path,
        default=None,
        help="Convenience: directory containing observations.jsonl, investigation.json, provenance.json",
    )
    args = parser.parse_args(argv)

    if args.example is not None:
        example = args.example
        return reproduce(
            observations_path=example / "observations.jsonl",
            published_path=example / "investigation.json",
            provenance_path=example / "provenance.json",
            episode_id=args.episode_id,
            example_dir=example,
        )
    if not args.observations or not args.published_investigation or not args.provenance_sidecar:
        parser.error(
            "provide --example DIR or all of --observations, "
            "--published-investigation, and --provenance-sidecar"
        )
    return reproduce(
        observations_path=args.observations,
        published_path=args.published_investigation,
        provenance_path=args.provenance_sidecar,
        episode_id=args.episode_id,
    )


if __name__ == "__main__":
    raise SystemExit(main())
