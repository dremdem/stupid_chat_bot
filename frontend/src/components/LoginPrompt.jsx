import { useState } from 'react'
import PropTypes from 'prop-types'
import { useAuth } from '../contexts/AuthContext'
import './LoginPrompt.css'

/**
 * Modal component shown when user reaches message limit.
 * Prompts anonymous users to sign in for more messages.
 * Supports OAuth providers and email/password authentication.
 */
function LoginPrompt({ isOpen, onClose, message, limitInfo }) {
  const {
    providers,
    isProviderAvailable,
    loginWithProvider,
    loginWithEmail,
    registerWithEmail,
    isLoading: authLoading,
  } = useAuth()

  const [loginLoading, setLoginLoading] = useState(null)
  const [authMode, setAuthMode] = useState('login') // 'login' | 'register'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState(null)

  if (!isOpen) return null

  const isAnonymous = limitInfo?.user_role === 'anonymous'
  const hasAnyProvider = providers.length > 0

  const handleOAuthLogin = async provider => {
    try {
      setLoginLoading(provider)
      setError(null)
      await loginWithProvider(provider)
      // Will redirect to OAuth provider
    } catch (err) {
      console.error(`Failed to login with ${provider}:`, err)
      setError(err.message)
      setLoginLoading(null)
    }
  }

  const handleEmailSubmit = async e => {
    e.preventDefault()
    setError(null)

    try {
      setLoginLoading('email')
      if (authMode === 'register') {
        await registerWithEmail(email, password, displayName || null)
      } else {
        await loginWithEmail(email, password)
      }
      // Success - close modal
      onClose()
    } catch (err) {
      console.error(`${authMode} failed:`, err)
      setError(err.message)
    } finally {
      setLoginLoading(null)
    }
  }

  const toggleAuthMode = () => {
    setAuthMode(authMode === 'login' ? 'register' : 'login')
    setError(null)
  }

  const resetForm = () => {
    setEmail('')
    setPassword('')
    setDisplayName('')
    setError(null)
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
            {/* OAuth Providers */}
            {hasAnyProvider && (
              <>
                <div className="login-prompt-providers">
                  <button
                    className="login-btn login-btn-google"
                    disabled={!isProviderAvailable('google') || loginLoading !== null}
                    onClick={() => handleOAuthLogin('google')}
                  >
                    <span className="login-btn-icon">G</span>
                    {loginLoading === 'google' ? 'Redirecting...' : 'Google'}
                  </button>
                  <button
                    className="login-btn login-btn-github"
                    disabled={!isProviderAvailable('github') || loginLoading !== null}
                    onClick={() => handleOAuthLogin('github')}
                  >
                    <span className="login-btn-icon">GH</span>
                    {loginLoading === 'github' ? 'Redirecting...' : 'GitHub'}
                  </button>
                  <button
                    className="login-btn login-btn-facebook"
                    disabled={!isProviderAvailable('facebook') || loginLoading !== null}
                    onClick={() => handleOAuthLogin('facebook')}
                  >
                    <span className="login-btn-icon">f</span>
                    {loginLoading === 'facebook' ? 'Redirecting...' : 'Facebook'}
                  </button>
                </div>
                <div className="login-prompt-divider">
                  <span>or</span>
                </div>
              </>
            )}

            {/* Email/Password Form */}
            <form className="login-prompt-form" onSubmit={handleEmailSubmit}>
              <h3 className="login-prompt-form-title">
                {authMode === 'login' ? 'Sign in with Email' : 'Create Account'}
              </h3>

              {error && <div className="login-prompt-error">{error}</div>}

              {authMode === 'register' && (
                <input
                  type="text"
                  className="login-prompt-input"
                  placeholder="Display name (optional)"
                  value={displayName}
                  onChange={e => setDisplayName(e.target.value)}
                  disabled={loginLoading !== null}
                  maxLength={100}
                />
              )}

              <input
                type="email"
                className="login-prompt-input"
                placeholder="Email address"
                value={email}
                onChange={e => setEmail(e.target.value)}
                disabled={loginLoading !== null}
                required
              />

              <input
                type="password"
                className="login-prompt-input"
                placeholder={authMode === 'register' ? 'Password (min 8 chars)' : 'Password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                disabled={loginLoading !== null}
                required
                minLength={authMode === 'register' ? 8 : undefined}
              />

              <button
                type="submit"
                className="login-btn login-btn-primary"
                disabled={loginLoading !== null || authLoading}
              >
                {loginLoading === 'email'
                  ? authMode === 'login'
                    ? 'Signing in...'
                    : 'Creating account...'
                  : authMode === 'login'
                    ? 'Sign In'
                    : 'Create Account'}
              </button>

              <p className="login-prompt-toggle">
                {authMode === 'login' ? (
                  <>
                    Don&apos;t have an account?{' '}
                    <button
                      type="button"
                      className="login-prompt-toggle-btn"
                      onClick={() => {
                        toggleAuthMode()
                        resetForm()
                      }}
                    >
                      Sign up
                    </button>
                  </>
                ) : (
                  <>
                    Already have an account?{' '}
                    <button
                      type="button"
                      className="login-prompt-toggle-btn"
                      onClick={() => {
                        toggleAuthMode()
                        resetForm()
                      }}
                    >
                      Sign in
                    </button>
                  </>
                )}
              </p>
            </form>

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
