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
