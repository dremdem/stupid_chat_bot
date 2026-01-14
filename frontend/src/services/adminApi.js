/**
 * Admin API service for user management.
 */

const API_BASE = '/api/admin'

/**
 * Helper to handle API responses.
 * @param {Response} response - Fetch response
 * @returns {Promise<object>} Parsed JSON response
 * @throws {Error} If response is not ok
 */
async function handleResponse(response) {
  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Not authenticated')
    }
    if (response.status === 403) {
      throw new Error('Admin access required')
    }
    const data = await response.json().catch(() => ({}))
    throw new Error(data.detail || `Request failed with status ${response.status}`)
  }
  return response.json()
}

/**
 * List users with pagination and filtering.
 * @param {object} options - Query options
 * @param {number} [options.page=1] - Page number
 * @param {number} [options.pageSize=20] - Items per page
 * @param {string} [options.search] - Search by email or name
 * @param {string} [options.role] - Filter by role (user, unlimited, admin)
 * @param {boolean} [options.blocked] - Filter by blocked status
 * @returns {Promise<{users: object[], total: number, page: number, page_size: number, total_pages: number}>}
 */
export async function listUsers({ page = 1, pageSize = 20, search, role, blocked } = {}) {
  const params = new URLSearchParams()
  params.append('page', page)
  params.append('page_size', pageSize)
  if (search) params.append('search', search)
  if (role) params.append('role', role)
  if (blocked !== undefined) params.append('blocked', blocked)

  const response = await fetch(`${API_BASE}/users?${params}`, {
    credentials: 'include',
  })

  return handleResponse(response)
}

/**
 * Get detailed information about a user.
 * @param {string} userId - User ID
 * @returns {Promise<object>} User details
 */
export async function getUser(userId) {
  const response = await fetch(`${API_BASE}/users/${userId}`, {
    credentials: 'include',
  })

  return handleResponse(response)
}

/**
 * Update user role.
 * @param {string} userId - User ID
 * @param {string} role - New role (user, unlimited, admin)
 * @returns {Promise<{success: boolean, message: string, user: object}>}
 */
export async function updateUserRole(userId, role) {
  const response = await fetch(`${API_BASE}/users/${userId}/role`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ role }),
  })

  return handleResponse(response)
}

/**
 * Block or unblock a user.
 * @param {string} userId - User ID
 * @param {boolean} isBlocked - Whether to block the user
 * @returns {Promise<{success: boolean, message: string, user: object}>}
 */
export async function updateUserBlock(userId, isBlocked) {
  const response = await fetch(`${API_BASE}/users/${userId}/block`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ is_blocked: isBlocked }),
  })

  return handleResponse(response)
}

/**
 * Update user message limit.
 * @param {string} userId - User ID
 * @param {number|null} messageLimit - New message limit (null for default)
 * @returns {Promise<{success: boolean, message: string, user: object}>}
 */
export async function updateUserLimit(userId, messageLimit) {
  const response = await fetch(`${API_BASE}/users/${userId}/limit`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ message_limit: messageLimit }),
  })

  return handleResponse(response)
}
