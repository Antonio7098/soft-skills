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

The canon is now grouped into subfolders to keep related artifacts together:

- `foundational/`
  - `PRD.md`, `product-spec.md`, `domain-model.md`, `technical-architecture.md`
- `platform/`
  - `assessment-and-progression.md`, `soft-skill-progression.md`, `soft-skill-recommendation.md`
- `engines/`
  - `marking-engine.md`, `recommendation-engine.md`, `progression-engine.md`
- `operations/`
  - `content-system.md`, `observability-and-operations.md`

Each file keeps the same intent detailed below; only the paths changed.

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
