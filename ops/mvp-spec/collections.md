# Collections Feature Specification

## Overview

Collections are curated groups of soft skill learning materials (prompts and scenarios) that users can create, share, and discover.

## Current State

Collections are user-authored with flat bookmarking only. No nesting, organisation scoping, or rating system exists.

## Target Features

### 1. Collection Authorship

- Users author collections with metadata: title, summary, target audience, difficulty, target skills/competencies
- Collections have lifecycle states: `draft` → `review` → `published_private` | `published_public` → `archived`
- Collections have verification states: `unverified` → `verified` | `rejected`

### 2. Discovery Tiers

| Tier | Criteria |
|------|----------|
| `private` | `lifecycle_state` = draft, review, published_private, or archived |
| `standard_public` | `published_public` AND `verification_state` = unverified |
| `verified_public` | `published_public` AND `verification_state` = verified |

### 3. Organisation Scoping

Two hub levels:

- **Global Hub** — Collections with `organisation_id = NULL` that are `verified_public`
- **Organisation Hub** — Collections scoped to a specific organisation (`organisation_id` = org id)

Users can only view organisation collections for orgs they are members of.

### 4. Bookmarking (Flat)

- Users can save/bookmark any collection via `CollectionSaveRecord` (user_id + collection_id)
- Saved collections appear in user's personal "Saved" list
- No nesting or custom grouping of saved collections

### 5. Rating System

- Users can rate collections 1-5 stars
- One rating per user per collection (updateable)
- Denormalized fields on CollectionRecord: `avg_rating` (float), `rating_count` (int)

### 6. Admin Controls

- Admin verification queue for collections pending review
- Org admin can verify, reject, or control visibility of collections within their organisation
- Admins can feature/highlight collections in discovery

## Data Models

### New: OrganisationRecord

```python
class OrganisationRecord(Base):
    __tablename__ = "organisations"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime]
```

### New: OrganisationMembershipRecord

```python
class OrganisationMembershipRecord(Base):
    __tablename__ = "organisation_memberships"
    organisation_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    role: Mapped[str] = mapped_column(String(32))  # "admin" | "member"
    joined_at: Mapped[datetime]
```

### Updated: CollectionRecord

Add fields:

- `organisation_id: Mapped[str | None]` — NULL for global hub collections
- `avg_rating: Mapped[float | None]`
- `rating_count: Mapped[int]` = default 0
- `featured: Mapped[bool]` = default False — org admin can feature in discovery

### New: CollectionRatingRecord

```python
class CollectionRatingRecord(Base):
    __tablename__ = "collection_ratings"
    user_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    collection_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    rating: Mapped[int]  # 1-5
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

## API Endpoints

### New

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/organisations` | List user's organisations |
| GET | `/organisations/{org_id}/collections` | List collections in org |
| POST | `/collections/{id}/rate` | Rate a collection |
| DELETE | `/collections/{id}/rate` | Remove rating |
| GET | `/collections/discover` | Global hub (verified_public, organisation_id=NULL) |

### Updated

- `GET /collections` — Add `organisation_id` filter
- `POST /collections` — Optional `organisation_id` for org-scoped collections

## Permissions

| Action | Who |
|--------|-----|
| Create collection in org | Org members |
| Publish collection to org | Org admin |
| Verify collections | Org admin |
| Feature collections | Org admin |
| View org collections | Org members only |
| Rate collection | Any authenticated user |
| Bookmark collection | Any authenticated user |
