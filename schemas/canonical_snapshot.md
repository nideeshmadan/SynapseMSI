# Canonical Snapshot Schema

This document defines the structure of a canonical snapshot produced by SynapseMSI External Reconstruction.

Field semantics are defined in the [Canonical Field Specification](../specifications/canonical-field-specification.md). Reconstruction algorithms are defined in the [Reconstruction Standard](../specifications/reconstruction-standard.md). Provenance semantics are defined in the [Provenance Standard](../specifications/provenance-standard.md). This document defines snapshot structure only.

## Top-Level Structure

```json
{
  "instrument": "string",
  "consensus": {},
  "normalized": [],
  "l1_metrics": {},
  "meta": {},
  "engines": {},
  "traces": {},
  "raw": []
}
```

## Consensus

The `consensus` object contains reconstructed cross-venue values and derived metrics for the canonical snapshot.

Its field semantics are defined in the Canonical Field Specification. Consensus construction and derived metrics are defined in the Reconstruction Standard.

## Normalized Observations

The `normalized` array contains one canonical observation for each eligible venue represented in the reconstructed snapshot.

Field definitions are specified in the Canonical Field Specification.

## L1 Metrics

The `l1_metrics` object contains metrics derived from reconstructed Level 1 observations.

Metric definitions and reconstruction methodology are defined in the Reconstruction Standard.

## Metadata

The `meta` object contains the information required to identify, version, and reproduce a canonical snapshot.

Versioning and provenance semantics are defined in the Provenance Standard.

## Optional Sections

Canonical snapshots may also include the following optional sections:

* `engines`
* `traces`
* `raw`

These sections are not required to reproduce or interpret the published investigation artifacts.

## Related Documentation

* [Canonical Field Specification](../specifications/canonical-field-specification.md)
* [Reconstruction Standard](../specifications/reconstruction-standard.md)
* [Provenance Standard](../specifications/provenance-standard.md)
* [Architecture](../docs/architecture.md)
