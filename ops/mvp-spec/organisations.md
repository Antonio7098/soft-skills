# Organisations Specification

## Overview

Organisations provide tenant isolation for collections and related resources. All admins are organisation-scoped — there is no global platform admin. Users belong to organisations and can create/administer collections scoped to their organisation.

## Admin Model

### Organisation Admin Only

- All admins are scoped to a specific organisation
- Admin role is stored in `OrganisationMembershipRecord.role = "admin"`
- No global admin flag on `UserAccountRecord`
- `UserAccountRecord.role` field removed — role is org-scoped only
- An admin can only manage resources within their organisation
- Cannot affect other organisations

### Role on UserAccountRecord

```python
# Removed: role field from UserAccountRecord
class UserAccountRecord(Base):
    __tablename__ = "user_accounts"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    # role removed — admin status is org-scoped via OrganisationMembershipRecord
    auth_provider: Mapped[str] = mapped_column(String(64))
    auth_subject: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
```

## Data Models

### OrganisationRecord

```python
class OrganisationRecord(Base):
    __tablename__ = "organisations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
```

### OrganisationMembershipRecord

```python
class OrganisationMembershipRecord(Base):
    __tablename__ = "organisation_memberships"

    organisation_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    role: Mapped[str] = mapped_column(String(32))  # "admin" | "member"
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("ix_organisation_memberships_user_id", "user_id"),
    )
```

### Updated: CollectionRecord

Add field:

```python
organisation_id: Mapped[str | None] = mapped_column(
    String(32),
    ForeignKey("organisations.id"),
    index=True,
    nullable=True  # NULL = global hub
)
```

### Updated: Actor (Auth)

```python
@dataclass(slots=True)
class Actor:
    user_id: str
    email: str
    organisation_id: str | None  # organisation context for current request
    organisation_role: str | None  # "admin" | "member" | None

    @property
    def is_org_admin(self) -> bool:
        return self.organisation_role == "admin"
```

## Discovery Tiers

| Tier | Criteria |
|------|----------|
| `global_public` | `organisation_id = NULL` AND `verification_state = verified` |
| `org_public` | `organisation_id = X` AND published_public AND member of org |
| `private` | Author's own or org's draft/private |

## API Endpoints

### Organisation Management (First org creator becomes admin)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/organisations` | Create organisation (creator becomes first admin) |
| GET | `/organisations/{org_id}` | Get organisation details |
| PATCH | `/organisations/{org_id}` | Update organisation |
| DELETE | `/organisations/{org_id}` | Delete organisation (soft delete) |

### Organisation Membership (Org Admin)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/organisations/{org_id}/members` | List org members |
| POST | `/organisations/{org_id}/members` | Add member |
| PATCH | `/organisations/{org_id}/members/{user_id}` | Update member role |
| DELETE | `/organisations/{org_id}/members/{user_id}` | Remove member |

### Collections with Organisation Scope

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/collections` | List collections (filter by `organisation_id`) |
| POST | `/collections` | Create collection (optionally in org) |
| GET | `/collections/discover` | Global hub (org_id=NULL, verified_public) |
| GET | `/organisations/{org_id}/collections` | Org hub collections |

### Collection Access Rules

| Condition | Who Can View |
|-----------|--------------|
| `organisation_id = NULL` AND `verified_public` | Everyone |
| `organisation_id = X` AND published_public | Org members only |
| Any state, own collection | Owner |
| Any state | Org admin of collection's org |

## Permissions Matrix

| Action | Who |
|--------|-----|
| Create organisation | Any authenticated user (becomes first org admin) |
| Delete organisation | Org admin |
| View organisation | Org members |
| Add org member | Org admin |
| Remove org member | Org admin |
| Change member role | Org admin |
| Create collection in org | Org members |
| Publish collection to org | Org admin |
| Verify collection | Org admin |
| View org collections | Org members |

## Notes

- A user can be a member of multiple organisations (multiple `OrganisationMembershipRecord` entries)
- `Actor.organisation_id` reflects the organisation context of the current request (from header or session)
- Collections without `organisation_id` belong to the global hub
- Deleting an organisation should archive its collections, not hard delete
- AdminLearnerRelationshipRecord (user-to-user relationships) remains unchanged
