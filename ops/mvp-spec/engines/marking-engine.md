# Marking Engine

## Purpose

The marking engine is the reusable system responsible for taking a prompt, a
candidate response, and a rubric, then producing a validated judgment artifact.
It should be portable across domains, including but not limited to soft skills,
education, certification practice, QA review, and structured writing feedback.

The engine exists to separate general assessment mechanics from any
domain-specific taxonomy such as consultancy skills, interview competencies, or
role-specific content.

## Engine Principle

Marking must be explicit, versioned, evidence-based, and testable. The engine
should not depend on a particular subject area. Domain projects supply the
prompt definitions, rubric definitions, and score interpretation layers; the
engine supplies the workflow, contracts, validation, and evaluation discipline.

## Core Abstractions

### Prompt

The task or stimulus presented to the user.

A prompt may be:

- a single question
- a multi-part task
- a scenario step
- a document review task
- an open-ended writing instruction

Each prompt should define:

- `prompt_id`
- `prompt_version`
- `prompt_type`
- `prompt_text` or structured prompt payload
- expected response mode
- optional context artifacts
- linked rubric identifier
- optional domain tags

### Candidate Response

The user-submitted answer to a prompt.

Each response should define:

- `response_id`
- `prompt_id`
- `user_id` or actor identifier
- response content
- response mode
- timestamps
- optional attachments or transcript metadata

### Rubric

A versioned scoring specification used to judge a response.

Each rubric should define:

- `rubric_id`
- `rubric_version`
- scale definition
- dimensions or criteria
- criterion descriptions
- scoring anchors
- evidence expectations
- feedback requirements
- optional weighting rules
- optional pass or fail thresholds

### Marking Decision

The validated output of the engine for one response against one rubric version.

Each decision should define:

- `marking_id`
- `response_id`
- `prompt_id`
- `rubric_id`
- `rubric_version`
- engine version
- prompt version
- model or evaluator metadata
- overall judgment
- criterion-level judgments
- evidence references
- rationale
- strengths
- weaknesses
- next-action guidance
- confidence metadata for internal diagnostics if used
- trace identifier
- timestamps

## Processing Pipeline

The engine should run the following stages in order:

1. Resolve the prompt, response, and rubric versions.
2. Validate that the prompt can be judged by the selected rubric.
3. Normalize the response into a canonical input shape.
4. Generate a provisional judgment.
5. Validate the provisional output against the decision schema.
6. Check evidence coverage and contradiction rules.
7. Finalize and persist the marking decision.
8. Emit evaluation and observability artifacts.

The engine should fail closed. If validation or evidence checks fail, it should
reject the result rather than silently returning weak or partial feedback.

## Separation Of Responsibilities

### Domain Layer

The domain project defines:

- prompt content
- rubric content
- criterion semantics
- score interpretation
- downstream progression or business rules

### Engine Layer

The marking engine defines:

- canonical schemas
- execution workflow
- validation steps
- evidence requirements
- observability contracts
- replay behavior
- evaluation harness

This separation allows the same engine to score soft-skills responses, written
explanations, educational short answers, or review tasks without embedding
domain assumptions in core workflow code.

## Canonical Contracts

### Input Contract

At minimum, the engine requires:

- versioned prompt payload
- versioned rubric payload
- candidate response payload
- evaluator configuration
- trace context

### Output Contract

Every finalized marking decision must contain:

- stable identifiers
- prompt and rubric versions
- evaluator or model metadata
- criterion-level results
- overall result
- evidence references tied to the response
- rationale tied to rubric criteria
- actionable feedback
- validation status
- trace linkage

No project should consume unvalidated raw evaluator output directly.

## Judgment Model

The engine should support multiple result types without changing the workflow:

- numeric scoring
- categorical grading
- pass or fail decisions
- banded proficiency levels
- binary checks per criterion
- hybrid outcomes combining score and qualitative judgment

The rubric, not the engine, defines which result type applies.

## Evidence Rules

Evidence is required for trust-sensitive marking.

The engine should enforce:

- every criterion judgment must cite supporting evidence or explicitly mark why
  evidence is unavailable
- evidence must reference concrete spans, claims, or structured observations
  from the response
- rationale must not contradict cited evidence
- generic praise or generic criticism without response-linked support is invalid

Projects may choose how evidence is rendered to users, but the stored artifact
should retain enough information for audit and replay.

## Validation Rules

A marking decision should be rejected when:

- prompt version is missing
- rubric version is missing
- response content is empty when content is required
- criterion outputs are incomplete
- scores fall outside the rubric scale
- rationale contradicts the criterion result
- feedback is generic and unsupported
- evaluator metadata is missing
- trace linkage is missing

Validation should happen before user delivery and before downstream analytics or
progress updates.

## Configurable Extension Points

To stay reusable, the engine should expose configuration points for:

- rubric format adapters
- response normalization
- evaluator provider or model choice
- post-processing rules
- score aggregation logic
- decision rendering format
- thresholding and pass or fail logic
- domain-specific policy checks

These extension points should be explicit interfaces, not ad hoc conditionals.

## Eval Framework

### Eval Principle

A marking engine is not trustworthy because it produces structured output. It
is trustworthy only if its behavior is measured against stable reference cases
and monitored for drift.

The eval framework should be part of the engine, not a later add-on.

### Eval Dataset Model

The eval harness should support versioned benchmark cases containing:

- prompt payload
- response payload
- rubric payload
- expected outcome or expected range
- expected criterion judgments
- expected evidence properties
- tags such as domain, difficulty, prompt type, and edge case class

Benchmark cases should be small enough to review manually and broad enough to
cover realistic failure modes.

### Eval Levels

### Contract Evals

Verify that engine outputs always satisfy the required schema and metadata
rules.

### Rubric Fidelity Evals

Verify that criterion judgments follow rubric anchors and thresholds.

### Evidence Quality Evals

Verify that evidence is specific, grounded, and aligned with the assigned
judgment.

### Consistency Evals

Verify that repeated runs on stable benchmark cases stay within acceptable
variance.

### Regression Evals

Verify that prompt, rubric, model, or engine changes do not degrade known-good
behavior.

### Adversarial Evals

Verify robustness against empty, irrelevant, contradictory, overly verbose, or
prompt-injection-style responses.

### Eval Metrics

The exact metrics may vary by domain, but the framework should track at minimum:

- schema pass rate
- judgment validity rate
- criterion agreement against reference labels
- score deviation from reference outcomes
- evidence coverage rate
- contradiction rate
- retry and failure rate
- latency by workflow type
- drift across engine versions or model versions

Projects can add domain-specific learning or business metrics on top, but these
engine metrics should remain common.

### Goldens And References

The framework should support multiple benchmark types:

- goldens with expected exact outputs where determinism is realistic
- bounded references where a score range or allowed label set is acceptable
- pairwise comparisons where response A should score higher than response B
- invariant checks where a metadata or safety rule must always hold

This avoids overfitting the engine to a single exact wording while still making
quality measurable.

### Release Gates

No marking-engine change should ship unless it demonstrates:

- passing contract evals
- acceptable rubric fidelity on benchmark cases
- acceptable evidence quality
- no unexplained regression on tracked benchmarks
- complete observability metadata

Projects can tighten thresholds, but should not remove these gates.

## Observability Requirements

Every marking run should emit:

- `trace_id`
- `workflow_id`
- `prompt_id`
- `prompt_version`
- `response_id`
- `rubric_id`
- `rubric_version`
- engine version
- evaluator version or model slug
- validation outcome
- final decision status
- latency
- failure code if applicable

Every eval run should also persist:

- eval suite identifier
- benchmark set version
- engine version
- evaluator version or model slug
- aggregate metrics
- per-case outcomes

## Storage Guidance

Persist separately but link explicitly:

- prompt definitions
- rubric definitions
- raw responses
- finalized marking decisions
- observability artifacts
- eval benchmark cases
- eval results

Historical meaning must remain reconstructable after rubric or engine changes.

## Reuse Guidance

A project adopting this engine should only need to provide:

1. its prompt schema or prompt adapter
2. its rubric schema or rubric adapter
3. its score interpretation rules
4. any domain-specific reporting built on top of decisions

The underlying marking workflow, validation rules, observability model, and
eval harness should remain shared.

## Naming Guidance

`marking-engine` is a good neutral name if the project centers on assessment.
If a more general platform-neutral term is preferred, `judgment-engine` is the
best alternative. `rubric-engine` is narrower and works only if rubric-based
evaluation is always required.
