import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import StatsOverview from './StatsOverview'
import ActivityChart from './ActivityChart'
import TopUsersTable from './TopUsersTable'
import UserMessagesModal from './UserMessagesModal'
import './AdminStats.css'

/**
 * AdminStats component - main statistics dashboard page
 */
function AdminStats() {
  const { user, isLoading } = useAuth()
  const [selectedUser, setSelectedUser] = useState(null)

  // Show loading state
  if (isLoading) {
    return (
      <div className="admin-stats">
        <div className="admin-loading">Loading...</div>
      </div>
    )
  }

  // Check admin access
  if (!user?.is_admin) {
    return (
      <div className="admin-stats">
        <div className="access-denied">
          <h2>Access Denied</h2>
          <p>You need admin privileges to access this page.</p>
          <a href="/" className="back-link">
            Back to Chat
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="admin-stats">
      <header className="admin-header">
        <div className="header-content">
          <h1>Statistics Dashboard</h1>
          <p className="header-subtitle">Monitor user activity and engagement</p>
        </div>
        <nav className="admin-nav">
          <a href="/admin/users" className="nav-link">
            User Management
          </a>
          <a href="/" className="nav-link">
            Back to Chat
          </a>
        </nav>
      </header>

      <main className="admin-main">
        <StatsOverview />
        <ActivityChart />
        <TopUsersTable onViewMessages={setSelectedUser} />
      </main>

      {selectedUser && (
        <UserMessagesModal user={selectedUser} onClose={() => setSelectedUser(null)} />
      )}
    </div>
  )
}

export default AdminStats
