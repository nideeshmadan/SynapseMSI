# Reconstruction Boundaries

External Reconstruction establishes only those conclusions that can be supported by externally observable evidence within a defined investigation window.

Each investigation report identifies the reconstruction boundary that applies to its findings and references the scope defined in this document. Reviewers should interpret every conclusion within these limits and distinguish between what the archived evidence establishes, what it only suggests, and what remains outside the available evidence.

## Supported Conclusions

External Reconstruction can support the following conclusions when the required observations are present in the archived evidence:

| Conclusion                          | Supported | Required evidence                                                       |
| ----------------------------------- | :-------: | ----------------------------------------------------------------------- |
| Displayed best bid                  |     ✓     | Archived L1 bid observations                                            |
| Displayed best ask                  |     ✓     | Archived L1 ask observations                                            |
| Displayed L1 midpoint               |     ✓     | Archived or deterministically reconstructed L1 bid and ask observations |
| Native mark value                   |     ✓     | Venue-native mark observations with sufficient provenance               |
| Venue timestamp age                 |     ✓     | Archived venue and observation timestamps                               |
| Cross-venue disagreement            |     ✓     | Reconstructed venue observations and comparison metrics                 |
| Disagreement persistence            |     ✓     | A sequence of archived snapshots within the investigation window        |
| Funding comparison                  |     ✓     | Archived funding observations                                           |
| Open-interest comparison            |     ✓     | Archived open-interest observations                                     |
| Deterministic metric recomputation  |     ✓     | Archived observations and the recorded methodology version              |
| Investigation-window reconstruction |     ✓     | Archived observations within the bounded reconstruction window          |

Support is conditional on the presence, provenance, and completeness of the required evidence. The existence of a supported conclusion type does not mean that every investigation contains enough evidence to establish that conclusion.

`reconstruction_confidence` measures the completeness and consistency of the evidence used to produce a reconstruction. It does not measure execution quality, executable liquidity, market efficiency, fair value, economic correctness, or the probability that an order would have filled.

## Unsupported Conclusions

External Reconstruction alone does not support the following conclusions:

| Conclusion                     | Additional evidence required                                       |
| ------------------------------ | ------------------------------------------------------------------ |
| Executable liquidity           | Full order-book depth and order-size context                       |
| Queue position                 | Venue queue state or order-level queue data                        |
| Hidden liquidity               | Hidden-order or venue-internal liquidity information               |
| Iceberg orders                 | Order-level venue data or venue acknowledgements                   |
| Market impact                  | Executed trades, order size, and depth evolution                   |
| Expected fill price            | Order details, order size, and executable depth                    |
| Realized fill quality          | Orders, executions, fees, and applicable benchmarks                |
| Execution probability          | Order submission, acknowledgement, cancellation, and fill records  |
| Routing quality                | Internal routing decisions and available alternatives              |
| End-to-end latency attribution | Collector, network, venue, application, and system telemetry       |
| Exchange fault                 | Operational evidence sufficient to isolate venue behavior          |
| Collector fault                | Collector logs, telemetry, and runtime evidence                    |
| Internal OMS behavior          | Internal order-management records                                  |
| Internal risk decisions        | Internal risk-system evidence                                      |
| Strategy intent                | Strategy configuration, decision records, or internal logic        |
| Causality                      | Evidence sufficient to establish a causal mechanism                |
| Responsibility                 | Internal and external evidence sufficient to assign responsibility |
| Execution attribution          | Internal evidence correlated with the reconstructed external state |

Synapse reconstructs externally observable market conditions. External Reconstruction does not, by itself, determine why an execution occurred, whether a system behaved correctly, which party was responsible, or whether an outcome was economically favorable.

Those conclusions require proprietary Internal Evidence and Local Correlation in addition to the reconstructed external market state.

## Evidence Sufficiency

A conclusion is supported only when the archived evidence contains the fields, timestamps, provenance, and observation coverage required for that conclusion.

Missing or ambiguous evidence must not be silently inferred.

When evidence is incomplete:

* the affected conclusion should be omitted, qualified, or marked as insufficiently supported;
* `reconstruction_confidence` may be reduced;
* missing observations should remain visible as evidence limitations;
* later observations must not be used to manufacture certainty about an earlier undocumented state.

A deterministic reconstruction can still be reproducible when its evidence is incomplete. Reproducibility means that an independent reviewer can obtain the same result from the same inputs and methodology. It does not mean that the underlying evidence is complete.

## L1 Evidence Boundary

The public investigation examples reconstruct **L1, or top-of-book, market state**.

Depending on venue, acquisition regime, and retained provenance, the archived evidence may include:

* native mark price;
* displayed best bid price;
* displayed best ask price;
* displayed best bid or ask size when captured;
* venue timestamp;
* collector observation timestamp;
* funding observations;
* open-interest observations.

The available fields are determined by the recorded observation and its provenance. A value must not be treated as venue-native merely because it appears in a field commonly associated with a native venue value.

The canonical consensus is a deterministic median reference used to compare externally observable venue state. It is not fair value, market truth, an executable market price, or a prediction of where an order should have traded.

Market disagreement describes divergence among archived venue observations using the `disagreement_score` defined in [methodology.md](../specifications/reconstruction-standard.md).

L1 reconstruction can support comparison of:

* displayed best bid;
* displayed best ask;
* displayed top-level size when captured;
* L1 midpoint;
* venue-native mark when directly observed and supported by provenance;
* cross-venue divergence among those values.

L1 evidence does not establish executable liquidity beyond the displayed top level.

A venue may display a divergent top-of-book value because of shallow displayed liquidity, stale observations, market fragmentation, venue-specific mark methodology, or other causes not distinguishable from L1 evidence alone. Deeper displayed liquidity or hidden liquidity may materially change the economic significance of the observed divergence.

For that reason, Synapse reports **observable market-state disagreement**, not executable-liquidity disagreement.

Because the current public methodology is limited to L1 observations, investigation reports cannot establish:

* full order-book state;
* executable liquidity at a specified size;
* queue position;
* hidden liquidity;
* iceberg activity;
* expected or realized market impact;
* execution probability;
* strategy intent;
* causality;
* fair value;
* market truth.

Archived L2 or order-level market data may support additional conclusions in future methodologies, but those conclusions remain outside the current L1 reconstruction boundary unless explicitly documented.

## Native and Derived Value Boundary

A reconstructed value must be interpreted according to its provenance.

A venue-native value is supported only when the archived observation records that value from an authoritative venue source and the applicable acquisition regime identifies it as native.

A derived value, such as a midpoint calculated from best bid and best ask, remains a derived value even when it is stored in a field historically associated with a native mark.

Native and derived values must not be treated as semantically interchangeable.

When a native mark is unavailable, a midpoint or other deterministic proxy may support comparison of observable state, but it must be identified as a proxy and must not be described as the venue-native mark.

## Temporal Boundary

Reconstruction is limited to the archived investigation window and to the observation coverage available within that window.

A reconstructed snapshot is evidence of the market state represented by the archived observations at their recorded observation times. It is not evidence of market conditions:

* before the earliest supported observation;
* after the latest supported observation;
* during undocumented gaps;
* at timestamps for which the required fields were not captured;
* between observations except where the methodology explicitly defines a deterministic rule.

Missing observations reduce the available evidence. They are not filled using undocumented interpolation, later state, assumed continuity, or venue behavior inferred from other periods.

A sequence of snapshots may establish persistence within the retained window. It does not establish that the same condition existed before the window began or continued after the window ended.

Venue timestamps and collector observation timestamps may describe different temporal properties. Venue timestamp age, collector lag, network delay, and application delay must not be treated as equivalent unless the required telemetry is available to distinguish them.

## Acquisition-Regime Boundary

Historical observations may have been produced under different acquisition methods, transports, field semantics, and provenance regimes.

Interpretation is governed by the recorded evidence for each observation, including where available:

* `ingest_type`;
* `transport`;
* payload shape;
* field provenance;
* venue timestamp;
* collector metadata;
* applicable historical acquisition regime.

A historical corpus must not be treated as uniformly REST-derived, uniformly WebSocket-derived, or semantically uniform.

Regime boundaries describe the retained evidence documented by the applicable inventory. They do not necessarily establish exact collector deployment, shutdown, or traffic-cutover times unless those facts are supported separately.

Unknown regime bounds remain unknown. Gaps and overlaps in retained observations must be preserved rather than normalized into artificial cutover timestamps.

## Attribution Boundary

External Reconstruction alone cannot determine:

* why an execution occurred;
* why a routing decision was made;
* why a strategy submitted, modified, or cancelled an order;
* whether an internal system behaved correctly;
* whether a collector or exchange caused a timing anomaly;
* whether an execution outcome was avoidable;
* who was responsible for an execution outcome.

Those conclusions require additional evidence such as:

* order submissions;
* exchange acknowledgements;
* fills and cancellations;
* routing decisions;
* OMS and EMS records;
* strategy decision logs;
* collector logs;
* application logs;
* network telemetry;
* system telemetry;
* risk decisions;
* exchange status information;
* fees and execution benchmarks.

External Reconstruction can provide the external market-state context against which that internal evidence is evaluated. It cannot replace the internal evidence.

## Operational Boundary

Externally observable venue state and the operation of the collection system are separate subjects.

A stale or missing archived observation may be consistent with multiple explanations, including:

* venue publication delay;
* network interruption;
* collector delay;
* application backpressure;
* persistence failure;
* archive failure;
* incomplete retention.

External market observations alone are insufficient to distinguish among these explanations.

Collector fault, exchange fault, network fault, application fault, and storage fault require operational telemetry appropriate to the component being evaluated.

## Independent Review

An independent reviewer can verify, subject to the available evidence:

* the archived observations used as inputs;
* the reconstruction window;
* field definitions;
* acquisition provenance;
* historical regime classification;
* deterministic metric computation;
* canonical consensus computation;
* disagreement metrics;
* operational episode detection;
* investigation summaries;
* whether reproduced outputs match the published investigation artifacts.

An independent reviewer cannot verify, without additional evidence:

* executable liquidity beyond the captured level;
* queue position;
* hidden liquidity;
* execution quality;
* order-routing decisions;
* strategy intent;
* internal system behavior;
* end-to-end latency attribution;
* fault;
* causality;
* responsibility;
* execution attribution.

Independent reproducibility establishes that the published methodology produces the published result from the published evidence. It does not establish conclusions that the evidence itself cannot support.

## Report Interpretation

An investigation report should be interpreted as a bounded statement about the externally observable evidence included in that investigation.

The report should not be read as claiming:

* a complete reconstruction of all market activity;
* a reconstruction of unobserved order-book depth;
* proof of fair value;
* proof of an executable price;
* proof of venue or collector fault;
* proof of causality;
* proof of responsibility;
* proof of execution quality.

Where a report contains qualified language, provenance warnings, unknown classifications, or reduced reconstruction confidence, those limitations are part of the result and must not be removed from interpretation.

## Versioning

Each investigation should be interpreted using the methodology, field definitions, schema versions, provenance rules, and historical regime information applicable when it was generated.

Later methodology or documentation changes do not retroactively change the meaning of a previously generated investigation.

A later implementation may reproduce an earlier result only when it applies the recorded historical methodology and field semantics or explicitly documents the effect of any migration.

## Related References

* [Reconstruction Standard](../specifications/reconstruction-standard.md)
* [Provenance Standard](../specifications/provenance-standard.md)
* [Canonical Field Specification](../specifications/canonical-field-specification.md)
* [Historical Acquisition Regimes](historical-acquisition-regimes.md)
* [Architecture](architecture.md)
