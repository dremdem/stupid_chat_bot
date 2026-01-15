import PropTypes from 'prop-types'
import './BlockedBadge.css'

function BlockedBadge({ isBlocked }) {
  if (!isBlocked) return null

  return <span className="blocked-badge">Blocked</span>
}

BlockedBadge.propTypes = {
  isBlocked: PropTypes.bool.isRequired,
}

export default BlockedBadge
