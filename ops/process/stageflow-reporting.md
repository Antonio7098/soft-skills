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
