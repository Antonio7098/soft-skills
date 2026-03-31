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

## Docker & Cloud Run Deployment

Build and deploy both frontend and backend as a single container:

```bash
# Build the image
docker build -t softskills .

# Run locally
docker run -p 8080:8080 softskills

# Deploy to Cloud Run
gcloud run deploy softskills \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="SOFT_SKILLS_DATABASE_URL=your-db-url"
```

**Note:** For production, use Cloud SQL or another managed database instead of SQLite.

### Cloud SQL Setup

1. Create a Cloud SQL PostgreSQL instance:
```bash
gcloud sql instances create softskills-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1
```

2. Create a database:
```bash
gcloud sql databases create softskills --instance=softskills-db
```

3. Get the connection name:
```bash
gcloud sql instances describe softskills-db --format="value(connectionName)"
```

4. Set the database URL in Cloud Run:
```bash
SOFT_SKILLS_DATABASE_URL="postgresql+psycopg2://USER:PASSWORD@/softskills?host=/cloudsql/PROJECT:REGION:INSTANCE"
```

### Required Environment Variables

Set these in Cloud Run or your deployment environment:

- `SOFT_SKILLS_DATABASE_URL` - PostgreSQL connection string (see Cloud SQL setup above)
- `SOFT_SKILLS_OPENROUTER_API_KEY` - OpenRouter API key
- `GROQ_API_KEY` - Groq API key
- `DEEPGRAM_API_KEY` - Deepgram API key
- `SOFT_SKILLS_CORS_ALLOWED_ORIGINS` - Allowed CORS origins (comma-separated)

For Cloud SQL, also add the `--add-cloudsql-instances` flag when deploying:
```bash
gcloud run deploy softskills \
  --add-cloudsql-instances PROJECT:REGION:INSTANCE
```

### Security Note

The container runs as root to allow nginx to bind to port 8080. For production hardening, consider:
- Using a non-root user with proper nginx configuration
- Setting up proper file permissions
- Using a read-only filesystem where possible

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
