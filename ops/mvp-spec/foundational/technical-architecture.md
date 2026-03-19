# Technical Architecture

## Architecture Principle

The system must be modular, typed, schema-validated, and explicit about
orchestration. Observability is part of the architecture, not an afterthought.

## Required Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- OpenAI SDK
- Stageflow

### Frontend

- TypeScript
- React
- Vite

## Architectural Rules

- All external boundaries must be schema-validated.
- Route handlers stay thin and delegate to application or domain services.
- Domain logic must remain independent from UI and persistence concerns.
- Stageflow orchestrates workflows but does not become a god layer.
- Invalid state should fail loudly with stable error codes.

## MVP System Areas

### Identity And Profile

Owns account creation, learner profile, goals, target roles, and permissions.
The MVP permission model should assume standard user accounts plus admin.

### Content Catalog

Owns collections, prompt items, scenarios, mock-world assets, browsing, and
publication state.

### Practice Runtime

Owns session start, prompt delivery, learner attempt submission, and attempt
state transitions.

### Assessment Pipeline

Owns rubric selection, prompt execution, output validation, assessment
persistence, and feedback delivery.

### Progress Engine

Owns skill history, competency history, recommendation inputs, and dashboard
aggregation.

### Admin Analytics

Owns learner, cohort, and collection-level reporting views.

### Observability Layer

Owns traces, structured events, logs, prompt metadata, and workflow diagnostics.

## Boundary Guidance

### API Layer

- expose explicit request and response schemas
- version contracts deliberately
- never return raw ORM models

### Domain Layer

- model skills, competencies, rubrics, content, attempts, assessments, and progression
- enforce core invariants
- avoid framework leakage

### Orchestration Layer

- coordinate multi-step workflows
- emit step-level traces
- keep business rules in dedicated services or domain modules

### Persistence Layer

- store transactional product data separately from observability-heavy event data where useful
- evolve schemas only through Alembic migrations
- preserve versions for scoring-relevant artifacts

### Frontend Layer

- use strict TypeScript
- build from reusable primitives and token-driven design system foundations
- provide consistent loading, error, empty, and success states
- make asynchronous work feel active and informative

## Recommended Repository Shape

The exact folder names can vary, but responsibilities should remain clear.

```text
backend/
  api/
  domain/
  application/
  orchestration/
  persistence/
  schemas/
  prompts/
  observability/
frontend/
  app/
  features/
  components/
  design-system/
  lib/
docs/
```

## Non-Functional Requirements

### Performance

- quick practice feedback should feel near-immediate
- longer scenario scoring should still present visible progress and state

### Reliability

- attempts must never be silently lost
- failures must surface with machine-readable and human-readable context

### Consistency

- scoring semantics, rubrics, and prompts must be versioned
- frontend interaction patterns should remain consistent across similar surfaces

### Documentation

- core workflows, prompt contracts, event models, and scoring semantics must be documented alongside implementation

### Testing

- domain logic requires deterministic tests
- Pydantic contracts require positive and negative coverage
- FastAPI contracts require endpoint tests
- Stageflow flows require success, failure, retry, and trace tests
- frontend contract boundaries and critical flows require coverage

## MVP Delivery Gates

No MVP slice is complete unless it includes:

- typed schemas
- persistence for critical artifacts
- structured errors
- structured logs
- trace emission
- tests for the main path and failure path
- corresponding documentation updates
