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

### Event Naming Convention

- Use dotted domain-action versions, for example `assessment.started.v1`, `assessment.validated.v1`, `progress.updated.v1`.
- Major semantic changes require a new event version suffix.
- Event payloads must keep correlation fields stable across versions even when additional fields are added.

### Wide Event Baseline

Emit wide events for these critical backend workflows:

- assessment runs
- progression updates
- recommendation generation
- content generation

### Quick Practice V1 Event Set

The first quick-practice runtime should emit these concrete events:

- `practice.session_started.v1`
- `practice.prompt_delivered.v1`
- `practice.attempt_submitted.v1`
- `assessment.started.v1`
- `assessment.validated.v1`
- `assessment.rejected.v1`
- `workflow.failed.v1`

These events must preserve stable correlation fields so an attempt can be
replayed from prompt delivery through assessment persistence or failure.

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

### Error Code Convention

Use `SS-<CATEGORY>-<NUMBER>` with stable categories, for example:

- `SS-VALIDATION-001`
- `SS-DOMAIN-001`
- `SS-SCORING-001`
- `SS-ORCHESTRATION-001`
- `SS-PROVIDER-001`
- `SS-PERSISTENCE-001`
- `SS-AUTH-001`
- `SS-UI-001`

Numbers must be stable once assigned. Rewording a message does not justify
changing the code.

## Versioning Rules

The following artifacts require explicit persisted versions wherever they
affect system meaning:

- prompt contracts
- rubric definitions
- engine and scoring configs
- API contract versions when introduced
- event versions
- typed-output schema versions
- error code taxonomy revisions when categories expand

Use semantic major versions for contract-breaking changes. Do not silently
reinterpret historical artifacts under a new rubric, prompt, or config version.

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
- passing real-provider smoke coverage for provider-backed workflows

## MVP Operational Boundaries

- Informal logs are not sufficient for trust-sensitive workflows.
- Silent fallback behavior is prohibited for scoring and progression paths.
- Blank loading states and silent hangs are operational failures, not cosmetic issues.
