# Human Approval Workflows for Assistant Actions

**Status**: Not Implemented — Out of Scope for MVP

---

## Background

The assistant module (`backend/src/soft_skills_backend/modules/assistant/`) executes tools automatically without human approval. All tool calls dispatched by `AssistantToolExecutor._dispatch_tool()` run immediately with no pause for confirmation.

The MVP spec (`operations/chat-assistant.md:540`) explicitly excludes human approval workflows:

> "The MVP does not need human approval workflows because the tool set is bounded to reads and draft generation through existing guarded services."

Similarly, "human approval flows for tools" is listed as out of scope at line 185.

---

## Current Behavior

| Aspect | Detail |
|--------|--------|
| Pipeline | Stageflow-based in `workflows/service.py` |
| Tool iterations | Up to 6 per assistant turn |
| Approval stage | Does not exist |
| Config | No approval settings in `config.py` |

---

## Stageflow Pipeline (Current)

```
input_guard
  → history_enrich / profile_enrich / progress_enrich / attempts_enrich / session_state_enrich
  → planning_prompt_request / planning_prompt_render
  → assistant_runtime (tool loop, auto-execute)
  → final_response_work
```

---

## What Would Be Needed to Add Approval

If approval workflows are desired in a future iteration, the following would be required:

### 1. Configuration

Add approval settings to `backend/src/soft_skills_backend/config.py`:

- Per-tool or per-category approval requirements
- Ability to enable/disable approval globally
- Fallback to auto-approve for certain trusted tools

### 2. Stageflow Pipeline Changes

Insert an `approval_wait` stage in `workflows/service.py` that:

- Pauses tool execution after a tool is selected
- Emits an approval request event to a broker
- Waits for approval/rejection before dispatching to `AssistantToolExecutor`

### 3. Approval Service

- New service or use case to manage approval requests
- API endpoint(s) for listing pending approvals and approving/rejecting
- Persistence of approval state (approved/rejected/pending)

### 4. Frontend UI

- Chat.tsx renders `ChatPage` from `@/features/chat`
- `ToolCallsAccumulator` component would need approval-aware rendering
- Pending approvals should surface as interruptible UI elements
- Endpoint: `POST /api/assistant/sessions/{session_id}/turns` would need to support approval responses

---

## Key Files Reference

| File | Role |
|------|------|
| `workflows/service.py` | Pipeline orchestration |
| `workflows/tools.py` | `AssistantToolExecutor._dispatch_tool()` — tool execution |
| `workflows/runtime_models.py` | `AssistantDecision`, `AssistantToolRequest` |
| `infra/realtime.py` | SSE streaming broker |
| `use_cases/assistant_service.py` | Facade entrypoint |

---

## Decision Points

1. **Scope**: Should all tools require approval, or only destructive/writing tools?
2. **Timeout**: How long should the pipeline wait for approval before failing?
3. **Batch**: Can multiple pending approvals be processed together?
4. **UI**: Should approvals appear inline in chat, or as a separate notification panel?
