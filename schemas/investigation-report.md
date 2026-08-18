# Investigation Report Schema

This document defines the structure of SynapseMSI External Reconstruction investigation reports.

Field semantics are defined in the [Canonical Field Specification](../specifications/canonical-field-specification.md). Reconstruction algorithms are defined in the [Reconstruction Standard](../specifications/reconstruction-standard.md). Provenance semantics are defined in the [Provenance Standard](../specifications/provenance-standard.md). This document defines report structure only.

## Report Structure

A published investigation report may include the following sections:

* **Investigation Summary** — Investigation identifier, instrument, investigation window, and report version. For published reproducibility packages, `investigation_id` is the derived SHA-256 identity defined in [Reconstruction Standard §9](../specifications/reconstruction-standard.md#9-independent-reproduction-requirements) (`cluster_id` = published `episode_id`). Published freshness investigations additionally record `pre_entry_scan_timestamp`, `adoption_scan_timestamp`, and `peak_sequence` as defined in [Reconstruction Standard §6](../specifications/reconstruction-standard.md#6-operational-episode-methodology).
* **Reconstruction Metadata** — Methodology, schema, reconstruction, and evidence versions used during reproduction.
* **Investigation Trigger** — Reason the investigation was generated.
* **Investigation Scope** — Affected venues, investigation window, and summary metrics.
* **Evidence Reviewed** — Archived observations and evidence used during reconstruction.
* **Reconstructed Observations** — Findings supported by the archived evidence.
* **Peak Reconstructed Market State** — Representative reconstructed snapshot.
* **Acquisition Provenance** — Assignment status, linkage status, and comparability classification recorded in the accompanying `provenance.json`. Modern published packages additionally derive package-level provenance and comparability from the packaged observations together with the frozen acquisition-regime evidence pin recorded in `input_manifest.json`.
* **Investigation Timeline** — Chronological summary of the reconstructed investigation.
* **Historical Context** — Comparison with similar historical investigations, when applicable.
* **Additional Evidence Required for Attribution** — Information required to establish execution attribution or operational root cause beyond the archived evidence.
* **Interpretation** — Supported conclusions, limitations, and evidentiary boundaries.
* **Appendix** — Version information and supporting metadata.

Individual published investigation reports may omit sections that are not applicable.

## Versioning

Each published investigation report records the versions required for deterministic reproduction, including the report schema, reconstruction methodology, canonical field specification, provenance model, and any package-pinned evidence versions referenced by the investigation.

## Related Documentation

* [Canonical Field Specification](../specifications/canonical-field-specification.md)
* [Reconstruction Standard](../specifications/reconstruction-standard.md)
* [Provenance Standard](../specifications/provenance-standard.md)
* [Architecture](../docs/architecture.md)
