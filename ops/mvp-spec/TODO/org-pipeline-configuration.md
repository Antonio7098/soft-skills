# Org Pipeline Configuration MVP

## Problem Statement

Currently, all organizations share the same app-level model and prompt configuration for pipelines. We need to allow organizations to select what models and prompts are used for each pipeline.

## Current Architecture

### Model Selection
- `OpenAICompatibleLLMProvider` uses `resolve_llm_provider_config()` → `settings.get_llm_model_for_task(task)`
- App-level defaults in `config.py` (`llm_default_model`, `llm_assistant_model`, etc.)

### Prompt Selection
- `CatalogGenerationRuntimeConfig` (loaded from JSON artifact) contains prompt names/versions
- `build_*_prompt_request()` functions use `config.structured_prompt_name` and `config.structured_prompt_version` directly

### Org Context
- Commands like `StructuredCollectionGenerationCommand` have `organisation_id` field, but it's NOT used for model/prompt selection

## Plan

### 1. Database Layer

**New model:** `OrganisationPipelineConfigRecord` in `platform/db/models.py`

```python
class OrganisationPipelineConfigRecord(Base):
    """Organisation-level pipeline configuration overrides."""
    
    __tablename__ = "organisation_pipeline_configs"
    __table_args__ = (
        UniqueConstraint("organisation_id", "pipeline_type", name="uq_org_pipeline"),
    )
    
    organisation_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("organisations.id"), primary_key=True
    )
    pipeline_type: Mapped[str] = mapped_column(String(64), primary_key=True)  # e.g., "catalog_generation", "prompt_item", "assistant"
    model_slug: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
```

### 2. Organisation Service Extension

**New file:** `modules/organisations/use_cases/organisation_pipeline_config_service.py`

```python
class OrganisationPipelineConfigService:
    """Service for managing org-level pipeline configuration."""
    
    def get_pipeline_config(
        self, 
        session: Session, 
        organisation_id: str, 
        pipeline_type: str
    ) -> OrganisationPipelineConfig | None:
        """Get org pipeline config if exists."""
        
    def upsert_pipeline_config(
        self,
        session: Session,
        organisation_id: str,
        pipeline_type: str,
        model_slug: str | None = None,
        prompt_name: str | None = None,
        prompt_version: str | None = None,
    ) -> OrganisationPipelineConfig:
        """Create or update org pipeline config."""
```

### 3. Config Resolution

**New function:** `resolve_org_aware_provider_config()` in `platform/providers/llm/openai_compatible.py`

- Accept `organisation_id` and `pipeline_type` parameters
- First check `OrganisationPipelineConfigService` for org overrides
- Fall back to app-level `Settings` if no override configured

### 4. Pipeline Integration

**Modified:** `modules/catalog/workflows/generation/service.py`

```python
class CatalogGenerationService:
    def __init__(
        self,
        # ... existing params
        organisation_pipeline_config_service: OrganisationPipelineConfigService | None = None,
    ):
        # ... existing setup
        self._org_pipeline_config = organisation_pipeline_config_service
        
    async def _resolve_org_config(
        self,
        session: Session,
        organisation_id: str | None,
        default_config: CatalogGenerationRuntimeConfig,
    ) -> ResolvedCatalogGenerationConfig:
        """Resolve effective config, applying org overrides if present."""
        # Returns a config with org-specific model/prompt values merged with defaults
```

**Modified:** `modules/catalog/workflows/generation/prompting.py`

- Update `build_collection_blueprint_prompt_request()` to accept resolved config with org-specific values
- Use `config.structured_prompt_name` / `config.structured_prompt_version` from resolved config (already the pattern, just needs org-aware resolution)

### 5. API Layer

**New admin endpoints** in `modules/admin/routes/` or `modules/organisations/routes/`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/orgs/{org_id}/pipeline-config/{pipeline_type}` | Get org pipeline config |
| PUT | `/api/admin/orgs/{org_id}/pipeline-config/{pipeline_type}` | Update org pipeline config |
| DELETE | `/api/admin/orgs/{org_id}/pipeline-config/{pipeline_type}` | Reset to defaults |

**Request/Response models** in `modules/organisations/contracts/`:

```python
class OrganisationPipelineConfigResponse(BaseModel):
    organisation_id: str
    pipeline_type: str
    model_slug: str | None  # None means use app default
    prompt_name: str | None
    prompt_version: str | None

class OrganisationPipelineConfigUpdate(BaseModel):
    model_slug: str | None = None
    prompt_name: str | None = None
    prompt_version: str | None = None
```

### 6. Validation

- `model_slug` must be a supported model (validate against known providers)
- `prompt_name` and `prompt_version` must exist in `PromptRegistry`
- Only org admins can modify their org's config (use `require_org_admin` validator)

## Key Files to Modify

| File | Changes |
|------|---------|
| `platform/db/models.py` | Add `OrganisationPipelineConfigRecord` |
| `modules/organisations/use_cases/organisation_pipeline_config_service.py` | **NEW** - config service |
| `modules/organisations/contracts/` | **NEW** - request/response models |
| `modules/organisations/routes/` | **NEW** - admin endpoints |
| `modules/catalog/workflows/generation/service.py` | Accept config service, resolve org-aware config |
| `modules/catalog/workflows/generation/prompting.py` | Use org-aware config values |
| `platform/providers/llm/openai_compatible.py` | Add `resolve_org_aware_provider_config()` |
| `platform/container.py` | Wire up new service |

## Open Questions

1. **Granularity:** Should config be per `LLMTaskKind` or per pipeline type?
   - `LLMTaskKind`: ASSISTANT, MARKING_PER_SKILL, CREATOR_BLUEPRINT, CREATOR_PROMPT_ITEM, CREATOR_SCENARIO
   - Pipeline type: catalog_generation, prompt_item, assistant_turn
   
   Recommendation: Start with pipeline type for simplicity.

2. **Supported models:** Should we maintain a list of allowed models per org, or allow any model slug?

3. **Audit trail:** Should pipeline config changes be logged in `PipelineRunRecord` or a new audit table?
