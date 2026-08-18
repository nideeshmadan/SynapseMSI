# Architecture

SynapseMSI reconstructs archived market observations into deterministic investigation artifacts.

```text
Archived Observations
        │
        ▼
Canonical Observations
        │
        ▼
Canonical Snapshots
        │
        ▼
Operational Episodes
        │
        ▼
Investigation Artifacts
```

Each stage is deterministic. Given the same archived observations, published methodology, and version pins, every downstream stage produces the same result.

**Archived Observations** are the archived evidence captured during market observation. Reconstruction is limited to this archived evidence and does not infer information that was never observed.

**Canonical Observations** normalize archived observations into a consistent representation while preserving evidence lineage. Field definitions are specified in the [Canonical Field Specification](../specifications/canonical-field-specification.md).

**Canonical Snapshots** group canonical observations into a reconstructed view of market state at a single observation time. Their structure is defined in the [Canonical Snapshot Schema](../schemas/canonical_snapshot.md).

**Operational Episodes** are bounded investigation windows identified by applying the published reconstruction methodology to canonical snapshots. The reconstruction methodology is defined in the [Reconstruction Standard](../specifications/reconstruction-standard.md).

**Investigation Artifacts** summarize operational episodes in a deterministic, human-readable form suitable for independent review. Their structure is defined in the [Investigation Report Schema](../schemas/investigation-report.md).

## Investigation Bundle

Each published reproducibility example consists of an investigation bundle that enables an independent reviewer to verify the published results.

Published examples are located under `examples/historical/<id>/` or `examples/modern/<id>/` (see [examples/README.md](../examples/README.md)). Each bundle contains:

* `investigation.json`
* `observations.jsonl`
* `observations.parquet`
* `provenance.json`
* `input_manifest.json`
* `report.md` (when a narrative report is published for that package)

The accompanying `scripts/reproduce_investigation.py` script deterministically reconstructs the published investigation from the bundled observations.

`observations.jsonl` is the normative observation representation. `observations.parquet` is a deterministic, typed analytical representation of the same logical observations for analytical tooling. Both formats contain the same logical observation set, while `input_manifest.json` records the hashes and metadata required to verify the published bundle. Their equivalence is verified by the repository's reproducibility test suite.

## Determinism

Given the same archived observations, reconstruction methodology version, canonical field specification, and published evidence, reconstruction produces identical outputs. This applies to canonical observations, canonical snapshots, derived metrics, operational episodes, and investigation artifacts.

An independent reviewer can reproduce a published investigation using the archived observations together with the recorded methodology version, canonical field specification, provenance, investigation window, and package-pinned evidence.

Reconstruction is limited to the archived evidence contained in the published package. The scope of conclusions that can and cannot be supported by that evidence is defined in [Reconstruction Boundaries](reconstruction-boundaries.md) and is not restated here.

## Related References

* [Canonical Field Specification](../specifications/canonical-field-specification.md)
* [Reconstruction Standard](../specifications/reconstruction-standard.md)
* [Provenance Standard](../specifications/provenance-standard.md)
* [Reconstruction Boundaries](reconstruction-boundaries.md)
