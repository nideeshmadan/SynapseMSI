# Investigation reproducibility demonstration

This document demonstrates that every published investigation package can be independently reconstructed from the committed observations using the published methodology, reference implementation, and package-pinned evidence. No private infrastructure, production systems, or hidden implementation details are required.

## Historical provenance

Historical investigation packages intentionally preserve unknown or insufficient acquisition lineage. Acquisition-sensitive comparisons therefore remain excluded (`excluded_fail_closed`) rather than relying on inferred historical provenance.

## Public reference corpus

Five committed packages constitute the public reference corpus.

### Modern known-lineage examples

#### Native-mark disagreement

`examples/modern/op_native_mark_000005/`

Modern native-mark disagreement demonstrating deterministic reconstruction, field-level provenance under observation `acquisition`, and partitioned Binance–Bybit comparison (`comparable_after_partition`). Native-mark comparability is field-specific: Hyperliquid and OKX are excluded from native-mark consensus because the retained observations for the reconstructed window do not contain a comparable native mark (`missing_or_zero_mark_price`).

```bash
python scripts/reproduce_investigation.py \
  --example examples/modern/op_native_mark_000005
```

Expected successful output (tail):

```text
REPRODUCTION VERIFIED
Published consensus: 1898.42
Recomputed consensus: 1898.42
Published disagreement: 24.1
Recomputed disagreement: 24.1
Exact match: true
```

| Artifact | Path |
|---|---|
| Observations | `examples/modern/op_native_mark_000005/observations.jsonl` |
| Published investigation | `.../investigation.json` |
| Provenance sidecar | `.../provenance.json` |
| Narrative report | `.../report.md` |
| Input hashes | `.../input_manifest.json` |

#### Freshness

`examples/modern/op_stale_014639/`

Modern **bounded temporal freshness** package. The fixture retains a minimal multi-snapshot sequence (healthy pre-entry through five consecutive recovery snapshots). Reproduction recomputes episode start/end, duration, peak age, adoption, and recovery from that sequence using `scan_timestamp − venue observation timestamp`; it does not trust precomputed episode metadata alone. The report separates Observed Evidence, Deterministic Detector Result, Operational Interpretation (`mixed/indeterminate operational cause`), and Not Established.

```bash
python scripts/reproduce_investigation.py \
  --example examples/modern/op_stale_014639
```

Expected successful output (tail):

```text
REPRODUCTION VERIFIED
Published consensus: 1939.61
Recomputed consensus: 1939.61
Published disagreement: 1.8
Recomputed disagreement: 1.8
Exact match: true
```

### Historical public examples

Historical examples demonstrate deterministic reconstruction under incomplete historical acquisition lineage. Investigation metrics remain reproducible, while acquisition-sensitive comparisons intentionally remain fail-closed.

- `examples/historical/op_disagree_000244`
- `examples/historical/op_stale_000012`
- `examples/historical/op_consensus_000042`

Reproduce with the same script and `--example <dir>`.

## Methodology

- Canonical observation / consensus / disagreement: [reconstruction-standard.md](../specifications/reconstruction-standard.md) §§3–5, 7, 9
- Acquisition provenance: [provenance-standard.md](../specifications/provenance-standard.md)
- Field semantics: [canonical-field-specification.md](../specifications/canonical-field-specification.md)
