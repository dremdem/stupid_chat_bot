import { useState, useEffect, useCallback } from 'react'
import PropTypes from 'prop-types'
import { getUserMessages } from '../../services/adminApi'
import './UserMessagesModal.css'

/**
 * UserMessagesModal component - displays user message history
 */
function UserMessagesModal({ user, onClose }) {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)

  const fetchMessages = useCallback(async () => {
    if (!user) return
    try {
      setLoading(true)
      setError(null)
      const response = await getUserMessages(user.id, { page, pageSize: 20 })
      setMessages(response.messages)
      setTotalPages(response.total_pages)
      setTotal(response.total)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [user, page])

  useEffect(() => {
    fetchMessages()
  }, [fetchMessages])

  // Close on escape key
  useEffect(() => {
    const handleEscape = e => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [onClose])

  const formatDate = dateStr => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (!user) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <h2>Message History</h2>
            <p className="modal-subtitle">
              {user.display_name || user.email || 'User'} - {total.toLocaleString()} total messages
            </p>
          </div>
          <button className="modal-close" onClick={onClose}>
            &times;
          </button>
        </div>

        <div className="modal-body">
          {loading ? (
            <div className="modal-loading">Loading messages...</div>
          ) : error ? (
            <div className="modal-error">
              <p>Failed to load messages: {error}</p>
              <button onClick={fetchMessages}>Retry</button>
            </div>
          ) : messages.length === 0 ? (
            <div className="modal-empty">No messages found</div>
          ) : (
            <div className="messages-list">
              {messages.map(msg => (
                <div key={msg.id} className={`message-item message-${msg.sender}`}>
                  <div className="message-header">
                    <span className="message-sender">
                      {msg.sender === 'user' ? 'User' : 'Assistant'}
                    </span>
                    <span className="message-date">{formatDate(msg.created_at)}</span>
                  </div>
                  <div className="message-content">{msg.content}</div>
                  <div className="message-meta">
                    <span className="message-session">Session: {msg.session_id.slice(0, 8)}...</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {totalPages > 1 && (
          <div className="modal-footer">
            <div className="pagination">
              <button
                className="pagination-btn"
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
              >
                Previous
              </button>
              <span className="pagination-info">
                Page {page} of {totalPages}
              </span>
              <button
                className="pagination-btn"
                disabled={page >= totalPages}
                onClick={() => setPage(p => p + 1)}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

UserMessagesModal.propTypes = {
  user: PropTypes.shape({
    id: PropTypes.string.isRequired,
    email: PropTypes.string,
    display_name: PropTypes.string,
  }),
  onClose: PropTypes.func.isRequired,
}

export default UserMessagesModal
