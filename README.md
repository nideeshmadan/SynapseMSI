# SynapseMSI

SynapseMSI publishes a deterministic method for reconstructing and interpreting market-state evidence from archived observations.

It is the public External Reconstruction layer of the Synapse MSI model: observation and reconstruction specifications, a reference implementation, independently reproducible worked examples, and fail-closed provenance with field-level comparability.

## Quick start

### Requirements

* Python 3.11 or later
* Git
* Run all commands from the repository root after cloning

### Clone the repository

```bash
git clone https://github.com/nideeshmadan/SynapseMSI.git
cd SynapseMSI
```

### Create an environment and install

```bash
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .
```

`pyproject.toml` declares no third-party runtime dependencies. The editable installation registers the local `synapse_msi` package.

Optional test dependencies can be installed with:

```bash
python -m pip install -e ".[dev]"
```

### Reproduce the first investigation

```bash
python scripts/reproduce_investigation.py \
  --example examples/modern/op_native_mark_000005
```

A successful reproduction ends with:

```text
REPRODUCTION VERIFIED
Exact match: true
```

This means the independently reconstructed investigation matches the committed package under its declared methodology, schema, and evidence-version pins.

Committed examples reproduce offline from the cloned repository. No network access, credentials, private repositories, or external services are required.

## What SynapseMSI is not

SynapseMSI is **not**:

* an execution system, trading strategy, or signal generator;
* an attribution engine, because attribution requires proprietary internal evidence;
* a claim of universal venue truth or industry-standard status;
* a complete order-book reconstruction;
* a root-cause or causal-attribution system based on L1 observations alone.

## Core guarantees

When a published package reproduces successfully:

* required investigation metrics match exactly under the declared methodology version;
* acquisition-sensitive comparison eligibility fails closed when lineage is insufficient;
* native-mark and other field comparisons exclude venues that lack a usable comparable field rather than inserting substitutes;
* reproduction uses only committed fixtures, repository code, published specifications, and package-pinned evidence;
* no network access or hidden production state is required.

## Specifications

Normative documents live under [`specifications/`](specifications/README.md):

| Document                                                                            | Role                                                           |
| ----------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| [canonical-field-specification.md](specifications/canonical-field-specification.md) | Field meanings, authoritative sourcing, and absence rules      |
| [reconstruction-standard.md](specifications/reconstruction-standard.md)             | Consensus, disagreement, freshness, and episode reconstruction |
| [provenance-standard.md](specifications/provenance-standard.md)                     | Evidence hierarchy, acquisition lineage, and comparability     |
| [observation-standard.md](specifications/observation-standard.md)                   | Observation-layer requirements                                 |
| [investigation-standard.md](specifications/investigation-standard.md)               | Investigation-package and reproduction requirements            |
| [conformance.md](specifications/conformance.md)                                     | Conformance claims and version requirements                    |

Explanatory and usage documentation lives under [`docs/`](docs/README.md).

## Five worked examples

| Example                 | Era        | Primary demonstration                     | Acquisition status               | Comparison status            |
| ----------------------- | ---------- | ----------------------------------------- | -------------------------------- | ---------------------------- |
| `op_native_mark_000005` | Modern     | Native-mark field comparability           | `derived_from_preserved_lineage` | `comparable_after_partition` |
| `op_stale_014639`       | Modern     | Bounded temporal freshness reconstruction | `derived_from_preserved_lineage` | `comparable_after_partition` |
| `op_disagree_000244`    | Historical | Disagreement reproduction                 | `insufficient_raw_lineage`       | `excluded_fail_closed`       |
| `op_stale_000012`       | Historical | Historical freshness evidence             | `insufficient_raw_lineage`       | `excluded_fail_closed`       |
| `op_consensus_000042`   | Historical | Consensus-quality reconstruction          | `insufficient_raw_lineage`       | `excluded_fail_closed`       |

See [`examples/README.md`](examples/README.md) for package contents and reproduction details.

## Why historical and modern examples are both included

The repository intentionally includes both historical and modern reproducibility packages.

**Modern examples** demonstrate reconstruction under explicitly identified acquisition regimes with preserved field-level provenance and acquisition-sensitive comparison eligibility.

**Historical examples** demonstrate deterministic reconstruction of archived investigations for which complete acquisition lineage is unavailable. Their investigation metrics remain reproducible, but acquisition-sensitive comparisons remain `excluded_fail_closed` rather than relying on retroactive assumptions.

Together, the examples show that SynapseMSI can reproduce both current and historical evidence while keeping differences in acquisition confidence explicit.

The historical examples are not presented as equivalent to the modern examples. Their retained uncertainty is part of the evidence and demonstrates that the system does not invent missing lineage.

## Reproduce any example

Use the same command with any committed example directory:

```bash
python scripts/reproduce_investigation.py --example <example-directory>
```

### Modern examples

```bash
python scripts/reproduce_investigation.py \
  --example examples/modern/op_native_mark_000005

python scripts/reproduce_investigation.py \
  --example examples/modern/op_stale_014639
```

### Historical examples

```bash
python scripts/reproduce_investigation.py \
  --example examples/historical/op_disagree_000244

python scripts/reproduce_investigation.py \
  --example examples/historical/op_stale_000012

python scripts/reproduce_investigation.py \
  --example examples/historical/op_consensus_000042
```

Every successful run ends with:

```text
REPRODUCTION VERIFIED
Exact match: true
```

## Provenance and fail-closed behavior

Modern examples retain explicit acquisition-regime identity and support partitioned comparability where venue acquisition regimes or canonical field sources differ.

Historical examples retain unknown or insufficient acquisition lineage. Investigation metrics remain reproducible, but acquisition-sensitive comparison stays `excluded_fail_closed` with reason `unknown_assignment`.

The repository does not retroactively infer or invent missing lineage.

## Evidence artifacts

The `evidence/` directory contains the package-pinned empirical evidence required to reproduce acquisition-sensitive behavior in the committed modern investigation packages.

It is distinct from the rest of the repository:

- `specifications/` defines the normative rules.
- `evidence/` contains the frozen empirical evidence evaluated under those rules.
- `examples/` contain the observations and expected investigation artifacts reproduced from that evidence.

The published evidence artifact, `acquisition_regime_fixture_registry_v1`, is authoritative only for the committed modern packages that explicitly reference it. It is not a live operational registry or a universal methodology specification.

The production working registry is not part of the public conformance surface and is not used to determine equality for the published modern fixtures.

## Repository map

```text
specifications/   Normative standards and conformance requirements
docs/             Explanatory and usage documentation
evidence/         Fixture-pinned evidence and working provenance registries
examples/         Five independently reproducible investigation packages
schemas/          Artifact structure and validation definitions
synapse_msi/      Installable Python reference implementation
scripts/          Reproduction and verification entry points
tests/            Conformance, methodology, provenance, and fixture tests
```

## Current scope and limitations

* External reconstruction from archived observations only.
* L1 and canonical-field reconstruction within the declared fixture scope.
* No complete order-book reconstruction.
* Fixture-pinned acquisition-regime evidence is authoritative only for the packages and versions that reference it.
* Field comparability is field-specific. A venue present in an observation set may still be excluded from a particular comparison.
* Acquisition-sensitive comparisons fail closed when the necessary lineage cannot be established.
* Operational cause for freshness episodes may remain mixed or indeterminate when timing evidence alone cannot localize the delay.
* Reproducible external evidence does not by itself establish internal execution attribution or root cause.

## Conformance and versioning

See [`specifications/conformance.md`](specifications/conformance.md).

Each investigation package records the applicable methodology, schema, artifact-format, and evidence versions. Independent implementations must reproduce the required outputs under those declared pins before making a conformance claim.

## License

All rights reserved. See [LICENSE](LICENSE).
