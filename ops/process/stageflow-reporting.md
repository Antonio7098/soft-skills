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
