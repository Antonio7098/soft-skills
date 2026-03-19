# SoftSkills Post-MVP Spec Canon

This directory captures forward-looking concepts that extend the MVP canon once the
text-first practice loop is stable. Each document frames a discrete initiative,
its rationale, constraints inherited from the MVP, and open decisions that must
be resolved before delivery.

## Source Relationship

1. `CONSTITUTION.yml`
2. `docs/`
3. `ops/mvp-spec/`
4. `ops/post-mvp-spec/` *(this folder)*

Post-MVP specs cannot contradict higher-precedence sources. Instead, they build
on proven patterns (rubric explainability, progression semantics, observability)
and describe how to safely layer richer modalities and intelligence.

## Documents

| Document | Focus |
| --- | --- |
| `live-chat-interview-practice.md` | Real-time interviewer loop, UX, infra, and safety rails |
| `media-archive.md` | Unified storage of audio/video attempts, transcripts, and metadata |
| `knowledge-graph-substrate.md` | Platform-wide graph model that turns attempts, skills, and assets into a navigable substrate for agents |

Add new specs here only after the upstream canon is updated or explicitly
extended. Each document should enumerate dependencies, data contracts, and
observability rules to keep the broader system coherent.
