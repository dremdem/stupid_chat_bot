# OAuth 2.0 Authentication - Implementation Plan

## Table of Contents

- [Overview](#overview)
- [Requirements Summary](#requirements-summary)
- [Architecture Overview](#architecture-overview)
- [Implementation Phases](#implementation-phases)
  - [Phase 1: Database Schema & User Model](#phase-1-database-schema--user-model)
  - [Phase 2: Message Limits & Anonymous Users](#phase-2-message-limits--anonymous-users)
  - [Phase 3: OAuth 2.0 Providers](#phase-3-oauth-20-providers)
  - [Phase 4: Email/Password Authentication](#phase-4-emailpassword-authentication)
  - [Phase 5: Admin Panel](#phase-5-admin-panel)
  - [Phase 6: Testing & Documentation](#phase-6-testing--documentation)
- [Progress Tracking](#progress-tracking)
- [Dependencies](#dependencies)
- [Related Documents](#related-documents)

---

## Overview

This document outlines the implementation plan for adding OAuth 2.0 authentication to the Stupid Chat Bot application, as specified in [Issue #56](https://github.com/dremdem/stupid_chat_bot/issues/56).

**Goal**: Implement a tiered access system with OAuth 2.0 authentication, message limits, and an admin panel for user management.

---

## Requirements Summary

### User Tiers

| Tier | Access Level | Message Limit | Requirements |
|------|--------------|---------------|--------------|
| Anonymous | Basic | 5 messages | None |
| Authenticated | Standard | 30 messages | OAuth or email login |
| Unlimited | Full | Unlimited | Admin-granted |
| Admin | Full + Management | Unlimited | Admin-designated |

### Authentication Methods

- OAuth 2.0: Google, GitHub, Facebook
- Email/Password fallback

### Admin Capabilities

- Block/unblock users
- Grant unlimited access
- Adjust context window size (default: 20 messages)
- Designate admin accounts

---

## Architecture Overview

```mermaid
graph TB
    subgraph Client["Frontend (React)"]
        UI[Chat UI]
        AuthUI[Auth Components]
        AdminUI[Admin Panel]
    end

    subgraph Auth["Authentication Layer"]
        OAuth[OAuth 2.0 Handler]
        EmailAuth[Email/Password Auth]
        JWT[JWT Token Manager]
        Session[Session Manager]
    end

    subgraph Providers["OAuth Providers"]
        Google[Google OAuth]
        GitHub[GitHub OAuth]
        Facebook[Facebook OAuth]
    end

    subgraph Backend["FastAPI Backend"]
        API[API Endpoints]
        Middleware[Auth Middleware]
        Limits[Rate Limiter]
        AdminAPI[Admin API]
    end

    subgraph Storage["Database"]
        Users[(Users Table)]
        Sessions[(Sessions Table)]
        Messages[(Messages Table)]
    end

    UI --> AuthUI
    AuthUI --> OAuth
    AuthUI --> EmailAuth
    OAuth --> Google
    OAuth --> GitHub
    OAuth --> Facebook
    OAuth --> JWT
    EmailAuth --> JWT
    JWT --> Session
    Session --> API
    API --> Middleware
    Middleware --> Limits
    API --> AdminAPI
    API --> Users
    API --> Sessions
    API --> Messages
    AdminUI --> AdminAPI
```

### Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant O as OAuth Provider
    participant D as Database

    U->>F: Click "Login with Google"
    F->>B: GET /auth/google
    B->>O: Redirect to Google OAuth
    O->>U: Show consent screen
    U->>O: Grant permission
    O->>B: Callback with auth code
    B->>O: Exchange code for tokens
    O->>B: Return access token + user info
    B->>D: Create/update user record
    B->>B: Generate JWT
    B->>F: Return JWT + user info
    F->>F: Store JWT, update UI
    F->>B: API requests with JWT
    B->>B: Validate JWT, check limits
    B->>F: Response
```

---

## Implementation Phases

### Phase 1: Database Schema & User Model

**Goal**: Extend database to support users, authentication, and message tracking.

#### Tasks

- [ ] Create `users` table with fields:
  - `id` (UUID, primary key)
  - `email` (unique, nullable for OAuth-only users)
  - `password_hash` (nullable for OAuth users)
  - `display_name`
  - `avatar_url`
  - `provider` (google, github, facebook, email)
  - `provider_id` (external OAuth ID)
  - `role` (anonymous, user, unlimited, admin)
  - `message_limit` (nullable, overrides default)
  - `context_window_size` (default: 20)
  - `is_blocked` (boolean)
  - `created_at`, `updated_at`

- [ ] Create `user_sessions` table:
  - `id` (UUID)
  - `user_id` (foreign key)
  - `refresh_token_hash`
  - `expires_at`
  - `created_at`

- [ ] Update `messages` table:
  - Add `user_id` foreign key
  - Add index for user message counting

- [ ] Create Alembic migrations
- [ ] Create SQLAlchemy models
- [ ] Create Pydantic schemas

#### Deliverables

- `backend/app/models/user.py`
- `backend/app/schemas/user.py`
- `backend/alembic/versions/xxx_add_users_table.py`

---

### Phase 2: Message Limits & Anonymous Users

**Goal**: Implement message counting and limits for anonymous users.

#### Tasks

- [ ] Create message counting service
- [ ] Implement anonymous user tracking (via cookies/fingerprint)
- [ ] Add middleware to check message limits
- [ ] Create limit exceeded response with login prompt
- [ ] Add WebSocket support for limit notifications
- [ ] Update frontend to show remaining messages
- [ ] Add "login required" modal

#### Deliverables

- `backend/app/services/message_limits.py`
- `backend/app/middleware/rate_limit.py`
- `frontend/src/components/LoginPrompt.jsx`
- Updated `frontend/src/components/Chat.jsx`

---

### Phase 3: OAuth 2.0 Providers

**Goal**: Implement OAuth 2.0 authentication with Google, GitHub, and Facebook.

#### Tasks

- [ ] Install and configure `authlib` or `python-social-auth`
- [ ] Implement OAuth callback handler
- [ ] Create JWT token generation and validation
- [ ] Implement refresh token rotation

**Google OAuth**:
- [ ] Register app in Google Cloud Console
- [ ] Implement `/auth/google` and `/auth/google/callback`
- [ ] Handle user creation/login

**GitHub OAuth**:
- [ ] Register OAuth app in GitHub
- [ ] Implement `/auth/github` and `/auth/github/callback`
- [ ] Handle user creation/login

**Facebook OAuth**:
- [ ] Register app in Facebook Developers
- [ ] Implement `/auth/facebook` and `/auth/facebook/callback`
- [ ] Handle user creation/login

**Frontend**:
- [ ] Create login page with OAuth buttons
- [ ] Implement token storage (httpOnly cookies preferred)
- [ ] Add auth context/state management
- [ ] Update API client to include auth headers

#### Deliverables

- `backend/app/routers/auth.py`
- `backend/app/services/oauth.py`
- `backend/app/services/jwt.py`
- `frontend/src/pages/Login.jsx`
- `frontend/src/context/AuthContext.jsx`
- `frontend/src/hooks/useAuth.js`

---

### Phase 4: Email/Password Authentication

**Goal**: Provide email/password fallback for users without OAuth accounts.

#### Tasks

- [ ] Implement password hashing (bcrypt/argon2)
- [ ] Create registration endpoint with email verification
- [ ] Create login endpoint
- [ ] Implement password reset flow
- [ ] Add email sending service (or use third-party)
- [ ] Create frontend forms:
  - [ ] Registration form
  - [ ] Login form
  - [ ] Password reset form
- [ ] Add form validation

#### Deliverables

- `backend/app/routers/auth_email.py`
- `backend/app/services/email.py`
- `frontend/src/components/auth/RegisterForm.jsx`
- `frontend/src/components/auth/LoginForm.jsx`
- `frontend/src/components/auth/PasswordReset.jsx`

---

### Phase 5: Admin Panel

**Goal**: Create admin dashboard for user management and provide tools for initial admin bootstrapping.

#### Admin Bootstrap Problem

When the system is first deployed, no admin users exist. This creates a "chicken and egg" problem: you need admin access to create admins, but there are no admins yet.

**Solution**: Provide two mechanisms for creating the initial admin:

```mermaid
flowchart TD
    A[Fresh Deployment] --> B{How to create first admin?}
    B --> C[CLI Command]
    B --> D[Environment Variable]

    C --> E[Run: invoke make-admin --email user@example.com]
    E --> F[User promoted to admin]

    D --> G[Set INITIAL_ADMIN_EMAIL in .env]
    G --> H[User logs in]
    H --> I{Is user email == INITIAL_ADMIN_EMAIL?}
    I -->|Yes| J[Auto-promote to admin]
    I -->|No| K[Normal user flow]

    F --> L[Admin can access /admin]
    J --> L
```

#### Tasks

**Admin Bootstrap Tooling**:
- [ ] Create CLI module (`backend/app/cli.py`)
- [ ] Implement `make-admin` command
- [ ] Implement `remove-admin` command
- [ ] Implement `list-admins` command
- [ ] Add invoke task wrappers
- [ ] Implement `INITIAL_ADMIN_EMAIL` environment variable auto-promotion
- [ ] Add startup check for initial admin promotion
- [ ] Add logging for admin promotions

**Admin API & Middleware**:
- [ ] Create admin-only middleware/decorator
- [ ] Implement admin API endpoints:
  - [ ] `GET /admin/users` - List all users with pagination
  - [ ] `GET /admin/users/:id` - Get user details
  - [ ] `PATCH /admin/users/:id` - Update user (role, limits, block)
  - [ ] `DELETE /admin/users/:id` - Delete user
  - [ ] `GET /admin/stats` - Usage statistics

**Admin Frontend**:
- [ ] Create admin frontend:
  - [ ] User list with search/filter
  - [ ] User detail view
  - [ ] Block/unblock toggle
  - [ ] Grant unlimited access button
  - [ ] Context window size adjustment
  - [ ] Admin role assignment

**Audit & Security**:
- [ ] Add audit logging for admin actions
- [ ] Log all CLI admin operations

#### Admin Bootstrap: CLI Command Design

##### Command Structure

```bash
# Primary command - promote user to admin
python -m app.cli make-admin user@example.com

# Or via invoke (recommended)
cd backend && invoke make-admin --email user@example.com

# Additional commands
invoke list-admins              # List all admin users
invoke remove-admin --email user@example.com  # Demote admin to regular user
```

##### CLI Implementation

```python
# backend/app/cli.py
import asyncio
import click
from app.database import get_db_session
from app.models.user import User
from app.services.admin import AdminService

@click.group()
def cli():
    """Stupid Chat Bot admin CLI."""
    pass

@cli.command()
@click.argument('email')
def make_admin(email: str):
    """Promote a user to admin role."""
    async def _make_admin():
        async with get_db_session() as session:
            service = AdminService(session)
            user = await service.get_user_by_email(email)

            if not user:
                click.echo(f"Error: User '{email}' not found.", err=True)
                click.echo("Note: User must log in at least once before promotion.", err=True)
                return 1

            if user.role == 'admin':
                click.echo(f"User '{email}' is already an admin.")
                return 0

            await service.promote_to_admin(user.id)
            click.echo(f"Success: User '{email}' promoted to admin.")
            return 0

    return asyncio.run(_make_admin())

@cli.command()
def list_admins():
    """List all admin users."""
    async def _list_admins():
        async with get_db_session() as session:
            service = AdminService(session)
            admins = await service.get_all_admins()

            if not admins:
                click.echo("No admin users found.")
                return

            click.echo("Admin users:")
            for admin in admins:
                click.echo(f"  - {admin.email} (id: {admin.id})")

    return asyncio.run(_list_admins())

@cli.command()
@click.argument('email')
@click.option('--force', is_flag=True, help='Skip confirmation')
def remove_admin(email: str, force: bool):
    """Demote an admin to regular user."""
    async def _remove_admin():
        async with get_db_session() as session:
            service = AdminService(session)

            # Prevent removing last admin
            admin_count = await service.count_admins()
            if admin_count <= 1:
                click.echo("Error: Cannot remove the last admin.", err=True)
                return 1

            if not force:
                click.confirm(f"Demote '{email}' from admin?", abort=True)

            await service.demote_from_admin(email)
            click.echo(f"Success: User '{email}' demoted to regular user.")

    return asyncio.run(_remove_admin())

if __name__ == '__main__':
    cli()
```

##### Invoke Task Wrappers

```python
# backend/tasks.py (add to existing)
@task
def make_admin(c, email):
    """Promote a user to admin role."""
    c.run(f"python -m app.cli make-admin {email}")

@task
def list_admins(c):
    """List all admin users."""
    c.run("python -m app.cli list-admins")

@task
def remove_admin(c, email, force=False):
    """Demote an admin to regular user."""
    force_flag = "--force" if force else ""
    c.run(f"python -m app.cli remove-admin {email} {force_flag}")
```

##### Docker Usage

```bash
# When running in Docker
docker compose exec backend python -m app.cli make-admin user@example.com

# Or via invoke
docker compose exec backend invoke make-admin --email user@example.com
```

#### Admin Bootstrap: Environment Variable Approach

##### Configuration

```bash
# .env or docker-compose environment
INITIAL_ADMIN_EMAIL=admin@example.com
```

##### Implementation

```python
# backend/app/services/auth.py (in login/OAuth callback flow)
from app.config import settings

async def handle_user_login(user: User, session: AsyncSession):
    """Called after successful authentication."""

    # Check for initial admin promotion
    if settings.INITIAL_ADMIN_EMAIL and user.email == settings.INITIAL_ADMIN_EMAIL:
        if user.role != 'admin':
            user.role = 'admin'
            await session.commit()
            logger.info(f"Auto-promoted initial admin: {user.email}")

    # ... rest of login handling
```

##### Startup Check (Alternative)

```python
# backend/app/main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await check_initial_admin()
    yield
    # Shutdown

async def check_initial_admin():
    """Check and log initial admin configuration."""
    if settings.INITIAL_ADMIN_EMAIL:
        logger.info(f"Initial admin email configured: {settings.INITIAL_ADMIN_EMAIL}")
        logger.info("This user will be auto-promoted to admin on first login.")
```

##### Behavior

| Scenario | Result |
|----------|--------|
| `INITIAL_ADMIN_EMAIL` not set | No auto-promotion |
| User with matching email logs in | Promoted to admin, logged |
| User already admin | No change |
| `INITIAL_ADMIN_EMAIL` changed | New email will be promoted on login |
| Multiple logins | Idempotent, only logs first promotion |

##### Security Considerations

- Environment variable is only checked at login time
- Promotion is logged for audit trail
- Safe to leave set after initial setup (idempotent)
- Can be removed from `.env` after initial admin is created
- Does not create users, only promotes existing ones

#### Deliverables

- `backend/app/cli.py` - CLI commands
- `backend/app/routers/admin.py` - Admin API endpoints
- `backend/app/services/admin.py` - Admin business logic
- Updated `backend/tasks.py` - Invoke wrappers
- `frontend/src/pages/Admin.jsx` - Admin panel
- `frontend/src/components/admin/UserList.jsx`
- `frontend/src/components/admin/UserDetail.jsx`

---

### Phase 6: Testing & Documentation

**Goal**: Ensure reliability and document the feature.

#### Tasks

- [ ] Unit tests for auth services
- [ ] Integration tests for OAuth flows
- [ ] E2E tests for login/logout
- [ ] Security testing:
  - [ ] JWT validation
  - [ ] CSRF protection
  - [ ] Rate limiting on auth endpoints
- [ ] Update API documentation
- [ ] Update user documentation
- [ ] Update CLAUDE.md with auth configuration

#### Deliverables

- `backend/tests/test_auth.py`
- `backend/tests/test_admin.py`
- `frontend/src/__tests__/auth.test.js`
- Updated `docs/oauth-technical-details.md`

---

## Progress Tracking

### Overall Status

| Phase | Status | Progress |
|-------|--------|----------|
| Phase 1: Database Schema | Not Started | 0% |
| Phase 2: Message Limits | Not Started | 0% |
| Phase 3: OAuth Providers | Not Started | 0% |
| Phase 4: Email/Password | Not Started | 0% |
| Phase 5: Admin Panel | Not Started | 0% |
| Phase 6: Testing & Docs | Not Started | 0% |

### Detailed Progress

#### Phase 1 Tasks
- [ ] Create users table
- [ ] Create user_sessions table
- [ ] Update messages table
- [ ] Create Alembic migrations
- [ ] Create SQLAlchemy models
- [ ] Create Pydantic schemas

#### Phase 2 Tasks
- [ ] Message counting service
- [ ] Anonymous user tracking
- [ ] Rate limit middleware
- [ ] Limit exceeded response
- [ ] WebSocket notifications
- [ ] Frontend remaining messages
- [ ] Login required modal

#### Phase 3 Tasks
- [ ] OAuth library setup
- [ ] JWT implementation
- [ ] Google OAuth
- [ ] GitHub OAuth
- [ ] Facebook OAuth
- [ ] Frontend auth components

#### Phase 4 Tasks
- [ ] Password hashing
- [ ] Registration endpoint
- [ ] Login endpoint
- [ ] Password reset
- [ ] Email service
- [ ] Frontend forms

#### Phase 5 Tasks
- [ ] CLI module (`app/cli.py`)
- [ ] `make-admin` command
- [ ] `remove-admin` command
- [ ] `list-admins` command
- [ ] Invoke task wrappers
- [ ] `INITIAL_ADMIN_EMAIL` auto-promotion
- [ ] Startup check for initial admin
- [ ] Admin middleware
- [ ] Admin API endpoints
- [ ] Admin frontend
- [ ] Audit logging

#### Phase 6 Tasks
- [ ] Unit tests
- [ ] Integration tests
- [ ] E2E tests
- [ ] Security testing
- [ ] Documentation

---

## Dependencies

### Backend Dependencies

| Package | Purpose |
|---------|---------|
| `authlib` | OAuth 2.0 client |
| `python-jose[cryptography]` | JWT handling |
| `passlib[bcrypt]` | Password hashing |
| `click` | CLI commands |
| `aiosmtplib` | Async email sending (optional) |

### Frontend Dependencies

| Package | Purpose |
|---------|---------|
| `react-router-dom` | Routing for auth pages |
| `@tanstack/react-query` | Auth state management (optional) |

### Environment Variables

```bash
# OAuth Providers
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
GITHUB_CLIENT_ID=xxx
GITHUB_CLIENT_SECRET=xxx
FACEBOOK_CLIENT_ID=xxx
FACEBOOK_CLIENT_SECRET=xxx

# JWT
JWT_SECRET_KEY=xxx
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Admin Bootstrap (optional)
# User with this email will be auto-promoted to admin on first login
INITIAL_ADMIN_EMAIL=admin@example.com

# Email (optional)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=xxx
SMTP_PASSWORD=xxx
```

---

## Related Documents

- [OAuth Technical Details](./oauth-technical-details.md) - Technical implementation details
- [Issue #56](https://github.com/dremdem/stupid_chat_bot/issues/56) - Original feature request
- [Main README](../README.md) - Project overview

---

**Document Version**: 1.1
**Created**: 2025-12-23
**Updated**: 2025-12-23
**Status**: Planning
**Issue**: [#56](https://github.com/dremdem/stupid_chat_bot/issues/56)
**Changelog**:
- v1.1: Added admin bootstrap tooling (CLI + environment variable) to Phase 5
