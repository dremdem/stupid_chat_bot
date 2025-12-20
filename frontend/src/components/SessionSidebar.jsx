import { useState } from 'react'
import PropTypes from 'prop-types'
import './SessionSidebar.css'

function SessionSidebar({
  sessions,
  currentSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  isLoading,
}) {
  const [isCreating, setIsCreating] = useState(false)

  const handleCreateClick = async () => {
    setIsCreating(true)
    try {
      await onCreateSession()
    } finally {
      setIsCreating(false)
    }
  }

  const handleDeleteClick = (e, sessionId, isDefault) => {
    e.stopPropagation()
    if (isDefault) {
      return // Cannot delete default session
    }
    if (window.confirm('Delete this conversation?')) {
      onDeleteSession(sessionId)
    }
  }

  const formatDate = dateString => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now - date
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) {
      return 'Today'
    } else if (diffDays === 1) {
      return 'Yesterday'
    } else if (diffDays < 7) {
      return `${diffDays} days ago`
    } else {
      return date.toLocaleDateString()
    }
  }

  return (
    <aside className="session-sidebar">
      <div className="sidebar-header">
        <h2>Conversations</h2>
        <button
          className="new-chat-btn"
          onClick={handleCreateClick}
          disabled={isCreating}
          title="New conversation"
        >
          {isCreating ? '...' : '+'}
        </button>
      </div>

      <div className="session-list">
        {isLoading ? (
          <div className="loading-sessions">Loading...</div>
        ) : sessions.length === 0 ? (
          <div className="no-sessions">No conversations yet</div>
        ) : (
          sessions.map(session => {
            const isDefault = session.metadata?.is_default
            const isActive = session.id === currentSessionId
            return (
              <div
                key={session.id}
                className={`session-item ${isActive ? 'active' : ''}`}
                onClick={() => onSelectSession(session.id)}
              >
                <div className="session-info">
                  <span className="session-title" title={session.title}>
                    {session.title}
                  </span>
                  <span className="session-date">{formatDate(session.updated_at)}</span>
                </div>
                {!isDefault && (
                  <button
                    className="delete-btn"
                    onClick={e => handleDeleteClick(e, session.id, isDefault)}
                    title="Delete conversation"
                  >
                    x
                  </button>
                )}
              </div>
            )
          })
        )}
      </div>
    </aside>
  )
}

SessionSidebar.propTypes = {
  sessions: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      title: PropTypes.string.isRequired,
      metadata: PropTypes.object,
      updated_at: PropTypes.string.isRequired,
    })
  ).isRequired,
  currentSessionId: PropTypes.string,
  onSelectSession: PropTypes.func.isRequired,
  onCreateSession: PropTypes.func.isRequired,
  onDeleteSession: PropTypes.func.isRequired,
  isLoading: PropTypes.bool,
}

SessionSidebar.defaultProps = {
  currentSessionId: null,
  isLoading: false,
}

export default SessionSidebar
