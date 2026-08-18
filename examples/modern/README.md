# Modern examples

Packages with preserved modern acquisition lineage (`linkage_status`: `derived_from_preserved_lineage`).

Comparability is field- and regime-aware. Both packages report `comparability_eligibility`: `comparable_after_partition`.

Both packages pin the frozen acquisition-regime evidence artifact `acquisition_regime_fixture_registry_v1` in `input_manifest.json` (`acquisition_regime_evidence`). Provenance/comparability equality is derived from that pin under [provenance-standard.md §9](../../specifications/provenance-standard.md#9-published-package-acquisition-regime-classification-normative).

| Example | Demonstration | Entry point |
|---------|---------------|-------------|
| [op_native_mark_000005](op_native_mark_000005/) | Partitioned native-mark field comparability (Binance–Bybit); Hyperliquid/OKX excluded | `report.md` |
| [op_stale_014639](op_stale_014639/) | Bounded temporal freshness reconstruction with receive-time vs venue-event-time evidence for separating venue-side age from collector-side receipt delay; mixed/indeterminate operational cause | `report.md` |

```bash
python scripts/reproduce_investigation.py --example examples/modern/op_native_mark_000005
python scripts/reproduce_investigation.py --example examples/modern/op_stale_014639
```
