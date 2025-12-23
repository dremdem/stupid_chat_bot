import { useState } from 'react'
import PropTypes from 'prop-types'
import { useAuth } from '../contexts/AuthContext'
import './LoginPrompt.css'

/**
 * Modal component shown when user reaches message limit.
 * Prompts anonymous users to sign in for more messages.
 */
function LoginPrompt({ isOpen, onClose, message, limitInfo }) {
  const { providers, isProviderAvailable, loginWithProvider, isLoading: authLoading } = useAuth()
  const [loginLoading, setLoginLoading] = useState(null)

  if (!isOpen) return null

  const isAnonymous = limitInfo?.user_role === 'anonymous'
  const hasAnyProvider = providers.length > 0

  const handleOAuthLogin = async provider => {
    try {
      setLoginLoading(provider)
      await loginWithProvider(provider)
      // Will redirect to OAuth provider
    } catch (error) {
      console.error(`Failed to login with ${provider}:`, error)
      setLoginLoading(null)
    }
  }

  return (
    <div className="login-prompt-overlay" onClick={onClose}>
      <div className="login-prompt-modal" onClick={e => e.stopPropagation()}>
        <button className="login-prompt-close" onClick={onClose} aria-label="Close">
          &times;
        </button>

        <div className="login-prompt-icon">{isAnonymous ? '🔐' : '📨'}</div>

        <h2 className="login-prompt-title">
          {isAnonymous ? 'Sign in to Continue' : 'Message Limit Reached'}
        </h2>

        <p className="login-prompt-message">{message}</p>

        {limitInfo && (
          <div className="login-prompt-stats">
            <span className="login-prompt-stat">
              <strong>{limitInfo.used}</strong> / {limitInfo.limit} messages used
            </span>
          </div>
        )}

        {isAnonymous ? (
          <div className="login-prompt-actions">
            {!hasAnyProvider && !authLoading && (
              <p className="login-prompt-coming-soon">OAuth sign-in coming soon!</p>
            )}
            <div className="login-prompt-providers">
              <button
                className="login-btn login-btn-google"
                disabled={!isProviderAvailable('google') || loginLoading !== null}
                onClick={() => handleOAuthLogin('google')}
              >
                <span className="login-btn-icon">G</span>
                {loginLoading === 'google' ? 'Redirecting...' : 'Sign in with Google'}
              </button>
              <button
                className="login-btn login-btn-github"
                disabled={!isProviderAvailable('github') || loginLoading !== null}
                onClick={() => handleOAuthLogin('github')}
              >
                <span className="login-btn-icon">GH</span>
                {loginLoading === 'github' ? 'Redirecting...' : 'Sign in with GitHub'}
              </button>
              <button
                className="login-btn login-btn-facebook"
                disabled={!isProviderAvailable('facebook') || loginLoading !== null}
                onClick={() => handleOAuthLogin('facebook')}
              >
                <span className="login-btn-icon">f</span>
                {loginLoading === 'facebook' ? 'Redirecting...' : 'Sign in with Facebook'}
              </button>
            </div>
            <button className="login-btn login-btn-secondary" onClick={onClose}>
              Maybe Later
            </button>
          </div>
        ) : (
          <div className="login-prompt-actions">
            <p className="login-prompt-contact">For extended access, please contact us:</p>
            <a
              href="https://dremdem.ru"
              target="_blank"
              rel="noopener noreferrer"
              className="login-btn login-btn-primary"
            >
              Contact Us
            </a>
            <button className="login-btn login-btn-secondary" onClick={onClose}>
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

LoginPrompt.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  message: PropTypes.string,
  limitInfo: PropTypes.shape({
    limit: PropTypes.number,
    used: PropTypes.number,
    remaining: PropTypes.number,
    is_unlimited: PropTypes.bool,
    can_send: PropTypes.bool,
    user_role: PropTypes.string,
  }),
}

export default LoginPrompt
