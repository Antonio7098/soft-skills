# Domain Model

## Domain Principle

SoftSkills is competency-first. Content, assessments, and dashboards exist to
measure and improve real capability, not to accumulate disconnected activity.

## Core Entities

### Skill

A specific, trainable ability that can be practiced and scored directly.

Examples:

- active listening
- concise speaking
- structured thinking
- empathy
- expectation setting
- negotiation
- conflict handling
- prioritization under pressure
- executive summary writing
- decision justification

### Competency

A broader capability composed of multiple weighted skills and their application
in realistic situations.

Examples:

- stakeholder management
- communication
- teamwork
- leadership
- prioritization
- professionalism
- problem solving
- adaptability
- managing ambiguity
- client delivery

### Rubric

A versioned scoring framework that defines assessment criteria, scale,
skill mapping, evidence expectations, and feedback structure for a content type
or practice mode.

### Collection

A grouped set of practice items organized around a theme, audience, level, or
learning objective.

Collections may also carry a verification status that indicates whether the
platform has elevated them beyond standard user-created content.

### Scenario

A realistic workplace situation with context, actors, constraints, goals, and
supporting artifacts.

### Mock Company

A fictional organization used to ground scenarios in believable business
context.

### Mock Person

A fictional stakeholder with role, goals, communication style, and relationship
to the scenario.

### Prompt Item

A discrete interview question, quick practice prompt, or scenario turn that a
learner responds to.

### Attempt

A learner response to a prompt item or scenario step, including response
content, timestamps, mode metadata, trace identifiers, and persistence status.

### Assessment

A validated scoring artifact linked to an attempt, rubric version, prompt
version, and model metadata. It contains overall score, skill-level scores,
evidence, rationale, and improvement guidance.

### Progress History

A time-series record of demonstrated performance across skills and
competencies, derived from assessed attempts.

### Observability Artifact

The recorded trace, event stream, prompt metadata, model metadata, and failure
artifacts associated with a workflow execution.

## Core Relationships

- Skills belong to one or more competencies with defined weighting.
- Rubrics score one or more skills and may roll those scores into competencies.
- Collections contain prompt items, scenarios, and supporting mock-world assets.
- Scenarios may reference a mock company, multiple mock people, and multiple artifacts.
- Each attempt is linked to exactly one learner, one content item, one rubric version, and one trace.
- Each assessment is linked to exactly one attempt and must preserve the prompt version and model identity used to create it.
- Progress history is derived from validated assessments, not from raw activity logs.
- A collection may be authored by any standard user account, but only admin verification can elevate it for wider trust or discovery.

## MVP Content Hierarchy

1. A collection packages a coherent learning unit.
2. A collection contains one or more prompt items or scenarios.
3. A scenario may contain multiple steps, actors, and artifacts.
4. Each learner interaction creates an attempt.
5. Each attempt may yield exactly one finalized assessment artifact.

## Required Lifecycle States

### Content

- `draft`
- `review`
- `published_private`
- `published_public`
- `archived`

### Collection Verification

- `unverified`
- `verified`
- `rejected`

### Attempt

- `started`
- `submitted`
- `assessment_pending`
- `assessed`
- `assessment_failed`

### Assessment

- `validated`
- `rejected`
- `superseded`

## Domain Invariants

- Every assessable content item must map to at least one skill and one rubric.
- Every competency score must be explainable through underlying skill evidence.
- Every assessment must reference explicit versions for rubric, prompt contract, and model metadata.
- Invalid or partial scoring artifacts must never update progress history.
- Content marked public must be internally consistent and review-approved.
- Verified collections must be a strict subset of user-authored public collections and require explicit admin action.
- Mock companies, people, and artifacts must remain coherent within the same scenario.

## Initial MVP Skill Framework

The platform-defined MVP framework should start narrow enough to calibrate
assessment quality.

### Frozen MVP V1 Competencies

- stakeholder management
- communication
- teamwork
- prioritization
- professionalism
- problem solving
- adaptability
- managing ambiguity

### Frozen MVP V1 Skills

- active listening
- structured communication
- concise explanation
- empathy
- expectation setting
- prioritization under pressure
- conflict handling
- negotiation
- executive summary
- decision justification

### Frozen MVP V1 Competency Mapping

This mapping is the initial source of truth for Sprint 1 and Sprint 2 seed
data. Expansion is allowed later, but changes must be explicit canon updates
rather than ad hoc implementation drift.

| Competency | Seed skills |
| --- | --- |
| stakeholder management | active listening, empathy, expectation setting, negotiation |
| communication | structured communication, concise explanation, executive summary |
| teamwork | active listening, empathy, conflict handling |
| prioritization | prioritization under pressure, decision justification, executive summary |
| professionalism | expectation setting, concise explanation, conflict handling |
| problem solving | structured communication, decision justification, executive summary |
| adaptability | active listening, prioritization under pressure, decision justification |
| managing ambiguity | expectation setting, prioritization under pressure, negotiation |

### Frozen MVP V1 Rubric Families

The MVP starts with a narrow rubric set tied to the text-first practice modes.
Rubrics are platform-defined and versioned.

- `quick_practice_text`: compact single-response rubric for one prompt with one to three target skills
- `scenario_text`: rubric for workplace scenario responses with tradeoffs, stakeholder handling, and reasoning
- `interview_text`: rubric for interview-style answers with clarity, evidence, and follow-up readiness

All rubric families must produce:

- an overall score
- skill-level scores for mapped skills
- evidence excerpts
- rationale tied to rubric dimensions
- strengths
- weaknesses
- suggested next actions

### Frozen MVP V1 Assessable Content Types

Only the following content types are assessable in the initial MVP:

- `quick_practice_prompt`
- `scenario_step`
- `interview_prompt`

Non-assessable supporting artifacts may exist for context, but they must not be
treated as independently scored attempt targets.

## Modeling Guidance

- Prefer explicit entities over generic metadata blobs.
- Version any object that affects scoring semantics or learner-visible meaning.
- Keep domain models separate from API transport models, ORM models, and LLM response shapes.
- Treat observability artifacts as first-class linked records, not debug leftovers.
