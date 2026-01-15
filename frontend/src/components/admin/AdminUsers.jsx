import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { listUsers } from '../../services/adminApi'
import RoleBadge from './RoleBadge'
import BlockedBadge from './BlockedBadge'
import UserEditModal from './UserEditModal'
import './AdminUsers.css'

function AdminUsers() {
  const { user, logout } = useAuth()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [blockedFilter, setBlockedFilter] = useState('')
  const [selectedUser, setSelectedUser] = useState(null)
  const [searchInput, setSearchInput] = useState('')

  const pageSize = 20

  const fetchUsers = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const params = { page, pageSize }
      if (search) params.search = search
      if (roleFilter) params.role = roleFilter
      if (blockedFilter !== '') params.blocked = blockedFilter === 'true'

      const data = await listUsers(params)
      setUsers(data.users)
      setTotalPages(data.total_pages)
      setTotal(data.total)
    } catch (err) {
      if (err.message === 'Not authenticated' || err.message === 'Admin access required') {
        setError('You must be an admin to access this page')
      } else {
        setError(err.message)
      }
    } finally {
      setLoading(false)
    }
  }, [page, search, roleFilter, blockedFilter])

  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  const handleSearch = e => {
    e.preventDefault()
    setSearch(searchInput)
    setPage(1)
  }

  const handleUserUpdate = updatedUser => {
    setUsers(prev =>
      prev.map(u =>
        u.id === updatedUser.id
          ? {
              ...u,
              ...updatedUser,
            }
          : u
      )
    )
  }

  const handleBackToChat = () => {
    window.location.href = '/'
  }

  // Check if current user is admin
  if (!user?.is_admin) {
    return (
      <div className="admin-container">
        <div className="admin-error">
          <h1>Access Denied</h1>
          <p>You must be an admin to access this page.</p>
          <button className="btn btn-primary" onClick={handleBackToChat}>
            Back to Chat
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="admin-container">
      <header className="admin-header">
        <div className="admin-header-left">
          <button className="btn btn-back" onClick={handleBackToChat}>
            &larr; Back to Chat
          </button>
          <h1>User Management</h1>
        </div>
        <div className="admin-header-right">
          <span className="admin-user">
            {user.email} <RoleBadge role={user.role} />
          </span>
          <button className="btn btn-secondary" onClick={logout}>
            Sign Out
          </button>
        </div>
      </header>

      <div className="admin-content">
        <div className="admin-toolbar">
          <form className="search-form" onSubmit={handleSearch}>
            <input
              type="text"
              placeholder="Search by email or name..."
              value={searchInput}
              onChange={e => setSearchInput(e.target.value)}
              className="search-input"
            />
            <button type="submit" className="btn btn-primary">
              Search
            </button>
          </form>

          <div className="filters">
            <select
              value={roleFilter}
              onChange={e => {
                setRoleFilter(e.target.value)
                setPage(1)
              }}
              className="filter-select"
            >
              <option value="">All Roles</option>
              <option value="user">User</option>
              <option value="unlimited">Unlimited</option>
              <option value="admin">Admin</option>
            </select>

            <select
              value={blockedFilter}
              onChange={e => {
                setBlockedFilter(e.target.value)
                setPage(1)
              }}
              className="filter-select"
            >
              <option value="">All Status</option>
              <option value="false">Active</option>
              <option value="true">Blocked</option>
            </select>
          </div>
        </div>

        {error && <div className="error-banner">{error}</div>}

        {loading ? (
          <div className="loading">Loading users...</div>
        ) : (
          <>
            <div className="users-summary">
              Showing {users.length} of {total} users
            </div>

            <div className="users-table-container">
              <table className="users-table">
                <thead>
                  <tr>
                    <th>Email</th>
                    <th>Name</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Messages</th>
                    <th>Joined</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id} className={u.is_blocked ? 'blocked' : ''}>
                      <td>
                        <span className="email">
                          {u.email || 'N/A'}
                          {!u.is_email_verified && u.email && (
                            <span className="unverified" title="Email not verified">
                              (unverified)
                            </span>
                          )}
                          <BlockedBadge isBlocked={u.is_blocked} />
                        </span>
                      </td>
                      <td>{u.display_name || '-'}</td>
                      <td>
                        <RoleBadge role={u.role} />
                      </td>
                      <td>
                        <span className={`status ${u.is_blocked ? 'blocked' : 'active'}`}>
                          {u.is_blocked ? 'Blocked' : 'Active'}
                        </span>
                      </td>
                      <td>{u.message_count}</td>
                      <td>{new Date(u.created_at).toLocaleDateString()}</td>
                      <td>
                        <button
                          className="btn btn-small btn-secondary"
                          onClick={() => setSelectedUser(u)}
                        >
                          Edit
                        </button>
                      </td>
                    </tr>
                  ))}
                  {users.length === 0 && (
                    <tr>
                      <td colSpan="7" className="no-data">
                        No users found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {totalPages > 1 && (
              <div className="pagination">
                <button
                  className="btn btn-secondary"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </button>
                <span className="page-info">
                  Page {page} of {totalPages}
                </span>
                <button
                  className="btn btn-secondary"
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {selectedUser && (
        <UserEditModal
          user={selectedUser}
          onClose={() => setSelectedUser(null)}
          onUpdate={handleUserUpdate}
        />
      )}
    </div>
  )
}

export default AdminUsers
