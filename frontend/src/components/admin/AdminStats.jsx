import { useState, useCallback, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import {
  sendAdminReport,
  getReportSchedule,
  updateReportSchedule,
  getReportSubscribers,
} from '../../services/adminApi'
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

  // Schedule state
  const [schedule, setSchedule] = useState(null)
  const [scheduleEnabled, setScheduleEnabled] = useState(false)
  const [scheduleType, setScheduleType] = useState('weekly')
  const [dayOfWeek, setDayOfWeek] = useState('mon')
  const [scheduleHour, setScheduleHour] = useState(9)
  const [scheduleMinute, setScheduleMinute] = useState(0)
  const [savingSchedule, setSavingSchedule] = useState(false)
  const [scheduleMessage, setScheduleMessage] = useState(null)
  const [subscribers, setSubscribers] = useState([])
  const [loadingSubscribers, setLoadingSubscribers] = useState(false)

  // Load schedule and subscribers on mount
  useEffect(() => {
    const loadScheduleData = async () => {
      try {
        const [scheduleData, subscribersData] = await Promise.all([
          getReportSchedule(),
          getReportSubscribers(),
        ])
        setSchedule(scheduleData)
        setScheduleEnabled(scheduleData.enabled)
        setScheduleType(scheduleData.schedule_type || 'weekly')
        setDayOfWeek(scheduleData.day_of_week || 'mon')
        setScheduleHour(scheduleData.hour ?? 9)
        setScheduleMinute(scheduleData.minute ?? 0)
        setSubscribers(subscribersData.subscribers || [])
      } catch (err) {
        console.error('Failed to load schedule:', err)
      }
    }
    loadScheduleData()
  }, [])

  const handleSaveSchedule = useCallback(async () => {
    setSavingSchedule(true)
    setScheduleMessage(null)

    try {
      const result = await updateReportSchedule({
        enabled: scheduleEnabled,
        schedule_type: scheduleType,
        day_of_week: dayOfWeek,
        hour: scheduleHour,
        minute: scheduleMinute,
      })

      setScheduleMessage({
        type: result.success ? 'success' : 'error',
        text: result.message,
      })

      if (result.schedule) {
        setSchedule(result.schedule)
      }

      // Refresh subscribers
      const subscribersData = await getReportSubscribers()
      setSubscribers(subscribersData.subscribers || [])
    } catch (err) {
      setScheduleMessage({
        type: 'error',
        text: err.message || 'Failed to save schedule',
      })
    } finally {
      setSavingSchedule(false)
    }
  }, [scheduleEnabled, scheduleType, dayOfWeek, scheduleHour, scheduleMinute])

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
          <h2>Scheduled Reports</h2>
          <p className="section-description">
            Configure automatic report delivery to subscribed users.
          </p>

          <div className="report-form">
            <div className="form-row">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={scheduleEnabled}
                  onChange={e => setScheduleEnabled(e.target.checked)}
                />
                Enable scheduled reports
              </label>
            </div>

            {scheduleEnabled && (
              <>
                <div className="form-row">
                  <label htmlFor="schedule-type">Schedule Type</label>
                  <select
                    id="schedule-type"
                    value={scheduleType}
                    onChange={e => setScheduleType(e.target.value)}
                    className="form-select"
                  >
                    <option value="weekly">Weekly</option>
                    <option value="daily">Daily</option>
                  </select>
                </div>

                {scheduleType === 'weekly' && (
                  <div className="form-row">
                    <label htmlFor="day-of-week">Day of Week</label>
                    <select
                      id="day-of-week"
                      value={dayOfWeek}
                      onChange={e => setDayOfWeek(e.target.value)}
                      className="form-select"
                    >
                      <option value="mon">Monday</option>
                      <option value="tue">Tuesday</option>
                      <option value="wed">Wednesday</option>
                      <option value="thu">Thursday</option>
                      <option value="fri">Friday</option>
                      <option value="sat">Saturday</option>
                      <option value="sun">Sunday</option>
                    </select>
                  </div>
                )}

                <div className="form-row">
                  <label htmlFor="schedule-time">Time (UTC)</label>
                  <div className="time-inputs">
                    <select
                      id="schedule-hour"
                      value={scheduleHour}
                      onChange={e => setScheduleHour(Number(e.target.value))}
                      className="form-select time-select"
                    >
                      {[...Array(24)].map((_, i) => (
                        <option key={i} value={i}>
                          {i.toString().padStart(2, '0')}
                        </option>
                      ))}
                    </select>
                    <span className="time-separator">:</span>
                    <select
                      id="schedule-minute"
                      value={scheduleMinute}
                      onChange={e => setScheduleMinute(Number(e.target.value))}
                      className="form-select time-select"
                    >
                      {[0, 15, 30, 45].map(m => (
                        <option key={m} value={m}>
                          {m.toString().padStart(2, '0')}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </>
            )}

            {subscribers.length > 0 && (
              <div className="subscribers-info">
                <span className="subscriber-count">{subscribers.length} subscriber(s):</span>
                <span className="subscriber-list">
                  {subscribers.map(s => s.display_name || s.email).join(', ')}
                </span>
              </div>
            )}

            {subscribers.length === 0 && scheduleEnabled && (
              <div className="subscribers-info warning">
                No users have opted in to receive reports yet.
              </div>
            )}

            {schedule?.next_run && scheduleEnabled && (
              <div className="next-run-info">
                Next run: {new Date(schedule.next_run).toLocaleString()}
              </div>
            )}

            {scheduleMessage && (
              <div className={`report-message ${scheduleMessage.type}`}>{scheduleMessage.text}</div>
            )}

            <button
              className="btn-send-report"
              onClick={handleSaveSchedule}
              disabled={savingSchedule}
            >
              {savingSchedule ? 'Saving...' : 'Save Schedule'}
            </button>
          </div>
        </section>

        <section className="report-section">
          <h2>Send Report Now</h2>
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
