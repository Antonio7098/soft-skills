# PRD — AI-Driven Consultancy & Professional Skills Practice Platform

## 1. Product Overview

### Product Name

Working title: **SoftSkills**
(alternative placeholder names: **COnsultencySkills**, **ConsultIQ**, **CompetencyLab**, **PracticeOS**)

### Product Vision

Create an AI-driven platform that helps users practice and improve consultancy and professional skills in tech and AI environments through realistic simulations, structured assessment, and long-term progression tracking.

### Problem Statement

Aspiring consultants, tech professionals, and candidates preparing for behavioural interviews often struggle to practice professional skills in a structured, realistic, and repeatable way. Existing tools tend to be static, generic, or focused only on interview questions rather than real workplace performance.

Users need a system that allows them to practice skills such as stakeholder management, communication, teamwork, deadline handling, prioritisation, and professional judgement in realistic contexts, while receiving clear feedback and measurable progress over time.

### Product Thesis

Professional performance can be trained more effectively when users:

* practice in realistic contexts
* receive feedback against explicit rubrics
* improve underlying skills over time
* repeatedly apply those skills across scenarios, interviews, and simulated workplace interactions

This product will combine **AI simulation**, **AI marking**, **content generation**, and **skill progression** into a single practice platform.

---

# 2. Goals

## Primary Goals

* Help users improve consultancy and professional skills through deliberate practice
* Provide realistic AI-generated and curated practice experiences
* Assess responses using structured, skill-linked rubrics
* Track user development over time at both skill and competency level
* Enable scalable content creation through forms, manual authoring, and natural language generation

## Secondary Goals

* Build a shareable content ecosystem through collections and scenario banks
* Provide educators, mentors, or programme administrators with learner analytics
* Create a trusted AI assessment system with strong observability and traceability

---

# 3. Non-Goals (MVP)

The MVP will not aim to:

* fully replace human coaching
* provide certified hiring decisions
* support every profession beyond consultancy / tech / AI initially
* provide perfect voice sentiment or body-language analysis
* build a fully open creator marketplace with monetisation on day one
* generate unrestricted content without moderation or review workflows

---

# 4. Target Users

## Primary User: Individual Learner

A learner preparing for:

* consultancy roles
* behavioural interviews
* client-facing tech roles
* AI / digital transformation roles
* graduate schemes / internships / early-career roles

They want:

* realistic practice
* clear, actionable feedback
* measurable progress
* flexible modes of practice

## Secondary User: Coach / Educator / Programme Admin

A mentor, bootcamp lead, university trainer, or internal L&D manager who wants:

* student activity data
* progress tracking
* skill gap visibility
* curated collections for cohorts

## Tertiary User: Content Creator

A user who wants to create and share:

* scenario collections
* mock company simulations
* question banks
* curated practice paths

---

# 5. Core Concepts

## Skill

A specific, trainable ability used to perform tasks.

Examples:

* structured communication
* active listening
* prioritisation
* conflict handling
* presenting clearly

## Competency

A broader capability formed by the application of multiple skills, behaviours, judgement, and experience in real situations.

Examples:

* stakeholder management
* leadership
* client communication
* teamwork
* managing ambiguity

## Collection

A grouped set of practice content around a theme, topic, level, or use case.

Examples:

* Consultancy Fundamentals
* Behavioural Interview Prep
* AI Delivery Under Pressure
* Junior Consultant Client Scenarios

## Scenario

A realistic workplace situation with context, goals, constraints, people, and supporting materials.

## Mock Company / Mock Person

Fictional but realistic business entities and stakeholders used to create immersive practice environments.

## Attempt

A user response to a question or scenario, including transcript, score, evidence, feedback, and metadata.

---

# 6. Product Scope

## In Scope

* interview simulation
* scenario-based practice
* quick practice questions
* speech exercises
* AI marking with rubric scoring
* skill and competency progression
* collections and scenario banks
* content creation via form, manual authoring, or chatbot
* mock companies, people, and projects
* user dashboard
* admin / educator dashboard
* traceability and observability infrastructure

## Out of Scope for MVP

* real-time multiplayer roleplay
* advanced peer collaboration features
* video analysis
* enterprise SSO / full enterprise permissions
* monetised creator marketplace
* official psychometric evaluation

---

# 7. User Needs

## Individual Learner Needs

* I need realistic practice, not generic questions
* I need feedback that is actionable and not vague
* I need to see whether I am improving
* I need short practice options as well as deeper simulations
* I need practice that reflects consultancy / tech / AI workplaces

## Educator / Admin Needs

* I need to assign or recommend content
* I need to understand learner progress
* I need insight into weak skills across a group
* I need confidence that scores are consistent and traceable

## Creator Needs

* I need easy ways to create content
* I need AI assistance without losing control
* I need a clean way to package and share content

---

# 8. Key Features

## 8.1 Practice Modes

### A. Interview Simulation

Users engage in simulated interviews, optionally through voice mode.

Includes:

* behavioural interview questions
* follow-up probing
* role-specific questioning
* competency-focused scoring

### B. Scenario Practice

Users respond to workplace situations such as:

* unhappy stakeholders
* conflicting deadlines
* project risk escalation
* team misalignment
* scope changes
* ambiguous client asks

### C. Quick Practice

Short low-friction questions focused on a single skill or compact scenario.

### D. Speech Exercises

Practice concise speaking tasks such as:

* executive summary
* difficult conversation
* persuasion
* meeting update
* client explanation

---

## 8.2 Skill & Competency Framework

The platform will include:

* a predefined skill taxonomy
* competencies composed of weighted underlying skills
* rubrics for scoring attempts
* user progression across time

Example:

* Competency: Stakeholder Management

  * communication clarity
  * empathy
  * negotiation
  * prioritisation
  * expectation setting

---

## 8.3 AI Marking & Feedback

Each attempt will produce:

* overall score
* skill-level scores
* rubric-based assessment
* strengths
* weaknesses
* suggested improvement actions
* optional example stronger answer structure

Scoring should be:

* evidence-based
* rubric-linked
* transparent
* consistent over time

---

## 8.4 Content Model

Collections may contain:

* interview questions
* quick questions
* scenarios
* mock companies
* mock people
* artefacts such as emails, reports, messages, notes

Content can be:

* platform-authored
* AI-generated
* user-created
* shared publicly or privately

---

## 8.5 Content Authoring

Three creation flows:

* manual creation
* structured generation form
* chatbot-based agentic creation

Examples:

* “Generate a junior consultant collection focused on difficult stakeholders and deadline pressure”
* “Create 10 questions for a mock AI transformation project in the public sector”

---

## 8.6 Community / Scenario Bank

Users can:

* upload scenarios
* save collections
* upvote useful content
* browse public content
* build personal collections

---

## 8.7 User Dashboard

Displays:

* recent activity
* skill progression
* competency progression
* streak / engagement metrics
* strengths and gaps
* recommended next practice

---

## 8.8 Admin / Educator Dashboard

Displays:

* learner activity
* cohort performance
* weak skills by learner or cohort
* collection usage
* assessment trends

---

## 8.9 Observability & Traceability

The product should support:

* structured logging
* prompt versioning
* trace IDs for every AI workflow
* model/version metadata
* error taxonomy
* event capture across generation, simulation, scoring, and feedback

This is essential for trust, debugging, and product quality.

---

# 9. MVP Definition

## MVP User Outcome

A user can practice professional skills in realistic scenarios, receive AI feedback against a rubric, and track improvement over time.

## MVP Includes

* account and profile
* skill / competency framework
* collections
* interview questions
* scenario practice
* AI marking and feedback
* progress tracking
* lightweight mock companies and stakeholders
* manual + AI-assisted content creation
* basic admin dashboard
* observability foundations

## MVP Excludes

* fully open public marketplace
* advanced voice analytics
* multiplayer collaboration
* complex moderation pipelines
* enterprise-grade permissioning

---

# 10. User Stories

## 10.1 Individual Learner Stories

### Onboarding

* As a learner, I want to choose my goals so that the platform can recommend relevant practice.
* As a learner, I want to select my target role or skill area so that my practice feels relevant.
* As a learner, I want to understand the difference between skills and competencies so that progress makes sense.

### Practice

* As a learner, I want to complete a behavioural interview simulation so that I can prepare for real interviews.
* As a learner, I want to practice realistic workplace scenarios so that I can improve how I respond under pressure.
* As a learner, I want to do quick practice in a few minutes so that I can improve consistently even when busy.
* As a learner, I want to practice speech-based responses so that I can improve verbal delivery and confidence.

### Feedback

* As a learner, I want my answer to be scored against clear criteria so that I understand how I performed.
* As a learner, I want feedback linked to specific skills so that I know what to work on.
* As a learner, I want examples of how to improve so that I can apply the feedback immediately.
* As a learner, I want to see evidence from my answer that drove the score so that the assessment feels trustworthy.

### Progress

* As a learner, I want to track my progress over time so that I can see whether I am improving.
* As a learner, I want to see my strongest and weakest skills so that I can practice strategically.
* As a learner, I want my competency level to reflect repeated performance over time so that the system feels meaningful.

### Content Discovery

* As a learner, I want to browse collections by theme and difficulty so that I can find relevant practice.
* As a learner, I want to save useful collections so that I can revisit them later.
* As a learner, I want recommended next questions or scenarios so that I do not need to plan everything myself.

---

## 10.2 Creator Stories

* As a creator, I want to manually build a collection so that I can design practice content intentionally.
* As a creator, I want to generate a collection from a form so that I can create content quickly.
* As a creator, I want to generate content through natural language chat so that I can create content more flexibly.
* As a creator, I want to define linked skills and difficulty so that the content fits the learning model.
* As a creator, I want to include mock companies, stakeholders, and artefacts so that the content feels realistic.
* As a creator, I want to preview generated questions before publishing so that I can maintain quality.
* As a creator, I want to share collections publicly or keep them private so that I control distribution.

---

## 10.3 Admin / Educator Stories

* As an educator, I want to view learner progress by skill so that I can identify where support is needed.
* As an educator, I want to see cohort-level weaknesses so that I can improve teaching focus.
* As an educator, I want to recommend or assign collections so that learners follow structured practice.
* As an educator, I want to monitor usage and completion so that I know whether learners are engaging.
* As an educator, I want confidence in the scoring process so that I can trust the platform.

---

## 10.4 Trust / Platform Stories

* As a system admin, I want AI prompts and model versions logged so that outputs can be traced and debugged.
* As a system admin, I want failures categorised clearly so that issues can be identified and fixed quickly.
* As a system admin, I want structured events across key workflows so that the system is observable.
* As a product owner, I want scoring behaviour to be monitored over time so that drift and inconsistency can be detected.

---

# 11. Functional Requirements

## 11.1 Accounts & Profiles

* Users can create an account and log in
* Users can define role, goals, and preferred practice areas
* Users have a persistent progress profile

## 11.2 Content Browsing

* Users can browse collections
* Users can filter by difficulty, skill, competency, and format
* Users can save collections

## 11.3 Practice Sessions

* Users can start an interview session
* Users can start a scenario session
* Users can answer text-based questions
* Users can answer speech-based prompts
* Sessions store attempt history

## 11.4 Scoring

* Every attempt is scored against a rubric
* Scores are stored at overall, skill, and competency level
* Feedback is returned in a structured format
* Users can view scoring rationale

## 11.5 Progress Tracking

* Skill progression updates over time
* Competency progression is derived from linked skills and weighted performance
* History is viewable through dashboard

## 11.6 Authoring

* Users can manually create collections and items
* Users can generate content from a structured form
* Users can generate content from chatbot prompts
* Draft content can be edited before publishing

## 11.7 Community

* Users can publish public collections
* Users can upvote content
* Users can save content to personal libraries

## 11.8 Admin Dashboard

* Admins can view learner and cohort progress
* Admins can inspect usage trends
* Admins can review content performance

## 11.9 System Observability

* All AI workflows emit structured events
* Every AI output links to prompt version and model metadata
* Errors are classified by taxonomy
* End-to-end traces exist for critical workflows

---

# 12. Non-Functional Requirements

## Performance

* feedback should be returned quickly enough to feel interactive
* quick practice should feel near-immediate
* longer scenario scoring should still remain responsive

## Reliability

* user attempts must never be silently lost
* AI generation failures must surface clearly
* retries and failure states should be visible

## Consistency

* scoring should be calibrated to reduce randomness
* prompt versions must be controlled
* rubric changes must be versioned

## Security & Privacy

* user recordings, transcripts, and performance data must be protected
* public content sharing must avoid exposing private attempt data
* auditability is required for assessment workflows

## Explainability

* users should understand why they received a score
* admins should be able to inspect scoring metadata where appropriate

---

# 13. Success Metrics

## User Metrics

* weekly active learners
* practice sessions per user
* completion rate per collection
* repeat practice rate
* retention after first week / first month

## Learning Metrics

* improvement in skill scores over time
* percentage of users with sustained progression
* number of weak-skill recommendations completed

## Content Metrics

* collections created
* public collections shared
* upvotes / saves per collection
* AI-generated content acceptance rate

## Trust / Quality Metrics

* scoring consistency over benchmarked samples
* prompt failure rate
* generation failure rate
* percentage of attempts with complete trace metadata

---

# 14. Risks

## AI Scoring Trust

Risk: users may not trust feedback if it feels inconsistent or generic.
Mitigation: rubric grounding, evidence extraction, versioning, calibration sets.

## Content Quality

Risk: generated scenarios may feel bland or repetitive.
Mitigation: strong templates, editable drafts, human curation, content feedback loops.

## Scope Creep

Risk: the product becomes too broad before the core loop is strong.
Mitigation: focus MVP on practice, scoring, progress, and structured content.

## Progress Inflation

Risk: skill levels rise too quickly and lose credibility.
Mitigation: slow progression curves, weighting, recency controls, confidence scoring.

## Voice Complexity

Risk: voice mode increases implementation complexity early.
Mitigation: keep voice lightweight or phase it after robust text workflows.

---

# 15. Open Questions

* Should competencies be editable by creators, or platform-defined only?
* How much control should creators have over rubrics?
* Should user-generated collections require review before going public?
* How should progress decay or recency weighting work?
* Should AI feedback ever show a “model confidence” indicator?
* How much transparency should admins get into learner attempts?
* When should voice mode ship relative to text MVP?

---

# 16. Suggested MVP Skill Framework

## Example Competencies

* stakeholder management
* communication
* teamwork
* leadership
* prioritisation
* professionalism
* problem solving
* adaptability
* managing ambiguity
* client delivery

## Example Skills

* active listening
* concise speaking
* structured thinking
* expectation setting
* negotiation
* conflict handling
* prioritisation under pressure
* executive summary writing
* empathy
* decision justification

---

# 17. Core User Flow

## Learner Flow

1. User signs up
2. User selects role / goals
3. User chooses collection or recommended practice
4. User completes question / scenario
5. AI scores response using rubric
6. User reviews feedback and skill breakdown
7. User dashboard updates
8. User is recommended next practice

## Creator Flow

1. Creator chooses manual / form / chatbot creation
2. Creator defines collection theme and audience
3. AI generates draft content or creator writes manually
4. Creator edits and assigns skills
5. Creator publishes privately or publicly

## Admin Flow

1. Admin views dashboard
2. Admin filters learner or cohort
3. Admin reviews progress and weak skills
4. Admin recommends collections or adjusts content strategy

---

# 18. Future Extensions

* role-specific learning paths
* company-specific interview prep
* peer review
* mentor review mode
* live mock meetings
* adaptive difficulty
* certification or milestone badges
* enterprise team spaces
* richer speech coaching
* scenario generation from uploaded company documents or job descriptions

---

# 19. One-Sentence Product Summary

An AI-driven simulation and assessment platform that helps users build consultancy and professional skills in tech and AI through realistic practice, structured feedback, and measurable progression over time.

