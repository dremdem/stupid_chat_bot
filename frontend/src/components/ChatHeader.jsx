import { useState, useRef, useEffect } from 'react'
import PropTypes from 'prop-types'
import { useTheme } from '../contexts/ThemeContext'
import { useAuth } from '../contexts/AuthContext'
import './ChatHeader.css'

/**
 * ChatHeader component - displays the chat title, connection status, and message limits
 */
function ChatHeader({ status, limitInfo, onSignInClick }) {
  const { theme, toggleTheme } = useTheme()
  const { user, isAuthenticated, logout, isLoading: authLoading } = useAuth()
  const [showUserMenu, setShowUserMenu] = useState(false)
  const userMenuRef = useRef(null)

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = event => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setShowUserMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLogout = async () => {
    setShowUserMenu(false)
    await logout()
  }

  // Get user display info
  const getUserDisplay = () => {
    if (!user) return null
    return user.display_name || user.email || 'User'
  }

  // Get user initials for avatar
  const getUserInitials = () => {
    const display = getUserDisplay()
    if (!display) return '?'
    return display.charAt(0).toUpperCase()
  }

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

        {/* User menu / Sign in */}
        {!authLoading && (
          <div className="user-menu-container" ref={userMenuRef}>
            {isAuthenticated ? (
              <>
                <button
                  className="user-avatar-btn"
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  title={getUserDisplay()}
                >
                  <span className="user-avatar">{getUserInitials()}</span>
                </button>
                {showUserMenu && (
                  <div className="user-dropdown">
                    <div className="user-dropdown-header">
                      <span className="user-dropdown-email">{user?.email}</span>
                      {user?.display_name && (
                        <span className="user-dropdown-name">{user.display_name}</span>
                      )}
                    </div>
                    <div className="user-dropdown-divider" />
                    <button className="user-dropdown-item logout-btn" onClick={handleLogout}>
                      <span className="dropdown-icon">🚪</span>
                      Log out
                    </button>
                  </div>
                )}
              </>
            ) : (
              <button className="sign-in-btn" onClick={onSignInClick}>
                Sign in
              </button>
            )}
          </div>
        )}
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
  onSignInClick: PropTypes.func,
}

export default ChatHeader
