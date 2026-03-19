# Assessment And Progression

## Assessment Principle

Assessment must be explainable, evidence-based, and stable enough that users
can trust improvement signals over time.

## Assessment Inputs

Each assessment workflow requires:

- learner attempt content
- content item metadata
- linked skills and competencies
- rubric version
- prompt contract version
- model and provider metadata

No assessment should run against unversioned rubric or prompt definitions.

## Assessment Output Contract

Each finalized assessment must contain:

- assessment identifier
- attempt identifier
- rubric version
- prompt version
- model slug
- provider
- overall score
- skill-level scores
- evidence extracted from the learner response
- rationale tied to rubric dimensions
- strengths
- weaknesses
- suggested next actions
- trace identifier
- timestamps

The stored artifact must be schema-validated before it can be shown to users or
used to update progress.

## Scoring Rules

- Every score must map back to rubric criteria.
- Skill-level scoring is mandatory when the content item targets multiple skills.
- Evidence should cite concrete parts of the learner response, not generic impressions.
- Feedback must separate observed strengths, observed weaknesses, and actionable improvement steps.
- Contradictory feedback is a validation failure, not an acceptable edge case.

## Feedback Standard

Learner-facing feedback should answer three questions:

1. What went well?
2. What was missing or weak?
3. What should the learner do next?

The answer must stay grounded in the actual attempt and the selected rubric.

## Progression Principle

Progress reflects repeated demonstrated performance over time. It does not
measure activity volume, streak length, or isolated spikes.

## Progress Model

### Skill Progress

Skill progress should aggregate validated evidence across multiple attempts.
Recent performance can carry more weight, but historical results must remain
visible in the learner record.

### Competency Progress

Competency progress is derived from linked skill evidence using defined
weighting. Competency changes must feel earned and should not move sharply after
one outlier attempt.

### Confidence

Confidence represents how much evidence supports the current view of the
learner's level. It should be tracked separately from proficiency.

## Progress Update Rules

- Only validated assessments may update progression.
- Failed, rejected, or partial assessments must not change learner progress.
- Progress updates must be reproducible from stored assessment history.
- Rubric or scoring changes must not silently rewrite historical meaning.
- Recalculation workflows must be versioned and auditable.

## Recommendation Rules

Next-practice recommendations should prioritize:

- weak skills with sufficient evidence
- skills that are stagnating
- under-practiced but important competencies
- content that matches learner goals and role context

Recommendations must not optimize for novelty alone.

## Calibration Requirements

- Maintain benchmark samples for scoring consistency checks.
- Compare scoring behavior across prompt versions and model versions.
- Detect drift in rubric interpretation and feedback quality.
- Preserve enough data to replay assessments during quality review.

## Failure Rules

- If structured output validation fails, stop the workflow.
- If evidence does not support the score, reject the artifact.
- If model metadata or prompt version is missing, reject the artifact.
- If rubric and content mapping is invalid, fail before model execution where possible.

## MVP Boundaries

- Human override workflows are optional, not required for MVP.
- Learner-facing confidence indicators are excluded from MVP.
- Progress decay that hides historical evidence is excluded from MVP.
