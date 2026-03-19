# Live Chat Interview Practice

## Purpose

Extend the text-first loop into realtime practice where an interviewer (LLM- or
coach-driven) converses with the learner in a synchronous chat experience. The
feature keeps rubric explainability and scoring transparency from the MVP while
enabling higher-pressure interview drills.

## Goals

- Deliver a conversational UX that feels like a real interviewer probing and
  adapting in real time.
- Preserve the `attempt -> assessment -> progression` contract even when the
  attempt is composed of many turns.
- Provide rich observability (latency, failures, scoring drift) for live flows.
- Allow admins or coaches to shadow or take over a session without breaking
  traceability.

## Non-Goals

- Voice calls or video interviewers (covered separately by media archive).
- Multiplayer candidate panels.
- Automated hiring or decisioning.

## User Stories

1. **Learner:** Start a live interview aligned to a job target, complete a
   15-minute session, and receive rubric-scored feedback with transcripts.
2. **Coach/Admin:** View live sessions, intervene when needed, and review
   assessment artifacts afterwards.
3. **System:** Adjust follow-up questions using assessment signals without
   exposing raw LLM prompts to the learner.

## Experience Flow

1. Learner selects a collection or role-based interview and opts into "Live
   Chat" mode.
2. System preps the session: loads scenario state, fetches calibrated prompts,
   reserves compute, emits session trace ID.
3. Session runs as a structured multi-turn conversation:
   - Interviewer sends scripted opener.
   - Learner responds within time boxes (typing indicator, countdowns).
   - Interviewer issues adaptive follow-ups referencing rubric-linked skills.
4. When timer elapses or learner ends the session, the transcript is frozen and
   passed to the assessment pipeline (same rubric contract as MVP).
5. Feedback page renders: overall score, skill deltas, recommended next
   practice, and transcript snippets tagged to rubric evidence.

## Interaction Requirements

- **Latency:** <2 seconds for interviewer responses to keep flow natural.
- **Turn Budget:** Configurable (default: 8-10 turns). Hard limit enforced to
  protect model costs.
- **Pause/Resume:** Learner can pause once per session (max 2 minutes) without
  invalidating assessment.
- **Safeguards:** Auto-stop on platform policy violations with clear messaging
  and trace capture.

## Technical Architecture

```
Client (Live Chat UI)
  ↓ websocket
Realtime Session Service (state machine, timers)
  ↓ RPC
LLM Interviewer Agent (scenario + rubric aware)
  ↓
Assessment Pipeline (existing marking engine)
  ↓
Progression Engine / Dashboards
```

### Key Components

- **Realtime Session Service:** new service (Node or Go) that maintains session
  state, orchestrates turn-taking, enforces timers, and records structured
  events to the observability pipeline.
- **Interview Agent:** specialized prompt stack built on top of the existing
  content scaffolding. Must log every prompt variant with version IDs.
- **Assessment Bridge:** converts multi-turn transcripts into a single attempt
  contract before calling the existing marking engine.
- **Web Client:** React/Vite app additions for live chat UI, typing indicators,
  network resilience, and post-session review.

## Data Contracts

- `LiveSession` (new): references learner, scenario, collection, rubric version,
  and carries session state machine metadata.
- `LiveTurn`: ordered records of interviewer/learner messages with timestamps,
  tone markers, and safety flags.
- `Attempt`: extended to allow `source=live_chat` and link back to the
  `LiveSession` ID. No changes to scoring schema.
- `Trace`: minted at session creation; every prompt and response event attaches
  to this trace.

## Observability & Operations

- Emit structured events for session start/end, model invocations, latency
  buckets, and safety cutoffs.
- Record fallbacks (e.g., switch to scripted question when LLM call fails).
- Provide dashboards for concurrent sessions, failure rate, and average
  assessment turnaround.
- Support replay mode for QA: reconstruct a session from stored turns and traces
  to investigate issues.

## Dependencies & Sequencing

1. Harden existing marking engine to accept multi-turn transcripts.
2. Ensure recommendation engine can target live chat attempts when suggesting
   next practice.
3. Expand progression engine rules to weigh live attempts appropriately.
4. Align content collections with live-ready scripts (intro, follow-ups, closing
   prompts).

## Open Questions

- Should learners schedule live sessions or launch on demand? (affects compute
  reservations.)
- Do we allow hybrid sessions where a human coach takes over mid-run?
- What is the escalation path when a learner times out or disconnects?
- How do we price throttling to avoid overuse on free tiers?
