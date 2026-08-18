# Market Disagreement Event Investigation

## Incident

| Field | Value |
|-------|-------|
| Incident ID | `op_disagree_000244` |
| Instrument | `ETHUSDT_PERP` |
| Detection | Market Disagreement |
| Time window | 2026-04-23T17:36:38.410960Z → 2026-04-23T17:44:18.115657Z |
| Affected venue(s) | bybit |
| Reference venues | hyperliquid, okx, binance |

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
| Reproducibility fixture | `examples/historical/op_disagree_000244` |
| Archive references | `archives/snapshots/date=2026-04-23/instrument=ETHUSDT_PERP/part-seq0000159348-0000160497.ndjson.gz`, `archives/snapshots/date=2026-04-23/instrument=ETHUSDT_PERP/part-seq0000160498-0000161634.ndjson.gz`, `examples/historical/op_disagree_000244/observations.jsonl` |
| Peak scan timestamp | 2026-04-23T17:42:17.232318Z |

---

## Acquisition Provenance

`examples/historical/op_disagree_000244/provenance.json` remains the authoritative provenance record. This section summarizes values recorded in that sidecar for reader convenience.

| Field | Value |
|-------|-------|
| Schema version | `acquisition_regime_investigation_sidecar_v1` |
| Investigation ID | `9ea4f8d05919d70c5fa04061` |
| Linked episode ID(s) | `op_disagree_000244` |
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

Cross-venue disagreement exceeded the configured threshold during the reconstructed investigation window, with Bybit exhibiting the largest observed deviation from the reconstructed cross-venue market state.

---

## Scope

| Field | Value |
|-------|-------|
| Affected venue(s) | bybit |
| Reference venues included in reconstruction | hyperliquid, okx, binance |
| Affected instrument | `ETHUSDT_PERP` |
| Peak disagreement score | 84.9 |
| Consensus mark (peak) | 2288.48 |
| Reconstruction completeness | Complete for externally available archived observations in the fixture |

---

## Evidence

Reconstruction used:

* operational episode metadata
* archived canonical snapshots referenced by the reproducibility fixture
* archived venue observations in `examples/historical/op_disagree_000244/observations.jsonl`
* archived venue timestamps

Derived outputs:

* reconstructed peak market state for the investigation window
* venue-level deviation table from the fixture

---

## External Observations

| Observation | Supporting Evidence | Reference |
|------------|---------------------|-----------|
| Episode window | Operational episode `op_disagree_000244` spanned 2026-04-23 17:36:38 UTC – 2026-04-23 17:44:18 UTC. | E1 |
| Cross-venue disagreement | Peak reconstructed disagreement score reached 84.9. | E2 |
| Consensus mark | Peak consensus mark was 2288.48. | E3 |
| Largest observed deviation | Bybit exhibited the largest observed deviation (84.90 bps). | E4 |

---

## Peak Reconstructed Market State

Timestamp: **2026-04-23 17:42:17 UTC**

Sequence: **160393**

Consensus mark: **2288.48**

Disagreement score: **84.9**

| Venue | Usable | Age (s) | Mark | Deviation (bps) |
|-------|:------:|--------:|------:|----------------:|
| hyperliquid | True | 0.2 | 2287.65 | 3.60 |
| okx | True | 0.1 | 2287.575 | 4.00 |
| binance | True | 0.2 | 2289.32 | 3.70 |
| bybit | True | 0.0 | 2307.905 | 84.90 |

---

## Timeline

| Timestamp | Observation | Evidence |
|-----------|-------------|----------|
| 17:36:38 UTC | Cross-venue disagreement first observed in the archived episode window. | E1 |
| 17:42:17 UTC | Peak disagreement score reached 84.9 bps at consensus mark 2288.48. | E2 |
| 17:44:18 UTC | Episode window closed. | E1 |

---

## Reconstruction Boundaries

This investigation should be interpreted in conjunction with the reconstruction methodology, provenance model, and evidence boundaries documented in:

* [reconstruction-standard.md](../../../specifications/reconstruction-standard.md)
* [provenance-standard.md](../../../specifications/provenance-standard.md)
* [reconstruction-boundaries.md](../../../docs/reconstruction-boundaries.md)
* [investigation-reproducibility.md](../../../docs/investigation-reproducibility.md)

The observations presented in this report are generated from the committed reproducibility fixture `examples/historical/op_disagree_000244` and establish externally observable market state for the peak snapshot within the archived investigation window.

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
python scripts/reproduce_investigation.py --example examples/historical/op_disagree_000244
```

Expected: `REPRODUCTION VERIFIED` with `Exact match: true`.


## Appendix

### Schema Versions

| Field | Value |
|-------|-------|
| report_schema_version | `synapse_investigation_report_v1` |
| detection_version | `operational_episode_v1` |
| reconstruction_version | `l1_canonical_v1` |
| investigation_id | `9ea4f8d05919d70c5fa04061` |

### Evidence References

* E1 — Episode window
* E2 — Cross-venue disagreement
* E3 — Consensus mark
* E4 — Largest observed deviation
