# Soft Skills Progression Engine

## Purpose

This document describes the Soft Skills applications progression engine implementation. It translates validated assessments into persistent views of learner skill and competency growth, powering Soft Skills dashboards, recommendation inputs, and admin reporting so improvements reflect repeated evidence rather than isolated spikes. It operates inside the Soft Skills Progress Engine system area, extends the platform-agnostic contracts defined in `progression-engine.md`, and must stay explainable, auditable, and reproducible.

## Design Principles

1. **Evidence over activity**  only validated assessments update progression; raw attempts never do.
2. **Recency with memory**  recent evidence carries more weight but historical performance remains visible and reconstructable.
3. **Confidence tracking**  proficiency and confidence are separate signals derived from evidence volume and freshness.
4. **Version awareness**  rubric, prompt, and scoring changes never silently rewrite past meaning; recalculations are explicit workflows.
5. **Explainable outputs**  every progression change links back to concrete assessment artifacts and weights.

## Required Inputs

| Input | Source | Notes |
| --- | --- | --- |
| Validated assessment artifacts | Assessment Pipeline | Include skill-level scores, rubric/prompt versions, timestamps, trace IDs |
| Skill/competency taxonomy | Domain Model | Defines weighting of skills within competencies and required invariants |
| Learner profile & goals | Identity/Profile | Provides target role, focus competencies, practice preferences |
| Progress configuration | Progress Engine config | Defines decay factors, recency windows, minimum evidence counts |
| Recalculation instructions | Admin / ops tooling | Triggered when rubrics or models change meaning |

## Skill Progress Computation

1. **Evidence normalization**
   - Extract skill-level scores from each assessment.
   - Standardize onto canonical scale (e.g., 01) respecting rubric anchors.
   - Attach metadata: `assessment_id`, `rubric_version`, `prompt_version`, `timestamp`, `trace_id`.

2. **Weighted aggregation**
   - Maintain rolling windows (e.g., last 90 days) plus lifetime history.
   - Compute weighted average score per skill: `score = (Σ evidence_i * decay_factor_i) / Σ decay_factor_i`, where `decay_factor` decays smoothly with age but never reaches zero within retention horizon.
   - Track `evidence_count`, `recent_count` (last N days), and `streak` indicators (consecutive assessments above threshold).

3. **Confidence signal**
   - Map evidence volume and recency into qualitative bands (e.g., Low/Medium/High) or numerical confidence score `confidence = sigmoid( evidence_count_recent / min_required )`, capped by time since last evidence.
   - Skill changes below a minimum evidence delta remain tentative and are flagged for low confidence.

4. **Explainability ledger**
   - For each skill update, store contributing assessment IDs and their weights to enable replay and UI drill-down.

## Competency Progress Computation

1. **Skill projection**
   - For each competency, pull constituent skills and weighting from the taxonomy (weights sum to 1).

2. **Aggregation**
   - `competency_score = Σ (skill_score_i * weight_i)` using the latest skill scores.
   - Confidence inherits the minimum of contributing skills or a weighted combination, ensuring a weakly evidenced skill keeps competency confidence low.

3. **Threshold handling**
   - Apply floor/ceiling logic where competencies require minimum proficiency in critical skills (e.g., stakeholder management cannot exceed 0.6 if expectation setting < 0.4).

## Progress Update Pipeline

1. **Ingest assessment event**
   - Validate schema, ensure assessment status == `validated`.
   - Check for duplicates or superseded artifacts.

2. **Skill update transaction**
   - Update per-skill rolling aggregates and confidence metrics atomically.

3. **Competency recompute**
   - Recalculate impacted competencies using updated skill values.

4. **Snapshot emit**
   - Persist progression snapshot with versioned config identifiers (`progress_config_version`, `decay_profile_version`).
   - Publish event for downstream consumers (dashboard, recommender) containing delta summary and trace linkage.

5. **Observability**
   - Emit structured log with inputs, weights, outputs, and validation status.

## Recalculation & Drift Handling

- **Trigger conditions**: rubric reweighting, scoring model changes, bug fixes in aggregation logic.
- **Process**:
  1. Snapshot current progression state and config version.
  2. Replay historical validated assessments through updated pipeline in an isolated workspace.
  3. Diff old vs. new progression outputs; generate audit report.
  4. When approved, promote new config version and backfill learner-facing records with explicit changelog entry.
- **Audit**: every recalculation run stores `recalc_id`, input range, config version, and before/after summaries.

## Failure Modes & Safeguards

| Failure | Mitigation |
| --- | --- |
| Missing rubric/prompt version | Reject assessment before progression update |
| Contradictory assessment evidence | Escalate to marking engine validation; hold progression |
| Unbounded decay causing forgetfulness | Clamp decay factors, keep lifetime history for context |
| Rapid oscillations from sparse data | Require minimum evidence before large swings; cap per-update delta |

## Observability Requirements

- Emit traces for each progression update containing:
  - `trace_id`, `learner_id`, `assessment_id`, `skills_updated`, `competencies_updated`, `config_version`, `latency`, `status`.
- Maintain metrics: update latency, failure rate, queue depth, per-skill evidence distribution, confidence band counts.
- Provide admin dashboards to inspect individual learner evidence trails.

## Evaluation Strategy

1. **Deterministic tests**
   - Unit tests asserting aggregation math, decay behavior, threshold rules, and confidence mapping for fixed inputs.

2. **Replay harness**
   - Run anonymized learner timelines through the engine to verify reproducibility (same inputs produce same outputs) and check that replays match stored snapshots.

3. **Quality metrics**
   - Monitor correlation between recommended practice completions and subsequent skill score changes to validate that progression reflects real improvements.
   - Flag learners with high completion but flat progression for potential rubric or assessment drift investigations.

## Integration Points

- **Assessment Pipeline**: supplies validated artifacts via event stream.
- **Recommendation Engine**: consumes progression snapshots and evidence counts as primary inputs.
- **Dashboards (learner/admin)**: query progression snapshots for visualization, including confidence bands and evidence drill-down.
- **Observability Layer**: collects traces, metrics, and emits alerts on failure modes.

## Open Questions / Next Steps

1. Finalize decay profile parameters per practice mode (quick vs. scenario vs. interview).
2. Decide on confidence scale (numeric 01 vs. categorical) for UI consistency.
3. Implement replay tooling and storage for historical assessments to enable quick recalculations.
4. Define admin-facing changelog format when progression config versions change.
