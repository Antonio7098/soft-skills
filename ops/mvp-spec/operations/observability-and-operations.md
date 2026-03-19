# Observability And Operations

## Operating Principle

Observability artifacts are the source of truth for system behavior. Critical
AI and assessment workflows must be reconstructable from stored traces, events,
and versioned artifacts.

## Trace Requirements

Every major workflow must emit an end-to-end trace, including:

- practice session start
- attempt submission
- assessment execution
- feedback generation
- progress update
- content generation
- recommendation generation where applicable

Each trace should preserve step-level execution metadata.

## Required Correlation Fields

Where applicable, logs and events should include:

- `request_id`
- `user_id`
- `session_id`
- `attempt_id`
- `assessment_id`
- `workflow_id`
- `trace_id`
- `prompt_version`
- `rubric_version`
- `model_slug`
- `provider`
- `error_code`

## Event Model

The MVP should emit structured events for:

- session started
- prompt delivered
- attempt submitted
- assessment started
- assessment validated
- assessment rejected
- progress updated
- content draft generated
- content published
- recommendation generated
- workflow failed

Events must be machine-readable and queryable.

## Logging Rules

- Use structured logging only.
- Log state transitions, validations, external provider calls, retries, and persistence outcomes.
- Do not rely on print debugging or free-form logs as an operational contract.
- Preserve causal chains across retries and failures.

## Error Taxonomy

The MVP must classify errors into stable categories, at minimum:

- validation
- domain
- scoring
- orchestration
- provider
- persistence
- auth
- UI

Each failure should expose a stable error code and enough context for diagnosis.

## LLM Artifact Rules

Every stored LLM-derived artifact must preserve:

- validated structured payload
- prompt version
- model slug
- provider
- timestamps
- trace linkage

Missing metadata is a hard failure for production workflows.

## Monitoring And Quality Metrics

Track at minimum:

- prompt failure rate
- structured validation failure rate
- end-to-end assessment success rate
- retry rate by workflow type
- percentage of attempts with complete trace metadata
- scoring consistency against benchmark samples
- content generation acceptance rate

## Replay And Audit

The system should support replay or audit of assessment-relevant workflows by
using stored artifacts rather than maintainer memory or ad hoc logs.

## Release Requirements

Before release, critical workflows must demonstrate:

- versioned prompt metadata
- replayable trace artifacts
- validated LLM contracts
- passing tests
- migration discipline for schema changes
- documentation updates for behavioral changes

## MVP Operational Boundaries

- Informal logs are not sufficient for trust-sensitive workflows.
- Silent fallback behavior is prohibited for scoring and progression paths.
- Blank loading states and silent hangs are operational failures, not cosmetic issues.
