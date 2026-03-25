# SoftSkills Sprint Execution Guide

This guide defines how to execute a sprint in SoftSkills. It is the default
working procedure for backend and platform work. Frontend work is intentionally
decoupled and is not covered here.

## 1. Start The Sprint Branch

Begin every sprint by working on a dedicated branch.

- Check the current branch: `git branch`
- Switch to `main` and update it
- Create the sprint branch using a stable naming pattern such as:
  - `sprint/00-canon-lock`
  - `sprint/03-quick-practice-vertical-slice`
  - `sprint/05-progression-and-recommendation-v1`
- Confirm the branch matches the sprint being executed before making changes

## 2. Load The Sprint Context

Before planning or coding, open and read:

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml)
- The active sprint doc in [ops/sprints](/home/antonioborgerees/df/soft-skills/ops/sprints)
- The relevant canonical spec files in [ops/mvp-spec/](/home/antonioborgerees/df/soft-skills/ops/mvp-spec)
- [ops/mvp-spec/README.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/README.md)
- Stageflow patterns and reference: [/home/antonioborgerees/coding/stageflow/docs](/home/antonioborgerees/coding/stageflow/docs)
- 
At minimum, determine:

- What user or system outcome the sprint is supposed to deliver
- Which workflows are in scope
- Which domain invariants apply
- Which provider-backed flows need real smoke coverage
- Which docs must be updated if behavior changes

## 3. Re-State The Sprint In Constitution Terms

Do not jump from sprint title to implementation. First translate the sprint into
constitution constraints.

For the sprint at hand, reason explicitly about:

- Competency growth: how this work strengthens the `practice -> assess -> reflect -> progress -> repeat` loop
- Schema validation: which new request, response, persistence, or LLM boundaries must be typed and validated
- Fail-fast behavior: where invalid state or bad output must stop the workflow
- Explainability: how assessment, progression, or recommendation outputs remain understandable
- Observability: which traces, events, logs, and IDs must exist for the changed flow
- Persistence: which artifacts must be stored durably for replay, audit, and progress semantics
- Modularity: which interfaces, adapters, and dependency-injection boundaries are needed

If a proposed implementation conflicts with the constitution, change the design
before writing code.

## 4. Identify The Relevant MVP Canon

Map the sprint to the exact spec files that govern it.

Typical mapping:

- foundation work: `foundational/technical-architecture.md`, `operations/observability-and-operations.md`
- domain and catalog work: `foundational/domain-model.md`, `operations/content-system.md`
- practice and marking work: `foundational/product-spec.md`, `platform/assessment-and-progression.md`, `engines/marking-engine.md`
- progression and recommendation work: `platform/soft-skill-progression.md`, `platform/soft-skill-recommendation.md`, `engines/progression-engine.md`, `engines/recommendation-engine.md`

Do not rely on memory if the file exists in the canon.

## 5. Turn The Sprint Into Concrete Deliverables

Break the sprint into implementation slices before coding.

For each slice, define:

- the contract changes
- the domain or orchestration logic
- the persistence changes
- the observability changes
- the tests required
- the docs that must be updated

Prefer narrow vertical slices over broad unfinished scaffolding.

## 6. Check Dependencies Before You Build

Before implementation starts, verify:

- migrations needed
- prompt or rubric versions needed
- config versions needed
- repository or adapter interfaces that must be introduced first
- whether an existing smoke harness needs to be extended
- whether the sprint depends on unfinished work from an earlier sprint

If dependencies are missing, resolve them first rather than coding around them.

## 7. Implement On Explicit Boundaries

While coding, keep the repository coherent.

- Keep route handlers thin
- Put business rules in domain or application services
- Keep Stageflow orchestration explicit and limited to workflow coordination
- Keep vendor logic behind adapters
- Keep schemas explicit at every external boundary
- Avoid generic utility dumping grounds
- Keep files focused and responsibilities clear

Every implementation should answer:

- what is the contract
- where is it validated
- what gets persisted
- what gets logged and traced
- how does it fail

## 8. Enforce Organisational Hygiene While Coding

Operational discipline is part of implementation, not cleanup. Do not accept
"working code" if it degrades structure, readability, or change safety.

### File Size And Scope Limits

- Target files under 400 lines
- Hard limit: no file may exceed 600 lines
- If a file crosses 400 lines during a sprint, stop and assess whether it must
  be split before continuing
- If a change would push a file past 600 lines, split it in the same sprint
- A file must have one clear reason to change. If it mixes orchestration,
  persistence, validation, mapping, and event emission, it is already too broad

### Module Structure Rules

- Organise by feature first, then by responsibility
- Prefer directories such as `practice/quick_practice/`,
  `catalog/collections/`, and `catalog/scenarios/` over large feature-agnostic
  modules
- Do not keep adding unrelated behavior to a top-level `service.py` once a
  feature has multiple workflows or subdomains
- Keep shared code in `_shared/` only if it is genuinely cross-cutting and used
  by more than one feature
- Do not create generic dumping grounds such as `utils.py`, `helpers.py`, or
  `misc.py`

### Responsibility Split Inside A Feature

For any non-trivial feature, split code across explicit files instead of
accumulating everything in one service or repository.

- `commands.py`: request and command models for write operations
- `views.py` or `queries.py`: read models and query-facing shapes
- `models.py`: application-layer DTOs only, not mixed with orchestration or SQL
- `service.py`: workflow orchestration and use-case coordination only
- `repository.py`: persistence operations only
- `events.py`: event recording and event payload helpers only
- `validators.py` or `policies.py`: business validation, state guards, and
  lifecycle rules
- `mappers.py`: translation between persistence records and application views

Do not let a single file both define models and implement business workflows.
Do not let a repository also own event taxonomy, permission policy, and view
assembly unless the module is still trivially small.

### Model Discipline

- Put request models, response models, DTOs, and view models in dedicated model
  files
- Keep Pydantic or schema definitions separate from workflow execution code
- Keep SQLAlchemy records in the persistence layer, not the application layer
- Do not define large inline data shapes inside service methods when they belong
  in named models
- When a workflow has more than a couple of intermediate payloads, extract them
  into explicit model classes instead of ad hoc dictionaries

### Service And Repository Rules

- Services coordinate workflows; they should not contain large blocks of SQL or
  record-construction code
- Repositories load and persist state; they should not own workflow branching,
  provider-calling logic, or complex response shaping
- Validation that does not require I/O should live outside repositories
- Event recording should be delegated to a focused event helper when the event
  surface becomes non-trivial
- Mapping persistence records to API or workflow views should be extracted once
  the mapping is longer than a small helper

### Refactor Triggers

Refactor immediately during the sprint if any of these appear:

- one file exceeds 400 lines and is still growing
- one class has more than roughly 7 public methods
- one method exceeds 80 lines
- a service starts constructing multiple persistence records directly
- a repository starts returning many different view shapes
- a module needs section comments to explain unrelated chunks of behavior
- code review feedback includes phrases such as "mixed concerns",
  "hard to navigate", "where should this live?", or "I am afraid to edit this"

### PR And Review Hygiene

- No sprint PR should introduce a new oversized file without an explicit written
  justification
- If a touched file is already oversized, reduce or isolate the damage instead
  of expanding it casually
- Review for structure, not only correctness
- "It passes tests" is not sufficient if the change increases coupling or hides
  responsibilities
- If a reviewer cannot identify where contracts, validation, persistence, and
  orchestration live within a few minutes, the structure is not acceptable

### Done Criteria For Code Organisation

Before calling a slice done, confirm:

- files respect the size limits
- each new module has a single clear purpose
- models are in dedicated files
- feature directories are coherent and discoverable
- orchestration, validation, persistence, and event emission are separated
- another engineer could predict where the next related change should go

## 9. Add Observability As Part Of The Work

Observability is not a cleanup step.

For every changed workflow, add or update:

- structured events
- structured logs with correlation fields
- trace propagation and workflow IDs
- stable error codes
- stored metadata such as prompt version, rubric version, model slug, provider, config version, and trace ID where applicable

If the workflow cannot be replayed or diagnosed, it is incomplete.

## 10. Add Tests While The Design Is Fresh

Every sprint must include backend verification at three levels.

### Unit Tests

Add deterministic tests for:

- domain logic
- schema validation
- lifecycle transitions
- scoring or aggregation rules
- failure rules and invariants

### Integration Tests

Add integration coverage for:

- API contracts
- persistence behavior
- orchestration paths
- trace and event emission
- permission and access rules where applicable

### Smoke Tests With Real Provider

Run backend smoke flows against the real provider for the sprint scope.

- If the sprint adds or changes provider-backed behavior, extend the smoke suite
- If the sprint does not add a new provider-backed flow, the baseline smoke suite must still pass
- Prefer backend-driven smoke coverage that exercises real end-to-end workflows rather than isolated provider pings

## 11. Test Failure Paths, Not Only Happy Paths

Every sprint should explicitly test:

- schema rejection
- invalid state transitions
- provider failure
- persistence failure where practical
- missing version metadata
- contradiction or unsupported output cases

Soft failure that hides corruption or ambiguity is not acceptable in this codebase.

## 12. Update The Canonical Docs During The Sprint

Documentation updates are part of done, not post-work.

Update as needed:

- the active sprint doc in `ops/sprints/`
- [ROADMAP.md](/home/antonioborgerees/df/soft-skills/ROADMAP.md) if sequencing or exit criteria changed
- [ops/ROADMAP.md](/home/antonioborgerees/df/soft-skills/ops/ROADMAP.md) if the detailed execution plan changed
- the relevant files in [ops/mvp-spec/](/home/antonioborgerees/df/soft-skills/ops/mvp-spec) if implementation changed expected behavior
- any prompt, event, config, or contract documentation introduced by the sprint

If the code changes behavior and the docs do not, the sprint is incomplete.

## 13. Keep The Sprint Doc Current

Throughout execution, update the sprint doc with:

- completed scope items
- changes in interpretation
- risks that appeared during implementation
- decisions that affect later sprints
- what was actually tested
- what was explicitly deferred

The sprint doc should be usable as historical context for future work.

## 14. Run The Final Verification Pass

Before considering the sprint complete, run the full sprint verification set:

- formatting checks
- linting
- type checks
- unit tests
- integration tests
- backend smoke tests with the real provider
- migration checks if schema changed

Also verify:

- docs match implementation
- trace and event coverage is present
- persisted artifacts contain required version metadata
- no silent fallback was introduced

## 15. Create The Sprint Execution Report

Before handing off or opening a PR, create or update the sprint execution
report in `ops/reports/` using
[ops/process/sprint-ecexuton-report-template.md](/home/antonioborgerees/df/soft-skills/ops/process/sprint-ecexuton-report-template.md).

The report should capture:

- what was planned vs what was actually delivered
- the real sprint outcome, not just the intended one
- constitution conformance and where the sprint was strained
- testing completed, including smoke coverage status
- technical debt, architectural debt, and documentation debt introduced
- open risks, deferred work, and recommendations for the next sprint
- Stageflow observations if the sprint used Stageflow

The report is part of the deliverable, not optional project hygiene.

## 16. Close Out The Sprint Cleanly

Before handing off or opening a PR:

- review the sprint doc and mark completed items
- record any residual risks or known gaps
- note the minimum viable completion achieved
- list next sprint priorities based on what was learned
- review the diff for accidental scope expansion

The sprint is only complete when the implementation, tests, observability, and
documentation all agree.

## 16. Execution Checklist

Use this as the short-form procedure:

- [ ] Create and confirm the sprint branch
- [ ] Read `CONSTITUTION.yml`
- [ ] Read the active sprint doc
- [ ] Read the relevant `ops/mvp-spec/`
- [ ] Restate the sprint in constitution terms
- [ ] Break work into concrete backend slices
- [ ] Confirm dependencies, versions, migrations, and smoke needs
- [ ] Implement on explicit modular boundaries
- [ ] Add observability with the feature
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Run or extend real-provider backend smokes and run realistic user flows
- [ ] Test failure paths
- [ ] Update canonical docs in `ops/mvp-spec/` and root `README.md`
- [ ] If Stageflow was used, update [ops/process/stageflow-reporting.md](/home/antonioborgerees/df/soft-skills/ops/process/stageflow-reporting.md) with any bugs, DX improvements, or notable observations
- [ ] Update the sprint doc
- [ ] Create or update the sprint report in `ops/reports/` using [ops/process/sprint-ecexuton-report-template.md](/home/antonioborgerees/df/soft-skills/ops/process/sprint-ecexuton-report-template.md)
- [ ] Run format, lint, typecheck, tests, and smokes
- [ ] Verify traces, versions, and persistence artifacts
- [ ] Review residual risks and close the sprint cleanly
