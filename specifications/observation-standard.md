# Observation Standard

**Status:** Normative (index)  
**Applies to:** Synapse MSI External Reconstruction  
**Last updated:** 2026-07-28

This document does not redefine field semantics, reconstruction algorithms, or provenance rules. It identifies the normative specifications that govern observation-layer requirements.

## Required references

1. **Field semantics, sourcing, aliases, and absence.**  
   Implementations MUST follow [canonical-field-specification.md](canonical-field-specification.md). Exact zero is treated as unavailable only for the narrowly specified canonical fields documented there.

2. **Per-venue observation selection and eligibility for reconstruction.**  
   Implementations MUST follow [reconstruction-standard.md](reconstruction-standard.md) §3 (Canonical observation selection) and the metric-specific eligibility rules in that standard.

3. **Provenance accompanying observations.**  
   Implementations MUST follow [provenance-standard.md](provenance-standard.md) for evidence hierarchy and lineage. Unknown or insufficient acquisition lineage MUST NOT be invented.

4. **Public fixture representation.**  
   For published reproducibility packages, `observations.jsonl` is the normative observation evidence. `observations.parquet`, when present, MUST be a deterministic typed mirror of the same logical rows (see repository verification tests and [../schemas/README.md](../schemas/README.md)).

## Substitutes

Implementations MUST NOT insert midpoint, oracle, index, last-trade, or other derived substitutes in place of a missing native mark when the reconstruction claims native-mark comparability. Exclusion and partition rules in the reconstruction and provenance standards apply instead.
