# Investigation Standard

**Status:** Normative (index)  
**Applies to:** Synapse MSI External Reconstruction  
**Last updated:** 2026-07-30

This document states investigation-layer requirements implemented by the public reference package and verified by the public examples. Detailed reconstruction algorithms are defined in the Reconstruction Standard. Artifact structure is defined in the Schemas.

Published-package conformance covers only the algorithms, fields, and version pins declared by that package. The presence of a broader algorithm in [reconstruction-standard.md](reconstruction-standard.md) does not by itself require a package to exercise it. See the public reference package scope statement in that standard.

## Episode detection and metrics

1. Implementations that publish operational episodes MUST compute episode bounds and freshness metrics according to [reconstruction-standard.md](reconstruction-standard.md) (episode / staleness rules, including `age_seconds = max(0, scan_timestamp − venue observation timestamp)` where that detector applies).
2. Independent reproduction of a freshness example MUST recompute episode start, end, duration, peak observation age, peak scan timestamp, `peak_sequence`, threshold crossing, recovery snapshot count, recovery qualification, `pre_entry_scan_timestamp`, and `adoption_scan_timestamp` where a `freshness_episode` is published, from packaged observations under [reconstruction-standard.md](reconstruction-standard.md) §5–§6 — it MUST NOT treat stored episode metadata as sole authority when a sequence fixture is provided.

## Investigation artifacts

1. Published investigation packages MUST include the evidence required for independent reproduction: at minimum `observations.jsonl`, `investigation.json`, `provenance.json`, and `input_manifest.json` (see [../schemas/investigation-report.md](../schemas/investigation-report.md) and [../docs/architecture.md](../docs/architecture.md)). Modern packages that publish resolved acquisition regimes MUST also pin frozen acquisition-regime evidence per [provenance-standard.md §9](provenance-standard.md#9-published-package-acquisition-regime-classification-normative).
2. Provenance sidecars MUST retain fail-closed eligibility outcomes. When acquisition lineage is insufficient, comparability eligibility MUST remain `excluded_fail_closed` with reason code `unknown_assignment`. Implementations MUST NOT rewrite unknown lineage as known. Modern packages MUST derive package-level provenance/comparability equality fields from the pinned frozen evidence and the normative classification policy in provenance-standard §9.

## Published package exclusion reasons

When a published package’s equality surface includes `excluded_venues` for legacy mark consensus reproduction, the serialized reason codes MUST be those defined in [reconstruction-standard.md](reconstruction-standard.md) §4 (Published package mark exclusion reasons):

* `missing_or_zero_mark_price`
* `mark_price_parse_failure`

These codes describe unavailable or unparseable **package evidence**. They MUST NOT be rewritten to conceptual semantic-methodology labels such as `no_native_mark_price`. Midpoint, oracle, index, or last-trade values MUST NOT be substituted for an unavailable native mark.

A package MAY retain an original `episode_type` vocabulary (for example `native_mark_disagreement`) while still requiring peak-package reproduction of `consensus_mark`, `disagreement_score`, `included_venues`, and `excluded_venues` via the legacy mark consensus path and the exclusion codes above, unless the package explicitly declares another recomputation path.

## Exact reproduction

The canonical reproduction interface is:

```bash
python scripts/reproduce_investigation.py --example <example-directory>
```

Reproduction MUST use only committed fixtures, repository code, and published methodology/specifications. It MUST exit non-zero when required published fields do not exactly match recomputed values. It MUST NOT require network access.
