# Sprint Execution Report Template: [Sprint Name]

> Project: SoftSkills
> Report Type: Sprint execution retrospective and delivery report
> Output Location: `ops/reports/[sprint-slug]-report.md`
> Scope: Backend and platform execution only. Frontend work is tracked separately.

## Report Overview

- Sprint Name: [Insert sprint name]
- Sprint Window: [Start date] -> [End date]
- Sprint Status: [Completed / Partially Completed / Blocked]
- Report Author: [Name]
- Related Sprint Doc: [Link to `ops/sprints/...`]
- Related Branch / PR: [Branch name and PR link if applicable]

## Source Docs Used

- [ops/CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml)
- [Active sprint doc in `ops/sprints/`](/home/antonioborgerees/df/soft-skills/ops/sprints)
- [Relevant canonical spec files in `ops/mvp-spec/`](/home/antonioborgerees/df/soft-skills/ops/mvp-spec)
- [ops/process/sprint-execution.md](/home/antonioborgerees/df/soft-skills/ops/process/sprint-execution.md)
- [ops/process/stageflow-reporting.md](/home/antonioborgerees/df/soft-skills/ops/process/stageflow-reporting.md) if Stageflow was used

## Sprint Summary

- Sprint Goal: [What this sprint was meant to deliver]
- Actual Outcome: [What was actually delivered]
- Overall Result: [Short assessment of how the sprint went]

## Planned Vs Delivered

| Area | Planned | Delivered | Status | Notes |
| --- | --- | --- | --- | --- |
| [Area 1] | [Planned outcome] | [Delivered outcome] | [Done/Partial/Not Done] | [Notes] |
| [Area 2] | [Planned outcome] | [Delivered outcome] | [Done/Partial/Not Done] | [Notes] |

## Key Outcomes

- [Outcome 1]
- [Outcome 2]
- [Outcome 3]

## What Worked Well

- [Execution practice, design choice, or process that helped]
- [Testing or architecture decision that paid off]
- [Anything worth repeating next sprint]

## Challenges And Friction

- [Problem encountered]
- [Root cause]
- [Impact on scope, quality, or speed]
- [What should change next time]

## Constitution Conformance

For each item, state how the sprint conformed, where it was strained, and any
follow-up needed.

- Competency growth: [How the sprint strengthened the core loop or why it did not]
- Schema validation: [What boundaries were typed and validated]
- Fail-fast behavior: [How invalid state or bad outputs were handled]
- Explainability: [How outputs remain understandable and reviewable]
- Observability: [What traces, logs, events, and IDs were added or improved]
- Persistence: [What critical artifacts were stored durably]
- Modularity: [How interfaces, adapters, and DI boundaries were preserved]
- No silent fallback: [How hidden degradation was avoided]

## Testing And Verification

- Unit Tests: [What was added or changed]
- Integration Tests: [What was added or changed]
- Smoke Tests With Real Provider: [What ran, what did not, and why]
- Failure Path Coverage: [What failure cases were exercised]
- Manual Verification: [Any additional checks done]

## Documentation Updates

- [Docs updated in `ops/mvp-spec/`]
- [Sprint doc updates]
- [Roadmap or process doc updates]
- [Any docs intentionally deferred]

## Stageflow Usage And Reporting

- Stageflow Used: [Yes / No]
- Relevant Features Used: [Pipelines, interceptors, typed outputs, tracing, wide events, agent stages, tools, checkpoints, etc.]
- What Worked: [Useful framework capabilities]
- What Hurt: [DX issues, gaps, awkward patterns, bugs]
- Follow-Up Logged In `ops/process/stageflow-reporting.md`: [Yes / No, with short note]

## Technical And Architectural Debt

| Debt Item | Type | Why It Exists | Impact | Recommended Follow-Up | Owner |
| --- | --- | --- | --- | --- | --- |
| [Debt item] | [Technical/Architectural/Test/Docs] | [Reason] | [Impact] | [Action] | [Owner] |

## Open Risks

| Risk | Severity | Why It Matters | Mitigation | Carry To Next Sprint |
| --- | --- | --- | --- | --- |
| [Risk] | [High/Med/Low] | [Reason] | [Mitigation] | [Yes/No] |

## Deferred Work

- [Deferred item]
- [Why it was deferred]
- [What must happen before it is picked up]

## Retrospective

- Stop: [What should stop next sprint]
- Start: [What should start next sprint]
- Continue: [What should continue next sprint]

## Next Sprint Recommendations

1. [Highest-priority next step]
2. [Second-priority next step]
3. [Third-priority next step]

## Sign-Off

- Report Status: [Draft / Final]
- Reviewed By: [Name]
- Review Date: [Date]

Checklist:

- [ ] Outcomes are recorded honestly
- [ ] Constitution conformance is assessed explicitly
- [ ] Testing and smoke status is documented
- [ ] Debt and risks are captured
- [ ] Follow-ups for next sprint are clear
- [ ] Report is saved in `ops/reports/`
