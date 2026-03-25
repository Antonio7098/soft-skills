# SoftSkills — Capstone Project Proposal

## Project Vision

An AI-powered consultancy skills practice platform where users practice realistic workplace scenarios, receive rubric-based feedback against explicit competency frameworks, and track measurable improvement over time.

**What I'm building:** A platform that lets users practice consultancy and professional skills in simulated environments — think stakeholder management, communication under pressure, conflict handling — and get AI-generated marks and feedback that are traceable, evidence-based, and linked to a competency progression system.

**Why it matters to me:** I wanted a way to practice consultancy skills in realistic simulated environments. There are corporate upskilling platforms, but they tend to be generic, expensive, or focused on compliance rather than genuine skill development. I learn best through deliberate practice with good feedback loops, and nothing existing quite hit that for the tech/AI consultancy space I operate in.

---

## Part 1 — The Big Picture

### 1. What's the idea, and why does it matter to you personally?

An AI powered consultancy skills practice platform.

**What's the itch?** I wanted to practice consultancy skills in simulated environments. Currently the alternatives are either nothing (just reading theory) or recording yourself and manually reviewing — both poor feedback loops. Corporate tools like Skillsoft's CAISY exist but are expensive, generic, and not tailored to tech/AI consultancy contexts.

**Why me?** I have a passion for learning systems that make picking up new knowledge and skills easier and more efficient. I'm also close enough to the consultancy world to know what realistic practice looks like and what bad feedback feels like.

### 2. Who is this for?

Primarily for myself, but extensible to anyone wanting to practice consultancy skills — DF consultants, tech professionals preparing for behavioural interviews, client-facing AI practitioners.

Currently they either do nothing or resort to recording themselves. Recording is labour-intensive and provides no structured feedback.

A real person would use this: I would. The system can be generalised for any kind of competency-based learning.

### 3. What already exists?

Corporate upskilling platforms (Skillsoft Percipio with CAISY), AI interview tools (Interviews by AI, CasewithAI).

**What can be learned:**
- Traceability is key — users need to understand why they got a score
- Mock scenarios must be grounded and realistic, not generic
- Progress analytics drive engagement
- Accessibility helps people fit practice into busy schedules

**USP of this version:**
- Driven by competency and skills with progress tracking
- Tailored for tech and AI consultancy
- Creator and scenario ecosystem (versioned mark schemes, LLM assessment)
- Trace-linked evidence gives explainability

### 4. What are your assumptions?

- An LLM can consistently, accurately, and reliably mark and score answers
- If this assumption is wrong, the entire platform collapses — this is the core dependency

**Validation approach:** An evaluation framework with benchmark cases, rubric fidelity checks, and consistency evals must be built alongside the marking engine.

---

## Part 2 — System Design

### 5. What is the core job of the AI?

**Generation and Reason/Decide.** The AI drives:
- Content generation (scenarios, questions, mock companies/stakeholders)
- Response marking (rubric-based scoring with evidence extraction)

### 6. What goes in, and what comes out?

| Flow | Input | Output |
|---|---|---|
| Practice | User selects collection/scenario, types or speaks a response | Attempt stored, sent for assessment |
| Assessment | Attempt + rubric + prompt version | Score out of 10, skill breakdown, evidence, feedback, next steps |
| Progress | Validated assessment | Updated skill/competency aggregates, confidence bands |
| Recommendation | Learner context + progress snapshot + content catalog | Ranked next-practice items with reason codes |

**Human in the loop:** Not required for MVP. Fully automated from attempt submission through to feedback delivery.

### 7. What context or knowledge does the AI need?

- **Locally stored guide/instructions** for creating content (mark schemes, rubric definitions)
- **RAG over scenario materials** for deeply guiding specific scenarios
- **Few-shot prompting** for consistent marking behaviour
- **System prompting** for persona and tone (coach/evaluator persona)

### 8. Rough System Components

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐
│   Frontend  │────▶│  FastAPI    │────▶│  Marking Engine  │
│  (React/TS) │◀────│  (Python)   │◀────│  (Stageflow)     │
└─────────────┘     └──────┬──────┘     └──────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Progress   │     │  Content    │     │Observability│
│  Engine     │     │  Catalog    │     │   Layer     │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Data flow:** Frontend → API → Marking Engine (Stageflow orchestration) → Validated Assessment → Progress Engine → Snapshot → Recommendation Engine → Frontend

**Likely failure points:**
- LLM returns malformed JSON from marking engine → validation rejects, retry
- Scoring inconsistency across runs → eval framework catches drift
- Attempt silently lost → observability layer requires trace confirmation at every step

**User journey (happy path):**
1. User selects a collection (e.g., "Stakeholder Management Scenarios")
2. User reads scenario context and prompt item
3. User types a response
4. System submits attempt → marking engine scores against rubric
5. User receives score, evidence citations, strengths, weaknesses, next steps
6. Progress snapshot updates
7. Recommendation engine suggests next practice based on weak skills

### 9. Minimum Viable Version (1-day fallback)

**The marking engine core:** Takes a user response + rubric + prompt contract → returns a validated marking decision with score, evidence, and feedback.

If everything else fails, this must work. It is the core value demonstrator.

---

## Part 3 — Definition of Done

### 10. What does a successful demo look like?

**Day 5 demo walkthrough:**

1. User opens the platform and lands on the dashboard
2. User selects a collection ("Consultancy Fundamentals")
3. User starts a practice session — a scenario loads with stakeholder context
4. User types a response to the prompt
5. System processes and returns:
   - Overall score (e.g., 7/10)
   - Skill-level breakdown (stakeholder communication: 8, structured thinking: 6, ...)
   - Evidence extracted from the response with citations
   - Strengths and weaknesses
   - Suggested next actions
6. Dashboard updates to show progress in the targeted competency

**What would make me proud:** A non-technical person watches the demo and immediately understands why the feedback is useful and trustworthy — not because they understand AI, but because the evidence is cited and the reasoning is clear.

### 11. What does failure look like?

| Failure Mode | Impact | Mitigation |
|---|---|---|
| Bad marking (wrong scores, generic feedback) | Core value destroyed | Eval framework with golden cases; rubric fidelity evals |
| Hallucinated evidence | Breaks trust entirely | Evidence must cite concrete spans; validation rejects unsupported claims |
| Inconsistent scoring across identical runs | Destroys progress signal | Consistency evals; bounded variance thresholds |
| Latency > 10s for quick practice | Breaks engagement | Near-immediate feedback target; async fallback with state |
| Cost explosion from LLM calls | Operational risk | Caching, retry limits, observability on per-call cost |

**The most embarrassing failure:** A user submits a response and gets back a generic "Good job!" with no evidence. This would be worse than returning nothing. Validation must reject generic or unsupported feedback.

**Pre-demo validation checklist:**
- Run all golden benchmark cases through marking engine
- Verify evidence citations are present and specific
- Check scoring consistency on repeated identical inputs
- Confirm all traces have complete metadata

### 12. What does success look like on Day 5?

- User can initiate a practice question and receive a score with competency/skill breakdown, feedback, and next steps
- Marking engine is the demonstrated core — it works reliably on golden cases
- Basic content catalog with at least one collection is browsable
- Progress snapshot updates after an assessment
- Recommendation engine surfaces a next-practice suggestion
- Observability traces cover the full practice → assess → progress loop

---

## Reference: MVP Spec Canonical Documents

This proposal is grounded in the following canonical documents from `ops/mvp-spec/`:

| Document | Key Points |
|---|---|
| `foundational/PRD.md` | Full product vision, user stories, feature scope, success metrics |
| `foundational/domain-model.md` | Skill/competency taxonomy, rubric versioning, attempt/assessment lifecycle |
| `foundational/technical-architecture.md` | Python/FastAPI backend, React/TypeScript frontend, Stageflow orchestration |
| `foundational/product-spec.md` | MVP goals, resolved decisions, excluded features |
| `engines/marking-engine.md` | Universal marking workflow, validation rules, eval framework, evidence requirements |
| `engines/progression-engine.md` | Evidence-only progression, decay weighting, confidence tracking |
| `engines/recommendation-engine.md` | Deficit-driven scoring, explainable recommendations with reason codes |
| `platform/assessment-and-progression.md` | Assessment output contract, scoring rules, progression update semantics |
| `platform/soft-skill-progression.md` | Skill aggregation, competency rollup, explainability ledger |
| `platform/soft-skill-recommendation.md` | Feature derivation, scoring pipeline, integration points |
| `operations/content-system.md` | Collection/scenario requirements, authoring flows, realism rules |
| `operations/observability-and-operations.md` | Trace requirements, event model, error taxonomy, LLM artifact rules |

---

## Key Assumptions to Validate

1. **LLM marking reliability** — Core assumption. Must be validated via eval framework before trusting in demo.
2. **Scoring consistency** — Same response should score within tight bounds across runs.
3. **Evidence extraction quality** — Feedback must cite specific spans, not generic praise.
4. **Progress signal coherence** — Repeated practice should produce measurable skill movement in the right direction.

---

*This document is a living artifact. Answers reflect actual thinking, not ideal thinking. Update as the project evolves.*
