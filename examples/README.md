# Examples

Independently reproducible investigation packages for SynapseMSI External Reconstruction.

The published examples are representative investigation packages rather than an exhaustive archive. Every package reproduces with exact-match equality using:

```bash
python scripts/reproduce_investigation.py --example <example-directory>
```

## Index

Status values correspond to the committed `provenance.json` sidecars.

| Example                 | Era        | Primary demonstration                     | Acquisition status (`linkage_status`) | Comparison status (`comparability_eligibility`) |
| ----------------------- | ---------- | ----------------------------------------- | ------------------------------------- | ----------------------------------------------- |
| `op_native_mark_000005` | Modern     | Native-mark field comparability           | `derived_from_preserved_lineage`      | `comparable_after_partition`                    |
| `op_stale_014639`       | Modern     | Bounded temporal freshness reconstruction | `derived_from_preserved_lineage`      | `comparable_after_partition`                    |
| `op_disagree_000244`    | Historical | Disagreement reproduction                 | `insufficient_raw_lineage`            | `excluded_fail_closed`                          |
| `op_stale_000012`       | Historical | Historical freshness reconstruction       | `insufficient_raw_lineage`            | `excluded_fail_closed`                          |
| `op_consensus_000042`   | Historical | Consensus-quality reconstruction          | `insufficient_raw_lineage`            | `excluded_fail_closed`                          |

Historical reason code (all three): `unknown_assignment`

Modern reason code (both): `mixed_regime_requires_partition`

## Directory Layout

```text
examples/
├── modern/       # preserved modern acquisition lineage
└── historical/   # unknown or insufficient acquisition lineage (fail-closed)
```

Each investigation package includes, where applicable:

* `report.md` — human-readable investigation summary
* `observations.jsonl` — normative observation representation
* `observations.parquet` — deterministic typed representation of the same logical observations
* `investigation.json` — published investigation artifact
* `provenance.json` — acquisition lineage and comparability sidecar
* `input_manifest.json` — input hashes and bundle metadata

## Reproducing an Example

```bash
python scripts/reproduce_investigation.py --example examples/modern/op_native_mark_000005
python scripts/reproduce_investigation.py --example examples/modern/op_stale_014639
python scripts/reproduce_investigation.py --example examples/historical/op_disagree_000244
python scripts/reproduce_investigation.py --example examples/historical/op_stale_000012
python scripts/reproduce_investigation.py --example examples/historical/op_consensus_000042
```

Every successful reproduction ends with:

```text
REPRODUCTION VERIFIED
Exact match: true
```

## Modern versus Historical

The repository intentionally publishes both modern and historical investigation packages because they demonstrate different properties of the reconstruction methodology.

* **Modern** packages demonstrate deterministic reconstruction with preserved acquisition lineage, field-level provenance, and acquisition-sensitive comparability where supported.
* **Historical** packages demonstrate deterministic reconstruction under incomplete historical acquisition lineage. Investigation metrics remain reproducible, while acquisition-sensitive comparisons intentionally remain fail-closed rather than relying on inferred historical provenance.

The historical packages are not deprecated or lower quality. Their retained uncertainty is part of the published evidence and demonstrates that SynapseMSI preserves unknown acquisition lineage rather than retroactively assigning it.

## Related References

* [modern/README.md](modern/README.md)
* [historical/README.md](historical/README.md)
* [../docs/investigation-reproducibility.md](../docs/investigation-reproducibility.md)
* [../specifications/README.md](../specifications/README.md)
