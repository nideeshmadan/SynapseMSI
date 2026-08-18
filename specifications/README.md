# Specifications

This directory contains the **normative** SynapseMSI External Reconstruction specifications. These documents define the required field semantics, reconstruction algorithms, provenance model, and conformance requirements. The published reference package implements a subset of these specifications; the package does not define them.

## Normative versus explanatory

| Kind | Location | Role |
|------|----------|------|
| **Normative specifications** | `specifications/` | Define required methodology using MUST, MUST NOT, REQUIRED, SHALL, and SHOULD. |
| **Explanatory documentation** | `docs/` | Explain architecture, reconstruction boundaries, historical acquisition regimes, and reproducibility. |

Explanatory documentation does not create normative requirements. If explanatory documentation conflicts with a specification on field semantics, reconstruction algorithms, provenance, or conformance, the specification is authoritative.

Where the public reference package claims to implement a normative algorithm, its behavior MUST conform to that algorithm. Published-package conformance is limited to the algorithms, fields, and version pins declared by that package (see [conformance.md](conformance.md)).

## Provenance Authorities

Two provenance authorities are intentionally distinguished.

### Fixture-pinned evidence

The frozen registry

`evidence/acquisition_regime_fixture_registry_v1.json`

(`acquisition_regime_fixture_registry_v1`)

is the package-pinned empirical evidence used to reproduce the committed modern public fixtures. Its normative use is defined in [provenance-standard.md §9](provenance-standard.md#9-published-package-acquisition-regime-classification-normative).

### Working implementation

`synapse_msi/historical_corpus/provenance_registry.py`

(`acquisition_provenance_working_registry_v1`)

is a working implementation used by the public reference package. It is intentionally **not** a frozen normative registry and MUST NOT be treated as the authority for modern published-package equality.

## Normative Documents

| Document | Governs |
|----------|---------|
| [canonical-field-specification.md](canonical-field-specification.md) | Canonical field definitions, sourcing, persistence, and absence rules |
| [reconstruction-standard.md](reconstruction-standard.md) | Consensus, disagreement, freshness, episode reconstruction, and deterministic reproduction |
| [provenance-standard.md](provenance-standard.md) | Acquisition provenance, evidence hierarchy, and comparability |
| [observation-standard.md](observation-standard.md) | Observation-layer requirements |
| [investigation-standard.md](investigation-standard.md) | Investigation artifact and reproduction requirements |
| [conformance.md](conformance.md) | Published-package conformance requirements |

## Related Documentation

* [Architecture](../docs/architecture.md)
* [Reconstruction Boundaries](../docs/reconstruction-boundaries.md)
* [Investigation Reproducibility](../docs/investigation-reproducibility.md)
* [Historical Acquisition Regimes](../docs/historical-acquisition-regimes.md)
* [Schemas](../schemas/)
