# Human Approval Workflows for Assistant Actions

**Status**: Not Implemented — Stageflow Support Available, Not Yet Used

---

## Background

The assistant module (`backend/src/soft_skills_backend/modules/assistant/`) executes tools automatically without human approval. All tool calls dispatched by `AssistantToolExecutor._dispatch_tool()` run immediately with no pause for confirmation.

The MVP spec (`operations/chat-assistant.md:540`) explicitly excludes human approval workflows:

> "The MVP does not need human approval workflows because the tool set is bounded to reads and draft generation through existing guarded services."

Similarly, "human approval flows for tools" is listed as out of scope at line 185.

**However**, stageflow itself has full approval infrastructure built in — it just isn't wired up to the assistant yet.

---

## Stageflow Built-In Approval Support

Stageflow already provides `AdvancedToolExecutor` with HITL (Human-in-the-Loop) approval as a first-class feature.

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `AdvancedToolExecutor` | `stageflow/tools/executor_v2.py:79` | Drop-in replacement for `ToolExecutor` with approval, undo, behavior gating |
| `ApprovalService` | `stageflow/tools/approval.py` | Manages approval requests and decisions |
| `ToolDefinition.requires_approval` | `stageflow/tools/tool.py` | Marks a tool as requiring human approval |
| `approval_message` | `stageflow/tools/tool.py` | Custom message shown to human during approval prompt |
| `approval.requested` event | `stageflow/tools/events.py:152` | Emitted when approval is requested |
| `approval.decided` event | `stageflow/tools/events.py:174` | Emitted when approval decision is made |
| `ToolApprovalDeniedError` | `stageflow/tools/errors.py:79` | Raised when approval is denied |

### How Stageflow Approval Works

From `stageflow/tools/executor_v2.py:176-177`:

```python
if tool.requires_approval and not await self._request_and_await_approval(tool, tool_input, ctx):
    raise ToolApprovalDeniedError(...)
```

The flow:
1. Tool is invoked with `requires_approval=True` and optional `approval_message`
2. `AdvancedToolExecutor` calls `_request_and_await_approval()` which:
   - Creates an `ApprovalRequest` via `ApprovalService.request_approval()`
   - Emits `approval.requested` event
   - Awaits the human decision with configurable timeout (default 60s)
   - Emits `approval.decided` event
3. If approved, tool executes normally
4. If denied, `ToolApprovalDeniedError` is raised

### AdvancedToolExecutor Configuration

```python
from stageflow.tools import AdvancedToolExecutor, ToolExecutorConfig, ApprovalService

config = ToolExecutorConfig(
    approval_timeout_seconds=120.0,  # How long to wait for approval
)
executor = AdvancedToolExecutor(
    config=config,
    approval_service=ApprovalService(),  # Wire in the approval service
)
```

### ToolDefinition with Approval

```python
from stageflow.tools import ToolDefinition, tool

@tool
def delete_user(user_id: str) -> bool:
    """Delete a user account."""
    ...

# Mark as requiring approval
delete_user.definition.requires_approval = True
delete_user.definition.approval_message = f"Are you sure you want to delete user {user_id}?"
```

---

## Current Behavior in Soft-Skills

| Aspect | Detail |
|--------|--------|
| Pipeline | Stageflow-based in `workflows/service.py` |
| Tool executor | Base `ToolExecutor` (not `AdvancedToolExecutor`) |
| Tool iterations | Up to 6 per assistant turn |
| Approval wired up | **No** — no `ApprovalService`, no `requires_approval` flags |
| Config | No approval settings in `config.py` |

### Stageflow Pipeline (Current)

```
input_guard
  → history_enrich / profile_enrich / progress_enrich / attempts_enrich / session_state_enrich
  → planning_prompt_request / planning_prompt_render
  → assistant_runtime (tool loop, auto-execute)
  → final_response_work
```

---

## Migration Path: How to Implement Approval

### Phase 1: Migrate to AdvancedToolExecutor

In `workflows/tools.py`, replace the current tool executor with `AdvancedToolExecutor`:

```python
# Before
from stageflow.tools import ToolExecutor

# After
from stageflow.tools import AdvancedToolExecutor, ToolExecutorConfig, ApprovalService
```

Wire in `ApprovalService` and configure it.

### Phase 2: Add Approval Settings to Config

In `backend/src/soft_skills_backend/config.py`:

```python
class Settings(BaseSettings):
    # Tool approval
    tool_approval_timeout_seconds: float = 60.0
    tool_approval_auto_allow: list[str] = []  # Tools that skip approval (read-only tools)
```

### Phase 3: Mark All Tools Requiring Approval by Default

In `workflows/tools.py` or wherever tools are registered, set `requires_approval=True` on all tools by default, then auto-allow the safe read-only ones:

```python
for tool_name, tool_func in assistant_tools.items():
    tool_func.definition.requires_approval = True
    tool_func.definition.approval_message = f"Approve {tool_name}?"

# Auto-allow read-only tools
for tool_name in settings.tool_approval_auto_allow:
    if tool_name in assistant_tools:
        assistant_tools[tool_name].definition.requires_approval = False
```

### Phase 4: Wire Up ApprovalService

Implement an `ApprovalService` that:
- Persists `ApprovalRequest` records (approved/rejected/pending)
- Provides async `await_decision()` to block until human responds
- Optionally integrates with SSE streaming to push `approval.requested` to frontend

### Phase 5: Frontend UI

- `ToolCallsAccumulator` in `ChatPage` needs approval-aware rendering
- Stream `approval.requested` events via `AssistantRealtimeBroker` to frontend
- Show inline approval prompts in the chat UI
- User approves/rejects via a new endpoint (e.g., `POST /api/assistant/approvals/{request_id}`)

---

## Key Files Reference

### Soft-Skills Backend

| File | Role |
|------|------|
| `workflows/service.py` | Pipeline orchestration |
| `workflows/tools.py` | `AssistantToolExecutor._dispatch_tool()` — **migrate to AdvancedToolExecutor** |
| `workflows/runtime_models.py` | `AssistantDecision`, `AssistantToolRequest` |
| `infra/realtime.py` | SSE streaming broker — **add approval.requested events** |
| `use_cases/assistant_service.py` | Facade entrypoint |
| `config.py` | **Add approval settings** |

### Stageflow

| File | Role |
|------|------|
| `stageflow/tools/executor_v2.py` | `AdvancedToolExecutor` — has all approval logic |
| `stageflow/tools/approval.py` | `ApprovalService`, `ApprovalRequest`, `ApprovalDecision` |
| `stageflow/tools/tool.py` | `ToolDefinition.requires_approval`, `approval_message` |
| `stageflow/tools/events.py` | `ApprovalRequestedEvent`, `ApprovalDecidedEvent` |
| `stageflow/tools/errors.py` | `ToolApprovalDeniedError` |
| `docs/guides/tools-approval.md` | Stageflow approval documentation |

---

## Decisions

| # | Decision |
|---|----------|
| 1 | **Approval by default** — all assistant tools require approval unless explicitly auto-allowed via config. Use a `tool_approval_auto_allow` list in config for tools that skip approval (e.g., read-only tools). |
| 2 | **60 second timeout** — matches stageflow's default. Pipeline fails with `ToolApprovalDeniedError` if no decision arrives. |
| 3 | **Batch processing** — multiple pending approvals can be accumulated and resolved together before the tool loop resumes. |
| 4 | **Inline in tool call display** — `ToolCallItem` / `ToolCallsAccumulator` shows an approval prompt state, then transitions to the normal tool result display once approved. |
| 5 | **Database (most robust)** — use the existing PostgreSQL database. Approval requests are audit-logged, survive restarts, support foreign keys to users/sessions/attempts, and integrate with the existing event infrastructure. |
| 6 | **Migrate to AdvancedToolExecutor first** — no behavior change initially; enables approval incrementally per-tool. |
