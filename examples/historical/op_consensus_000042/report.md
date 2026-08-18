# Consensus Quality Event Investigation

## Incident

| Field | Value |
|-------|-------|
| Incident ID | `op_consensus_000042` |
| Instrument | `BTCUSDT_PERP` |
| Detection | Consensus Quality |
| Time window | 2026-07-01T13:38:22.549111Z → 2026-07-01T13:53:40.703398Z |
| Affected venue(s) | bybit, hyperliquid, okx, binance |
| Reference venues | none listed |

---

## Reconstruction Metadata

| Field | Value |
|-------|-------|
| Methodology version | `canonical_snapshot_consensus_v1` |
| Detection version | `operational_episode_v1` |
| Reconstruction version | `l1_canonical_v1` |
| Schema version | `synapse_investigation_report_v1` |
| Methodology | [reconstruction-standard.md](../../../specifications/reconstruction-standard.md) |
| Provenance | [provenance-standard.md](../../../specifications/provenance-standard.md) |
| Reconstruction boundaries | [docs/reconstruction-boundaries.md](../../../docs/reconstruction-boundaries.md) |
| Reproducibility fixture | `examples/historical/op_consensus_000042` |
| Archive references | `archives/snapshots/date=2026-07-01/instrument=BTCUSDT_PERP/part-seq0002559383-0002559411.ndjson.gz`, `archives/snapshots/date=2026-07-01/instrument=BTCUSDT_PERP/part-seq0002559412-0002559471.ndjson.gz`, `examples/historical/op_consensus_000042/observations.jsonl` |
| Peak scan timestamp | 2026-07-01T13:52:14.605494Z |

---

## Acquisition Provenance

`examples/historical/op_consensus_000042/provenance.json` remains the authoritative provenance record. This section summarizes values recorded in that sidecar for reader convenience.

| Field | Value |
|-------|-------|
| Schema version | `acquisition_regime_investigation_sidecar_v1` |
| Investigation ID | `72005bfeebb0112dbd61d634` |
| Linked episode ID(s) | `op_consensus_000042` |
| Linkage status | `insufficient_raw_lineage` |
| Linkage method | `episode_sidecar_aggregation` |
| Comparison scope | `artifact` |
| Comparability eligibility | `excluded_fail_closed` |
| Comparability reason code | `unknown_assignment` |
| Assignment status | `unknown` |
| Assignment method | `unknown` |
| Assignment evidence | `episode_identity` |
| Acquisition regime ID | `unknown.insufficient_provenance` |
| Primary regime ID | `null` |
| Linked regime ID(s) | `unknown.insufficient_provenance` |
| Comparison group | `unknown` |
| Spans multiple regimes | `false` |
| Unresolved reason | `missing_snapshot_to_raw_lineage` |
| Assignment warnings | unresolved_acquisition_rows=1; fail-closed for claims relying on them |
| Known limitations | insufficient row-level acquisition metadata |
| Generator version | `acquisition_regime_linkage_v2026_07` |

---

## Detection

Cross-venue consensus disagreement exceeded the configured threshold during the reconstructed investigation window.

---

## Scope

| Field | Value |
|-------|-------|
| Affected venue(s) | bybit, hyperliquid, okx, binance |
| Affected instrument | `BTCUSDT_PERP` |
| Peak disagreement score | 85.1 |
| Consensus mark (peak) | 59356.93 |
| Reconstruction completeness | Complete for externally available archived observations in the fixture |

---

## Evidence

Reconstruction used:

* operational episode metadata
* archived canonical snapshots referenced by the reproducibility fixture
* archived venue observations in `examples/historical/op_consensus_000042/observations.jsonl`
* archived venue timestamps

Derived outputs:

* reconstructed peak market state for the investigation window
* venue-level deviation table from the fixture

---

## External Observations

| Observation | Supporting Evidence | Reference |
|------------|---------------------|-----------|
| Episode window | Operational episode `op_consensus_000042` spanned 2026-07-01 13:38:22 UTC – 2026-07-01 13:53:40 UTC. | E1 |
| Consensus degradation | Peak reconstructed disagreement score reached 85.1. | E2 |
| Consensus mark | Peak consensus mark was 59356.93. | E3 |
| Largest observed deviation | hyperliquid exhibited the largest observed deviation (85.10 bps). | E4 |

---

## Peak Reconstructed Market State

Timestamp: **2026-07-01 13:52:14 UTC**

Sequence: **2559473**

Consensus mark: **59356.93**

Disagreement score: **85.1**

| Venue | Usable | Age (s) | Mark | Deviation (bps) |
|-------|:------:|--------:|------:|----------------:|
| hyperliquid | True | 6.0 | 58852.00 | 85.10 |
| okx | True | 1.9 | 59356.25 | 0.10 |
| binance | True | 1.5 | 59357.60 | 0.10 |
| bybit | True | 0.0 | 59370.50 | 2.30 |

---

## Timeline

| Timestamp | Observation | Evidence |
|-----------|-------------|----------|
| 13:38:22 UTC | Consensus quality episode window opened. | E1 |
| 13:52:14 UTC | Peak disagreement score reached 85.1 bps at consensus mark 59356.93. | E2 |
| 13:53:40 UTC | Episode window closed. | E1 |

---

## Reconstruction Boundaries

This investigation should be interpreted in conjunction with the reconstruction methodology, provenance model, and evidence boundaries documented in:

* [reconstruction-standard.md](../../../specifications/reconstruction-standard.md)
* [provenance-standard.md](../../../specifications/provenance-standard.md)
* [reconstruction-boundaries.md](../../../docs/reconstruction-boundaries.md)
* [investigation-reproducibility.md](../../../docs/investigation-reproducibility.md)

The observations presented in this report are generated from the committed reproducibility fixture `examples/historical/op_consensus_000042` and establish externally observable market state for the peak snapshot within the archived investigation window.

---

## Fail-closed acquisition status

This historical example retains **unknown / insufficient** acquisition lineage. That is intentional.

* Investigation metrics remain independently reproducible from packaged observations.
* Acquisition assignment remains unknown where evidence is insufficient (`linkage_status`: `insufficient_raw_lineage`).
* Comparability eligibility is `excluded_fail_closed` with reason `unknown_assignment`.
* The repository does **not** retroactively invent acquisition lineage.

Historical examples are not inferior to modern examples; they serve a different evidentiary purpose: demonstrating fail-closed behavior when lineage cannot be established.

---

## Reproduction

```bash
python scripts/reproduce_investigation.py --example examples/historical/op_consensus_000042
```

Expected: `REPRODUCTION VERIFIED` with `Exact match: true`.


## Appendix

### Schema Versions

| Field | Value |
|-------|-------|
| report_schema_version | `synapse_investigation_report_v1` |
| detection_version | `operational_episode_v1` |
| reconstruction_version | `l1_canonical_v1` |
| investigation_id | `72005bfeebb0112dbd61d634` |

### Evidence References

* E1 — Episode window
* E2 — Consensus degradation
* E3 — Consensus mark
* E4 — Largest observed deviation
