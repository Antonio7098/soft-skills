# Sprint 12: Collections Enhancement — Rating, Discovery, and Org-Scoped Features

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Sprint 12: Collections Enhancement
- Sprint Focus: Implement collection rating system, global discovery hub, org-scoped collection endpoints, and admin featured collections
- Depends On: Sprint 11

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 1-427
- [ops/mvp-spec/README.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/README.md): lines 1-60
- [ops/mvp-spec/organisations.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/organisations.md): lines 1-159
- [ops/mvp-spec/collections.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/collections.md): lines 1-126

## Sprint Goals

- Primary Goal: Implement collection rating system, global discovery hub, and org-scoped collection listing with admin featured collections
- Secondary Goals:
  - Add CollectionRatingRecord model with user_id + collection_id composite key
  - Add avg_rating, rating_count, featured fields to CollectionRecord with alembic migration
  - Implement POST/DELETE /collections/{id}/rate endpoints
  - Implement GET /collections/discover for global hub (verified_public, organisation_id=NULL)
  - Implement GET /organisations/{org_id}/collections endpoint
  - Add admin feature/highlight collection capability
  - Update CollectionView with avg_rating, rating_count, rated_by_actor fields

## Scope Checklist

- [x] Task 1: Add CollectionRatingRecord model with composite primary key (user_id, collection_id), rating (1-5), created_at, updated_at
- [x] Task 2: Add avg_rating (float | None), rating_count (int, default 0), featured (bool, default False) to CollectionRecord with alembic migration
- [x] Task 3: Implement POST /collections/{id}/rate and DELETE /collections/{id}/rate endpoints
- [x] Task 4: Update CollectionView to include avg_rating, rating_count, rated_by_actor fields
- [x] Task 5: Implement GET /collections/discover endpoint (global hub: verified_public AND organisation_id=NULL)
- [x] Task 6: Implement GET /organisations/{org_id}/collections endpoint
- [x] Task 7: Add admin feature/highlight capability (PATCH /admin/collections/{collection_id}/feature)
- [x] Task 8: Add rating validation (1-5 range), update validators, update build_collection_view
- [x] Task 9: Extend unit, integration, and smoke coverage for rating and discovery surface
- [x] Task 10: Documentation updates for all changed behavior and contracts

## Constitution And Quality Checklist

- [ ] Competency growth remains the product outcome, not activity theater
- [ ] All new external boundaries are typed and schema-validated
- [ ] Fail-fast and fail-loud behavior is preserved with stable error codes
- [ ] Route handlers remain thin; business rules stay out of transport layers
- [ ] Dependency injection and adapter boundaries remain explicit
- [ ] Critical workflow artifacts are durably persisted where required
- [ ] Traces, logs, and events cover all changed workflow steps
- [ ] Prompt, rubric, model, and config versions are preserved where applicable
- [ ] Assessment and progression behavior remains explainable
- [ ] No silent fallback is introduced in scoring, progression, generation, or recommendation paths

## Testing And Documentation Checklist

- [ ] Unit Tests: deterministic coverage for rating logic, discovery tier logic, and validation rules
- [ ] Integration Tests: API, persistence, and event/trace coverage for rating, discovery, and org-scoped listing
- [ ] Smoke Tests With Real Provider: backend smoke flows for rating and discovery; baseline suite must still pass
- [ ] Failure Path Coverage: explicit rating validation, auth rejection, and persistence failure coverage
- [ ] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [ ] CollectionRatingRecord persists correctly with composite primary key
- [ ] CollectionRecord.avg_rating, rating_count, featured fields persist correctly
- [ ] Users can rate collections 1-5; one rating per user per collection (updateable)
- [ ] avg_rating and rating_count are denormalized correctly on CollectionRecord
- [ ] GET /collections/discover returns only global hub collections (verified_public, organisation_id=NULL)
- [ ] GET /organisations/{org_id}/collections filters by organisation correctly
- [ ] Admin can feature/highlight collections in discovery
- [ ] Rated_by_actor reflects authenticated user's rating state in CollectionView

Minimum Viable Sprint:
CollectionRatingRecord model, rate/unrate endpoints, avg_rating/rating_count denormalization, and GET /collections/discover endpoint functional. Rating validation enforces 1-5 range.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Rating update logic (one rating per user) requires care to avoid duplicates | High | Use upsert pattern with composite key; validate before insert | Mitigated |
| Denormalized avg_rating must stay consistent when ratings change | High | Update avg_rating and rating_count transactionally with each rating operation | Mitigated |
| Discovery endpoint must not leak collections across org boundaries | Critical | Verify organisation_id=NULL AND verification_state=verified filter is correct | Mitigated |
| Adding rating_count to existing queries may require index review | Medium | Add index on rating_count if discovery queries sort/filter by it | Deferred |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```text
- CollectionRatingRecord uses (user_id, collection_id) as composite primary key for uniqueness
- Rating upsert: if user already rated, update existing rating; otherwise insert new
- avg_rating calculation: SUM(rating) / COUNT(*) maintained denormalized on CollectionRecord
- DELETE /collections/{id}/rate removes the user's rating and recalculates avg_rating/count
- GET /collections/discover is separate from GET /collections; it enforces global hub rules
- featured field allows org admins to highlight collections within their org's discovery
- rated_by_actor field in CollectionView is None if not authenticated, False if not rated, 1-5 if rated
- Feature toggle endpoint: PATCH /admin/collections/{collection_id} with featured=True/False
- Discovery tier logic already exists in discovery_tier_for_collection() - extend if needed
```

## Review And Sign-Off

- Sprint Status: Completed
- Completion Date: 2026-03-26

Checklist:

- [x] Primary goal achieved
- [x] Constitution and quality checks passed
- [x] Unit tests completed
- [x] Integration tests completed
- [x] Smoke tests with real provider completed
- [x] Documentation updated
- [ ] Code review completed

Next Sprint Priorities:

1. Add collection browsing by skill/competency with pagination
2. Implement collection soft-delete / archival workflow
3. Add collection content preview (first N items) for discovery
4. Extend rating analytics for org admins
