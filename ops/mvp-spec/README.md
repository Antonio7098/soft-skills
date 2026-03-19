# SoftSkills MVP Canon

> **Location:** `soft-skills/ops/mvp-spec/`

This relocated `ops/mvp-spec` directory is the canonical documentation set for
the SoftSkills MVP. It exists to guide product, engineering, content, and
operational decisions during development and replaces any legacy copies that may
still exist elsewhere in the repo.

## Source Precedence

When documents disagree, use this order of precedence:

1. `CONSTITUTION.yml`
2. Files in `docs/`
3. `PRD.md`

The constitution defines non-negotiable architectural and product rules.
The docs in this directory turn those rules and the PRD into explicit MVP
decisions. The PRD remains the upstream product input, but it is not the
runtime source of truth once this canon exists.

## Canonical Documents

- `product-spec.md`: MVP purpose, users, scope, outcomes, and resolved product decisions
- `domain-model.md`: core entities, relationships, lifecycle states, and invariants
- `assessment-and-progression.md`: rubric semantics, scoring outputs, feedback rules, and progression model
- `marking-engine.md`: reusable marking pipeline, artifact contracts, evaluation framework, and calibration rules
- `content-system.md`: collection structure, authoring flows, publication rules, and realism constraints
- `technical-architecture.md`: system boundaries, stack decisions, repository structure, and delivery rules
- `observability-and-operations.md`: traces, events, logging, error taxonomy, metrics, and release gates
- `recommendation-engine.md` / `progression-engine.md`: platform-agnostic engines for capability recommendation and progression
- `soft-skill-recommendation.md` / `soft-skill-progression.md`: Soft Skills implementations that extend the shared engines with the platform taxonomy

## Working Rules

- Build the MVP around the `practice -> assess -> reflect -> progress -> repeat` loop.
- Optimize for demonstrated competency growth, not engagement theater.
- Treat text-first practice as the MVP baseline. Voice can be layered later, but it is not required for MVP completeness.
- Do not implement features that violate explainability, schema validation, traceability, or durable persistence.
- When a new product or engineering decision changes behavior, update the relevant file in this directory in the same change.

## MVP Decision Style

The PRD contains open questions. For MVP execution, these docs resolve them
where a default is necessary to keep development unblocked. Anything still
uncertain should be added explicitly as a pending decision rather than left
implicit in code.
