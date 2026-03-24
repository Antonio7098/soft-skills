# Hivemind Beta Testing Notes - SoftSkills Backend Setup

## Environment
- Hivemind version: 0.1.54
- Runtime: opencode with minimax-coding-plan/MiniMax-M2.7
- HIVEMIND_DATA_DIR: /tmp/hivemind-soft-skills/.hivemind

## Setup Operations Performed

### 1. Project Creation
- Created project "soft-skills-1" (ID: 1b4019f0-7051-4866-a296-ca88072a0332)
- Attached repo: /home/antonioborgerees/coding/soft-skills-1

### 2. Governance
- Initialized governance successfully
- Graph snapshot refreshed (728 nodes, 540 edges, fingerprint: ff38c96b0440b41d)

### 3. Constitution
- Constitution init FAILED with schema error: `ma_version` unknown field
- The source file /home/antonioborgerees/coding/soft-skills-1/CONSTITUTION.yml has typo: `ma_version: 1` instead of `version: 1`
- Despite init failure, constitution show works and returns valid constitution
- **BUG**: Constitution init should either fix the schema or give clearer error about the ma_version typo

### 4. Runtime Configuration
- Set worker adapter: opencode with model minimax-coding-plan/MiniMax-M2.7
- Max parallel tasks: 2, timeout: 600000ms

### 5. Workflow Creation (Phase 5)
- Created workflow "backend-setup-workflow" with 7 steps
- Used Phase 5 features: workflow context, append-only output bag, step contexts
- Workflow run created (ID: 62a4a00f-3435-4ea5-bb8e-df44c96ad43d)
- Synthetic graph and flow created automatically (graph: f670f161..., flow: 85302809...)
- Workflow tick triggers task execution through legacy flow bridge

## Phase 5 Features Observed

### Working:
1. **Workflow context initialized** - context schema v1, initialization_inputs captured
2. **Step contexts captured** - snapshot_hash, workflow_run_id, step_id all present
3. **Output bag ready** - schema v1, bag_hash computed, entries array ready
4. **Synthetic graph/flow creation** - workflow creates underlying graph and flow automatically
5. **Dependency tracking** - tasks properly blocked on dependencies
6. **Retry mechanism** - attempt 1 failed with timeout, attempt 2 started automatically
7. **Runtime stream** - events showing checkpoint_declared, checkpoint_activated, session, runtime_started
8. **Runtime selection** - opencode adapter selected, model specified correctly

### Issues Found:

#### BUG 1: Constitution schema validation error unclear
- **Error**: `unknown field 'ma_version', expected one of 'version', 'schema_version', 'compatibility', 'partitions', 'rules'`
- **Issue**: The error doesn't tell user WHICH file has the problem or suggest fix
- **Expected**: Clear message pointing to the source file and suggesting `ma_version` -> `version`
- **Severity**: Medium

#### BUG 2: Workflow step-add requires step IDs not names for dependencies
- **Observation**: `workflow step-add` --depends-on expects step ID (UUID), not step name
- **UX**: User creates step "initialize-foundation" with ID "13f3befd...", then another step can't use `--depends-on initialize-foundation`
- **UX**: Must use `--depends-on 13f3befd-...` which is not discoverable
- **Suggestion**: Support `--depends-on-step-name` or display step ID after creation
- **Severity**: Low (workaround exists but poor DX)

#### BUG 3: Task titles from workflow steps don't match original task descriptions
- **Observation**: Workflow created synthetic tasks with title="initialize-foundation" but description="Initialize backend foundation" (capitalization differs)
- **UX**: Original task created had proper description referencing ROADMAP section 1
- **Suggestion**: Workflow step description should flow through to synthetic task
- **Severity**: Low

#### BUG 4: No checkpoint commands for tasks directly
- **Observation**: Checkpoint commands (list, complete) are per-attempt, not per-task
- **UX**: To use checkpoints, must start task via flow and then manage checkpoints
- **Suggestion**: Add `task checkpoint` subcommands or task-level checkpoint management
- **Severity**: Low (workaround exists but not intuitive)

## DX Improvement Suggestions

### 1. Workflow authoring UX
- After `workflow step-add`, display the step ID prominently
- Allow using step names in --depends-on (resolve to IDs internally)
- Show "workflow step created: <id>" in output

### 2. Constitution init UX
- If constitution file has `ma_version` instead of `version`, suggest correction
- Point to exact file path in error message

### 3. Task creation via workflow
- Preserve full description from step-add when creating synthetic task
- Or allow passing task metadata when creating workflow steps

### 4. Progress visibility
- `workflow status` shows step state as "ready" but doesn't show underlying task state
- Add synthetic task ID to step run info for debugging

## Runtime Behavior

### Timeout Issue
- Task "initialize-foundation" timed out after 45s with "no_observable_progress_timeout"
- This is expected behavior when model is thinking but not producing output
- Retry happened automatically with same adapter
- Second attempt is now running

### Model: minimax-coding-plan/MiniMax-M2.7
- Working: adapter selection, environment setup, runtime stream
- Working: retry on timeout, backoff strategy
- Note: Model takes time to produce first output

## Current Workflow State (as of 09:37 UTC)
- Workflow run: running
- First step "initialize-foundation": running (attempt 2)
- Other 6 steps: pending (waiting on first step)
- Output bag: empty (step not completed)
- Context: initialized with no inputs

## Backend Creation Observed (09:38 UTC)

The opencode runtime successfully created the backend structure in the worktree:
- `/home/antonioborgerees/hivemind/worktrees/85302809.../fda45f59.../backend/`
- Directories created: api/, application/, domain/, observability/, orchestration/, persistence/, prompts/, schemas/
- `__init__.py` created
- `pyproject.toml` created with proper dependencies:
  - fastapi, sqlalchemy, alembic, pydantic, openai, stageflow
  - asyncpg, psycopg2-binary (DB adapters)
  - structlog (logging)
  - ruff, mypy, pytest (dev tools)

**This confirms Phase 5 workflow execution is working correctly!**

## Critical Issue: Missing Runtime Observability Events (Investigated 10:11 UTC)

### Problem
After `runtime_started` event, no `runtime_output_chunk`, `model_response_received`, `tool_call_started`, or other native runtime events appear. Only 24 events total for the attempt.

### Direct opencode CLI Test (Working)
Tested opencode directly with same model and format - it DOES emit proper JSON:

```json
{"type":"step_start","sessionID":"ses_2e5d2211fffeJjRU1V5m3CXaJP",...}
{"type":"step_finish","sessionID":"ses_2e5d2211fffeJjRU1V5m3CXaJP","part":{"type":"step-finish",...}}
```

opencode v1.3.0 with `--format json` produces:
- `sessionID` matches expected format
- `step_finish` with `snapshot` (provider_turn_id)
- `tool_use` events with write operations

### Root Cause Analysis (Revised)
Direct CLI test confirms opencode DOES emit valid JSON. So the issue is NOT that opencode fails to emit JSON.

Most likely causes:
1. **Threading/buffering issue**: `read_stream_to_string` runs in spawned thread. If thread blocks on read, tracker observations may be lost when process killed
2. **External kill doesn't trigger clean shutdown**: When we `kill -9`'d the process, the flow engine's blocking `execute()` call never returned, so `RuntimeExited`/`RuntimeTerminated` events were never emitted
3. **No timeout on stdout thread join**: `stdout_handle.join()` may block indefinitely if thread is stuck

### Missing Events
Expected but missing:
- `RuntimeSessionObserved` / `session_observed`
- `RuntimeTurnCompleted` / `turn_completed`  
- `RuntimeExited` - not emitted when process killed externally
- `RuntimeTerminated` - not emitted

### Checkpoint Behavior
- `checkpoint_complete` CLI command updates database but doesn't signal runtime
- Checkpoint completion events ARE emitted (checkpoint_completed, checkpoint_commit_created, all_checkpoints_completed)
- But these are separate from runtime events

### Why Workflow Stuck
1. `runtime_started` emitted when runtime begins
2. Runtime executes in blocking loop in flow engine
3. `LiveJsonRuntimeTracker` observes stdout (but we don't know if it sees JSON)
4. Checkpoints completed manually via CLI but runtime still running
5. When process killed externally with `kill -9`:
   - Process dies but flow engine still in blocking `execute()` call
   - `RuntimeExited` and `RuntimeTerminated` events NOT emitted
   - Workflow stuck in `running` state

### Workflow Run Aborted (10:05 UTC)
Workflow run `62a4a00f-3435-4ea5-bb8e-df44c96ad43d` aborted due to stuck runtime.

### Events Emitted (in order)
1. attempt_started
2. checkpoint_declared
3. checkpoint_activated
4. task_execution_started
5. baseline_captured
6. retry_context_assembled
7-15. context_op_applied (seed_constitution, seed_system_prompt, etc.)
16. attempt_context_assembled
17. context_window_snapshot_created
18. attempt_context_delivered
19. runtime_environment_prepared
20. runtime_capabilities_evaluated
21. **runtime_started** ← Last event before observation gap
22. checkpoint_completed ← After manual checkpoint complete
23. checkpoint_commit_created
24. all_checkpoints_completed
25. task_execution_failed (flow_aborted)

### Source Code Findings
- `runtime_impl.rs:73-129`: `LiveJsonRuntimeTracker` only emits SessionObserved and TurnCompleted
- `runtime_impl.rs:57-71`: `observe_stdout_line` - only parses JSON, ignores non-JSON lines
- `runtime_impl.rs:541-548`: Process wait loop - exits when `try_wait()` returns Some(status)
- `runtime.rs:306-325`: `RuntimeTerminated` and `RuntimeExited` emitted AFTER execute() returns

### Key Code Locations

| File | Lines | Purpose |
|------|-------|---------|
| `runtime_impl.rs:57-100` | `observe_stdout_line`, `observe_opencode_value` | JSON event parsing |
| `runtime_impl.rs:471-495` | stdout thread spawn + read | Thread setup |
| `runtime_impl.rs:507-552` | Wait loop | Process termination detection |
| `runtime_impl.rs:555-571` | `tracker.finish()` | Observation collection |
| `runtime.rs:306-325` | `RuntimeExited`/`RuntimeTerminated` emission | Happens AFTER execute returns |

### DX Issues Identified
1. **No visibility into runtime stdout**: User can't see what the runtime is doing
2. **Missing runtime termination events**: When process killed externally, no exit event
3. **No interrupt mechanism**: `attempt interrupt` command doesn't exist
4. **Runtime runs in blocking loop**: Can't poll or inspect runtime state externally
5. **No debug logging for JSON parsing**: Can't see if lines are being received but not parsed

### Recommended Investigation Steps
1. **Add debug logging** to `observe_stdout_line` to log raw lines before parsing
2. **Instrument `read_stream_to_string`** to count lines read vs lines that parse as JSON
3. **Add timeout to `stdout_handle.join()`** to detect if thread is stuck
4. **Test with `--print-logs`** flag to see if opencode is producing logs to stderr
5. **Check HIVEMIND env vars** passed to opencode - maybe HIVEMIND_ATTEMPT_ID causes issues

## What Would Make This Better
1. Ability to specify task scope/boundaries when creating workflow steps
2. Built-in checkpoint management for manual task completion
3. Constitution validation with auto-fix suggestions
4. Better error messages pointing to file locations
5. Step name support in dependency resolution
6. **Runtime interrupt command** to gracefully stop stuck runtimes
7. **Runtime status command** to inspect running runtime state
8. **stdout/stderr streaming** to see real-time runtime output
9. **opencode adapter**: emit progress events even without JSON mode

## Runtime Adapter Hardening Fix (Mar 23, 2026)

### Problem Addressed
- **Stuck workflows**: When a runtime process exits but background children keep stdout/stderr pipes open, the adapter would block indefinitely waiting on stream readers, preventing `RuntimeExited`/`RuntimeTerminated` events
- **Missing diagnostics**: No visibility into whether the adapter was actually receiving/parseing JSON lines from the runtime

### Fix Applied
- **Process-group isolation**: Runtimes now spawn in their own process group; termination signals the entire group
- **Bounded stream collection**: stdout/stderr readers use channels with timeouts instead of blocking thread joins
- **Observability added**: LiveJsonRuntimeTracker now reports:
  - total non-empty stdout lines
  - parsed JSON vs non-JSON line counts
  - first non-JSON line preview (truncated)
  - warnings when stream collection times out

### Files Changed
- `src/adapters/opencode/runtime_impl.rs`:
  - Added `configure_child_process_group` and `terminate_process_group_by_pid`
  - Replaced blocking `handle.join()` with channel-based collection and timeouts
  - Enhanced `LiveJsonRuntimeTracker` with line counters and diagnostics
  - Added regression test `execute_does_not_hang_when_background_child_keeps_stdout_open`

### Expected Impact
- Workflows should no longer hang when runtimes exit with lingering background processes
- Runtime failure/error messages now include diagnostics about JSON parsing and stream behavior
- Existing JSON event projection and session/turn tracking behavior preserved

## Retest Results (Mar 23, 2026 - 11:13 UTC)

### Build
- Successfully rebuilt Hivemind with fix at 10:35 UTC

### New Workflow Run (bee6f68b-fe8a-4af1-9f88-5ed30c0b3942)
- Created and started fresh workflow run
- Attempt ID: `31b20540-79e0-462e-ba17-6bb791c3766e`

### opencode Session Analysis
- Session `ses_2e59f9d84ffeoyp5V5ja66Mf67` shows opencode actively working:
  - 228 parts and counting
  - Multiple step-start, step-finish, tool events
  - Active from 11:06:57 to 11:13+ (~7 minutes)
  - Producing text, reasoning, and tool outputs
- **opencode IS working correctly and emitting events to its own DB**

### HIVEMIND Events
- Only 20 events captured, ending at `runtime_started`
- No `RuntimeSessionObserved`, `RuntimeTurnCompleted`, `RuntimeExited`, or `RuntimeTerminated` events
- **Same issue as before - HIVEMIND not capturing/parsing stdout JSON**

### Conclusion
The fix addressed the "stuck background child" issue but NOT the underlying JSON parsing issue. The `LiveJsonRuntimeTracker` is still not observing/parsing JSON from stdout.

**Root cause still unknown** - opencode produces JSON (verified in session DB) but HIVEMIND's stdout capture/parsing is not working.

### Next Steps Needed
1. Verify that opencode stdout is actually being captured by HIVEMIND
2. Check if the JSON is being emitted to stdout at all (vs. somewhere else)
3. Add debug logging to `observe_stdout_line` to see raw lines received
4. Consider that HIVEMIND might not be built with the latest code (build may have cached old code)

## ROOT CAUSE FOUND (Mar 23, 2026 - 13:17 UTC)

### Problem
When runtime times out (e.g., `no_observable_progress_timeout`), the `execute()` method in opencode adapter returned an `Err(RuntimeError)` directly, bypassing the normal success path where `append_structured_runtime_observations` was called.

### Code Path Analysis
1. `adapter.execute(input)` returns `Err(RuntimeError::timeout(...))` on line 773 of `runtime_impl.rs`
2. Error caught in `runtime.rs` lines 226-237
3. `handle_tick_runtime_adapter_error` called → `handle_runtime_failure` → emits `RuntimeExited`/`RuntimeTerminated`
4. **BUT**: `append_structured_runtime_observations` is never called because `execute()` returned error

### Evidence
- Debug output showed `LiveJsonRuntimeTracker` WAS emitting `SessionObserved` and `TurnCompleted`
- But events never appeared in `events.jsonl`
- Error path didn't persist observations

### Fix Applied
Changed timeout/no_observable_progress paths in `runtime_impl.rs` to return `Ok(ExecutionReport::failure_with_output(...).with_structured_runtime_observations(...))` instead of `Err(...)`.

**File**: `/home/antonioborgerees/coding/Hivemind/src/adapters/opencode/runtime_impl.rs:770-800`

**Before**:
```rust
WaitOutcome::TimedOut => {
    return Err(RuntimeError::new(
        "timeout",
        format!("Execution timed out after {:?}.{}", timeout, runtime_diagnostics),
        true,
    ));
}
```

**After**:
```rust
WaitOutcome::TimedOut => {
    return Ok(ExecutionReport::failure_with_output(
        -1,
        duration,
        RuntimeError::new(
            "timeout",
            format!("Execution timed out after {:?}.{}", timeout, runtime_diagnostics),
            true,
        ),
        stdout_content,
        stderr_content,
    )
    .with_structured_runtime_observations(structured_runtime_observations));
}
```

### Result
- Attempt `866f209f-6e6d-4d6d-af33-9bca62adde67` now shows events:
  - `runtime_session_observed` ✓
  - `runtime_turn_completed` (x3) ✓
  - `runtime_exited` (x2) ✓
  - `runtime_terminated` ✓
  - `runtime_error_classified` ✓

### Additional Fix
Also fixed silent error ignoring in `runtime.rs:288` - changed `let _ =` to proper error handling with debug logging.

## Runtime Projection Events (Mar 23, 2026 - 13:25 UTC)

### What are Projection Events?
`RuntimeEventProjector` produces events by parsing raw stdout/stderr text looking for patterns:
- `runtime_command_observed` - lines starting with `$ ` or similar
- `runtime_tool_call_observed` - lines with `Tool: `, `Using tool `, `tool=` patterns
- `runtime_todo_snapshot_updated` - lines with `- [ ] ` or `- [x] ` patterns
- `runtime_narrative_output_observed` - general narrative output lines

### Why They're NOT Appearing for opencode
opencode adapter outputs JSON to stdout, NOT text patterns:
```json
{"type":"tool_use","sessionID":"ses_xxx","part":{...}}
{"type":"step_finish",...}
```

The projector expects text patterns like:
```
Tool: Read
Using tool: Write
$ git status
- [ ] task item
```

These patterns don't exist in opencode's JSON output, so `RuntimeEventProjector` doesn't produce projection events.

### What IS Working
- `runtime_output_chunk` - raw stdout chunks are captured (15 chunks in test run)
- `runtime_filesystem_observed` - filesystem observations are captured
- These come from direct appending, not from the projector

### Events We Now Have (Working)
- `runtime_session_observed` ✓ (from JSON parsing)
- `runtime_turn_completed` ✓ (from JSON parsing)
- `runtime_output_chunk` ✓ (raw output)
- `runtime_filesystem_observed` ✓
- `runtime_exited` ✓
- `runtime_terminated` ✓

### Projection Events NOT Applicable to JSON Adapters
The `RuntimeEventProjector` is designed for text-based adapters (shell, codex interactive mode), NOT for JSON-based adapters like opencode.

For opencode, the `LiveJsonRuntimeTracker` handles JSON parsing and produces `StructuredRuntimeObservation` events instead.

### Additional Silent Error Handling Fixed
Fixed `runtime.rs:304` and `runtime.rs:315` which also used `let _ =` silently ignoring errors in `append_projected_runtime_observations` and `store.append` for `RuntimeTerminated`.

## Runtime Projection Events FIXED (Mar 23, 2026 - 14:05 UTC)

### Problem
Although `LiveJsonRuntimeTracker` was emitting `SessionObserved` and `TurnCompleted`, the projection events (`runtime_tool_call_observed`, `runtime_command_observed`, `runtime_narrative_output_observed`) were NOT appearing.

### Root Cause
The `RuntimeEventProjector` (which produces projection events) parses TEXT looking for patterns like `$ command`, `Tool: `, etc. But opencode outputs JSON, not text patterns. The projector ignores JSON lines.

Additionally, `ExecutionReport` had no field to carry `ProjectedRuntimeObservation` events from the adapter.

### Solution
Extended the opencode adapter's JSON output processing to emit `ProjectedRuntimeObservation` events directly:

1. **Added `projected_runtime_observations` field to `ExecutionReport`** (`adapters/runtime/adapter.rs`)

2. **Modified `transform_json_output` to emit projection events** (`adapters/json_output.rs`):
   - `ToolCallObserved` - from `tool_use` events with `part.tool` field
   - `CommandObserved` - from `tool_use` events with `part.state.input.command`
   - `NarrativeOutputObserved` - from `text` events

3. **Updated `render_opencode_event` to emit both structured AND projected observations**

4. **Modified `runtime.rs` to combine projector observations with adapter observations**

### Events Now Appearing (Verified)
```json
{"type":"runtime_tool_call_observed","tool_name":"glob","details":"Tool: glob"}
{"type":"runtime_tool_call_observed","tool_name":"bash","details":"Tool: bash"}
{"type":"runtime_tool_call_observed","tool_name":"read","details":"Tool: read"}
{"type":"runtime_command_observed","command":"pwd",...}
```

### Final Event Count for Attempt
- `runtime_tool_call_observed`: 11 events ✓
- `runtime_command_observed`: 3 events ✓
- `runtime_session_observed`: 1 event ✓
- `runtime_turn_completed`: 5 events ✓
- `runtime_output_chunk`: 26 events ✓

### Files Changed
1. `src/adapters/runtime/adapter.rs` - Added `projected_runtime_observations` field
2. `src/adapters/json_output.rs` - Added `projected_runtime_observations` to `ParsedJsonAdapterOutput`, updated `render_opencode_event`
3. `src/core/runtime_event_projection.rs` - Added `Serialize, Deserialize` derives
4. `src/adapters/opencode/runtime_impl.rs` - Collect and pass projected observations
5. `src/core/registry/flow/execution/tick/once/runtime.rs` - Combine projector observations with adapter observations

## Soft-Skills Backend Workflow Progress (Mar 23, 2026 - 14:10 UTC)

### Workflow Run: 1726d371-fc49-44dc-afe6-a4eeda8d891a

**Status**: First step "initialize-foundation" failed due to timeout

### Timeout Issue
- **Problem**: Runtime times out after 45s of no observable progress
- **Observation**: Model takes time to "think" before producing output
- **Evidence**: opencode IS creating files (see below) but timeout kills it before completion

### Files Created (Before Timeout)
From `runtime_output_chunk` events, confirmed these files were written:
- `backend/pyproject.toml` - Project configuration with dependencies
- `backend/README.md` - Documentation with architecture overview

### Backend Structure Created
```
backend/
├── api/           (empty - not yet populated)
├── application/   (empty - not yet populated)
├── domain/        (empty - not yet populated)
├── observability/ (empty - not yet populated)
├── orchestration/ (empty - not yet populated)
├── persistence/   (empty - not yet populated)
├── prompts/       (empty - not yet populated)
├── schemas/       (empty - not yet populated)
├── pyproject.toml ✓ (created)
└── README.md ✓ (created)
```

### Event Summary
- `runtime_tool_call_observed`: 8 events (glob, bash, write tools)
- `runtime_command_observed`: 1 event (pwd)
- `runtime_turn_completed`: 3 events
- `runtime_session_observed`: 1 event
- `runtime_output_chunk`: 17 events
- `runtime_exited`: 2 events (timeout + final exit)
- `runtime_terminated`: 1 event

### Root Cause of Failure
```
"error_occurred":{"category":"runtime","code":"runtime_runtime_nonzero_exit","message":"Runtime exited with code -1"}
```
Runtime exited with code -1 (SIGTERM from timeout).

### Key Insight
The opencode runtime IS working correctly - it's just the timeout that's too aggressive. The model needs more time to:
1. Analyze the task
2. Plan the file structure
3. Write initial files

### Files Modified
- Worktree path: `/home/antonioborgerees/hivemind/worktrees/3fa845c6-1cc4-413c-9180-7684d4efd2b6/8ca0efa8-e24a-4c1f-9495-56e62eae4c5d/`

### DX Improvements Needed
1. **Timeout should be configurable per task/step** - Some tasks need more time than others
2. **Show progress during thinking time** - Model produces no output while thinking
3. **Better timeout handling** - Maybe save checkpoint before timeout so work isn't lost

## Latest Update: Timeout Fix

### Problem Identified
- The `no_progress_timeout` was hardcoded to 45 seconds (capped) in `interactive.rs`
- opencode needs more time to produce output (model thinking time)
- Previous attempts failed after ~100 seconds with exit code -1 (SIGTERM from timeout)

### Solution Applied
- Set `HIVEMIND_RUNTIME_NO_PROGRESS_TIMEOUT_MS=300000` (5 minutes) via project runtime config:
  ```
  hivemind project runtime-set 1b4019f0-7051-4866-a296-ca88072a0332 --env HIVEMIND_RUNTIME_NO_PROGRESS_TIMEOUT_MS=300000
  ```

### New Workflow Run Created
- Aborted old workflow `1726d371-fc49-44dc-afe6-a4eeda8d891a`
- Created new workflow run `625a681a-6730-4218-8a00-22d1e274791c`
- First step `initialize-foundation` is now running with 5-minute no_progress_timeout

### Current Status
- Workflow run: `625a681a-6730-4218-8a00-22d1e274791c`
- Step: `initialize-foundation` [running] since ~14:24
- Backend structure created in worktree with directories: api, application, core, domain, observability, orchestration, persistence, prompts, schemas, tests
- Files created: main.py, alembic.ini, mypy.ini, pyproject.toml, ruff.toml, router.py, health.py, containers.py, settings.py, etc.

### Files Modified by Hivemind
- `/home/antonioborgerees/hivemind/worktrees/cbb8358f-82a9-41ff-a039-4cfdebf328ac/eb7e8779-b795-4663-a25a-76ec4d14a82a/backend/`

## MissingProcess Bug FIXED (Mar 23, 2026 - 15:15 UTC)

### Problem
When opencode process dies unexpectedly (crashes or killed), the `WaitOutcome::MissingProcess` path returned `Err(RuntimeError)` without any observations, bypassing the normal observation emission path.

### Code Path
1. `execute()` in `runtime_impl.rs` waits for process via `wait_loop`
2. If `self.process` becomes `None` before wait completes, returns `WaitOutcome::MissingProcess`
3. `MissingProcess` path returned `Err(RuntimeError::new("no_process", ...))`
4. Error caught but observations never appended

### Fix Applied
Changed `runtime_impl.rs:855-861` to return `Ok(ExecutionReport::failure_with_output(...).with_structured_runtime_observations(...).with_projected_runtime_observations(...))` instead of error.

### Current State
- New workflow run `fc195688-a03a-47aa-9572-10a2bf983675` created and started
- Runtime started at 15:14:10 (attempt ID: `1bcdc591-e114-411c-9201-99715410852c`)
- Backend directories created: api, application, core, domain, observability, orchestration, persistence, prompts, schemas
- Files created: pyproject.toml, alembic.ini, main.py, etc.
- Runtime appears stuck: no `runtime_exited` event after process exits
- Opencode process dies but workflow engine doesn't detect completion

### Remaining Issue
Even with MissingProcess fix, the runtime still isn't properly detecting process exit and emitting completion events. The opencode process runs, creates files, then exits without HIVEMIND capturing the exit.

### Files Changed
- `src/adapters/opencode/runtime_impl.rs` - MissingProcess path now returns ExecutionReport with observations

## Investigation Results (Mar 23, 2026 - 15:30 UTC)

### Test Methodology
1. Built HIVEMind debug binary with wait_loop debug logging
2. Created new workflow run `f570106e-c876-4da8-bebf-f3d87d0601bb`
3. Ran workflow tick and observed debug output
4. Monitored worktree for file creation activity

### Key Findings

**The wait_loop IS working correctly:**
- Debug output showed `try_wait()` is being called every 10ms
- `no_progress_timeout` check is working (elapsed time increases properly)
- `opencode stdout JSON parsing` IS working - events are being parsed correctly
- Backend files ARE being created in worktree

**Evidence of Correct Operation:**
```
DEBUG: no_progress_timeout check - elapsed: 221.817µs, limit: 300s
DEBUG: opencode stdout line received: {"type":"step_start",...}
DEBUG: opencode stdout JSON parsed successfully
DEBUG: observe_opencode_value called
DEBUG: new session, emitting SessionObserved
```

**Backend Files Being Created:**
- Directory timestamps show active creation: alembic/, observability/, persistence/ at 15:47
- Files: alembic.ini, pyproject.toml, api/, application/, core/, domain/, etc.

### Conclusion

The original issue ("opencode process runs, creates files, then exits without HIVEMIND detecting completion") was likely observed when:
1. Opencode was still running and creating files (15:15-15:22)
2. User checked workflow and saw no `runtime_exited` event
3. User concluded workflow was "stuck" but actually opencode was still working

**The HIVEMIND runtime is functioning correctly.** The `runtime_exited` event WILL be emitted when the opencode process completes its work and exits. The runtime simply takes time (5-10+ minutes) to set up the backend.

## CRITICAL BUG: Runtime Completion Detection Failure (Mar 23, 2026 - 16:30 UTC)

### Problem (REVISED)
After extensive testing, we discovered that HIVEMIND DOES successfully start the opencode runtime and the runtime DOES work correctly (JSON events are parsed, files are created). However, when the opencode session completes with `step_finish reason=stop`, the `runtime_exited` event is NOT emitted and the workflow step remains "running" forever.

### Evidence
1. Opencode session `ses_2e481501dffeM3I3acJhG9ngMo` shows:
   - `step_finish reason=stop` in the DB
   - Last updated: 2026-03-23 16:23:28
2. Backend files ARE created in worktree (alembic/, api/, app/, etc.)
3. HIVEMIND events show `runtime_started` but NO `runtime_exited`
4. Workflow step remains `running` indefinitely

### Root Cause
The opencode adapter's `execute()` method spawns `opencode run --format json` which runs to completion. When the session finishes, opencode outputs `step_finish reason=stop` and exits. The `wait_loop` should detect process exit via `try_wait()`, but something is preventing the completion signal from propagating.

### Symptom
- Tick command returns successfully but workflow step stays "running"
- No `runtime_exited` or `runtime_terminated` events appear
- Backend files ARE created (proving opencode worked correctly)
- No error messages - silent failure

### Files Changed
- Reverted debug logging additions to `runtime_impl.rs`
- Build verified successful

### Impact
- Cannot complete workflow steps
- Cannot test merge functionality
- Cannot advance beyond first step

### Files Changed
- Reverted debug logging additions to `runtime_impl.rs`
- Build verified successful

## wait_loop Debug Investigation (Mar 23, 2026 - 16:45 UTC)

### New Evidence
Added debug logging to `wait_loop` in `runtime_impl.rs:630-658` to trace execution:

```
DEBUG: wait_loop - checking process state
DEBUG: try_wait() returned: None (process still running)
...
(repeats every 10 seconds)
```

### Key Findings
1. **wait_loop IS running**: Debug shows the loop is executing
2. **try_wait() NEVER returns Some(status)**: Always returns `None` indicating process still running
3. **Backend files ARE being created**: opencode process is alive and working
4. **Session DB shows step_finish**: `ses_2e470fe3dffeQOoSA20f8nkG3G` has `step_finish reason=stop` at 16:42:08
5. **No "process exited" message ever appears**: `try_wait()` never returns the exit status

### Conclusion
The problem is NOT that the wait_loop isn't running or that JSON parsing fails. The problem is that `try_wait()` consistently returns `None` even when the opencode process has clearly exited (session DB shows stop, files are created).

### Possible Causes
1. **Zombie process**: opencode spawns child processes; if a child holds stdout open, wait() on parent may block
2. **Process group issue**: Even with process-group isolation, there may be a subprocess keeping the pipe open
3. **PID mismatch**: `self.process` may be pointing to wrong process after spawning
4. **Drop ordering**: Something is dropping/restoring the Child object before wait_loop completes

### Files Changed
- Added debug logging to `runtime_impl.rs:640-655` to trace try_wait() results

### Current Test Run
- Workflow run: `426e59a7-8ef3-4423-b226-13ec3f46edf8`
- Session: `ses_2e470fe3dffeQOoSA20f8nkG3G`
- Backend worktree: `/home/antonioborgerees/hivemind/worktrees/71281774-879a-44f8-a52b-b5871fba87ee/17269134-3177-46fb-bca6-0ebcfe365428/backend/`

## Resolution: Protocol Completion Unblocks wait_loop (Mar 23, 2026 - 17:05 UTC)

### Fix Summary
- `LiveJsonRuntimeTracker` now receives an `Arc<AtomicBool>` so that when it observes `step_finish`/`turn.completed`, it marks the protocol as completed.
- The adapter wait loop now treats "protocol completed + quiet period" as a successful exit path, terminates any lingering process-group members, and returns success with the captured stdout/stderr.
- Added warnings when protocol completion forces termination so we can see this path in stderr (helps future debugging).

### Regression Coverage
- Added `execute_returns_after_protocol_completion_even_if_process_lingers` covering the exact failure mode (process keeps running for 5s after emitting `step_finish`).
- Existing `execute_does_not_hang_when_background_child_keeps_stdout_open` still passes, proving mixed stdout/long-lived child handling survives the change.

### Impact / Next Steps
- Workflow steps should now finish as soon as opencode reports `step_finish`, even if a stray child keeps stdout open.
- Monitor stderr for the new warning; if it spikes, we can investigate upstream runtimes to shut down more cleanly.

## Protocol Completion Fix VERIFIED (Mar 23, 2026 - 17:30 UTC)

### Test Run
- Workflow run: `6d455314-865b-4ad2-9070-3878ca3f2850`
- Attempt: `57be7228-2b91-4ebf-86ea-a760fdb1a7e7`

### Evidence of Fix Working
1. **opencode step_finish detected**: Sequence 151 shows `"type":"step_finish","reason":"tool-calls"`
2. **runtime_exited with exit_code=0**: Sequence 158 - emitted BEFORE checkpoint completion
3. **runtime_terminated**: Sequence 160 - proper termination handling
4. **All structured observations captured**:
   - `runtime_session_observed` (sequence 152)
   - `runtime_turn_completed` (sequence 153)
   - `runtime_command_completed` (sequence 154)
   - `runtime_tool_call_observed` (sequences 155-157)
5. **Checkpoint completion**: Sequence 167 shows `all_checkpoints_completed`

### Key Timeline
- 17:26:07.403 - opencode emits `step_finish reason=tool-calls`
- 17:26:07.477 - `runtime_exited exit_code=0` emitted (70ms after step_finish)
- 17:26:07.505 - Error: checkpoints incomplete (expected)
- 17:27:01 - Checkpoint manually completed
- 17:27:01.934 - `all_checkpoints_completed` event

### What This Proves
The `WaitOutcome::ProtocolCompleted` path is working correctly:
1. When opencode emits `step_finish`, the `protocol_completed` flag is set
2. After the grace period (250ms) of quiet output, the wait_loop breaks with ProtocolCompleted
3. The execution returns success with exit_code=0
4. `runtime_exited` and `runtime_terminated` events are properly emitted

### Additional Fixes Applied
1. Added `protocol_completed` to tuple destructuring at line 558
2. Added type annotations for `MutexGuard` in closure parameters (lines 637, 646)

### Remaining Issue
Workflow step transition bug: After manually setting step to `succeeded`, the workflow engine tries to transition from Succeeded to Running when ticking. This is a separate bug in the workflow engine, not related to protocol completion detection.


## Workflow Step Completion Bug (Mar 23, 2026 - 17:35 UTC)

### Protocol Completion Fix Status: WORKING ✓
The protocol completion detection fix IS working correctly:
- `runtime_exited` with `exit_code=0` emitted within 26ms of `step_finish`
- All structured observations captured properly
- Checkpoints complete successfully

### Evidence (workflow run 5c62e640-34f6-40a9-aba2-013a3e6a2dbe)
- Sequence 314: `step_finish reason=tool-calls`
- Sequence 320: `runtime_exited exit_code=0` (26ms later)
- Sequence 327: `checkpoint_completed`  
- Sequence 329: `all_checkpoints_completed`

### New Bug: Workflow Step Not Transitioning to Succeeded
After task execution completes successfully with all checkpoints done, the workflow step remains in "running" state instead of transitioning to "succeeded".

**Events observed:**
- `task_execution_state_changed` → "running" ✓
- `runtime_exited exit_code=0` ✓
- `all_checkpoints_completed` ✓
- **Missing**: `task_execution_state_changed` → "succeeded"
- **Missing**: `workflow_step_state_changed` → "succeeded"

**Result:**
- `merge-prepare` fails with "Flow has not completed successfully"
- Workflow cannot advance to next step
- This is a separate bug in the workflow engine's step state machine

### Files Changed
- `src/adapters/opencode/runtime_impl.rs:558` - Added `protocol_completed` to tuple
- `src/adapters/opencode/runtime_impl.rs:637,646` - Added MutexGuard type annotations

### Root Cause of New Bug
The workflow engine receives the successful runtime completion but doesn't properly transition the step from "running" to "succeeded" after checkpoints are completed. This is in the flow/registry code, not in the opencode adapter.

## Workflow Step Completion Bug FIXED (Mar 23, 2026 - 17:46 UTC)

### Problem Summary
The workflow step remained in "running" state after `runtime_exited` and checkpoint completion, even though the underlying synthetic flow task had reached `Success`. This blocked workflow progression and merge operations.

### Root Cause
Workflow step/run reconciliation was too coupled to `tick_workflow_run()`. When task completion happened through the flow execution path (via `complete_task_execution()` or verification success), the workflow bridge didn't always reconcile back to update the step state.

### Fix Applied

#### 1. `complete_task_execution()` - `/home/antonioborgerees/coding/Hivemind/src/core/registry/flow/management/task_execution/complete.rs`
- Added `reconcile_workflow_bridge_for_flow()` call after emitting task completion events
- In auto mode, also reconcile after `auto_progress_flow()` completes
- Ensures workflow step reflects synthetic flow's new state immediately

#### 2. `process_verifying_task()` - `/home/antonioborgerees/coding/Hivemind/src/core/registry/flow/verification/process/task.rs`
- Added `reconcile_workflow_bridge_for_flow()` call after verification success transitions task to `Success`
- In auto-run branch, reconcile after follow-up `tick_flow()` as well

### Regression Test Added
- `workflow_bridge_reconciles_success_when_task_finishes_outside_workflow_tick` in `/home/antonioborgerees/coding/Hivemind/src/core/registry/workflow.rs`
- Verifies workflow step becomes `succeeded` and run becomes `completed` when task finishes through flow path without calling `tick_workflow_run()`

### Verification
- New regression test: PASS ✓
- Existing `workflow_tick_bridges_task_steps_into_synthetic_flow_execution`: PASS ✓

### Impact
Workflow steps now properly transition from `running` → `succeeded` when synthetic flow tasks complete, regardless of which code path drives the completion.

## End-to-End Test Results (Mar 23, 2026 - 18:00 UTC)

### Test Summary
- Workflow run: `80cfabe6-f09a-4f6e-a91e-a7a4116dc014`
- Regression tests: PASS ✓ (both `workflow_bridge_reconciles_success_when_task_finishes_outside_workflow_tick` and `workflow_tick_bridges_task_steps_into_synthetic_flow_execution`)

### What Works
1. Protocol completion detection ✓ - `runtime_exited exit_code=0` emitted within 26ms of step_finish
2. Checkpoint completion ✓ - manually via CLI, all_checkpoints_completed event emitted
3. Step can be manually set to succeeded ✓

### What Doesn't Work
After checkpoints are completed, the task does NOT automatically transition to "Success" and the workflow run does NOT transition to "completed".

**Event timeline:**
- seq 494: `runtime_exited exit_code=0` 
- seq 495: `error_occurred checkpoints_incomplete` - initial completion attempt failed
- seq 501: `checkpoint_completed` (manually via CLI)
- seq 503: `all_checkpoints_completed`
- **Missing**: `task_execution_state_changed` to "Success"
- **Missing**: `workflow_run_state_changed` to "completed"
- **Missing**: `workflow_step_state_changed` to "succeeded"

### Root Cause Analysis
The fix in `complete_task_execution()` calls `reconcile_workflow_bridge_for_flow()` when task completion events are emitted. However:
1. When `runtime_exited` with `exit_code=0` but checkpoints incomplete, `complete_task_execution()` returns an error
2. The reconciliation happens on error path too, but the task is still in "Running" state
3. When checkpoints are later completed via CLI, there's no code path that re-triggers task completion
4. The task remains "Running" even though all checkpoints are done

### Issue with Manual Checkpoint Completion
The reconciliation fix works when:
- Task completion happens through the flow engine (auto mode)
- The code calls `reconcile_workflow_bridge_for_flow()` after task state transitions

But when checkpoints are completed manually via CLI after the runtime has exited:
- No flow engine code is re-triggered
- The task remains in "Running" state
- The reconciliation is never called

### Remaining Work
Need a code path that, when checkpoints are completed manually, either:
1. Re-triggers the task completion flow, OR
2. Directly transitions the task to Success when all checkpoints complete

## Double runtime_exited Bug FIXED (Mar 23, 2026 - 18:40 UTC)

### Problem Summary
When runtime completed successfully (`exit_code=0`), but checkpoint gate failed (`checkpoints_incomplete`), the `handle_runtime_failure()` was still emitting `RuntimeExited(-1)` before the early return. This caused two `runtime_exited` events:
1. `runtime_exited exit_code=0` - from successful execution
2. `runtime_exited exit_code=-1` - from `handle_runtime_failure()` 

The second event overwrote the first in `attempt_runtime_outcome()`, causing task completion logic to fail.

### Root Cause
In `handle_runtime_failure()` (`recovery.rs`), the `RuntimeExited(-1)` event was emitted BEFORE checking if `failure_code == "checkpoints_incomplete"` for early return.

### Fix Applied
1. **`handle_runtime_failure()` in `recovery.rs`**: Moved the early return for `"checkpoints_incomplete"` to BEFORE the `RuntimeExited` event emission. Now when `failure_code == "checkpoints_incomplete"`, only `RuntimeTerminated` is emitted (without `RuntimeExited`).

2. **`attempt_runtime_outcome()` in `outcome.rs`**: Modified to track if `exit_code=0` was ever seen before a `checkpoints_incomplete:` termination. If so, returns `exit_code=0` instead of the last exit code.

### Files Changed
- `src/core/registry/runtime/recovery.rs` - Early return before RuntimeExited emission
- `src/core/registry/flow/support/retry/outcome.rs` - Track exit_code=0 before failure

### Verification
Flow `047c80dc-f464-435e-a062-919e0648fd32` completed successfully:
- seq=837: `runtime_exited exit_code=0` ✓
- seq=839: `runtime_terminated reason=checkpoints_incomplete:...` ✓
- seq=840: `checkpoint_completed` ✓
- Flow state: **completed** ✓

### Tests
All 344 tests pass ✓

