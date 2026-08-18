# Acquisition-Regime Fixture Registry

**Status:** Structure (schema)  
**Normative policy:** [provenance-standard.md §9](../specifications/provenance-standard.md#9-published-package-acquisition-regime-classification-normative)

This schema defines the structure of the **package-pinned empirical acquisition-regime registry** used to reproduce the committed modern public fixtures. It describes the published evidence artifact itself and does not define the acquisition-classification algorithm.

## Artifact Location

Committed file:

```text
evidence/acquisition_regime_fixture_registry_v1.json
```

## Root Object

| Field | Type | Required | Description |
|---|---|---|---|
| `artifact_format_version` | string | yes | Must be `acquisition_regime_fixture_evidence_v1`. |
| `registry_id` | string | yes | Must be `acquisition_regime_fixture_registry_v1`. |
| `registry_content_version` | string | yes | Frozen content version for the published registry. |
| `evidence_status` | string | yes | Declares asserted fixture coverage. |
| `scope_note` | string | yes | Human-readable scope limitation. |
| `boundary_semantics` | object | yes | Validity interval semantics and mismatch behavior. |
| `assignments` | array | yes | Non-empty list of acquisition-regime assignment records. |

### `boundary_semantics`

| Field | Meaning |
|---|---|
| `valid_from` | `inclusive` |
| `valid_to` | `inclusive` |
| `null_valid_from` | `unbounded_past` |
| `null_valid_to` | `open_ended` |
| `mismatch_behavior` | `advisory_warning_only` for published-package assignment |

## Assignment Record

| Field | Type | Required | Description |
|---|---|---|---|
| `venue` | string | yes | Venue identifier. |
| `instrument_scope` | string | yes | `*` or a specific instrument identifier. |
| `regime_id` | string | yes | Frozen acquisition-regime identifier. |
| `acquisition_regime` | string | yes | Acquisition-regime identifier recorded in the published registry. |
| `transport` | string | yes | Asserted transport. |
| `ingest_type` | string | yes | Asserted ingest type. |
| `collector_service_name` | string | yes | Asserted collector identity. |
| `valid_from` | string or null | yes | Inclusive lower validity bound. |
| `valid_to` | string or null | yes | Inclusive upper validity bound; `null` indicates open-ended validity. |
| `comparison_group` | string | yes | Comparison group used during aggregation. |
| `current_production` | boolean | yes | Tie-break indicator when multiple assignments match. |
| `evidence_status` | string | yes | Record-level evidence status. |

## Package Pin (`input_manifest.json`)

Modern published fixtures MUST include:

```json
"acquisition_regime_evidence": {
  "registry_id": "acquisition_regime_fixture_registry_v1",
  "registry_content_version": "2026-07-30.modern_fixtures.v1",
  "path": "../../../evidence/acquisition_regime_fixture_registry_v1.json",
  "sha256": "<lowercase hex of committed artifact bytes>"
}
```

Historical fixtures intentionally omit this object. Omission preserves unknown acquisition lineage and fail-closed comparability.

## Integrity

The SHA-256 digest is computed over the exact committed file bytes. Independent implementations MUST verify the recorded digest before using the registry during reproduction.
