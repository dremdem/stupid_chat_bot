/**
 * Sessions API service for REST endpoints
 *
 * All requests include credentials to send/receive cookies for user identification.
 */

// Use relative URL - works in both dev (Vite proxy) and prod (nginx proxy)
const API_BASE = '/api/sessions'

/**
 * Default fetch options with credentials
 * @param {Object} options - Additional fetch options
 * @returns {Object} Merged options with credentials
 */
function fetchOptions(options = {}) {
  return {
    ...options,
    credentials: 'include', // Send cookies with requests
  }
}

/**
 * Fetch all sessions for the current user
 * @param {number} limit - Max sessions to return
 * @param {number} offset - Pagination offset
 * @returns {Promise<{sessions: Array, total: number}>}
 */
export async function fetchSessions(limit = 50, offset = 0) {
  const response = await fetch(`${API_BASE}?limit=${limit}&offset=${offset}`, fetchOptions())
  if (!response.ok) {
    throw new Error('Failed to fetch sessions')
  }
  return response.json()
}

/**
 * Create a new session for the current user
 * @param {string} title - Session title
 * @returns {Promise<Object>} Created session
 */
export async function createSession(title = 'New Chat') {
  const response = await fetch(
    API_BASE,
    fetchOptions({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    })
  )
  if (!response.ok) {
    throw new Error('Failed to create session')
  }
  return response.json()
}

/**
 * Get a specific session for the current user
 * @param {string} sessionId - Session UUID
 * @returns {Promise<Object>} Session details
 */
export async function getSession(sessionId) {
  const response = await fetch(`${API_BASE}/${sessionId}`, fetchOptions())
  if (!response.ok) {
    throw new Error('Failed to get session')
  }
  return response.json()
}

/**
 * Update session title for the current user
 * @param {string} sessionId - Session UUID
 * @param {string} title - New title
 * @returns {Promise<Object>} Updated session
 */
export async function updateSession(sessionId, title) {
  const response = await fetch(
    `${API_BASE}/${sessionId}`,
    fetchOptions({
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    })
  )
  if (!response.ok) {
    throw new Error('Failed to update session')
  }
  return response.json()
}

/**
 * Delete a session for the current user
 * @param {string} sessionId - Session UUID
 * @returns {Promise<void>}
 */
export async function deleteSession(sessionId) {
  const response = await fetch(
    `${API_BASE}/${sessionId}`,
    fetchOptions({
      method: 'DELETE',
    })
  )
  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || 'Failed to delete session')
  }
}

/**
 * Get session history for the current user
 * @param {string} sessionId - Session UUID
 * @param {number} limit - Max messages to return
 * @returns {Promise<{messages: Array, count: number}>}
 */
export async function getSessionHistory(sessionId, limit = 50) {
  const response = await fetch(`${API_BASE}/${sessionId}/history?limit=${limit}`, fetchOptions())
  if (!response.ok) {
    throw new Error('Failed to get session history')
  }
  return response.json()
}

/**
 * Initialize user identity by making a request to trigger cookie creation.
 * This should be called before establishing WebSocket connection.
 * @returns {Promise<void>}
 */
export async function initializeUser() {
  // Make a lightweight request to trigger cookie creation
  // The sessions endpoint will set the user cookie if not present
  await fetchSessions(1, 0)
}
