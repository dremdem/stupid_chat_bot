import { useState, useCallback } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { sendAdminReport } from '../../services/adminApi'
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

  // Report form state
  const [reportEmail, setReportEmail] = useState('')
  const [reportDays, setReportDays] = useState(7)
  const [sendToAllAdmins, setSendToAllAdmins] = useState(false)
  const [sendingReport, setSendingReport] = useState(false)
  const [reportMessage, setReportMessage] = useState(null)

  const handleSendReport = useCallback(async () => {
    setSendingReport(true)
    setReportMessage(null)

    try {
      const result = await sendAdminReport({
        email: sendToAllAdmins ? undefined : reportEmail,
        days: reportDays,
        allAdmins: sendToAllAdmins,
      })

      setReportMessage({
        type: result.success ? 'success' : 'error',
        text: result.message,
      })

      if (result.success) {
        setReportEmail('')
      }
    } catch (err) {
      setReportMessage({
        type: 'error',
        text: err.message || 'Failed to send report',
      })
    } finally {
      setSendingReport(false)
    }
  }, [reportEmail, reportDays, sendToAllAdmins])

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

        <section className="report-section">
          <h2>Email Report</h2>
          <p className="section-description">
            Send an activity report via email with summary statistics.
          </p>

          <div className="report-form">
            <div className="form-row">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={sendToAllAdmins}
                  onChange={e => setSendToAllAdmins(e.target.checked)}
                />
                Send to all admins
              </label>
            </div>

            {!sendToAllAdmins && (
              <div className="form-row">
                <label htmlFor="report-email">Recipient Email</label>
                <input
                  id="report-email"
                  type="email"
                  value={reportEmail}
                  onChange={e => setReportEmail(e.target.value)}
                  placeholder="user@example.com"
                  className="form-input"
                />
              </div>
            )}

            <div className="form-row">
              <label htmlFor="report-days">Report Period</label>
              <select
                id="report-days"
                value={reportDays}
                onChange={e => setReportDays(Number(e.target.value))}
                className="form-select"
              >
                <option value={7}>Last 7 days</option>
                <option value={14}>Last 14 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
              </select>
            </div>

            {reportMessage && (
              <div className={`report-message ${reportMessage.type}`}>{reportMessage.text}</div>
            )}

            <button
              className="btn-send-report"
              onClick={handleSendReport}
              disabled={sendingReport || (!sendToAllAdmins && !reportEmail)}
            >
              {sendingReport ? 'Sending...' : 'Send Report'}
            </button>
          </div>
        </section>
      </main>

      {selectedUser && (
        <UserMessagesModal user={selectedUser} onClose={() => setSelectedUser(null)} />
      )}
    </div>
  )
}

export default AdminStats
