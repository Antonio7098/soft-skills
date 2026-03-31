# Backend Architectural Audit Report

**Date:** 2026-03-27 (Updated: 2026-03-31)
**Scope:** `/home/antonioborgerees/df/soft-skills/backend/src/`  
**Approach:** SOLID principles, Clean Architecture, layered architecture boundaries, coupling analysis

---

## 1. Executive Summary

The backend implements a **layered architecture with DDD-inspired modules** using FastAPI, SQLAlchemy, and Stageflow. The codebase demonstrates good separation between HTTP entrypoints, application services, domain logic, and infrastructure. However, several **SOLID violations** and architectural concerns require attention, particularly the **monolithic `models.py`** file (52 models, increased from 31), the **God Object `AppContainer`** (26 attributes, expanded from 22), and **cross-layer coupling** in configuration (partially addressed).

**Overall Assessment:** Sound foundations with targeted refactoring needs. New `voice` module added for Deepgram transcription.

---

## 2. Project Structure

```
src/soft_skills_backend/
├── app.py                      # Application factory
├── config.py                   # Pydantic Settings (IMPROVED - see §5.2)
├── engines/                    # App-agnostic domain engines
│   ├── config/                 # JSON config loader
│   ├── progression/            # Progression computation
│   ├── recommendation/         # Recommendation computation
│   └── marking/                # LLM-based assessment
├── entrypoints/http/           # HTTP API layer
│   ├── routes/                 # Route modules
│   ├── dependencies.py          # DI helpers (HAS ISSUES - see §5.10)
│   ├── error_handlers.py       # Global error handling
│   └── schemas.py              # Response envelopes (HAS ISSUES - see §5.12)
├── modules/                    # DDD-style feature modules
│   ├── admin/
│   ├── admin_agent/            # (NEW since audit)
│   ├── assistant/
│   ├── catalog/
│   ├── evaluation/
│   ├── events/
│   ├── identity/
│   ├── organisations/
│   ├── practice/               # (HAS ISSUES - see §5.7)
│   ├── progression/
│   ├── taxonomy/               # (NEW since audit)
│   └── voice/                  # (NEW since audit - Deepgram transcription)
├── platform/                   # Infrastructure layer
│   ├── container.py            # DI container (HAS ISSUES - see §5.3)
│   ├── db/
│   │   ├── base.py             # SQLAlchemy declarative base
│   │   ├── models.py           # 52 models (CRITICAL - see §5.6, expanded from 31)
│   │   └── repositories.py      # Repository implementations
│   ├── observability/           # structlog, middleware, events
│   ├── providers/llm/           # OpenAI-compatible LLM adapter
│   └── workflows/              # Stageflow integration (HAS ISSUES - see §5.9)
└── shared/                      # Cross-cutting concerns
    ├── auth.py                  # Header-based auth (HAS ISSUES - see §5.4)
    ├── errors.py                # AppError (HAS ISSUES - see §5.5)
    └── ports/                   # Interface definitions
```

---

## 3. Layered Architecture Assessment

| Layer | Responsibility | Adherence |
|-------|---------------|-----------|
| **Entry Points** | HTTP routes, schemas, error handling | ✅ Good |
| **Application** | Use cases, service orchestration | ⚠️ Mixed - some SRP violations |
| **Domain** | Business rules, domain models | ✅ Good - engines isolate domain |
| **Infrastructure** | DB, LLM providers, observability | ⚠️ Mixed - models.py issue |
| **Shared** | Auth, errors, ports | ⚠️ Mixed - auth leaks persistence |

### Dependency Rule Compliance
**Partially violated.** Infrastructure (DB models) imported by domain via repositories, but no strict layer isolation enforcement (no `layered-architecture` linter).

---

## 4. Positive Architectural Decisions

1. **Engine isolation** (`engines/`): App-agnostic domain logic properly separated, enabling potential reuse
2. **Repository pattern**: `SqlAlchemyWorkflowEventRepository` etc. cleanly abstract persistence
3. **Port interfaces**: `LLMProvider` Protocol properly defines the contract
4. **Envelope pattern**: Consistent `ApiEnvelope[T]` response wrapper with correlation IDs
5. **Structured errors**: `SS-*` error codes provide stability for clients
6. **No circular dependencies**: Engine dependencies form a clean one-way chain
7. **Event sourcing-lite**: Workflow events persisted for auditing/replay

---

## 5. Design Principles Findings

### 5.1 `app.py` - Application Factory

| Principle | Assessment |
|-----------|------------|
| **SRP** | PARTIAL - Factory handles app creation + middleware + routing |
| **DIP** | VIOLATION - `app.state.container = resolved_container` stores concrete `AppContainer`, not an abstraction |

**Line 50:** No interface defined; consumers depend on concrete `AppContainer`.

---

### 5.2 `config.py` - Configuration Management

| Principle | Assessment |
|-----------|------------|
| **SRP** | ✅ RESOLVED - Lines 68-86 no longer call into `engines.config.loader` |
| **DIP** | ✅ RESOLVED - Config layer no longer depends on domain engines module |

**Status: FIXED** - The cross-layer dependency violation has been addressed. `creator_structured_generation_prompt_version` and `creator_chat_generation_prompt_version` properties (lines 198-204) now return local values instead of importing from `soft_skills_backend.engines.config.loader`.

---

### 5.3 `platform/container.py` - Dependency Injection

| Principle | Assessment |
|-----------|------------|
| **SRP** | VIOLATION - 26-attribute dataclass (God Object anti-pattern, expanded from 22) |
| **ISP** | VIOLATION - Any consumer sees all 26 services even if only needing 1 |
| **DIP** | VIOLATION - No abstract interfaces for services |

**Lines 92-117:** `AppContainer` bundles unrelated services (settings, session_factory, CatalogService, PracticeService, AdminAgentService, TaxonomyService, etc.). All concrete implementations with no interface abstractions. **NEW services added:** `admin_agent_service`, `taxonomy_service`, `assistant_broker`, `generation_broker`, `background_tasks`.

---

### 5.4 `shared/auth.py` - Authentication Design

| Principle | Assessment |
|-----------|------------|
| **SRP** | VIOLATION - `HeaderAuthProvider` mixes actor resolution, DB queries, org context |
| **ISP** | PARTIAL - `optional_actor` and `require_actor` share duplicated membership lookup |
| **DIP** | VIOLATION - Direct SQLAlchemy queries (`session.query`) in auth boundary |

**Line 40-50:** `_resolve_organisation_context` queries `OrganisationMembershipRecord` directly - **persistence leak into auth layer**.  
**Lines 52-72:** User lookup + org context conflated in `optional_actor`.  
**Lines 74-78, 80-88:** `require_actor` and `require_org_admin` duplicate logic from `optional_actor`.

---

### 5.5 `shared/errors.py` - Error Handling

| Principle | Assessment |
|-----------|------------|
| **SRP** | OK |
| **DRY** | VIOLATION - 7 factory functions (lines 38-146) are nearly identical |

All error factories (`validation_error`, `persistence_error`, `auth_error`, `domain_error`, `provider_error`, `scoring_error`, `orchestration_error`) create identical 5-field `AppError` instances with only `code`, `category`, `message`, `status_code`, and `details` differing.

---

### 5.6 `platform/db/models.py` - Database Models ⚠️ CRITICAL

| Principle | Assessment |
|-----------|------------|
| **SRP** | VIOLATION - **52 models in single file** (expanded from 31) |
| **Cohesion** | LOW - Observability, identity, catalog, practice, progression, evaluation, assistant, admin, voice, prompt models all mixed |
| **Coupling** | HIGH - All models in one file creates high coupling |

**Line 285:** `avg_rating: Mapped[float | None] = mapped_column(Integer, ...)` - **type mismatch still exists** (float mapped to Integer column).  
**No relationships defined:** Despite FKs, no SQLAlchemy `relationship()` objects exist.

**This remains the most critical code smell in the codebase.** Should be split by domain/feature. The file has grown significantly since the original audit.

---

### 5.7 `modules/practice/use_cases/practice_service.py` - Service Layer

| Principle | Assessment |
|-----------|------------|
| **SRP** | VIOLATION - `_start_practice_session` (~120 lines), `submit_attempt` (~200 lines) |
| **DIP** | VIOLATION - `AssessmentService` created internally (lines 77-80), not injected |
| **ISP** | VIOLATION - `set_marker()` setter pattern (line 392) exposes implementation detail |

**Lines 77-80:** `self._assessment = AssessmentService(...)` - internal composition instead of dependency injection.  
**Line 392:** `self._assessment.set_marker(...)` - setter injection violates encapsulation.  
**Lines 107-154:** Inline lambda-style stage functions hard to reuse and test.

---

### 5.8 `modules/catalog/use_cases/catalog_service.py` - Service Layer

| Principle | Assessment |
|-----------|------------|
| **SRP** | OK - Primarily a facade |
| **DIP** | VIOLATION - Sub-services created internally (lines 65-90) |
| **ISP** | VIOLATION - Hidden dependencies |

**Lines 65-90:** `CollectionService`, `PromptItemService`, `ScenarioService`, `CatalogGenerationService` all created internally rather than injected. Facade owns sub-service lifecycles - hidden dependencies violate DIP.

---

### 5.9 `platform/workflows/stageflow.py` - Workflow Orchestration

| Principle | Assessment |
|-----------|------------|
| **DRY** | VIOLATION - `run_logged_pipeline` (138-249) and `run_logged_subpipeline` (262-376) have ~50% duplicated code |

**Lines 138-249 vs 262-376:** Substantial duplication between these two functions.  
**Lines 38-39:** `event_sink: Any`, `get_default_interceptors: Callable[..., list[Any]]` - untyped due to external library.

---

### 5.10 `entrypoints/http/dependencies.py` - Route Dependencies

| Principle | Assessment |
|-----------|------------|
| **SRP** | VIOLATION - `require_verification_actor` (49-62) contains business logic |
| **DIP** | VIOLATION - All functions depend on concrete `AppContainer` |
| **ISP** | PARTIAL - No interface for container access |

**Lines 49-62:** Business logic (org admin check) embedded in dependency layer.  
**No interface:** Cannot easily mock container for testing.

---

### 5.11 `entrypoints/http/error_handlers.py` - Error Handlers

| Principle | Assessment |
|-----------|------------|
| **SRP** | OK |
| **Exception handling** | RISKY - Line 54 catches broad `Exception` including `KeyboardInterrupt`, `SystemExit` |

**Line 54:** `@app.exception_handler(Exception)` catches ALL exceptions.

---

### 5.12 `entrypoints/http/schemas.py` - API Schemas

| Principle | Assessment |
|-----------|------------|
| **ISP** | VIOLATION - `ApiEnvelope[T]` and `ErrorEnvelope` share structure |
| **DRY** | VIOLATION - `ResponseMeta` duplicated in both |
| **Generics** | PARTIAL - `T = TypeVar("T")` unconstrained; should be `bound=BaseModel` |

**Line 12:** `T = TypeVar("T")` should be `T = TypeVar("T", bound=BaseModel)`.

---

### 5.13 `modules/voice/transcription.py` - NEW Voice Module

| Principle | Assessment |
|-----------|------------|
| **SRP** | OK - Single responsibility: Deepgram transcription |
| **DIP** | PARTIAL - Hard dependency on Deepgram SDK with optional import pattern |
| **OCP** | OK - Graceful degradation when SDK unavailable |

**New module added since original audit** - Provides streaming voice transcription via Deepgram. Uses optional import pattern with `DEEPGRAM_AVAILABLE` flag for graceful fallback.

---

## 6. Repository Pattern Issues

**`platform/db/repositories.py`:**

| Issue | Location |
|-------|----------|
| DRY violation | `list_` (56-77) and `count` (90-107) share repeated filter logic |
| Auth leak | Lines 206-223, 225-242: ownership check in repository instead of service layer |

**`modules/practice/infra/repository.py`:**
- Lines 206-223: `get_attempt` contains authorization logic - **should be in service layer**
- Lines 225-242: `get_practice_run` same issue

---

## 7. Configuration Loading Risk

**`modules/progression/domain/progression.py` lines 58-59:**
```python
PROGRESSION_ENGINE_CONFIG = load_progression_engine_config()
RECOMMENDATION_ENGINE_CONFIG = load_recommendation_engine_config()
```

**Risk:** Config loaded at module import time. If JSON configs are missing or malformed, the entire module fails to import. Should use lazy initialization.

---

## 8. Summary of Violations by Principle

| Principle | Most Violated Files |
|-----------|---------------------|
| **SRP** | `models.py` (52 models, expanded from 31), `container.py` (26 attrs, expanded from 22), `practice_service.py` (large methods), `auth.py` (mixed concerns) |
| **ISP** | `container.py` (26 attributes), `AppError` factories (identical signatures) |
| **DIP** | `app.py`, `dependencies.py`, `catalog_service.py`, `practice_service.py` |
| **DRY** | `errors.py`, `stageflow.py`, `repositories.py`, `auth.py` |
| **LSP** | ✅ RESOLVED - `config.py` no longer calls engines module |

---

## 9. Recommendations

### Critical (Address Immediately)

1. **Split `platform/db/models.py`** into multiple files by domain (now **52 models**, expanded from 31):
   - `models/observability.py` (WorkflowEvent, PipelineRun, ProviderCall)
   - `models/identity.py` (UserAccount, Organisation, Membership)
   - `models/catalog.py` (Collection, PromptItem, Scenario, MockCompany, MockPerson, etc.)
   - `models/practice.py` (PracticeRun, PracticeSession, Attempt, Assessment)
   - `models/progression.py`, `models/evaluation.py`, `models/assistant.py`, `models/admin.py`, `models/voice.py`, `models/prompt.py`

2. **Fix `avg_rating` type mismatch** (line 285 in models.py): `mapped_column(Float, ...)` not `Integer`

3. **Add SQLAlchemy `relationship()` definitions** for FK keys currently with no relationships

### High Priority

4. **Extract service interfaces** from `container.py` - define `Protocol` classes for `CatalogService`, `PracticeService`, etc. (now 26 attributes, expanded from 22)

5. ~~**Fix config.py cross-layer dependency**~~ ✅ **RESOLVED** - Engine config loading removed from Settings class

6. **Remove auth persistence leak** - extract `HeaderAuthProvider` DB queries into a separate auth repository/service

7. **Extract business logic from `dependencies.py`** - `require_verification_actor` should delegate to a service

### Medium Priority

8. **Refactor `practice_service.py`**:
   - Inject `AssessmentService` instead of internal creation
   - Remove setter injection pattern
   - Extract large methods into smaller, single-responsibility methods

9. **Deduplicate error factories** in `errors.py` - single factory with category parameter, or shared base

10. **Consolidate `stageflow.py` duplication** - extract common logic in `run_logged_pipeline`/`run_logged_subpipeline`

11. **Constrain `TypeVar`** in `schemas.py`: `T = TypeVar("T", bound=BaseModel)`

12. **Fix broad exception handler** in `error_handlers.py` - exclude `KeyboardInterrupt`, `SystemExit`

### Low Priority

13. **Defer config loading** in `modules/progression/domain/progression.py` - lazy initialization instead of module-level loading

14. **Add `relationship()` objects** between SQLAlchemy models

15. **Centralize magic strings** (e.g., `X-User-ID`, `X-Organisation-ID`) into constants

---

## 10. Positive Notes

- **No circular dependencies** - engine → progression → recommendation forms clean one-way chain
- **Clean engine/module separation** - engines are truly app-agnostic
- **Repository pattern** consistently applied with DI
- **Structured logging** via structlog with correlation IDs
- **Smoke test framework** is a valuable operational asset
- **Stageflow integration** provides good pipeline abstraction with interceptors
- **Swappable LLM provider** enables multi-backend support
- **Voice transcription module** - New Deepgram integration with graceful fallback
- **Config cross-layer dependency fixed** - `config.py` no longer depends on engines module

---

## 11. Changelog (2026-03-31 Update)

### Changes Since Original Audit

| Date | Change | Status |
|------|--------|--------|
| 2026-03-31 | New `voice` module added (Deepgram transcription) | ✅ Added |
| 2026-03-31 | New `admin_agent` module added | ✅ Added |
| 2026-03-31 | New `taxonomy` module added | ✅ Added |
| 2026-03-31 | `config.py` cross-layer dependency removed | ✅ Fixed |
| 2026-03-31 | `models.py` expanded from 31 to 52 models | ⚠️ Worsened |
| 2026-03-31 | `AppContainer` expanded from 22 to 26 attributes | ⚠️ Worsened |
| 2026-03-31 | Deepgram settings added to config | ✅ Added |

### Issues Addressed
- **§5.2 config.py** - Cross-layer dependency on `engines.config.loader` has been resolved

### New Issues Identified
- **§5.13 voice module** - New transcription service added
- Models file has grown significantly (52 vs 31 models)
- Container has grown (26 vs 22 attributes)

---

*Report generated from architectural audit of backend codebase*
*Updated: 2026-03-31*
