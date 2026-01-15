import { useState, useEffect, useCallback } from 'react'
import { getDailyActivity } from '../../services/adminApi'
import './ActivityChart.css'

/**
 * ActivityChart component - displays daily activity as a bar chart
 */
function ActivityChart() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [days, setDays] = useState(30)
  const [showUsers, setShowUsers] = useState(true)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await getDailyActivity(days)
      setData(response.data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  if (loading) {
    return (
      <div className="activity-chart">
        <div className="chart-header">
          <h3>Daily Activity</h3>
        </div>
        <div className="chart-loading">Loading chart data...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="activity-chart">
        <div className="chart-header">
          <h3>Daily Activity</h3>
        </div>
        <div className="chart-error">
          <p>Failed to load chart: {error}</p>
          <button onClick={fetchData}>Retry</button>
        </div>
      </div>
    )
  }

  // Calculate max values for scaling
  const maxMessages = Math.max(...data.map(d => d.messages), 1)
  const maxUsers = Math.max(...data.map(d => d.new_users), 1)

  // Calculate totals
  const totalMessages = data.reduce((sum, d) => sum + d.messages, 0)
  const totalNewUsers = data.reduce((sum, d) => sum + d.new_users, 0)

  return (
    <div className="activity-chart">
      <div className="chart-header">
        <h3>Daily Activity</h3>
        <div className="chart-controls">
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={showUsers}
              onChange={e => setShowUsers(e.target.checked)}
            />
            Show new users
          </label>
          <select value={days} onChange={e => setDays(Number(e.target.value))}>
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </div>
      </div>

      <div className="chart-summary">
        <span className="summary-item summary-messages">
          <span className="summary-dot"></span>
          {totalMessages.toLocaleString()} messages
        </span>
        {showUsers && (
          <span className="summary-item summary-users">
            <span className="summary-dot"></span>
            {totalNewUsers.toLocaleString()} new users
          </span>
        )}
      </div>

      <div className="chart-container">
        <div className="chart-bars">
          {data.map((item, index) => {
            const messageHeight = (item.messages / maxMessages) * 100
            const userHeight = showUsers ? (item.new_users / maxUsers) * 100 : 0
            const dateObj = new Date(item.date)
            const dayLabel = dateObj.toLocaleDateString('en-US', { weekday: 'short' })
            const dateLabel = dateObj.toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
            })

            return (
              <div key={index} className="chart-bar-group" title={`${dateLabel}: ${item.messages} messages, ${item.new_users} new users`}>
                <div className="bar-container">
                  <div
                    className="bar bar-messages"
                    style={{ height: `${messageHeight}%` }}
                  >
                    {item.messages > 0 && messageHeight > 15 && (
                      <span className="bar-value">{item.messages}</span>
                    )}
                  </div>
                  {showUsers && item.new_users > 0 && (
                    <div
                      className="bar bar-users"
                      style={{ height: `${userHeight}%` }}
                    >
                      {userHeight > 15 && (
                        <span className="bar-value">{item.new_users}</span>
                      )}
                    </div>
                  )}
                </div>
                <div className="bar-label">
                  {days <= 14 ? (
                    <>
                      <span className="label-day">{dayLabel}</span>
                      <span className="label-date">{dateLabel}</span>
                    </>
                  ) : (
                    index % Math.ceil(data.length / 10) === 0 && (
                      <span className="label-date">{dateLabel}</span>
                    )
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default ActivityChart
