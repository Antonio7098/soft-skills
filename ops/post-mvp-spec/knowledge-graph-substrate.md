# Knowledge Graph Substrate

## Purpose

Turn the platform's attempts, assessments, skills, collections, and media into a
typed knowledge graph so agentic copilots (recommendation, coaching, support)
can reason about learner progress, context, and intent. Each learner action
becomes a node or edge that captures evidence and relationships across time.

## Objectives

- Create a durable semantic layer that unifies practice data, content metadata,
  and progression history.
- Enable the chatbot coach to personalize responses using graph traversals (e.g.,
  "recent negotiation attempts with weak evidence").
- Support analytics (skill mastery paths, cohort comparisons) without duplicating
  storage logic across services.
- Ensure every graph fact is versioned, explainable, and trace-linked to source
  systems.

## Scope

Phase 1 focuses on learner progression data, connecting:

- Learner profile → goals → target roles
- Attempts → assessments → skills/competencies
- Recommendations → follow-up attempts
- Media artifacts → transcripts → evidence statements

Future phases can extend to content authoring lineage, coach annotations, and
support tickets.

## Graph Model

### Node Types

- `Learner`
- `Goal` (role, competency target)
- `Attempt`
- `Assessment`
- `Skill`
- `Competency`
- `Recommendation`
- `ContentItem` (prompt, scenario, collection)
- `MediaArtifact`
- `Trace`

### Edge Examples

- `Learner` **attempted** `Attempt`
- `Attempt` **was_assessed_by** `Assessment`
- `Assessment` **scored** `Skill`
- `Assessment` **evidenced_by** `MediaArtifact` / transcript snippet
- `Recommendation` **suggested** `ContentItem`
- `Learner` **followed** `Recommendation`
- `Learner` **pursues** `Goal`
- `Skill` **rolls_up_to** `Competency`

Edges carry attributes (score, timestamp, confidence, version IDs) to keep the
graph explainable.

## Data Contracts

- Graph ingestion subscribes to the same event bus that powers observability.
- Each event (attempt submitted, assessment validated, recommendation issued)
  produces a graph mutation with deterministic IDs derived from source records.
- Graph nodes reference canonical IDs from the transactional database to avoid
  drift.

## Storage & Access

- Backed by a managed graph database (e.g., Neo4j Aura, AWS Neptune) or a graph
  layer (Datomic, TerminusDB) depending on ops preferences.
- Provide two access surfaces:
  1. **Graph API**: internal service exposing read queries (GraphQL, Gremlin,
     Cypher) with strict role-based access.
  2. **Embedding Cache**: derived vector representations for realtime agent use,
     refreshed when node attributes change.

## Agent Integration

- Chat coach queries the graph at session start to retrieve learner context.
- Recommendation engine can traverse "weak skill" subgraphs to choose next
  practice.
- Progress dashboards render graph-derived aggregates (e.g., attempt streaks
  by skill, evidence saturation).

## Observability & Governance

- Version every schema change; graph migrations must be idempotent.
- Emit metrics for ingestion lag, mutation failures, orphaned nodes.
- Provide lineage tools: given a graph fact, fetch the source trace/attempt IDs.
- Enforce retention parity with transactional DB: deleting learner data requires
  cascading graph deletions plus audit logging.

## Dependencies

1. Stable event schema from marking, recommendation, and media subsystems.
2. Consistent ID strategy (UUIDv7 or ULID) across services.
3. Access control layer that mirrors platform roles (learner, coach, admin).
4. Documentation for graph query patterns to keep agent prompts deterministic.

## Open Questions

- Do we need multi-tenant graph partitions or a single shared graph with tenant
  tags?
- How do we expose graph insights to enterprise customers without leaking other
  cohorts?
- What SLA is required for graph updates before agents read stale data?
- Should we precompute learner "state summaries" (e.g., vector per skill) or let
  agents compute on demand?
