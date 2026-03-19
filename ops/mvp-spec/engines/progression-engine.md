# Progression Engine (App-Agnostic)

## Purpose

Provide a reusable pipeline that converts validated assessments into persistent views of learner capability across arbitrary dimensions. Host products supply their own taxonomies (e.g., skills, behavioral anchors, outcomes) and aggregate layers, while the engine guarantees consistent aggregation, explainability, versioning, and observability across domains.

## Design Principles

1. **Evidence-only** — only validated, versioned assessments affect progression state.
2. **Deterministic & replayable** — identical inputs + config must produce identical outputs.
3. **Recency without amnesia** — recent evidence is weighted more, but historical meaning remains recoverable.
4. **Confidence-aware** — proficiency and confidence are tracked separately.
5. **Versioned semantics** — decay curves, weighting, and thresholds are external config artifacts with explicit versions.
6. **Explainable** — every change references the assessments and weights that caused it.

## Core Inputs

| Input | Description |
| --- | --- |
| `assessment_event` | Validated artifact containing learner/entity ID, dimension-level scores, timestamps, rubric/prompt versions, trace metadata |
| `dimension_catalog` | Domain-provided list of measurable dimensions (e.g., skills, behaviors, criteria) plus metadata such as grouping and prerequisites |
| `aggregate_model` | Optional weighted grouping of dimensions into higher-level aggregates (e.g., competencies, themes, KPIs) |
| `engine_config` | Versioned parameters: decay profiles, confidence thresholds, minimum evidence counts, gating rules |
| `recalc_request` | Optional command to replay historical data under a new config or corrected logic |

All inputs carry version metadata (`rubric_version`, `engine_config_version`, etc.) so outputs can be replayed.

## Dimension-Level Aggregation

1. **Normalization** — convert rubric-specific scales into a canonical range (e.g., 0–1) using adapters.
2. **Decay weighting** — apply configured decay curves (exponential, segmented linear, stepwise) per dimension.
3. **Rolling state** — maintain per-dimension aggregates: weighted score, evidence count, recent evidence count, streak indicators, last update timestamp.
4. **Confidence computation** — derive a confidence score/band from evidence volume, recency, and variance.
5. **Explainability ledger** — store contributing assessment IDs, weights, and decay factors for replay and UI drill-down.

## Aggregate Computation

1. Pull constituent dimensions and weighting from the domain-provided aggregate model.
2. Compute aggregate scores via weighted combination of the latest dimension states.
3. Derive aggregate confidence via weighted combination or minimum of constituent dimension confidences.
4. Apply gating rules (e.g., aggregate score cannot exceed threshold if a critical dimension remains below a floor).

## Update Pipeline

1. **Ingest** — validate assessment schema, ensure status is `validated`, dedupe superseded artifacts.
2. **Dimension update** — recompute per-dimension aggregates atomically, recording config version.
3. **Aggregate recompute** — refresh impacted aggregates based on updated dimensions.
4. **Snapshot emission** — persist snapshot containing dimension/aggregate vectors, confidence, config version, and trace linkage.
5. **Event publication** — emit event for downstream consumers (dashboards, recommendation engines) with delta summary.
6. **Observability** — log structured record capturing inputs, outputs, and validation/failure status.

## Recalculation & Drift Handling

- **Triggers**: rubric changes, scoring model updates, bug fixes, config tweaks.
- **Process**:
  1. Freeze current progression state and config version.
  2. Replay historical assessments through new config in isolation.
  3. Diff outputs; produce audit report with aggregate and per-learner changes.
  4. Upon approval, promote new config version and persist changelog references in learner history.
- **Audit artifacts** store `recalc_id`, input window, configs, before/after summaries, and trace IDs.

## Failure Modes & Safeguards

| Failure | Mitigation |
| --- | --- |
| Missing version metadata | Reject assessment; alert upstream system |
| Contradictory assessment data | Escalate to marking engine validation; pause progression update |
| Decay misconfiguration causing data loss | Validate configs before deployment; enforce minimum lifetime retention |
| Oscillation from sparse data | Require minimum evidence count before large score shifts; cap per-update delta |

## Observability Requirements

- Emit traces per update containing `trace_id`, `entity_ref`, `assessment_id`, `dimensions_updated`, `aggregates_updated`, `config_version`, `latency`, `status`.
- Maintain metrics: update latency, queue depth, failure rate, evidence distribution per dimension, confidence band counts.
- Provide APIs/UI hooks for inspecting the explainability ledger per learner.

## Evaluation & Testing

1. **Deterministic unit tests** covering aggregation math, decay application, gating logic, and confidence computation.
2. **Replay harness** to verify that re-running historical data reproduces stored snapshots.
3. **Canary comparisons** when rolling out new configs—compare aggregate dimension deltas vs. prior version.
4. **Quality metrics** linking downstream outcomes (e.g., recommendation effectiveness) to progression signals to detect drift.

## Integration Guidance

- Host applications provide adapters translating their assessment schema into the engine’s canonical input contract.
- Progress snapshots are exposed via APIs/events for dashboards, recommendation engines, and analytics.
- Configuration artifacts live in source control with review + rollout process; engine loads them at startup or via hot-reload hooks.

## Adoption Checklist

1. Implement adapters for assessment input and taxonomy definitions.
2. Define and version engine configuration (decay, thresholds, gating rules).
3. Wire observability (logs, metrics, traces) per engine requirements.
4. Build replay datasets before first production deployment.
5. Establish governance for updating configs and running recalculations.
