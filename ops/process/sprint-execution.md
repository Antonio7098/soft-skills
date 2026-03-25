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

Operational discipline is part of implementation, not cleanup.

- Keep top-level responsibilities clear:
  - `entrypoints/http`: FastAPI routes, schemas, dependencies, error handling
  - `platform`: runtime/framework concerns such as container, DB,
    observability, providers, and Stageflow integration
  - `modules`: business features
  - `shared`: cross-cutting types, errors, and ports
- Inside each non-trivial feature, organise by layer:
  - `contracts`: commands, views, boundary DTOs
  - `domain`: pure business rules and policies
  - `use_cases`: service facades
  - `workflows`: Stageflow pipelines, stages, retry/idempotency policy
  - `infra`: repositories, persistence, mappers, event recording
- Keep boundaries strict:
  - route handlers stay thin
  - Stageflow code lives in `workflows`
  - SQLAlchemy and persistence concerns live in `platform/db` or feature `infra`
  - provider code stays behind `platform/providers`
  - cross-feature helpers go in `shared` only if they are genuinely reused
- Do not create dumping grounds such as `utils.py`, `helpers.py`, or `misc.py`
- Keep files focused:
  - target under 400 lines
  - hard limit 600 lines
  - split immediately when a file mixes contracts, orchestration, persistence,
    and validation
- A slice is not done unless another engineer can quickly tell:
  - where the contract lives
  - where the business rule lives
  - where the pipeline lives
  - where persistence lives

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
