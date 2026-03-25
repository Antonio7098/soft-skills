# Content System

## Content Principle

Generated and authored content must serve realism and learning. The system
should prefer coherent, specific, instructive scenarios over generic AI filler.

## Content Types

The MVP supports:

- collections
- interview prompts
- scenario prompts
- quick practice prompts
- mock companies
- mock people
- scenario artifacts such as emails, notes, reports, and messages

## Collection Requirements

Every collection should define:

- title and summary
- target audience
- intended difficulty
- target skills
- target competencies
- content format mix
- rubric mapping
- author and publication status
- verification status

Collections are the primary browsing and recommendation unit in MVP.

## Scenario Requirements

Every scenario should define:

- business context
- learner objective
- constraints and tensions
- stakeholder actors
- expected skill focus
- rubric mapping
- supporting artifacts when needed

Scenario realism matters more than narrative complexity.

## Runtime Delivery Rules

- Interview prompts and scenario steps should be deliverable through the same
  typed runtime contract as quick practice.
- Scenario runtime payloads may include validated artifacts such as emails,
  notes, or reports when the practice turn depends on them.
- Runtime-added artifacts must be persisted with the delivered prompt snapshot
  so assessment replay keeps the exact learner context.

## Authoring Flows

The MVP supports three authoring flows:

### Manual Authoring

Any authenticated user can write or edit content directly and assign skills,
competencies, difficulty, and rubric metadata.

### Structured Generation

Any authenticated user can fill a form that constrains generation around
audience, domain, difficulty, scenario type, and skill targets.

### Chat-Based Generation

Any authenticated user can use natural language prompts to generate drafts,
then review and edit before publication.

## Publication Workflow

1. Draft content is created manually or via AI assistance.
2. The user edits and assigns metadata.
3. The system validates required fields and mappings.
4. The content is saved for private use or published publicly as standard
   user-created content.
5. Admins can verify a user-created public collection and elevate it for broader discovery.

Elevation must not bypass admin verification controls in MVP.

## Authoring Guardrails

- Users map content to existing competencies and rubric types.
- Users cannot publish incomplete or unmapped content.
- AI-generated drafts must remain editable before publication.
- Supporting artifacts must stay consistent with the scenario context.

## Realism Rules

- Stakeholders should have plausible motives and constraints.
- Mock companies should reflect a believable operating context.
- Scenarios should include meaningful tradeoffs, not obvious textbook answers.
- Difficulty should come from ambiguity, pressure, and competing priorities, not artificial trick wording.
- Content should reflect consultancy, tech, and AI-adjacent workplace situations in MVP.

## Discovery And Reuse

Learners should be able to:

- browse collections
- filter by difficulty, skill, competency, and format
- save collections
- revisit previously used content

Admins and educators should be able to recommend collections to learners or
cohorts.

Verified collections should be discoverable as elevated content distinct from
standard user-created material.

## MVP Content Boundaries

- Open marketplace mechanics are out of scope.
- Community voting can exist, but it is secondary to the core learning loop.
- Uploaded external company documents are out of scope for MVP.
- Admin verification for elevated public content should stay lightweight but mandatory.
