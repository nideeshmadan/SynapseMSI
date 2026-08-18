# Schema Reference

This directory defines the **structure** of SynapseMSI External Reconstruction artifacts.

Field semantics are defined in [canonical-field-specification.md](../specifications/canonical-field-specification.md). Reconstruction algorithms are defined in [reconstruction-standard.md](../specifications/reconstruction-standard.md). Provenance lineage is defined in [provenance-standard.md](../specifications/provenance-standard.md). This directory defines artifact structure only.

## Published Schemas

* **[Investigation Report](investigation-report.md)** — Structure of the investigation report artifact.
* **[Canonical Snapshot](canonical_snapshot.md)** — Structure of a reconstructed canonical snapshot.
* **[Acquisition-Regime Fixture Registry](acquisition-regime-fixture-registry.md)** — Structure of the package-pinned empirical acquisition-regime registry used to reproduce the committed modern public fixtures.

## Versioning

Schemas are versioned to preserve compatibility between published investigation artifacts and independent implementations. Each published investigation package records the schema version required for deterministic reproduction.

## Related Documentation

* [Architecture](../docs/architecture.md)
* [Reconstruction Boundaries](../docs/reconstruction-boundaries.md)
* [Specifications](../specifications/README.md)
* [Examples](../examples/README.md)
