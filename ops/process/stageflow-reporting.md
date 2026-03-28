# Stageflow Reporting

This file tracks bugs, DX improvements, and notable observations related to
Stageflow workflows in SoftSkills.

## Bugs

<!-- Format:
**Title** (YYYY-MM-DD)
- **Reference File:** path/to/file
- **Description:** What the bug is
- **Recommendations:** How to fix or mitigate
-->

**Subpipeline Fork Dropped Timeout And Idempotency Data** (2026-03-26)
- **Reference File:** `backend/src/soft_skills_backend/platform/workflows/stageflow.py`
- **Description:** `run_logged_subpipeline(...)` set `_timeout_ms`, `idempotency_key`, and related controls on the pre-spawn `PipelineContext`, but `SubpipelineSpawner.spawn()` forks child contexts with a fresh `data={}` and only preserves the original values in `_parent_data`. That meant child generation workers silently fell back to Stageflow's default 30-second timeout even when the parent pipeline had a larger explicit budget.
- **Recommendations:** Rehydrate child `PipelineContext.data` from `_parent_data` before `Pipeline.run(...)`. Upstream, Stageflow should offer a first-class way to preserve selected context-data keys across subpipeline forks.

**Provider Payload Shape Failures Need Local Retry Policy** (2026-03-26)
- **Reference File:** `backend/src/soft_skills_backend/platform/providers/llm/openai_compatible.py`
- **Description:** Live provider runs sometimes returned completion message payloads whose `content` shape was not understood by the current parser. In smoke execution this surfaced as non-retried failures even though the underlying issue was transient provider payload variability rather than deterministic prompt drift.
- **Recommendations:** Treat malformed-but-retryable provider payload shape errors as retryable in the provider adapter, and make sure smoke and benchmark environments do not disable provider retries when the goal is operational envelope testing.

**Repo-Root Smoke Execution Missed Backend Env Loading** (2026-03-26)
- **Reference File:** `backend/src/soft_skills_backend/smoke/support/environment.py`
- **Description:** Assistant real-provider smokes initially appeared unconfigured when run from repo root because the backend runtime expected configuration loading from `backend/.env`. Running from `backend/` resolved the issue and the assistant smoke suites completed successfully.
- **Recommendations:** Make smoke environment loading independent of caller working directory, or document more explicitly that backend real-provider smokes must run from the backend root when local `.env` files are relied on.

## DX Improvements

<!-- Format:
**Title** (YYYY-MM-DD)
- **Reference File:** path/to/file
- **Description:** What could be improved
- **Recommendations:** Suggested improvement
-->

## Observations

<!-- Format:
**Title** (YYYY-MM-DD)
- **Reference File:** path/to/file
- **Description:** Notable pattern, edge case, or behavioral quirk
-->

**Shared Text Practice DAG Reuse** (2026-03-25)
- **Reference File:** `backend/src/soft_skills_backend/application/practice/quick_practice/service.py`
- **Description:** The same `input_guard -> enrich -> transform -> output_guard -> persistence` DAG shape scaled cleanly from quick practice to interview and scenario runtime once prompt resolution was widened behind typed enrich stages, and the runtime now executes directly through Stageflow `Pipeline.run(...)` with wide events and persisted pipeline-run logs.

**Callable Stage Registration Typing Gap** (2026-03-25)
- **Reference File:** `backend/src/soft_skills_backend/application/practice/quick_practice/service.py`
- **Description:** The installed `stageflow-core` runtime executes async callable stage runners correctly, but the exposed type hints for `stage()` still only admit stage classes or stage instances.
- **Recommendations:** Widen the Stageflow type hints to accept async callable runners so production code does not need local casts at registration boundaries.

**Stage-Scoped Idempotency Needed For Multi-Stage DAGs** (2026-03-25)
- **Reference File:** `backend/src/soft_skills_backend/application/_shared/stageflow.py`
- **Description:** The default idempotency interceptor keying is not sufficient for multi-stage DAGs because the same request-level key can collide across different stages in one pipeline. SoftSkills now scopes idempotency by `stage_name:idempotency_key` before using the Stageflow cache.
- **Recommendations:** Upstream a stage-aware idempotency mode or key extractor shape in Stageflow so multi-stage application pipelines do not need a local wrapper interceptor.

**Inline Progression Refresh Couples Submit Latency** (2026-03-26)
- **Reference File:** `backend/src/soft_skills_backend/modules/progression/workflows/service.py`
- **Description:** Sprint 5 runs progression refresh as an inline Stageflow pipeline immediately after validated assessment persistence. This gave simple and deterministic end-to-end semantics for V1, but it also means the learner submit path now depends on a nested workflow finishing before the request returns.
- **Recommendations:** Add an async trigger/checkpoint path for heavier progression refresh or replay workloads once operational tooling for background workflow execution is in place.

**Generation Pipelines Need Explicit Timeout Budgets** (2026-03-26)
- **Reference File:** `backend/src/soft_skills_backend/modules/catalog/workflows/generation/service.py`
- **Description:** The default Stageflow per-stage timeout was too small for provider-backed creator generation once corrective validation retries were enabled. The generation pipelines now set an explicit timeout budget instead of inheriting the default.
- **Recommendations:** Upstream a clearer per-pipeline timeout configuration surface so long-running but legitimate generation stages do not need local context-data overrides.

**Assistant Turns Also Need Explicit Long Timeout Budgets** (2026-03-26)
- **Reference File:** `backend/src/soft_skills_backend/modules/assistant/workflows/service.py`
- **Description:** Real-provider assistant generation runs inherited a timeout budget that was too small once the turn included a planning pass, tool execution, child generation subpipelines, and final streamed response generation. The assistant workflow now sets an explicit larger timeout budget for the full turn.
- **Recommendations:** Timeout sizing should be based on the whole workflow shape, not just the primary LLM stage. Upstream, Stageflow could expose clearer budget composition guidance for parent pipelines that orchestrate child provider-backed work.

**Tool-Required Prompts Improve Deterministic Agent Smokes** (2026-03-26)
- **Reference File:** `backend/src/soft_skills_backend/modules/assistant/workflows/prompting.py`
- **Description:** In live provider execution, generation requests could still be answered conversationally unless the system prompt made tool use mandatory for generation asks. Tightening that rule made the smoke path deterministic without changing the bounded tool model.
- **Recommendations:** For agent smokes, encode mandatory tool-routing rules in the prompt contract rather than depending on model preference. Upstream agent tooling could benefit from a stronger "tool required for intent X" control surface.

**Durable Event Sequences Make Parallel UI Replay Practical** (2026-03-26)
- **Reference File:** `backend/src/soft_skills_backend/modules/assistant/infra/repository.py`
- **Description:** Once assistant turns began running parallel enrich stages, parallel tools, and child subpipelines, durable monotonic stream sequence numbers became necessary to give the UI a stable replay and reconnect contract.
- **Recommendations:** Treat durable sequence assignment as part of the workflow contract whenever Stageflow parallelism feeds a live event stream. Upstream, Stageflow observability could benefit from a built-in ordered projection helper for UI-facing streams.

**PromptSecurityPolicy Fits Chat Generation Well Without Agent Loops** (2026-03-26)
- **Reference File:** `backend/src/soft_skills_backend/modules/catalog/workflows/generation/service.py`
- **Description:** Sprint 6 used `PromptSecurityPolicy` directly on chat-generation prompts and kept the workflow on a typed single-call path. This covered the trust requirement without introducing `AgentStage` or tools where no real tool loop existed.

**Provider-Backed Eval Pipelines Need Explicit Long Timeouts** (2026-03-26)
- **Reference File:** `backend/src/soft_skills_backend/modules/evaluation/workflows/service.py`
- **Description:** The first real provider-backed golden-dataset marking benchmark exceeded the default Stageflow stage timeout and needed an explicit longer pipeline timeout budget. Model benchmarking is materially slower than local validation-only evals.
- **Recommendations:** Derive evaluation timeouts from `case_count x model_count x provider_timeout` instead of inheriting the default stage timeout.

**Subpipelines Need Parent Metadata Rehydration** (2026-03-26)
- **Reference File:** `backend/src/soft_skills_backend/platform/workflows/stageflow.py`
- **Description:** Sprint 9 needed child generation pipelines with their own run IDs, persisted pipeline-run records, and provider-call correlation. That required a local `run_logged_subpipeline(...)` helper that reconstructs `PipelineContext` from the parent `StageContext` before spawning the child pipeline.
- **Recommendations:** Add a first-class Stageflow helper for parent-to-child pipeline spawning that carries request metadata, logging, and correlation without application-level context reconstruction.

**Subpipeline Data Does Not Survive Fork By Default** (2026-03-26)
- **Reference File:** `backend/src/soft_skills_backend/platform/workflows/stageflow.py`
- **Description:** Stageflow subpipeline forks preserve parent `data` in `_parent_data` and give the child a fresh mutable `data` dict. That is easy to miss, and it matters for any application-level controls stored in context data, including timeout budgets and idempotency keys.
- **Recommendations:** Treat child `data` rehydration as mandatory in local wrappers today. Upstream, Stageflow should document this more prominently or add an opt-in mode that copies a safe subset of parent data into the child.

**Prompt Rendering Works Best As An Explicit Shared Stage** (2026-03-28)
- **Reference File:** `backend/src/soft_skills_backend/modules/admin/workflows/prompt_render_stage.py`
- **Description:** Centralizing prompt construction behind a dedicated `prompt_request -> prompt_render -> llm` DAG shape made assistant and catalog workflows materially easier to reason about than embedding prompt lookup and templating inside each LLM transform. The stage boundary also gave one place to enforce strict missing-prompt failure, metrics, and render-event persistence.
- **Recommendations:** When prompts need governance, observability, or version lineage, treat prompt rendering as its own stage contract rather than an implementation detail inside provider-call code.

**Registry-Backed Prompt Stages Need Deterministic Bootstrap** (2026-03-28)
- **Reference File:** `backend/src/soft_skills_backend/modules/admin/domain/prompt_registry.py`
- **Description:** Moving from static in-code prompt libraries to a DB-backed registry introduced a lifecycle dependency that Stageflow itself does not solve: prompts must exist before the render stage runs. In SoftSkills, integration tests construct the app container before migrations, so eager seeding at container build time was not safe and lazy idempotent seeding became the pragmatic bridge.
- **Recommendations:** When stage execution depends on external configuration state, pair the stage with an explicit bootstrap contract. If bootstrap cannot be guaranteed at app startup, make initialization idempotent and tie it to the first safe post-migration use site.
