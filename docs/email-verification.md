# Email Verification System

Complete documentation for the email verification feature in Stupid Chat Bot.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [Frontend Components](#frontend-components)
- [Security Considerations](#security-considerations)
- [Development vs Production](#development-vs-production)
- [SMTP Provider Recommendations](#smtp-provider-recommendations)
- [Troubleshooting](#troubleshooting)

---

## Overview

The email verification system ensures that users who register with email/password have valid email addresses. This prevents abuse and enables important user communications.

### Key Features

- **Token-based verification**: Secure SHA-256 hashed tokens sent via email
- **Expiration**: Tokens expire after 24 hours (configurable)
- **Rate limiting**: Resend requests limited to once per 60 seconds
- **Dev-friendly**: Console logging when SMTP not configured
- **User feedback**: Clear UI for verification status and resend option

### User Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend API
    participant DB as Database
    participant E as Email Service

    U->>F: Register with email/password
    F->>B: POST /api/auth/register
    B->>DB: Create user (is_email_verified=false)
    B->>DB: Create verification token
    B->>E: Send verification email
    E-->>U: Email with verification link
    B-->>F: Registration success
    F-->>U: Show "check your email" message

    U->>F: Click verification link
    F->>B: POST /api/auth/verify-email
    B->>DB: Validate token, mark user verified
    B-->>F: Verification success
    F-->>U: Show success, redirect to chat
```

---

## Architecture

### Component Overview

```mermaid
graph TB
    subgraph Frontend["Frontend (React)"]
        VE["VerifyEmail.jsx<br/>Verification Page"]
        CH["ChatHeader.jsx<br/>User Menu + Status"]
        AA["authApi.js<br/>API Functions"]
    end

    subgraph Backend["Backend (FastAPI)"]
        AUTH["auth.py<br/>API Endpoints"]
        VS["verification_service.py<br/>Token Management"]
        ES["email_service.py<br/>Email Sending"]
    end

    subgraph Storage["Data Layer"]
        DB[(Database)]
        EVT["EmailVerificationToken"]
        USR["User Model"]
    end

    subgraph External["External"]
        SMTP["SMTP Server"]
        CONSOLE["Console Log<br/>(Dev Mode)"]
    end

    VE --> AA
    CH --> AA
    AA --> AUTH
    AUTH --> VS
    VS --> ES
    VS --> DB
    ES --> SMTP
    ES --> CONSOLE
    DB --> EVT
    DB --> USR
```

### File Structure

```
backend/
├── app/
│   ├── api/
│   │   └── auth.py              # Verification endpoints
│   ├── models/
│   │   └── email_verification.py # Token model
│   ├── services/
│   │   ├── email_service.py      # SMTP/console email
│   │   └── verification_service.py # Token logic
│   └── config.py                 # SMTP settings
└── alembic/versions/
    └── c3d4e5f6a7b8_add_email_verification_tokens_table.py

frontend/
└── src/
    ├── components/
    │   ├── VerifyEmail.jsx       # Verification page
    │   ├── VerifyEmail.css
    │   ├── ChatHeader.jsx        # User menu with status
    │   └── ChatHeader.css
    └── services/
        └── authApi.js            # API functions
```

---

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# SMTP Configuration (leave empty for dev mode console logging)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-username
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=Stupid Chat Bot
SMTP_USE_TLS=true

# Verification Settings
EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS=24
EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS=60
```

### Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `SMTP_HOST` | `""` (empty) | SMTP server hostname. Empty = console logging |
| `SMTP_PORT` | `587` | SMTP server port |
| `SMTP_USER` | `""` | SMTP authentication username |
| `SMTP_PASSWORD` | `""` | SMTP authentication password |
| `SMTP_FROM_EMAIL` | `noreply@stupidbot.local` | Sender email address |
| `SMTP_FROM_NAME` | `Stupid Chat Bot` | Sender display name |
| `SMTP_USE_TLS` | `true` | Use STARTTLS (true) or SSL (false) |
| `EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS` | `24` | Hours until token expires |
| `EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS` | `60` | Seconds between resend requests |

---

## Database Schema

### EmailVerificationToken Model

```mermaid
erDiagram
    User ||--o{ EmailVerificationToken : has

    User {
        uuid id PK
        string email
        string provider
        boolean is_email_verified
        datetime created_at
    }

    EmailVerificationToken {
        uuid id PK
        uuid user_id FK
        string token_hash "SHA-256 hash"
        datetime expires_at
        boolean is_used
        datetime created_at
    }
```

### Token Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Created: User registers
    Created --> Valid: Token generated
    Valid --> Used: User clicks link
    Valid --> Expired: 24 hours pass
    Used --> [*]: Verification complete
    Expired --> [*]: Token invalidated

    Valid --> Valid: Resend requested
    note right of Valid: Old token invalidated,\nnew token created
```

---

## API Endpoints

### POST /api/auth/verify-email

Verify a user's email address using the token from the email link.

**Request:**
```json
{
  "token": "<verification-token-from-email>"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Email verified successfully! You can now enjoy full access."
}
```

**Response (Error):**
```json
{
  "success": false,
  "message": "Verification link has expired. Please request a new one."
}
```

**Error Cases:**
| Status | Message |
|--------|---------|
| 400 | Verification link has expired |
| 400 | Verification link is invalid |
| 400 | Email already verified |

---

### POST /api/auth/resend-verification

Request a new verification email. Rate limited.

**Request:** None (uses session cookie)

**Response (Success):**
```json
{
  "success": true,
  "message": "Verification email sent! Check your inbox."
}
```

**Response (Rate Limited):**
```json
{
  "success": false,
  "message": "Please wait 45 seconds before requesting another email."
}
```

**Error Cases:**
| Status | Message |
|--------|---------|
| 401 | Not authenticated |
| 400 | Email already verified |
| 400 | Only email accounts need verification |
| 429 | Rate limit (wait N seconds) |

---

### Registration Flow Update

The `POST /api/auth/register` endpoint now:
1. Creates user with `is_email_verified=false`
2. Generates verification token
3. Sends verification email
4. Returns success with verification notice

---

## Frontend Components

### VerifyEmail Page

Handles the `/verify-email?token=...` URL when user clicks email link.

**States:**

```mermaid
stateDiagram-v2
    [*] --> Verifying: Page loads
    Verifying --> Success: Token valid
    Verifying --> Error: Token invalid/expired
    Success --> [*]: Click "Continue"
    Error --> [*]: Click "Go to App"
```

**Usage:**
```jsx
// In App.jsx
function getVerificationToken() {
  const path = window.location.pathname
  if (path === '/verify-email') {
    const params = new URLSearchParams(window.location.search)
    return params.get('token')
  }
  return null
}

// Render verification page if token present
if (verificationToken !== null) {
  return <VerifyEmail token={verificationToken} onComplete={...} />
}
```

---

### ChatHeader Verification Status

Shows verification warning in user dropdown for unverified email users.

**Detection Logic:**
```jsx
const needsVerification =
  user &&
  user.provider === 'email' &&
  user.is_email_verified === false
```

**UI Elements:**
- Warning message with icon
- "Resend email" button
- Disabled state during send
- Toast notifications for feedback

---

## Security Considerations

### Token Security

1. **Hashing**: Tokens are SHA-256 hashed before storage
   - Raw token sent to user via email
   - Only hash stored in database
   - Prevents token theft if database compromised

2. **Expiration**: Tokens expire after 24 hours
   - Limits window for interception attacks
   - Configurable via environment variable

3. **Single Use**: Tokens marked as used after verification
   - Prevents replay attacks
   - Old tokens invalidated on resend

### Rate Limiting

```mermaid
flowchart LR
    A[Resend Request] --> B{Cooldown?}
    B -->|Yes| C[Reject: Wait N seconds]
    B -->|No| D[Invalidate old tokens]
    D --> E[Create new token]
    E --> F[Send email]
    F --> G[Update last_sent time]
```

- 60-second cooldown between resend requests
- Prevents email bombing attacks
- Cooldown based on most recent token's `created_at`

### Best Practices Implemented

- No token in URL query params stored server-side
- HTTPS required for production (token in transit)
- Token not logged in production mode
- User feedback doesn't reveal if email exists (registration)

---

## Development vs Production

### Development Mode

When `SMTP_HOST` is empty (not configured), emails are logged to console:

```
============================================================
EMAIL (dev mode - not sent)
To: user@example.com
Subject: Verify your email - Stupid Chat Bot
------------------------------------------------------------
Hi user,

Thanks for signing up for Stupid Chat Bot!
Please verify your email address by clicking the link below:

http://localhost:5173/verify-email?token=abc123...

This link will expire in 24 hours.
============================================================
```

**Benefits:**
- No SMTP server needed for development
- Easy to test full flow locally
- Token visible in logs for manual testing

### Production Mode

When SMTP is configured, emails are sent via SMTP. See the [SMTP Provider Recommendations](#smtp-provider-recommendations) section for detailed setup.

---

## SMTP Provider Recommendations

Choosing the right SMTP provider is crucial for reliable email delivery. This section analyzes current options (as of January 2025).

### Provider Comparison

```mermaid
graph TB
    subgraph Free["Free Tier Options"]
        R["Resend<br/>3,000/month<br/>⭐ RECOMMENDED"]
        S2G["SMTP2GO<br/>1,000/month"]
        B["Brevo<br/>300/day"]
    end

    subgraph Paid["Pay-as-you-go"]
        SES["Amazon SES<br/>$0.10/1,000<br/>Best for scale"]
    end

    subgraph Trial["Trial Only"]
        SG["SendGrid<br/>60-day trial<br/>⚠️ No free tier"]
    end

    style R fill:#10b981,color:#fff
    style SES fill:#f59e0b,color:#fff
    style SG fill:#ef4444,color:#fff
```

### Detailed Provider Analysis

| Provider | Free Tier | Daily Limit | Best For | Notes |
|----------|-----------|-------------|----------|-------|
| **Resend** | 3,000/month | 100/day | This project | Modern API, React Email support |
| **SMTP2GO** | 1,000/month | 200/day | Simple needs | Never expires, reliable |
| **Brevo** | 9,000/month | 300/day | Higher volume | Brevo branding on free |
| **Amazon SES** | None | Unlimited | Production scale | $0.10/1,000 emails |
| **SendGrid** | ~~100/day~~ | N/A | ❌ Avoid | Free tier ended July 2025 |
| **Mailgun** | Trial only | N/A | Not recommended | No permanent free tier |

### Recommended: Resend

[Resend](https://resend.com) is the recommended provider for this project:

**Pros:**
- Permanent free tier (3,000 emails/month)
- Modern, developer-focused API
- React Email integration
- Clean documentation
- Simple setup

**Cons:**
- No analytics on free tier
- Single domain on free tier
- Newer service (less mature than incumbents)

**Setup:**

1. Create account at [resend.com](https://resend.com)
2. Verify your domain (add DNS records)
3. Get API key from dashboard
4. Configure environment:

```bash
# .env for Resend
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASSWORD=re_your_api_key_here
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=Stupid Chat Bot
SMTP_USE_TLS=true
```

### Alternative: SMTP2GO

[SMTP2GO](https://www.smtp2go.com) is a solid alternative:

**Setup:**
```bash
# .env for SMTP2GO
SMTP_HOST=mail.smtp2go.com
SMTP_PORT=587
SMTP_USER=your-smtp2go-username
SMTP_PASSWORD=your-smtp2go-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
```

### For Production Scale: Amazon SES

[Amazon SES](https://aws.amazon.com/ses/) offers the lowest cost at scale:

**Pricing:** $0.10 per 1,000 emails (no free tier)

**Setup:**
```bash
# .env for Amazon SES
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-ses-smtp-username
SMTP_PASSWORD=your-ses-smtp-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
```

**Note:** SES requires domain verification and starts in sandbox mode (can only send to verified addresses). Production access requires requesting removal from sandbox.

### Provider Selection Guide

```mermaid
flowchart TD
    A[Need SMTP Provider] --> B{Budget?}
    B -->|Free| C{Volume?}
    B -->|Paid| D{Scale?}

    C -->|< 3,000/month| E[✅ Resend]
    C -->|< 1,000/month| F[✅ SMTP2GO]
    C -->|> 3,000/month| G[Consider paid]

    D -->|High volume| H[✅ Amazon SES<br/>$0.10/1,000]
    D -->|Moderate| I[✅ Resend Pro<br/>$20/month]

    style E fill:#10b981,color:#fff
    style F fill:#10b981,color:#fff
    style H fill:#f59e0b,color:#fff
    style I fill:#3b82f6,color:#fff
```

### Important: SendGrid No Longer Free

> ⚠️ **Warning:** SendGrid retired its free tier on July 26, 2025. New accounts only get a 60-day trial. Existing documentation or tutorials referencing SendGrid's free tier are outdated.

If you see old tutorials recommending SendGrid for free email, they are no longer accurate. Use Resend or SMTP2GO instead.

---

## Troubleshooting

### Common Issues

#### "Verification link has expired"

**Cause:** Token older than 24 hours.

**Solution:** Click "Resend email" in user menu to get new link.

---

#### "Please wait N seconds before requesting another email"

**Cause:** Rate limit hit.

**Solution:** Wait for cooldown (60 seconds) before retrying.

---

#### Email not received

**Checklist:**
1. Check spam/junk folder
2. In dev mode: Check console logs for email content
3. Verify SMTP credentials in production
4. Check SMTP server logs

---

#### Verification page shows error immediately

**Possible causes:**
- Token already used
- Token expired
- Malformed URL (token parameter missing)

**Solution:** Request new verification email from user menu.

---

### Debug Logging

Enable debug logging to troubleshoot:

```python
# In backend, set logging level
import logging
logging.getLogger("app.services.email_service").setLevel(logging.DEBUG)
logging.getLogger("app.services.verification_service").setLevel(logging.DEBUG)
```

---

## Related Documentation

- [OAuth Implementation Plan](./oauth-implementation-plan.md) - Full authentication system
- [OAuth Technical Details](./oauth-technical-details.md) - OAuth provider setup
- [OAuth Setup Guide](./oauth-setup-guide.md) - Provider configuration

---

## Changelog

| Date | Change |
|------|--------|
| 2025-01-12 | Added SMTP provider recommendations (Resend, SMTP2GO, Amazon SES) |
| 2025-01-12 | Initial implementation (Issue #82) |
