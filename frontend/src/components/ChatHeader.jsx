import PropTypes from 'prop-types'
import { useTheme } from '../contexts/ThemeContext'
import './ChatHeader.css'

/**
 * ChatHeader component - displays the chat title, connection status, and message limits
 */
function ChatHeader({ status, limitInfo }) {
  const { theme, toggleTheme } = useTheme()

  const getStatusColor = () => {
    switch (status) {
      case 'connected':
        return 'green'
      case 'disconnected':
      case 'failed':
        return 'red'
      case 'error':
        return 'orange'
      default:
        return 'gray'
    }
  }

  const getStatusText = () => {
    switch (status) {
      case 'connected':
        return 'Connected'
      case 'disconnected':
        return 'Disconnected'
      case 'failed':
        return 'Connection Failed'
      case 'error':
        return 'Connection Error'
      default:
        return 'Connecting...'
    }
  }

  // Get message limit display info
  const getLimitDisplay = () => {
    if (!limitInfo) return null
    if (limitInfo.is_unlimited) return null

    const remaining = limitInfo.remaining ?? 0
    const isLow = remaining <= 2 && remaining > 0
    const isExhausted = remaining === 0

    return {
      text: `${remaining}/${limitInfo.limit}`,
      className: isExhausted ? 'exhausted' : isLow ? 'low' : 'normal',
    }
  }

  const limitDisplay = getLimitDisplay()

  return (
    <div className="chat-header">
      <div className="chat-title">
        <h1>Stupid Chat Bot v.0.0.1</h1>
        <p className="chat-subtitle">A simple, straightforward chat</p>
      </div>
      <div className="header-controls">
        {limitDisplay && (
          <div className={`message-limit ${limitDisplay.className}`} title="Messages remaining">
            <span className="limit-icon">💬</span>
            <span className="limit-text">{limitDisplay.text}</span>
          </div>
        )}
        <button className="theme-toggle" onClick={toggleTheme} title="Toggle theme">
          {theme === 'light' ? '🌙' : '☀️'}
        </button>
        <div className="connection-status">
          <span className={`status-indicator ${getStatusColor()}`}></span>
          <span className="status-text">{getStatusText()}</span>
        </div>
      </div>
    </div>
  )
}

ChatHeader.propTypes = {
  status: PropTypes.string.isRequired,
  limitInfo: PropTypes.shape({
    limit: PropTypes.number,
    used: PropTypes.number,
    remaining: PropTypes.number,
    is_unlimited: PropTypes.bool,
    can_send: PropTypes.bool,
    user_role: PropTypes.string,
  }),
}

export default ChatHeader
