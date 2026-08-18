# Historical examples

Packages with unknown or insufficient acquisition lineage.

| Field | Value (all three) |
|-------|-------------------|
| `linkage_status` | `insufficient_raw_lineage` |
| `comparability_eligibility` | `excluded_fail_closed` |
| `comparability_reason_code` | `unknown_assignment` |

They demonstrate fail-closed behavior:

* investigation metrics remain reproducible;
* acquisition assignment remains unknown where evidence is insufficient;
* comparability eligibility is excluded fail-closed;
* the repository does not invent acquisition lineage.

These examples are **not** deprecated relative to modern packages; they serve a different evidentiary purpose.

| Example | Primary demonstration | Entry point |
|---------|----------------------|-------------|
| [op_disagree_000244](op_disagree_000244/) | Disagreement reproduction | `report.md` |
| [op_stale_000012](op_stale_000012/) | Historical freshness evidence | `report.md` |
| [op_consensus_000042](op_consensus_000042/) | Consensus-quality reconstruction | `report.md` |

```bash
python scripts/reproduce_investigation.py --example examples/historical/op_disagree_000244
python scripts/reproduce_investigation.py --example examples/historical/op_stale_000012
python scripts/reproduce_investigation.py --example examples/historical/op_consensus_000042
```
