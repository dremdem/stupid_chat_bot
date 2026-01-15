import { useState, useEffect, useCallback } from 'react'
import { getStatsSummary } from '../../services/adminApi'
import './StatsOverview.css'

/**
 * StatsOverview component - displays summary statistics cards
 */
function StatsOverview() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getStatsSummary()
      setStats(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchStats()
  }, [fetchStats])

  if (loading) {
    return (
      <div className="stats-overview">
        <div className="stats-loading">Loading statistics...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="stats-overview">
        <div className="stats-error">
          <p>Failed to load statistics: {error}</p>
          <button onClick={fetchStats}>Retry</button>
        </div>
      </div>
    )
  }

  if (!stats) return null

  const cards = [
    {
      title: 'Total Users',
      value: stats.total_users,
      subtitle: `+${stats.new_users_today} today`,
      icon: '👥',
      color: 'blue',
    },
    {
      title: 'Active Users (7d)',
      value: stats.active_users_7d,
      subtitle: 'Sent messages',
      icon: '🔥',
      color: 'orange',
    },
    {
      title: 'Total Messages',
      value: stats.total_messages,
      subtitle: `+${stats.messages_today} today`,
      icon: '💬',
      color: 'green',
    },
    {
      title: 'Messages (7d)',
      value: stats.messages_7d,
      subtitle: `${stats.new_users_7d} new users`,
      icon: '📈',
      color: 'purple',
    },
  ]

  return (
    <div className="stats-overview">
      {cards.map((card, index) => (
        <div key={index} className={`stat-card stat-card-${card.color}`}>
          <div className="stat-card-icon">{card.icon}</div>
          <div className="stat-card-content">
            <div className="stat-card-value">{card.value.toLocaleString()}</div>
            <div className="stat-card-title">{card.title}</div>
            <div className="stat-card-subtitle">{card.subtitle}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default StatsOverview
