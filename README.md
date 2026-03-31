# SoftSkills

SoftSkills is an AI-driven simulation, assessment, and progression platform for
practising consultancy and professional skills in tech and AI contexts.

This repository currently holds the canonical MVP documentation used to guide
product and engineering development.

## What Is Here

### Operations & Documentation

- `ops/CONSTITUTION.yml`: non-negotiable architectural, testing, and operating rules
- `ops/mvp-spec/`: canonical MVP documentation set
- `ops/ROADMAP.md`: detailed backend execution roadmap
- `ops/sprints/`: sprint-by-sprint execution docs
- `ops/process/`: sprint execution process, templates, and Stageflow reporting
- `ops/post-mvp-spec/`: explicitly deferred post-MVP ideas

### Backend (`backend/src/soft_skills_backend/`)

```
soft_skills_backend/
├── entrypoints/http/     # FastAPI routes, schemas, dependencies
│   └── routes/          # API endpoint handlers
├── platform/             # Framework/runtime concerns
│   ├── container.py      # Dependency injection container
│   ├── db/              # SQLAlchemy models, session, repositories
│   ├── observability/   # Logging, middleware, event sink
│   ├── providers/llm/   # LLM provider adapters
│   └── workflows/       # Stageflow runtime integration
├── modules/              # Business features
│   ├── practice/        # Practice sessions, attempts, assessment
│   ├── catalog/         # Collections, prompt items, scenarios
│   ├── identity/        # User registration, authentication
│   └── taxonomy/        # Skills and competencies
└── shared/              # Cross-cutting: errors, ports, auth
```

Each business module follows a consistent layer pattern:

- `contracts/` - Command/query/view DTOs (Pydantic request/response types)
- `domain/` - Pure business rules, invariants, policies (no framework deps)
- `use_cases/` - Thin application service facades
- `workflows/` - Stageflow pipelines and stage implementations
- `infra/` - Repositories, persistence mappers, event recording

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

## Running the Backend

```bash
cd backend
pip install -e .
python -m soft_skills_backend
```

Run tests:
```bash
cd backend
pytest tests/ -v
```

Run linting:
```bash
cd backend
ruff check src/
mypy src/
```

## Architecture Principles

1. **Feature-first at business level, layer-second inside each feature**
2. **Platform/framework code separated at top level** - `entrypoints/`, `platform/`, `modules/`, `shared/`
3. **Domain stays pure** - No SQLAlchemy, FastAPI, or Stageflow imports
4. **Stageflow code only in workflows/** - No stage closures buried in service facades
5. **Persistence code only in infra/** - Queries, persistence, repositories live together
6. **One public facade per feature** - Routes call `modules.<feature>.use_cases` only
