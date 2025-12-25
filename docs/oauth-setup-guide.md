# OAuth Provider Setup Guide

This guide explains how to obtain OAuth credentials for Google, GitHub, and Facebook authentication.

## Table of Contents

- [Google OAuth Setup](#google-oauth-setup)
- [GitHub OAuth Setup](#github-oauth-setup)
- [Facebook OAuth Setup](#facebook-oauth-setup)
- [JWT Secret Key](#jwt-secret-key)
- [Environment Variables Summary](#environment-variables-summary)

---

## Google OAuth Setup

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** → **New Project**
3. Enter a project name (e.g., "Stupid Chat Bot") and click **Create**

### Step 2: Configure OAuth Consent Screen

1. In the left sidebar, go to **APIs & Services** → **OAuth consent screen**
2. Select **External** (for public apps) or **Internal** (for organization only)
3. Fill in the required fields:
   - **App name**: Stupid Chat Bot
   - **User support email**: Your email
   - **Developer contact email**: Your email
4. Click **Save and Continue**
5. On **Scopes** page, click **Add or Remove Scopes**:
   - Select `email` and `profile` (or `openid`, `email`, `profile`)
   - Click **Update** → **Save and Continue**
6. On **Test users** page (if External), add your email for testing
7. Click **Save and Continue** → **Back to Dashboard**

### Step 3: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Select **Web application**
4. Configure:
   - **Name**: Stupid Chat Bot Web Client
   - **Authorized JavaScript origins**:
     - `http://localhost:5173` (development)
     - `https://your-domain.com` (production)
   - **Authorized redirect URIs**:
     - `http://localhost:8000/api/auth/google/callback` (development)
     - `https://your-api-domain.com/api/auth/google/callback` (production)
5. Click **Create**
6. Copy the **Client ID** and **Client Secret**

### Step 4: Add to Environment

```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

---

## GitHub OAuth Setup

### Step 1: Register a New OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click **OAuth Apps** → **New OAuth App**
3. Fill in the form:
   - **Application name**: Stupid Chat Bot
   - **Homepage URL**: `http://localhost:5173` (or your production URL)
   - **Authorization callback URL**: `http://localhost:8000/api/auth/github/callback`
4. Click **Register application**

### Step 2: Get Credentials

1. On the app page, you'll see the **Client ID**
2. Click **Generate a new client secret**
3. Copy the secret immediately (it won't be shown again)

### Step 3: Add to Environment

```bash
GITHUB_CLIENT_ID=your-client-id
GITHUB_CLIENT_SECRET=your-client-secret
```

### Production Setup

For production, update the callback URL:
1. Go to your OAuth App settings
2. Update **Authorization callback URL** to `https://your-api-domain.com/api/auth/github/callback`

---

## Facebook OAuth Setup

### Step 1: Create a Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click **My Apps** → **Create App**
3. Select **Consumer** or **None** (for custom setup)
4. Enter app name: "Stupid Chat Bot"
5. Click **Create App**

### Step 2: Add Facebook Login Product

1. On the app dashboard, find **Add Products**
2. Find **Facebook Login** and click **Set Up**
3. Select **Web**
4. Enter your site URL: `http://localhost:5173`
5. Click **Save** → **Continue**

### Step 3: Configure OAuth Settings

1. In the left sidebar, go to **Facebook Login** → **Settings**
2. Add to **Valid OAuth Redirect URIs**:
   - `http://localhost:8000/api/auth/facebook/callback` (development)
   - `https://your-api-domain.com/api/auth/facebook/callback` (production)
3. Click **Save Changes**

### Step 4: Get Credentials

1. Go to **Settings** → **Basic** in the left sidebar
2. Copy the **App ID** (this is your Client ID)
3. Click **Show** next to **App Secret** and copy it

### Step 5: Add to Environment

```bash
FACEBOOK_CLIENT_ID=your-app-id
FACEBOOK_CLIENT_SECRET=your-app-secret
```

### App Review (Production)

For production with public users:
1. Go to **App Review** → **Permissions and Features**
2. Request access to `email` and `public_profile`
3. Submit for review (required for non-test users)

---

## JWT Secret Key

The JWT secret key is used to sign authentication tokens. **It must be kept secret and changed in production.**

### Generate a Secure Key

Using Python:
```python
import secrets
print(secrets.token_urlsafe(32))
```

Using OpenSSL:
```bash
openssl rand -base64 32
```

Using Node.js:
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

### Add to Environment

```bash
JWT_SECRET_KEY=your-generated-secret-key
```

**Security Notes:**
- Never commit the secret key to version control
- Use different keys for development and production
- Rotate keys periodically in production
- Minimum recommended length: 32 characters

---

## Environment Variables Summary

Create a `.env` file in the `backend/` directory:

```bash
# ===========================================
# OAuth Provider Credentials
# ===========================================

# Google OAuth (https://console.cloud.google.com/)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# GitHub OAuth (https://github.com/settings/developers)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Facebook OAuth (https://developers.facebook.com/)
FACEBOOK_CLIENT_ID=your-facebook-app-id
FACEBOOK_CLIENT_SECRET=your-facebook-app-secret

# ===========================================
# JWT Configuration
# ===========================================

# Secret key for signing JWT tokens (MUST change in production!)
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=change-me-in-production

# Token expiration (optional, defaults shown)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ===========================================
# Admin Bootstrap (Optional)
# ===========================================

# User with this email will be auto-promoted to admin on first login
INITIAL_ADMIN_EMAIL=admin@example.com

# ===========================================
# Frontend URL
# ===========================================

# URL to redirect after OAuth login
FRONTEND_URL=http://localhost:5173

# ===========================================
# Backend URL (for Docker environments)
# ===========================================

# External URL for OAuth callbacks (required when running in Docker)
# This ensures OAuth callbacks use localhost instead of Docker internal hostname
BACKEND_URL=http://localhost:8000
```

### Minimum Required for Each Provider

| Provider | Required Variables |
|----------|-------------------|
| Google | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` |
| GitHub | `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` |
| Facebook | `FACEBOOK_CLIENT_ID`, `FACEBOOK_CLIENT_SECRET` |
| All | `JWT_SECRET_KEY` (for token signing) |

You only need to configure the providers you want to use. Unconfigured providers will be disabled automatically.

---

## User Roles and Message Limits

After setting up OAuth, users can authenticate and get higher message limits.

### Default Message Limits by Role

| Role | Message Limit | Description |
|------|---------------|-------------|
| `anonymous` | 5 messages | Users who haven't logged in |
| `user` | 50 messages | Authenticated users (default after OAuth login) |
| `unlimited` | Unlimited | Users manually upgraded by admin |
| `admin` | Unlimited | Admin users |

### How It Works

1. **Anonymous users**: When someone visits the chat without logging in, they get a `user_id` cookie and can send 5 messages.

2. **After OAuth login**: The user is created in the database with role `user` and gets 50 messages. The WebSocket connection recognizes the JWT token and applies the authenticated user's limits.

3. **Admin override**: Admins can set custom limits per user via the database. If `message_limit` is set on a user record, it overrides the role default.

### Initial Admin Setup

To auto-promote a user to admin on first login, set:
```bash
INITIAL_ADMIN_EMAIL=your-email@example.com
```

When a user with this email logs in via OAuth, they'll automatically be promoted to admin role.

---

## Troubleshooting

### "redirect_uri_mismatch" Error
- Ensure the callback URL in your OAuth app settings exactly matches `http://localhost:8000/api/auth/{provider}/callback`
- Check for trailing slashes - they must match exactly

### "invalid_client" Error
- Verify Client ID and Client Secret are correct
- Check there are no extra spaces in your `.env` file

### Cookies Not Being Set
- Ensure `FRONTEND_URL` matches where your frontend is hosted
- In production, set `COOKIE_SECURE=True` and use HTTPS

### OAuth Buttons Disabled
- Check `/auth/providers` endpoint returns the expected providers
- Verify credentials are set in `.env` and the app was restarted

---

## Related Documents

- [OAuth Implementation Plan](./oauth-implementation-plan.md)
- [Main README](../README.md)
