# Swappable Auth Provider Architecture

## Context

CONSTITUTION.yml mandates `swappable_auth_provider_adapters` (CL-level requirement). This doc establishes the canonical adapter interface and provider-specific implementation notes for org-aware multi-tenant authentication.

## Design Goals

1. **Swap without code changes** - choose provider via config/env
2. **Org-aware** - all providers must support organization context and roles
3. **Normalized output** - all adapters produce the same `Actor` object
4. **Thin routes** - no business logic in transport; adapters normalize only

## Adapter Interface

```python
# shared/auth.py

from typing import Protocol
from fastapi import Request

class AuthAdapter(Protocol):
    """Swappable auth provider interface."""

    async def get_actor(self, request: Request) -> Actor | None:
        """Resolve authenticated actor from request, or None if not authenticated."""

    async def validate_session(self, token: str) -> ProviderSession | None:
        """Validate provider-specific token and return session info."""

class ProviderSession(TypedDict):
    """Normalized session data from any provider."""
    user_id: str
    email: str
    org_id: str | None
    org_role: str | None
```

## Actor Model

```python
# shared/auth.py

@dataclass(slots=True)
class Actor:
    """Authenticated actor resolved at the request boundary."""

    user_id: str
    email: str
    organisation_id: str | None = None
    organisation_role: str | None = None

    @property
    def is_org_admin(self) -> bool:
        return self.organisation_role == "admin"
```

## Provider Comparison

| Provider | Org Handling | Role Handling | Adapter Complexity |
|----------|-------------|---------------|-------------------|
| **WorkOS** | Native `profile.organization_id` | Native `profile.role.slug` from SSO groups | Low |
| **Clerk** | Native `Organization` membership | App-level Roles + Permissions per org | Low |
| **Firebase** | Custom claims or DB lookup | Custom claims in ID token | Medium |
| **Native/Header** | DB lookup via `X-Organisation-ID` header | DB lookup via `OrganisationMembershipRecord` | Low |

## Provider-Specific Notes

### WorkOS

- Returns `organization_id` and `role.slug` in SSO profile after JIT provisioning
- No org membership management - WorkOS stores org/role; your app receives it on each login
- Token validation: call `workos.sso.get_profile_and_token({ code })` on callback
- Session management: WorkOS handles sessions via cookies or your app stores session

```python
class WorkOSAuthAdapter:
    async def get_actor(self, request: Request) -> Actor | None:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        session = await self.validate_session(token)
        if not session:
            return None
        return Actor(
            user_id=session["user_id"],
            email=session["email"],
            organisation_id=session["org_id"],
            organisation_role=session["org_role"],
        )
```

### Clerk

- `ClerkBackendActor` embedded in request's auth token
- Contains `org_id`, `org_role`, `user_id`
- org membership is per-application; users can belong to multiple orgs with different roles
- Active org determined by session's active organization

```python
class ClerkAuthAdapter:
    async def get_actor(self, request: Request) -> Actor | None:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        # Use clerk-sdk-python to verify and decode
        session = await self.clerk.authenticate_request(token)
        if not session:
            return None
        actor_data = session.to_dict()
        return Actor(
            user_id=actor_data["user_id"],
            email=actor_data["email_addresses"][0]["email_address"],
            organisation_id=actor_data.get("org_id"),
            organisation_role=actor_data.get("org_role"),
        )
```

### Firebase

- **No native org concept** - org membership must be managed in your own DB
- Roles stored as custom claims on the ID token: `{"org_id": "...", "org_role": "admin"}`
- Validate ID token with Firebase Admin SDK
- **Org role always read from DB** (via `OrganisationMembershipRecord`) for accuracy; claims used only to establish identity

```python
class FirebaseAuthAdapter:
    async def get_actor(self, request: Request) -> Actor | None:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        try:
            decoded = self.admin.auth().verify_id_token(token)
        except Exception:
            return None
        
        # Look up canonical user via AuthIdentityRecord
        identity = await self._lookup_identity("firebase", decoded["uid"])
        if not identity:
            # Auto-link or create user based on email matching
            identity = await self._link_or_create_user(
                provider="firebase",
                provider_user_id=decoded["uid"],
                email=decoded["email"],
            )
        
        # Org role always from DB for accuracy (see Org Role Sync decision)
        org_id = decoded.get("org_id")
        org_role = None
        if org_id:
            membership = await self._lookup_org_membership(org_id, identity.user_id)
            org_role = membership.role if membership else None
        
        return Actor(
            user_id=identity.user_id,
            email=decoded["email"],
            organisation_id=org_id,
            organisation_role=org_role,
        )
```

### Native/Header (Current Implementation)

- Dev/test mode using `X-User-ID` and `X-Organisation-ID` headers
- Validates user exists in DB via `UserAccountRecord`
- Org context resolved via `OrganisationMembershipRecord` lookup
- No token validation - assumes infrastructure-level auth (e.g., API gateway)

## Composition Root Wiring

```python
# platform/container.py

from typing import Literal

@dataclass
class AppContainer:
    auth_provider: AuthAdapter

    @classmethod
    def from_config(cls, config: AppConfig) -> Self:
        match config.auth_provider:
            case "workos":
                from soft_skills_backend.infra.auth import WorkOSAuthAdapter
                auth_provider = WorkOSAuthAdapter(
                    api_key=config.workos_api_key,
                    client_id=config.workos_client_id,
                )
            case "clerk":
                from soft_skills_backend.infra.auth import ClerkAuthAdapter
                auth_provider = ClerkAuthAdapter(
                    publishable_key=config.clerk_publishable_key,
                    api_key=config.clerk_api_key,
                )
            case "firebase":
                from soft_skills_backend.infra.auth import FirebaseAuthAdapter
                auth_provider = FirebaseAuthAdapter(
                    credentials=config.firebase_credentials,
                )
            case "native" | _:
                from soft_skills_backend.shared.auth import HeaderAuthProvider
                auth_provider = HeaderAuthProvider(
                    session_factory=config.session_factory,
                    workflow_events=config.workflow_events,
                )
        return cls(auth_provider=auth_provider)
```

## Configuration

```yaml
# config.yaml or environment variables
auth:
  provider: "native"  # workos | clerk | firebase | native
  
workos:
  api_key: ${WORKOS_API_KEY}
  client_id: ${WORKOS_CLIENT_ID}

clerk:
  publishable_key: ${CLERK_PUBLISHABLE_KEY}
  api_key: ${CLERK_API_KEY}

firebase:
  credentials_path: ${FIREBASE_CREDENTIALS_PATH}
```

## Decisions Made

### 1. Token Refresh: Frontend/SDK

For WorkOS and Clerk, token refresh is delegated to the frontend SDK. The backend adapter only validates tokens; it does not manage refresh logic. This keeps adapters stateless.

For Firebase, ID tokens are stateless JWTs - the frontend obtains a fresh token via Firebase SDK on each login.

### 2. Session Storage: App-Managed for All Providers

All sessions are managed by our application, not by the auth provider. This gives us:
- Immediate session revocation capability
- Consistent session format across providers
- No dependency on provider uptime for session validity

```python
class SessionRecord(Base):
    __tablename__ = "sessions"
    
    id: str
    user_id: str  # FK to UserAccountRecord
    provider: str  # "workos" | "clerk" | "firebase" | "native"
    provider_session_id: str | None
    token_hash: str  # store hashed token for validation
    expires_at: datetime
    created_at: datetime
```

### 3. Org Role Sync: DB Lookup with Caching

Org role is always read from `OrganisationMembershipRecord` in the DB for accuracy. To balance performance:

- **Sensitive operations** (e.g., admin actions): Direct DB lookup, no cache
- **Normal reads**: Cache org role with 30-second TTL to reduce DB load

```python
class OrgRoleCache:
    """Short-lived cache for org roles to reduce DB queries."""

    async def get_role(self, org_id: str, user_id: str) -> str | None:
        cache_key = f"org_role:{org_id}:{user_id}"
        try:
            cached = await self.redis.get(cache_key)
            if cached:
                return cached
        except RedisConnectionError:
            pass  # Fallback to DB lookup
        
        role = await self._lookup_db(org_id, user_id)
        if role:
            try:
                await self.redis.setex(cache_key, ttl=30, value=role)
            except RedisConnectionError:
                pass  # Cache write failed, continue without caching
        return role

    async def invalidate(self, org_id: str, user_id: str) -> None:
        cache_key = f"org_role:{org_id}:{user_id}"
        try:
            await self.redis.delete(cache_key)
        except RedisConnectionError:
            pass  # Best effort invalidation
```

**Redis fallback**: If Redis is unavailable, all operations fall back to direct DB lookup. The cache is best-effort; DB is always the source of truth.

When org role changes (e.g., user promoted/demoted), invalidate the cache immediately.

### 4. Identity Mapping: `AuthIdentityRecord` Table

An identifier mapping table links provider identities to our `UserAccountRecord`. This supports:
- Multiple auth providers per user (e.g., WorkOS + Google OAuth)
- Migration from Native to WorkOS/Clerk without breaking existing users
- Single canonical user across all auth domains

```python
class AuthIdentityRecord(Base):
    __tablename__ = "auth_identities"
    
    id: str
    user_id: str  # FK to UserAccountRecord
    provider: str  # "workos" | "clerk" | "firebase" | "native" | "google" | "github"
    provider_user_id: str  # ID in the provider's system
    email: str  # normalized email for matching
    created_at: datetime
    linked_at: datetime  # when provider was linked to this account

class UserAccountRecord(Base):
    __tablename__ = "user_accounts"
    
    id: str
    email: str
    # existing fields...
```

**Lookup flow on login**:
1. Provider returns `provider_user_id` + `email`
2. Query `AuthIdentityRecord` by `(provider, provider_user_id)`
3. If found → return associated `UserAccountRecord`
4. If not found → check if email matches existing `UserAccountRecord` (migration path)
5. If email matches → link identity, return user
6. If no match → create new `UserAccountRecord` + `AuthIdentityRecord`

## Identity Mapping Model

```
┌─────────────────────┐      ┌─────────────────────┐
│  UserAccountRecord  │<────►│  AuthIdentityRecord │
│                     │ 1:N │                     │
│  id: str            │     │  id: str             │
│  email: str         │     │  user_id: str (FK)   │
│  ...                │     │  provider: str       │
└─────────────────────┘     │  provider_user_id   │
                            │  email: str          │
                            │  linked_at: datetime │
                            └─────────────────────┘
```

## Role Normalization

All providers map to a single canonical role model in our system:

| Canonical Role | WorkOS | Clerk | Firebase Claims | Native |
|----------------|--------|-------|-----------------|--------|
| `admin` | `role.slug == "admin"` | `membership.role == "admin"` | `org_role == "admin"` | `OrganisationMembershipRecord.role == "admin"` |
| `member` | `role.slug == "member"` | `membership.role == "basic_member"` | `org_role == "member"` | `OrganisationMembershipRecord.role == "member"` |

**Normalization happens in the adapter**, not in domain logic. Each adapter translates its provider-specific role to our canonical roles.

## Default Org Role

When a user joins an organization (via invitation, SSO, or direct add), their default role is `member`. Only an existing `admin` can promote them to `admin`.

## Open Question

### 3. Existing User Migration: Backfill or On-First-Login?

When existing Native users first authenticate via WorkOS/Clerk, should we:
- **Backfill `AuthIdentityRecord` for all existing users** (batch migration, complex, risky)
- **Link only on first re-login** (gradual, safe, some users may never link)

**Implication**: If we don't backfill, users who existed before the provider was added will have a new account created when they first use the new provider (email-matching links them, but it's a one-time event).

TBD - does not block implementation.

## Implementation Notes

- Route handlers call `require_actor()` / `require_org_admin()` which delegate to `AuthAdapter`
- No provider logic in routes or domain services
- Audit events (`auth.login.success.v1`, etc.) emitted from adapter layer
- All adapters must handle missing/invalid tokens gracefully, returning `None` for `optional_actor()`