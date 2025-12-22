/**
 * Sessions API service for REST endpoints
 */

// Use relative URL - works in both dev (Vite proxy) and prod (nginx proxy)
const API_BASE = '/api/sessions'

/**
 * Fetch all sessions
 * @param {number} limit - Max sessions to return
 * @param {number} offset - Pagination offset
 * @returns {Promise<{sessions: Array, total: number}>}
 */
export async function fetchSessions(limit = 50, offset = 0) {
  const response = await fetch(`${API_BASE}?limit=${limit}&offset=${offset}`)
  if (!response.ok) {
    throw new Error('Failed to fetch sessions')
  }
  return response.json()
}

/**
 * Create a new session
 * @param {string} title - Session title
 * @returns {Promise<Object>} Created session
 */
export async function createSession(title = 'New Chat') {
  const response = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  })
  if (!response.ok) {
    throw new Error('Failed to create session')
  }
  return response.json()
}

/**
 * Get a specific session
 * @param {string} sessionId - Session UUID
 * @returns {Promise<Object>} Session details
 */
export async function getSession(sessionId) {
  const response = await fetch(`${API_BASE}/${sessionId}`)
  if (!response.ok) {
    throw new Error('Failed to get session')
  }
  return response.json()
}

/**
 * Update session title
 * @param {string} sessionId - Session UUID
 * @param {string} title - New title
 * @returns {Promise<Object>} Updated session
 */
export async function updateSession(sessionId, title) {
  const response = await fetch(`${API_BASE}/${sessionId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  })
  if (!response.ok) {
    throw new Error('Failed to update session')
  }
  return response.json()
}

/**
 * Delete a session
 * @param {string} sessionId - Session UUID
 * @returns {Promise<void>}
 */
export async function deleteSession(sessionId) {
  const response = await fetch(`${API_BASE}/${sessionId}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || 'Failed to delete session')
  }
}

/**
 * Get session history
 * @param {string} sessionId - Session UUID
 * @param {number} limit - Max messages to return
 * @returns {Promise<{messages: Array, count: number}>}
 */
export async function getSessionHistory(sessionId, limit = 50) {
  const response = await fetch(`${API_BASE}/${sessionId}/history?limit=${limit}`)
  if (!response.ok) {
    throw new Error('Failed to get session history')
  }
  return response.json()
}
