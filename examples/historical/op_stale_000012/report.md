# Venue Freshness Event Investigation

## Incident

| Field | Value |
|-------|-------|
| Incident ID | `op_stale_000012` |
| Instrument | `ETHUSDT_PERP` |
| Detection | Venue Freshness |
| Time window | 2026-06-13T21:51:23.249226Z → 2026-06-13T22:00:16.165986Z |
| Affected venue(s) | okx |
| Reference venues | hyperliquid, binance, bybit |

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
| Reproducibility fixture | `examples/historical/op_stale_000012` |
| Archive references | `archives/snapshots/date=2026-06-13/instrument=ETHUSDT_PERP/part-seq0002331286-0002331397.ndjson.gz`, `archives/snapshots/date=2026-06-13/instrument=ETHUSDT_PERP/part-seq0002331405-0002331725.ndjson.gz`, `examples/historical/op_stale_000012/observations.jsonl` |
| Peak scan timestamp | 2026-06-13T22:00:03.418302Z |

---

## Acquisition Provenance

`examples/historical/op_stale_000012/provenance.json` remains the authoritative provenance record. This section summarizes values recorded in that sidecar for reader convenience.

| Field | Value |
|-------|-------|
| Schema version | `acquisition_regime_investigation_sidecar_v1` |
| Investigation ID | `87a9f4c7a3bde4cf70d1c0bc` |
| Linked episode ID(s) | `op_stale_000012` |
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

Observed venue freshness degradation during the reconstructed investigation window. The peak reconstructed market state archived in the reproducibility fixture is shown below.

---

## Scope

| Field | Value |
|-------|-------|
| Affected venue(s) | okx |
| Reference venues included in reconstruction | hyperliquid, binance, bybit |
| Affected instrument | `ETHUSDT_PERP` |
| Peak disagreement score | 11.0 |
| Consensus mark (peak) | 1685.93 |
| Reconstruction completeness | Complete for externally available archived observations in the fixture |

---

## Evidence

Reconstruction used:

* operational episode metadata
* archived canonical snapshots referenced by the reproducibility fixture
* archived venue observations in `examples/historical/op_stale_000012/observations.jsonl`
* archived venue timestamps

Derived outputs:

* reconstructed peak market state for the investigation window
* venue-level deviation table from the fixture

---

## External Observations

| Observation | Supporting Evidence | Reference |
|------------|---------------------|-----------|
| Episode window | Operational episode `op_stale_000012` spanned 2026-06-13 21:51:23 UTC – 2026-06-13 22:00:16 UTC. | E1 |
| Peak disagreement | Peak reconstructed disagreement score reached 11.0. | E2 |
| Consensus mark | Peak consensus mark was 1685.93. | E3 |
| Peak market state | Peak scan timestamp 2026-06-13T22:00:03.418302Z; sequence 2331730. | E4 |

---

## Peak Reconstructed Market State

Timestamp: **2026-06-13 22:00:03 UTC**

Sequence: **2331730**

Consensus mark: **1685.93**

Disagreement score: **11.0**

| Venue | Usable | Age (s) | Mark | Deviation (bps) |
|-------|:------:|--------:|------:|----------------:|
| hyperliquid | True | 570.4 | 1686.15 | 1.30 |
| okx | True | 580.5 | 1686.205 | 1.60 |
| binance | True | 0.0 | 1684.08 | 11.00 |
| bybit | True | 520.2 | 1685.71 | 1.30 |

---

## Timeline

| Timestamp | Observation | Evidence |
|-----------|-------------|----------|
| 21:51:23 UTC | Venue freshness episode window opened. | E1 |
| 22:00:03 UTC | Peak reconstructed market state archived in the fixture (consensus 1685.93; disagreement 11.0). | E2 |
| 22:00:16 UTC | Episode window closed. | E1 |

---

## Reconstruction Boundaries

This investigation should be interpreted in conjunction with the reconstruction methodology, provenance model, and evidence boundaries documented in:

* [reconstruction-standard.md](../../../specifications/reconstruction-standard.md)
* [provenance-standard.md](../../../specifications/provenance-standard.md)
* [reconstruction-boundaries.md](../../../docs/reconstruction-boundaries.md)
* [investigation-reproducibility.md](../../../docs/investigation-reproducibility.md)

The observations presented in this report are generated from the committed reproducibility fixture `examples/historical/op_stale_000012` and establish externally observable market state for the peak snapshot within the archived investigation window.

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
python scripts/reproduce_investigation.py --example examples/historical/op_stale_000012
```

Expected: `REPRODUCTION VERIFIED` with `Exact match: true`.


## Appendix

### Schema Versions

| Field | Value |
|-------|-------|
| report_schema_version | `synapse_investigation_report_v1` |
| detection_version | `operational_episode_v1` |
| reconstruction_version | `l1_canonical_v1` |
| investigation_id | `87a9f4c7a3bde4cf70d1c0bc` |

### Evidence References

* E1 — Episode window
* E2 — Peak disagreement
* E3 — Consensus mark
* E4 — Peak market state
