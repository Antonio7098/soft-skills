# Soft Skills Recommendation Engine

## Purpose

This document captures the Soft Skills application-specific recommendation engine. It sits inside the Soft Skills Progress Engine service to decide each learners next best practice step, honoring the platforms competency-first domain model, reinforcing the `practice -> assess -> reflect -> progress -> repeat` loop, and remaining explainable, traceable, and observable. It extends the shared capabilities described in `recommendation-engine.md` with Soft Skills taxonomy, personas, and content model.

## Design Principles

1. **Evidence-first** 1 outputs are derived from validated assessments, never raw attempts.
2. **Weakness-driven** 1 prioritize weak, stagnating, or under-practiced skills before novelty.
3. **Goal-aware** 1 respect learner goals, role targets, and preferred practice mode.
4. **Explainable** 1 every recommendation carries reason codes tied to data.
5. **Auditable** 1 decisions emit traces, inputs, weights, and outcomes for replay.

## Required Inputs

| Input | Source | Notes |
| --- | --- | --- |
| Learner profile | Identity/Profile service | Goals, target role, practice preferences, time budget |
| Assessment history | Assessment Pipeline | Only validated assessments with rubric & prompt versions |
| Progress snapshot | Progress Engine | Rolling skill/competency aggregates with evidence and confidence |
| Content graph | Content Catalog | Collections/items with skill tags, difficulty, verification state |
| System constraints | Config/Admin tools | Cooldowns, forced assignments, prerequisite rules |

## Feature Derivation

- **Skill Deficit Score** = target proficiency  current proficiency, weighted by confidence.
- **Stagnation Indicator** = low slope of improvement despite recent practice volume.
- **Coverage Gap** = important skills with insufficient evidence relative to learner goals.
- **Readiness Signal** = do prerequisite skills meet minimum thresholds for harder content?
- **Content Suitability Vector** = cosine-like similarity between item skill tags and active deficits, filtered by learner preferences, novelty, and verification level.

## Scoring Pipeline

1. **Candidate retrieval**
   - Filter content items by: skill tag overlap, practice mode, difficulty band, verification state, freshness (no recent repeats), and admin assignments.
   - Include at least one verified collection when available; fall back to trusted user-authored items with quality signals.

2. **Composite scoring**
   ```
   score = w1 * skill_deficit_alignment
         + w2 * stagnation_relief
         + w3 * coverage_gap_fit
         + w4 * goal_alignment
         - w5 * recent_repeat_penalty
         + w6 * admin_priority_boost
   ```
   - Weights are tiered by persona (e.g., early-career vs. advanced) but must be versioned and logged.

3. **Constraint enforcement**
   - Fails closed if candidate lacks stable rubric/skill mapping.
   - Respect cooldown windows and prerequisite requirements.
   - Enforce variety quotas (e.g., not more than two consecutive quick practices if goals require scenario depth).

4. **Decision + explanation**
   - Return top-N recommendations with reason codes such as `weak_skill`, `coverage_gap`, `goal_match`, `admin_assignment`.
   - Provide fallback alternatives so UI can offer "Try another" without recomputing.

## Output Contract

```json
{
  "recommendation_id": "UUID",
  "generated_at": "timestamp",
  "learner_id": "UUID",
  "context_snapshot_id": "hash",
  "items": [
    {
      "content_id": "UUID",
      "content_version": "v1",
      "score": 0.78,
      "reasons": ["weak_skill:expectation_setting", "goal_alignment:consulting"],
      "cooldown_expires_at": "timestamp"
    }
  ],
  "weights_version": "rec-weights-2026-03",
  "trace_id": "TRACE"
}
```

## Observability & Audit Trail

- Emit structured events with `trace_id`, `weights_version`, input snapshot hash, candidate list, component scores, selected items, and constraint decisions.
- Store recommendation artifacts separately from learner-facing history but link via `recommendation_id` for diagnostics.
- Include latency metrics and failure codes (e.g., `NO_CANDIDATES`, `MISSING_PROGRESS_SNAPSHOT`).

## Evaluation Strategy

1. **Offline replay**
   - Run historical learner timelines through the recommender and simulate outcomes to ensure selected items would have targeted the skills that later improved.
   - Compare against baselines (random, "weakest skill only," etc.) using uplift in targeted skill scores and completion rates.

2. **Online metrics**
   - Track completion rate of recommended content, improvement delta on targeted skills, rate of recommendation dismissals, and engagement after dismissals.
   - Monitor drift via rolling windows; alert when acceptance or effectiveness drops below thresholds.

3. **A/B guardrails**
   - When updating weights or features, run staged rollouts with regression gates tied to assessment quality and user satisfaction.

## Integration Points

- **Progress Engine** supplies progression snapshots and hosts the recommendation service.
- **Assessment Pipeline** streams validated assessments that trigger progression refresh and recommendation recalculation.
- **Content Catalog API** provides skill-tagged content metadata and availability.
- **Admin tools** can pin or override recommendations for cohorts; overrides are stored as constraint inputs.
- **Frontend** dashboard consumes the Recommendation API, displaying transparent reason codes and allowing users to request alternatives.

## Open Questions / Next Steps

1. Define versioned weight sets and governance process for updating them.
2. Agree on prerequisite graphs per collection difficulty tier.
3. Implement schema validation + observability tests for recommendation outputs.
4. Build offline replay harness and seed with at least two benchmark cohorts before production rollout.
