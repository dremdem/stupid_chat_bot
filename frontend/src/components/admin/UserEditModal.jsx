import { useState, useEffect } from 'react'
import PropTypes from 'prop-types'
import { updateUserRole, updateUserBlock, updateUserLimit } from '../../services/adminApi'
import RoleBadge from './RoleBadge'
import './UserEditModal.css'

function UserEditModal({ user, onClose, onUpdate }) {
  const [role, setRole] = useState(user.role)
  const [isBlocked, setIsBlocked] = useState(user.is_blocked)
  const [messageLimit, setMessageLimit] = useState(
    user.message_limit !== null ? user.message_limit.toString() : ''
  )
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    const handleEscape = e => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [onClose])

  const handleOverlayClick = e => {
    if (e.target === e.currentTarget) onClose()
  }

  const handleSave = async () => {
    setLoading(true)
    setError(null)

    try {
      let updatedUser = user

      if (role !== user.role) {
        const result = await updateUserRole(user.id, role)
        updatedUser = result.user
      }

      if (isBlocked !== user.is_blocked) {
        const result = await updateUserBlock(user.id, isBlocked)
        updatedUser = result.user
      }

      const newLimit = messageLimit === '' ? null : parseInt(messageLimit, 10)
      if (newLimit !== user.message_limit) {
        const result = await updateUserLimit(user.id, newLimit)
        updatedUser = result.user
      }

      onUpdate(updatedUser)
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const hasChanges =
    role !== user.role ||
    isBlocked !== user.is_blocked ||
    (messageLimit === '' ? null : parseInt(messageLimit, 10)) !== user.message_limit

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal-content">
        <div className="modal-header">
          <h2>Edit User</h2>
          <button className="modal-close" onClick={onClose}>
            &times;
          </button>
        </div>

        <div className="modal-body">
          <div className="user-info">
            <div className="user-info-row">
              <span className="label">Email:</span>
              <span className="value">{user.email || 'N/A'}</span>
            </div>
            <div className="user-info-row">
              <span className="label">Name:</span>
              <span className="value">{user.display_name || 'N/A'}</span>
            </div>
            <div className="user-info-row">
              <span className="label">Current Role:</span>
              <RoleBadge role={user.role} />
            </div>
            <div className="user-info-row">
              <span className="label">Messages:</span>
              <span className="value">{user.message_count}</span>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label htmlFor="role">Role</label>
            <select id="role" value={role} onChange={e => setRole(e.target.value)}>
              <option value="user">User</option>
              <option value="unlimited">Unlimited</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="blocked">
              <input
                type="checkbox"
                id="blocked"
                checked={isBlocked}
                onChange={e => setIsBlocked(e.target.checked)}
              />
              Block User
            </label>
            <span className="help-text">Blocked users cannot access the application</span>
          </div>

          <div className="form-group">
            <label htmlFor="messageLimit">Message Limit</label>
            <input
              type="number"
              id="messageLimit"
              value={messageLimit}
              onChange={e => setMessageLimit(e.target.value)}
              placeholder="Default (based on role)"
              min="0"
              max="10000"
            />
            <span className="help-text">Leave empty to use default limit for role</span>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose} disabled={loading}>
            Cancel
          </button>
          <button
            className="btn btn-primary"
            onClick={handleSave}
            disabled={loading || !hasChanges}
          >
            {loading ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  )
}

UserEditModal.propTypes = {
  user: PropTypes.shape({
    id: PropTypes.string.isRequired,
    email: PropTypes.string,
    display_name: PropTypes.string,
    role: PropTypes.string.isRequired,
    is_blocked: PropTypes.bool.isRequired,
    message_limit: PropTypes.number,
    message_count: PropTypes.number.isRequired,
  }).isRequired,
  onClose: PropTypes.func.isRequired,
  onUpdate: PropTypes.func.isRequired,
}

export default UserEditModal
