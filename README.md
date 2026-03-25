# SoftSkills

SoftSkills is an AI-driven simulation, assessment, and progression platform for
practising consultancy and professional skills in tech and AI contexts.

This repository currently holds the canonical MVP documentation used to guide
product and engineering development.

## What Is Here

- `ops/CONSTITUTION.yml`: non-negotiable architectural, testing, and operating rules
- `ops/mvp-spec/`: canonical MVP documentation set
- `ops/ROADMAP.md`: detailed backend execution roadmap
- `ops/sprints/`: sprint-by-sprint execution docs
- `ops/process/`: sprint execution process, templates, and Stageflow reporting
- `ops/post-mvp-spec/`: explicitly deferred post-MVP ideas

## Source Of Truth

When documents disagree, use this order:

1. `ops/CONSTITUTION.yml`
2. `ops/mvp-spec/`
3. `ops/ROADMAP.md` and `ops/sprints/`
4. `ops/post-mvp-spec/`

## Start Here

- Read [`ops/mvp-spec/README.md`](./ops/mvp-spec/README.md) for the MVP canon
- Read [`ops/CONSTITUTION.yml`](./ops/CONSTITUTION.yml) for the architectural and testing rules
- Read [`ops/ROADMAP.md`](./ops/ROADMAP.md) for the high-level execution sequence
- Read [`ops/sprints/README.md`](./ops/sprints/README.md) for sprint order and per-sprint docs
- Read [`ops/process/sprint-execution.md`](./ops/process/sprint-execution.md) before starting implementation work

## Key MVP Constraints

- The core loop is `practice -> assess -> reflect -> progress -> repeat`
- Competency growth is the product outcome
- Assessment must be explainable and traceable
- Complex provider-backed flows require real-provider smoke tests before release
- Auth providers and databases must be swappable through interfaces and dependency injection

## Current State

This repo is documentation-first at the moment. The next implementation work
should follow `ops/CONSTITUTION.yml`, the relevant `ops/mvp-spec/` files, and
the active sprint doc rather than extending old planning documents directly.
