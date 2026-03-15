# SoftSkills

SoftSkills is an AI-driven simulation, assessment, and progression platform for
practising consultancy and professional skills in tech and AI contexts.

This repository currently holds the canonical MVP documentation used to guide
product and engineering development.

## What Is Here

- `PRD.md`: original product requirements document
- `CONSTITUTION.yml`: non-negotiable architectural, testing, and operating rules
- `docs/`: canonical MVP documentation set
- `ops/`: delivery and execution documents, including the MVP roadmap

## Source Of Truth

When documents disagree, use this order:

1. `CONSTITUTION.yml`
2. `docs/`
3. `PRD.md`

## Start Here

- Read [`docs/README.md`](./docs/README.md) for the MVP canon
- Read [`docs/product-spec.md`](./docs/product-spec.md) for product scope and resolved MVP decisions
- Read [`docs/technical-architecture.md`](./docs/technical-architecture.md) for architecture constraints
- Read [`ops/ROADMAP.md`](./ops/ROADMAP.md) for the backend-first implementation checklist

## Key MVP Constraints

- The core loop is `practice -> assess -> reflect -> progress -> repeat`
- Competency growth is the product outcome
- Assessment must be explainable and traceable
- Complex provider-backed flows require real-provider smoke tests before release
- Auth providers and databases must be swappable through interfaces and dependency injection

## Current State

This repo is documentation-first at the moment. The next implementation work
should follow the canonical docs and the roadmap rather than extending the PRD
directly.
