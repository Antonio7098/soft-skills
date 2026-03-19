# Recommendation Engine (App-Agnostic)

## Purpose

Provide a reusable service that turns learner/activity state plus content metadata into transparent, explainable next-step recommendations. The engine should be embeddable in any practice or learning product by swapping adapters for domain taxonomies, scoring semantics, and content types.

## Design Principles

1. **Contract-first** — expose typed request/response schemas independent of any specific dimension model.
2. **Evidence-driven** — recommendations are built on validated performance signals, not raw activity.
3. **Explainable and auditable** — every output carries reason codes, trace IDs, and references to input snapshots.
4. **Configurable** — weights, constraints, and persona logic are supplied via versioned configuration artifacts.
5. **Fail-closed** — missing schema fields, stale versions, or invalid candidates cause explicit errors.

## Core Inputs

| Input | Description |
| --- | --- |
| `learner_context` | Goals, persona tags, preferences, optional constraints provided by host app |
| `progress_snapshot` | Normalized capability vectors (dimensions + aggregates) with scores, confidence, evidence counts |
| `assessment_history` | Recent validated assessments when incremental evidence is required |
| `content_catalog_view` | Candidate items with typed metadata: dimensions, aggregates, modes, difficulty, verification states |
| `engine_config` | Versioned file defining weights, cooldown windows, constraint rules, persona mappings |

All inputs must include version metadata so recommendations can be replayed.

## Candidate Selection & Scoring

1. **Adapter layer** transforms host-domain metadata into canonical structures (dimensions, tags, prerequisite graphs).
2. **Candidate retrieval** applies filters from config (dimension overlap, freshness, verification state, admin pins).
3. **Scoring function** combines reusable components:
   ```
   score = Σ (component_i(input_snapshot, candidate) * weight_i)
   ```
   Common components include deficit alignment, stagnation relief, coverage gap, goal alignment, novelty penalty, admin boost. Projects can plug in new components if they conform to the interface.
4. **Constraint enforcement** ensures prerequisites, cooldowns, diversity quotas, and policy rules are satisfied.
5. **Decision + explanation** returns ordered recommendations with component breakdown, constraint notes, and alternative options.

## Output Contract

```json
{
  "recommendation_id": "UUID",
  "generated_at": "timestamp",
  "engine_version": "semver",
  "config_version": "rec-config-2026-03",
  "learner_ref": "opaque_id",
  "context_snapshot_id": "hash",
  "items": [
    {
      "content_ref": "opaque_id",
      "content_version": "v1",
      "score": 0.82,
      "component_breakdown": {
        "dimension_deficit_alignment": 0.4,
        "coverage_gap": 0.25,
        "goal_alignment": 0.2,
        "novelty_penalty": -0.03
      },
      "reasons": ["weak_dimension:negotiation", "goal_fit:consulting"],
      "cooldown_expires_at": "timestamp"
    }
  ],
  "trace_id": "TRACE",
  "observability": {
    "latency_ms": 120,
    "candidate_count": 32
  }
}
```

## Observability Requirements

- Emit structured logs/events containing trace IDs, config versions, candidate lists, component scores, constraint outcomes, and latency.
- Record failures with explicit error codes (`NO_CANDIDATES`, `SCHEMA_INVALID`, `CONFIG_MISSING`).
- Store recommendation artifacts separately for audit and replay.

## Evaluation & Testing

1. **Contract tests** — ensure adapters and engine respect schema invariants.
2. **Offline replay** — run historical learner timelines to compare engine behavior against baselines and prior versions.
3. **A/B guardrails** — track completion rate, targeted-dimension uplift, and user acceptance for new configs or code.
4. **Drift monitoring** — alert when effectiveness metrics fall outside bounds.

## Integration Guidance

- Host applications provide adapters for learner context and content metadata.
- Engine exposes both synchronous API (request/response) and asynchronous workflow hooks (event-driven refresh).
- Recommendation artifacts feed downstream systems (dashboards, notifications) via well-defined contracts.

## Extensibility

- Component plugin interface allows domain teams to add scoring dimensions without modifying core workflow.
- Constraint engine can load domain-specific rules (e.g., compliance checks) via configuration.
- Support multiple persona profiles simultaneously by sending persona identifiers in `learner_context`.

## Adoption Checklist

1. Supply domain taxonomy and adapter implementations.
2. Define configuration files (weights, constraints, cooldowns) with versioning.
3. Implement observability wiring (traces, logs, metrics) conforming to engine requirements.
4. Build evaluation datasets for offline replay before production rollout.
5. Document governance for updating configs and deploying new versions.
