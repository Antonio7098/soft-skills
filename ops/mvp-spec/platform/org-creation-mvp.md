# Org Creation MVP — Implementation Spec

## Overview

Allow a user to create an organisation, become its first admin automatically, and access the org-scoped admin dashboard immediately after. All organisation memberships are driven by the backend — the frontend `deriveSessionFromUser` synthetic-org-memberships hack is removed.

---

## User Flow

1. User registers/logs in → lands on Dashboard
2. User has no org memberships → empty state in Settings with "Create Organisation" CTA
3. User clicks "Create Organisation" → Modal opens with name + slug fields
4. On submit: backend creates org, user becomes admin, response includes full `org_memberships`
5. Frontend replaces session with authoritative backend session
6. Auto-navigate to `/admin` scoped to new org
7. User sees their org in TopBar switcher and AdminHeader

---

## Backend Changes

### 1. Extend `UserView` to include `org_memberships`

**File:** `backend/src/soft_skills_backend/modules/identity/models.py`

Add `OrganisationMembershipView` Pydantic model and `org_memberships: list[OrganisationMembershipView]` field to `UserView`.

```python
class OrganisationMembershipView(BaseModel):
    """User's organisation membership."""
    organisation_id: str
    organisation_name: str
    role: str  # "admin" | "member"
    permissions: list[str]

class UserView(BaseModel):
    id: str
    email: str
    display_name: str
    auth_provider: str
    created_at: datetime
    profile: LearnerProfileView
    org_memberships: list[OrganisationMembershipView] = Field(default_factory=list)
```

### 2. Update `IdentityService.get_user()` to populate `org_memberships`

**File:** `backend/src/soft_skills_backend/modules/identity/service.py`

In `get_user()`, query `OrganisationMembershipRecord` joined with `OrganisationRecord` for the given `user_id`. Map to `OrganisationMembershipView` with permissions derived from role.

Permissions mapping:
- `admin` role → `['collections:read', 'practice:run', 'admin:access', 'org:read', 'org:write']`
- `member` role → `['collections:read', 'practice:run']`

```python
def get_user(self, user_id: str) -> UserView:
    with self._session_factory() as session:
        user = session.get(UserAccountRecord, user_id)
        ...
        # NEW: load org memberships
        memberships = session.query(OrganisationMembershipRecord).filter_by(user_id=user_id).all()
        org_memberships = []
        for m in memberships:
            org = session.get(OrganisationRecord, m.organisation_id)
            perms = ADMIN_PERMISSIONS if m.role == "admin" else MEMBER_PERMISSIONS
            org_memberships.append(OrganisationMembershipView(
                organisation_id=m.organisation_id,
                organisation_name=org.name if org else m.organisation_id,
                role=m.role,
                permissions=perms,
            ))
        return UserView(
            ...
            org_memberships=org_memberships,
        )
```

### 3. Add `GET /organisations` endpoint (list user's orgs)

**File:** `backend/src/soft_skills_backend/entrypoints/http/routes/organisations.py`

```python
@router.get("", response_model=ApiEnvelope[list[OrganisationListView]])
async def list_organisations(request: Request) -> ApiEnvelope[list[OrganisationListView]]:
    actor = await require_actor(request)
    service = get_organisation_service(request)
    return ok_response(request, service.list_organisations_for_user(actor))
```

**File:** `backend/src/soft_skills_backend/modules/organisations/use_cases/organisation_service.py`

```python
def list_organisations_for_user(self, actor: Actor) -> list[OrganisationListView]:
    """List all organisations the user belongs to."""
    with self._session_factory() as session:
        memberships = session.query(OrganisationMembershipRecord).filter_by(user_id=actor.user_id).all()
        orgs = []
        for m in memberships:
            org = session.get(OrganisationRecord, m.organisation_id)
            if org:
                member_count = session.query(OrganisationMembershipRecord).filter_by(organisation_id=org.id).count()
                orgs.append(OrganisationListView(
                    id=org.id,
                    name=org.name,
                    slug=org.slug,
                    member_count=member_count,
                ))
        return orgs
```

### 4. Ensure `create_organisation` returns full `OrganisationView` with membership

The existing `create_organisation` (line 90) already creates the membership record in the DB. After creating, it should return an `OrganisationView`. The frontend will call `getAuthSession()` afterwards to get the authoritative session with all memberships.

---

## Frontend Changes

### 1. New types

**File:** `frontend/src/data/types/organisation.ts` (NEW)

```typescript
export interface OrganisationView {
  readonly id: string;
  readonly name: string;
  readonly slug: string;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface OrganisationListView {
  readonly id: string;
  readonly name: string;
  readonly slug: string;
  readonly member_count: number;
}

export interface CreateOrganisationCommand {
  readonly name: string;
  readonly slug: string;
}
```

Export from `frontend/src/data/types/index.ts`.

### 2. Update `UserView` and `AuthSessionView` types

**File:** `frontend/src/data/types/identity.ts`

The `UserView` from the API will now include `org_memberships`. Update `AuthSessionView` construction to use the backend's `org_memberships` directly instead of deriving from `sessionStorage`.

### 3. Add `createOrganisation` and `listOrganisations` to `DataProvider` interface

**File:** `frontend/src/data/provider.ts`

```typescript
createOrganisation(cmd: CreateOrganisationCommand): Promise<OrganisationView>;
listOrganisations(): Promise<OrganisationListView[]>;
```

### 4. Implement in `ApiDataProvider`

**File:** `frontend/src/data/api-provider.ts`

```typescript
createOrganisation: (cmd) =>
  request<OrganisationView>('/organisations', { method: 'POST', body: JSON.stringify(cmd) }),
listOrganisations: () =>
  request<OrganisationListView[]>('/organisations'),
```

Remove the `deriveSessionFromUser` hack entirely. Instead, update `getAuthSession` to trust the backend response. The `org_memberships` will come from `UserView.org_memberships` returned by `/users/me`.

### 5. Implement in `MockDataProvider`

**File:** `frontend/src/data/mock-provider.ts`

Add `_organisations` array. `createOrganisation` creates an in-memory org and adds membership to the mock user. `listOrganisations` returns user's orgs. `getAuthSession` uses stored org memberships instead of deriving.

### 6. Add to `SwitchingDataProvider`

**File:** `frontend/src/data/switching-provider.ts`

```typescript
createOrganisation(cmd) {
  return this.withMode(
    () => apiDataProvider.createOrganisation(cmd),
    () => mockDataProvider.createOrganisation(cmd),
  );
},
listOrganisations() {
  return this.withMode(
    () => apiDataProvider.listOrganisations(),
    () => mockDataProvider.listOrganisations(),
  );
},
```

### 7. Remove `deriveSessionFromUser` and fix `getAuthSession`

**File:** `frontend/src/data/api-provider.ts`

Replace `deriveSessionFromUser` with direct use of `UserView.org_memberships` from backend. The `AuthSessionView` is now constructed from the actual API response, not synthesized from `sessionStorage`.

### 8. Create `OrganisationModal` component

**File:** `frontend/src/features/settings/OrganisationModal.tsx` (NEW)

Uses `Modal`, `ModalSection`, `ModalFooter`, `Input`, `Button` from design-system.

Props:
- `isOpen: boolean`
- `onClose: () => void`
- `onSuccess: (org: OrganisationView) => void`

Fields:
- `name` — `Input` with label, required, auto-generates slug on blur
- `slug` — `Input` with label, required, hint "lowercase with hyphens"

Validation:
- Name: non-empty, max 255 chars
- Slug: non-empty, max 64 chars, lowercase alphanumeric with hyphens
- Auto-generate slug from name: `"Acme Corp"` → `"acme-corp"`

States:
- Idle: form ready
- Loading: submit button shows spinner, inputs disabled
- Error: banner showing backend error message (e.g., "slug already taken")

### 9. Create `OrganisationList` component

**File:** `frontend/src/features/settings/OrganisationList.tsx` (NEW)

Uses `Card`, `Badge`, `Button`, `EmptyState` from design-system.

Shows all `org_memberships` from session:
- Each row: org name, role badge (`Admin` or `Member`), member count
- "Switch" button calls `setActiveOrganisation(orgId)` then navigates to `/admin`
- Uses `Building2` icon from lucide-react

Empty state when user has no orgs: uses `EmptyState` with `Building2` icon, "No organisations yet", "Create your first organisation" CTA that opens `OrganisationModal`.

### 10. Update `Settings` page

**File:** `frontend/src/pages/Settings.tsx`

Compose existing `ProfileCard` + new `OrganisationModal` + new `OrganisationList`. Minimal HTML — mostly component composition.

Structure:
```
PageShell
  ProfileCard
  Card (section: "Organisations")
    OrganisationList
    Button("Create Organisation") → opens OrganisationModal
  Card (section: Appearance)
    ThemeSwitcher
```

### 11. Add auto-navigation after org creation

**File:** `frontend/src/features/settings/OrganisationModal.tsx`

On `onSuccess`: call `navigate('/admin')`. The `AdminScopeProvider` will resolve the new org from `session.active_organisation_id` (set by the session refresh after create).

---

## File Manifest

### Backend (new/changed)

| File | Change |
|------|--------|
| `backend/src/soft_skills_backend/modules/identity/models.py` | Add `OrganisationMembershipView`, extend `UserView` with `org_memberships` |
| `backend/src/soft_skills_backend/modules/identity/service.py` | `get_user()` queries and populates `org_memberships` |
| `backend/src/soft_skills_backend/entrypoints/http/routes/organisations.py` | Add `GET /organisations` endpoint |
| `backend/src/soft_skills_backend/modules/organisations/use_cases/organisation_service.py` | Add `list_organisations_for_user()` |
| `backend/src/soft_skills_backend/modules/organisations/contracts/__init__.py` | Export `OrganisationMembershipView` if needed |

### Frontend (new/changed)

| File | Change |
|------|--------|
| `frontend/src/data/types/organisation.ts` | NEW — `OrganisationView`, `OrganisationListView`, `CreateOrganisationCommand` |
| `frontend/src/data/types/index.ts` | Export new types |
| `frontend/src/data/types/identity.ts` | Update to reflect backend `UserView` with `org_memberships` |
| `frontend/src/data/provider.ts` | Add `createOrganisation`, `listOrganisations` to interface |
| `frontend/src/data/api-provider.ts` | Implement both, remove `deriveSessionFromUser` hack |
| `frontend/src/data/mock-provider.ts` | Implement both, update `getAuthSession` |
| `frontend/src/data/switching-provider.ts` | Add both wrapper methods |
| `frontend/src/features/settings/OrganisationModal.tsx` | NEW — create org modal |
| `frontend/src/features/settings/OrganisationList.tsx` | NEW — list/switch orgs |
| `frontend/src/pages/Settings.tsx` | Compose new components, wire up modal |
| `frontend/src/features/settings/index.ts` | Export new components |

---

## Notes

- Backend `UserView` gets `org_memberships` — frontend trusts this entirely
- `sessionStorage['ss_active_organisation_id']` is still used to persist which org is "active" across page reloads, but `org_memberships` now comes from the backend, not from synthetic derivation
- Slug conflict errors from backend (HTTP 409) are surfaced in the modal error state
- No localStorage hacks for org memberships — everything backend-driven as specified
