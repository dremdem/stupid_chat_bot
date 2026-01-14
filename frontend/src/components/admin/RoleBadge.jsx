import PropTypes from 'prop-types'
import './RoleBadge.css'

const roleConfig = {
  admin: {
    label: 'Admin',
    className: 'role-badge-admin',
  },
  unlimited: {
    label: 'Unlimited',
    className: 'role-badge-unlimited',
  },
  user: {
    label: 'User',
    className: 'role-badge-user',
  },
}

function RoleBadge({ role }) {
  const config = roleConfig[role] || roleConfig.user

  return <span className={`role-badge ${config.className}`}>{config.label}</span>
}

RoleBadge.propTypes = {
  role: PropTypes.string.isRequired,
}

export default RoleBadge
