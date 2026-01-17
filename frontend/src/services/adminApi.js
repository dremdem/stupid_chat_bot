/**
 * Admin API service for user management and statistics.
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

// ============================================================================
// Statistics API
// ============================================================================

/**
 * Get summary statistics.
 * @returns {Promise<{total_users: number, active_users_7d: number, total_messages: number, messages_today: number, messages_7d: number, new_users_today: number, new_users_7d: number}>}
 */
export async function getStatsSummary() {
  const response = await fetch(`${API_BASE}/stats/summary`, {
    credentials: 'include',
  })

  return handleResponse(response)
}

/**
 * Get daily activity data for charts.
 * @param {number} [days=30] - Number of days (7-90)
 * @returns {Promise<{days: number, data: Array<{date: string, messages: number, new_users: number}>}>}
 */
export async function getDailyActivity(days = 30) {
  const response = await fetch(`${API_BASE}/stats/daily-activity?days=${days}`, {
    credentials: 'include',
  })

  return handleResponse(response)
}

/**
 * Get top active users.
 * @param {object} options - Query options
 * @param {number} [options.days=30] - Time period in days (1-365)
 * @param {number} [options.limit=10] - Number of users to return (1-50)
 * @returns {Promise<{users: object[], total: number, days: number}>}
 */
export async function getTopUsers({ days = 30, limit = 10 } = {}) {
  const params = new URLSearchParams()
  params.append('days', days)
  params.append('limit', limit)

  const response = await fetch(`${API_BASE}/stats/top-users?${params}`, {
    credentials: 'include',
  })

  return handleResponse(response)
}

/**
 * Get user message history (read-only).
 * @param {string} userId - User ID
 * @param {object} options - Query options
 * @param {number} [options.page=1] - Page number
 * @param {number} [options.pageSize=20] - Items per page
 * @returns {Promise<{user_id: string, user_email: string, user_display_name: string, messages: object[], total: number, page: number, page_size: number, total_pages: number}>}
 */
export async function getUserMessages(userId, { page = 1, pageSize = 20 } = {}) {
  const params = new URLSearchParams()
  params.append('page', page)
  params.append('page_size', pageSize)

  const response = await fetch(`${API_BASE}/stats/user-messages/${userId}?${params}`, {
    credentials: 'include',
  })

  return handleResponse(response)
}

// ============================================================================
// Reports API
// ============================================================================

/**
 * Send admin activity report via email.
 * @param {object} options - Report options
 * @param {string} [options.email] - Recipient email (required if not allAdmins)
 * @param {number} [options.days=7] - Days to include in report
 * @param {boolean} [options.allAdmins=false] - Send to all admin users
 * @returns {Promise<{success: boolean, message: string, details?: object}>}
 */
export async function sendAdminReport({ email, days = 7, allAdmins = false } = {}) {
  const response = await fetch(`${API_BASE}/reports/send`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({
      email,
      days,
      all_admins: allAdmins,
    }),
  })

  return handleResponse(response)
}
