# Product Spec

## Product Summary

SoftSkills is an AI-driven practice platform for consultancy and professional
skills in tech and AI contexts. The MVP helps users practice realistic
workplace and interview situations, receive rubric-based feedback, and track
improvement over time.

## Product Outcome

The product outcome is meaningful competency growth over time. The MVP is
successful when users can repeatedly demonstrate better judgment,
communication, prioritization, and stakeholder handling through structured
practice and explainable assessment.

## Target Users

### Primary User: Individual Learner

Learners preparing for:

- consultancy roles
- behavioral interviews
- client-facing tech roles
- AI and digital transformation roles
- graduate and early-career roles

They need realistic practice, actionable feedback, measurable progress, and
flexible session length.

### Secondary User: Coach, Educator, or Program Admin

These users need cohort visibility, learner progress insight, weak-skill
detection, and confidence that assessment outputs are traceable and consistent.

### Tertiary Use Case: Learner As Creator

The same authenticated user account can also create content. Learners who
author collections need fast authoring, control over generated drafts, and a
clean model for packaging collections, scenarios, mock companies, and
supporting artifacts.

## MVP Product Goals

- Help users improve professional performance through deliberate practice.
- Make assessment explainable at rubric, skill, and evidence level.
- Track progression using repeated demonstrated performance, not simple activity.
- Support scalable content authoring without sacrificing realism or quality.
- Give admins enough visibility to guide learners and review platform quality.

## MVP Core Loop

1. A learner selects or is recommended practice.
2. The learner completes a text-based attempt.
3. The system validates, scores, and explains the attempt against a rubric.
4. The learner reviews strengths, weaknesses, and next actions.
5. Progress history updates.
6. The system recommends a next step based on weak skills and recent evidence.

## MVP Scope

### Included

- account and profile creation
- learner goals, target role, and practice preferences
- platform-defined skill and competency framework
- collections, scenarios, interview prompts, and quick practice prompts
- text-first interview simulation
- text-first scenario practice
- structured AI assessment and feedback
- attempt history and progress dashboards
- lightweight mock companies, mock people, and supporting artifacts
- manual and AI-assisted content creation
- basic admin dashboard for learner and cohort insight
- end-to-end observability foundations

### Explicitly Excluded

- multiplayer roleplay
- advanced peer collaboration
- enterprise SSO and enterprise-grade permissions
- monetized creator marketplace
- unrestricted public publishing without review controls
- advanced voice analytics
- video analysis
- psychometric or hiring-grade certification

## MVP Practice Modes

### Interview Simulation

The MVP supports text-first simulated interview practice with follow-up probing
and competency-linked scoring.

### Scenario Practice

The MVP supports realistic workplace scenarios involving pressure, ambiguity,
stakeholder tension, and tradeoff handling.

### Quick Practice

The MVP supports short prompts focused on a single skill or compact scenario.

### Voice Position

Speech and voice interaction are not required for MVP completeness. If included
early, they must behave as a thin input layer on top of the same typed attempt,
assessment, and trace contracts as text flows.

## MVP User Outcomes

### Learner

- complete realistic practice in minutes, not only long simulations
- understand why a score was given
- see which skills are improving or stagnating
- receive recommended next practice tied to actual weaknesses

### Admin or Educator

- review learner and cohort progress by skill and competency
- identify weak-skill clusters
- inspect scoring metadata and trace identifiers when needed

### Learner As Creator

- create or generate draft collections quickly
- edit content before publication
- align each item to skills, competencies, difficulty, and rubric expectations
- submit strong collections for admin verification and broader discovery

## Resolved MVP Decisions

These decisions close ambiguities from the PRD so development can proceed.

### Competencies

Competencies are platform-defined for MVP. Users authoring content map to the
existing framework rather than creating new competency models.

### Rubrics

Rubrics are platform-defined and versioned. Users authoring content can select
from supported rubric types and assign skills, but they cannot define arbitrary
scoring logic in MVP.

### Account Model

There is one standard authenticated user account for MVP. Any learner can also
author content. Admin is the only distinct elevated role required in MVP.

### Public Content

Public sharing is gated. Users can save drafts and publish private collections
freely, but admin verification is required before a user-created collection is
elevated for broader discovery or trusted public visibility.

### Progress Semantics

Progress uses repeated evidence over time with recency weighting. Historical
performance remains visible and is never replaced by a single strong or weak
attempt.

### Confidence Display

Model confidence is not a user-facing MVP feature. Internal confidence signals
may exist for diagnostics, but learner-facing trust should come from evidence,
rubrics, and traceability.

### Admin Visibility

Admins see learner and cohort progress, assessment summaries, and trace-linked
diagnostic metadata. Access to full attempt content should be limited to users
with a legitimate management or educational relationship.

## Success Metrics

### Product Metrics

- weekly active learners
- repeat practice rate
- completion rate per collection
- percentage of learners returning after first week and first month

### Learning Metrics

- improvement in skill scores over time
- percentage of learners with sustained progression
- completion rate of recommended weak-skill practice

### Trust and Quality Metrics

- scoring consistency on benchmarked samples
- percentage of attempts with complete trace metadata
- assessment validation failure rate
- content generation acceptance and edit rate

## Non-Goals for MVP Execution

- maximizing prompt volume or content count
- shipping novelty features before the assessment loop is trustworthy
- hiding ambiguity behind vague AI language
- equating completion with learning
