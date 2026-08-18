# Conformance

**Status:** Normative  
**Applies to:** Claims about SynapseMSI External Reconstruction  
**Last updated:** 2026-07-30

## Authority

When prose in this repository conflicts with executable reference code, the **normative specifications** under `specifications/` are authoritative. The authority relationship is:

```text
normative specification
        ↓
reference implementation
```

The `synapse_msi/` package and `scripts/reproduce_investigation.py` are a verified reference implementation of those specifications; they are not a substitute for the specifications themselves and MUST NOT be treated as defining the normative contract when code and prose conflict.

An independent implementation MAY implement the algorithms declared in the specifications without using this repository’s Python entrypoint, language, or internal function names. It MUST still reproduce the specified outputs from the same committed evidence and the same declared version pins.

## Conformance classes

Conformance claims MUST identify which class is claimed. The classes are distinct.

| Class | Who it applies to | Pass means |
|---|---|---|
| **1. Specification conformance** | An independent implementation claiming specific normative algorithms | For each claimed algorithm, field, reconstruction, and provenance rules match the normative documents for the declared version pins |
| **2. Published-package conformance** | One reproducibility package (worked example or equivalent publication) | The package’s committed evidence offline-reproduces its published investigation outputs exactly under the rules below |
| **3. Repository release verification** | This SynapseMSI reference publication as a whole | The full test suite and all five committed examples pass offline |

Meeting class 3 implies the five committed packages meet class 2 under this repository’s tooling. Meeting class 2 for one package does not by itself establish class 1 for an arbitrary implementation, and does **not** establish that every algorithm in [reconstruction-standard.md](reconstruction-standard.md) is implemented. Meeting class 1 does not require use of `scripts/reproduce_investigation.py`.

**Scope distinction.** [reconstruction-standard.md](reconstruction-standard.md) is the complete normative methodology. The public `synapse_msi/` reference package implements and verifies a declared subset of that methodology for the committed packages. The presence of an algorithm in the normative standard does not by itself mean the public reference package implements it. A package conformance claim covers only the algorithms, fields, and version pins declared by that package. A claim of full methodology implementation conformance for a particular semantic metric or detector requires implementing that normative algorithm; appearance in the specification alone is insufficient.

The public reference package is not authoritative over the normative methodology. Where it claims to implement a normative algorithm, its behavior MUST conform to that algorithm.

---

## 1. Specification conformance (independent implementation)

An independent implementation MAY claim specification conformance for a declared set of version pins and algorithms only when all of the following hold:

1. **Fields.** Canonical field meanings, aliases, absence rules, and evidence limits MUST match [canonical-field-specification.md](canonical-field-specification.md) for the field and methodology versions declared on the artifacts under test.
2. **Reconstruction.** For each consensus, disagreement, and episode detector the implementation claims to implement, behavior MUST match [reconstruction-standard.md](reconstruction-standard.md) for the declared `methodology_version` / `detection_version`. Algorithms labeled as not implemented by this public reference package remain normatively specified; claiming them requires implementing those algorithms.
3. **Provenance.** Evidence hierarchy and lineage interpretation MUST match [provenance-standard.md](provenance-standard.md), including the published-package acquisition-regime classification policy in §9. Unknown or insufficient acquisition lineage MUST be preserved and MUST remain fail-closed for acquisition-sensitive comparison ([investigation-standard.md](investigation-standard.md); [observation-standard.md](observation-standard.md)). Modern packages that pin frozen acquisition-regime evidence MUST derive equality-surface provenance/comparability fields from that pin plus packaged observations.
4. **Native-mark integrity.** Implementations MUST NOT insert midpoint, oracle, index, last-trade, or other derived substitutes in place of a missing native mark when the reconstruction claims native-mark comparability ([observation-standard.md](observation-standard.md)).
5. **Version-bound interpretation.** Outputs MUST be interpreted under the version pins recorded on the artifact (see [canonical-field-specification.md §11](canonical-field-specification.md#11-versioning)). Current production changes MUST NOT silently alter the meaning of an already published version.

**Pass condition:** For the same committed evidence and the same declared version pins, the implementation’s outputs equal the outputs required by the normative algorithms it claims for the fields listed in §2 below (and freshness fields when a freshness episode is published). Equality is exact for those published fields.

**Non-requirement:** The implementation is not required to invoke `python scripts/reproduce_investigation.py`. The five committed examples do not demonstrate every algorithm in the reconstruction standard.

---

## 2. Published-package conformance

A published reproducibility package MAY claim conformance only when all of the following hold.

### 2.1 Required package files

The package MUST include the files required by [investigation-standard.md](investigation-standard.md):

* `observations.jsonl`
* `investigation.json`
* `provenance.json`
* `input_manifest.json`

### 2.2 Offline reproduction

Reproduction MUST use only committed package evidence, repository code or an equivalent independent implementation of the normative algorithms, and the published specifications. Reproduction MUST NOT require network access.

Using this repository’s reference entrypoint:

```bash
python scripts/reproduce_investigation.py --example <example-directory>
```

**Normative published equality surface.** Exact equality MUST hold between published and recomputed values for each of the following fields:

* `investigation_id` — recomputed per [reconstruction-standard.md §9](reconstruction-standard.md#9-independent-reproduction-requirements) published-package rules (`cluster_id` = published `episode_id`; exact serialization and SHA-256 truncation)
* `instrument`
* `window_start`
* `window_end`
* `included_venues`
* `excluded_venues`
* `consensus_mark`
* `disagreement_score`
* `methodology_version`
* `provenance_classification.assignment_status`
* `provenance_classification.primary_regime_id`
* `provenance_classification.spans_multiple_regimes`
* `provenance_classification.comparison_group`
* `comparability_eligibility`
* `comparability_reason_code`

When `investigation.json` publishes a `freshness_episode` object, equality MUST also hold for each of the following freshness fields, recomputed from packaged observations under [reconstruction-standard.md §5–§6](reconstruction-standard.md#5-disagreement-methodology) (including published `venue_staleness` package fields in §6):

* `affected_venue`
* `episode_start`
* `episode_end`
* `peak_scan_timestamp`
* `peak_sequence`
* `recovery_start`
* `recovery_snapshot_count`
* `recovery_qualified`
* `threshold_crossed`
* `pre_entry_scan_timestamp`
* `adoption_scan_timestamp`
* `duration_seconds`
* `peak_observation_age_seconds`

All listed fields, including floating-point freshness fields (`duration_seconds`, `peak_observation_age_seconds`), MUST match exactly. No float tolerance or closeness rule is defined by the normative reconstruction rules for these published fields.

When a published package includes non-empty `excluded_venues` for legacy mark consensus reproduction, the reason strings MUST be exactly the serialized codes defined in [reconstruction-standard.md](reconstruction-standard.md) §4 (`missing_or_zero_mark_price`, `mark_price_parse_failure`). Conceptual semantic-methodology labels such as `no_native_mark_price` MUST NOT be substituted on this equality surface.

**Pass conditions for the reference entrypoint:**

1. Process exit status MUST be `0`.
2. The tool MUST report `REPRODUCTION VERIFIED` and `Exact match: true`.
3. The reference implementation MUST verify the normative equality surface defined in this section.
4. Provenance sidecar eligibility MUST recompute identically: `comparability_eligibility` and `comparability_reason_code` on `provenance.json` MUST match both the evaluator recompute and the corresponding fields on `investigation.json` (fail-closed preservation; see [investigation-standard.md](investigation-standard.md)).

An independent implementation that does not use the reference script MUST still satisfy the same equality obligations for the fields listed above when given the same package evidence and version pins.

> **Non-normative implementation note.** The current Python reference implementation verifies this equality surface in `synapse_msi/investigation_reproduction.py` (functions presently named `compare_published` and `compare_freshness_episode`). Those function names and the surrounding code structure are implementation details. They do not define or limit the normative field set. Another implementation need not reproduce those function names, language, or code structure.

### 2.3 Manifest and hash integrity

When `input_manifest.json` publishes content hashes, those hashes MUST match the corresponding committed files. The fields verified by this repository’s tests include, when present:

* `observations_sha256` ↔ `observations.jsonl`
* `investigation_sha256` ↔ `investigation.json`
* `provenance_sha256` ↔ `provenance.json`
* `observations_parquet_sha256` ↔ `observations.parquet` (when Parquet is published)
* `acquisition_regime_evidence.sha256` ↔ the frozen artifact at `acquisition_regime_evidence.path` (when the modern pin is present; see [provenance-standard.md §9](provenance-standard.md#9-published-package-acquisition-regime-classification-normative))

When `acquisition_regime_evidence` is present, published-package reproduction MUST load that artifact, verify identifier/version/digest, assign observations from it, and derive provenance/comparability equality fields under provenance-standard §9. Reproduction MUST NOT obtain those modern equality values solely from the working registry identifier `acquisition_provenance_working_registry_v1`.

### 2.4 JSONL / Parquet logical parity

When the package includes `observations.parquet` (as recorded by `input_manifest.json`), the Parquet rows MUST be logically identical to `observations.jsonl` under the public observation schema verified by this repository’s Parquet equivalence tests. JSONL remains the normative observation representation ([docs/architecture.md](../docs/architecture.md)).

### 2.5 Provenance and native-mark rules

Published-package reproduction MUST preserve fail-closed provenance and acquisition eligibility outcomes. It MUST NOT substitute midpoint or other derived values for unavailable native-mark fields when native-mark comparability is claimed ([observation-standard.md](observation-standard.md); [reconstruction-standard.md](reconstruction-standard.md) §5).

---

## 3. Repository release verification

A release of **this** SynapseMSI reference publication MAY be treated as release-verified only when all of the following hold:

1. **Full test suite.** `python -m pytest -q` MUST exit `0`.
2. **All five committed examples.** Each of the following MUST reproduce successfully under §2 (exit status `0`, `REPRODUCTION VERIFIED`, `Exact match: true`):

   * `examples/modern/op_native_mark_000005`
   * `examples/modern/op_stale_014639`
   * `examples/historical/op_disagree_000244`
   * `examples/historical/op_stale_000012`
   * `examples/historical/op_consensus_000042`

3. **No network dependency.** Fixture reproduction MUST succeed with network access disabled; only committed repository files are used.

---

## What conformance does not mean

Conformance does **not** imply:

* industry-standard status;
* universal venue truth;
* root-cause determination;
* complete order-book reconstruction;
* causal attribution from L1 observations alone;
* that every venue is directly comparable on every field;
* that the reference Python scripts are the only permitted implementation vehicle.

## Versioning

Methodology and schema versions recorded on investigation artifacts (for example `methodology_version=canonical_snapshot_consensus_v1`, `semantics_version=investigation_evidence_v1`) identify which published rules applied. Field and reconstruction rules apply to their declared version pins. Current production changes MUST NOT silently modify the meaning of an already published version.

The working provenance registry version `acquisition_provenance_working_registry_v1`, implemented in `synapse_msi/historical_corpus/provenance_registry.py`, is a **working implementation identifier**. It is **not** a frozen normative registry pin.

The fixture-pinned frozen evidence artifact `acquisition_regime_fixture_registry_v1` (`evidence/acquisition_regime_fixture_registry_v1.json`, content version `2026-07-30.modern_fixtures.v1`) **is** normative package evidence for modern published-package reproduction under [provenance-standard.md §9](provenance-standard.md#9-published-package-acquisition-regime-classification-normative). It freezes only the empirical assignment records required by the committed modern fixtures; it does not freeze the entire live operational registry.
