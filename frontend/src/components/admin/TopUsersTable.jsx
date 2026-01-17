import { useState, useEffect, useCallback } from 'react'
import PropTypes from 'prop-types'
import { getTopUsers } from '../../services/adminApi'
import RoleBadge from './RoleBadge'
import './TopUsersTable.css'

/**
 * TopUsersTable component - displays most active users
 */
function TopUsersTable({ onViewMessages }) {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [days, setDays] = useState(30)
  const [limit, setLimit] = useState(10)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await getTopUsers({ days, limit })
      setUsers(response.users)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [days, limit])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const formatDate = dateStr => {
    if (!dateStr) return 'Never'
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatRelativeTime = dateStr => {
    if (!dateStr) return 'Never'
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return formatDate(dateStr)
  }

  return (
    <div className="top-users-table">
      <div className="table-header">
        <h3>Top Active Users</h3>
        <div className="table-controls">
          <select value={days} onChange={e => setDays(Number(e.target.value))}>
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>
          <select value={limit} onChange={e => setLimit(Number(e.target.value))}>
            <option value={5}>Top 5</option>
            <option value={10}>Top 10</option>
            <option value={20}>Top 20</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="table-loading">Loading top users...</div>
      ) : error ? (
        <div className="table-error">
          <p>Failed to load users: {error}</p>
          <button onClick={fetchData}>Retry</button>
        </div>
      ) : users.length === 0 ? (
        <div className="table-empty">No active users in this period</div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>User</th>
                <th>Role</th>
                <th>Messages</th>
                <th>Last Active</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user, index) => (
                <tr key={user.id}>
                  <td className="rank-cell">
                    {index < 3 ? (
                      <span className={`rank-badge rank-${index + 1}`}>
                        {index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'}
                      </span>
                    ) : (
                      <span className="rank-number">{index + 1}</span>
                    )}
                  </td>
                  <td className="user-cell">
                    <div className="user-info">
                      <span className="user-name">
                        {user.display_name || user.email || 'Anonymous'}
                      </span>
                      {user.email && user.display_name && (
                        <span className="user-email">{user.email}</span>
                      )}
                    </div>
                  </td>
                  <td>
                    <RoleBadge role={user.role} />
                  </td>
                  <td className="messages-cell">
                    <span className="message-count">{user.message_count.toLocaleString()}</span>
                  </td>
                  <td className="date-cell" title={formatDate(user.last_message_at)}>
                    {formatRelativeTime(user.last_message_at)}
                  </td>
                  <td className="actions-cell">
                    <button
                      className="view-messages-btn"
                      onClick={() => onViewMessages && onViewMessages(user)}
                      title="View messages"
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

TopUsersTable.propTypes = {
  onViewMessages: PropTypes.func,
}

export default TopUsersTable
