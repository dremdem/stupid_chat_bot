/**
 * Authentication API service for OAuth and user management.
 */

const API_BASE = '/api'

/**
 * Get list of configured OAuth providers.
 * @returns {Promise<string[]>} List of provider names (google, github, facebook)
 */
export async function getProviders() {
  const response = await fetch(`${API_BASE}/auth/providers`, {
    credentials: 'include',
  })

  if (!response.ok) {
    throw new Error('Failed to fetch providers')
  }

  const data = await response.json()
  return data.providers
}

/**
 * Initiate OAuth login flow.
 * @param {string} provider - OAuth provider name (google, github, facebook)
 * @param {string} [redirectUrl] - Optional URL to redirect after login
 * @returns {Promise<string>} Authorization URL to redirect to
 */
export async function initiateOAuthLogin(provider, redirectUrl = null) {
  const params = new URLSearchParams()
  if (redirectUrl) {
    params.append('redirect_url', redirectUrl)
  }

  const url = `${API_BASE}/auth/${provider}${params.toString() ? `?${params}` : ''}`
  const response = await fetch(url, {
    credentials: 'include',
  })

  if (!response.ok) {
    throw new Error(`Failed to initiate ${provider} login`)
  }

  const data = await response.json()
  return data.authorization_url
}

/**
 * Refresh access token using refresh token (stored in HTTP-only cookie).
 * @returns {Promise<{user: object, access_token: string}>}
 */
export async function refreshTokens() {
  const response = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
  })

  if (!response.ok) {
    if (response.status === 401) {
      return null // Not authenticated
    }
    throw new Error('Failed to refresh tokens')
  }

  return response.json()
}

/**
 * Logout user (invalidates refresh token).
 * @returns {Promise<void>}
 */
export async function logout() {
  const response = await fetch(`${API_BASE}/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  })

  if (!response.ok) {
    throw new Error('Failed to logout')
  }
}

/**
 * Get current authenticated user.
 * @returns {Promise<{user: object|null, authenticated: boolean}>}
 */
export async function getCurrentUser() {
  const response = await fetch(`${API_BASE}/auth/me`, {
    credentials: 'include',
  })

  if (!response.ok) {
    return { user: null, authenticated: false }
  }

  return response.json()
}

/**
 * Register a new user with email and password.
 * @param {string} email - User's email address
 * @param {string} password - User's password (min 8 chars, must have letter and number)
 * @param {string} [displayName] - Optional display name
 * @returns {Promise<{user: object, access_token: string}>}
 */
export async function register(email, password, displayName = null) {
  const body = { email, password }
  if (displayName) {
    body.display_name = displayName
  }

  const response = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || 'Registration failed')
  }

  return response.json()
}

/**
 * Login with email and password.
 * @param {string} email - User's email address
 * @param {string} password - User's password
 * @returns {Promise<{user: object, access_token: string}>}
 */
export async function login(email, password) {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ email, password }),
  })

  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || 'Login failed')
  }

  return response.json()
}

/**
 * Get all available authentication methods.
 * @returns {Promise<{oauth_providers: string[], email_password_enabled: boolean}>}
 */
export async function getAuthMethods() {
  const response = await fetch(`${API_BASE}/auth/methods`, {
    credentials: 'include',
  })

  if (!response.ok) {
    throw new Error('Failed to fetch auth methods')
  }

  return response.json()
}

/**
 * Verify email using token from verification link.
 * @param {string} token - Verification token from email link
 * @returns {Promise<{success: boolean, message: string, user?: object}>}
 */
export async function verifyEmail(token) {
  const response = await fetch(`${API_BASE}/auth/verify-email`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ token }),
  })

  return response.json()
}

/**
 * Request a new verification email.
 * @returns {Promise<{success: boolean, message: string}>}
 */
export async function resendVerification() {
  const response = await fetch(`${API_BASE}/auth/resend-verification`, {
    method: 'POST',
    credentials: 'include',
  })

  if (!response.ok && response.status === 401) {
    throw new Error('Please log in to resend verification email')
  }

  return response.json()
}
