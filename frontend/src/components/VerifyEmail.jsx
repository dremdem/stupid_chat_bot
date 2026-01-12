import { useState, useEffect } from 'react'
import PropTypes from 'prop-types'
import { verifyEmail } from '../services/authApi'
import { useAuth } from '../contexts/AuthContext'
import './VerifyEmail.css'

/**
 * Email verification page component.
 * Handles verification token from URL and shows result.
 */
function VerifyEmail({ token, onComplete }) {
  const { refresh } = useAuth()
  const [status, setStatus] = useState('verifying') // verifying, success, error
  const [message, setMessage] = useState('')

  useEffect(() => {
    const verify = async () => {
      if (!token) {
        setStatus('error')
        setMessage('No verification token provided.')
        return
      }

      try {
        const result = await verifyEmail(token)

        if (result.success) {
          setStatus('success')
          setMessage(result.message)
          // Refresh auth state to get updated user
          await refresh()
        } else {
          setStatus('error')
          setMessage(result.message)
        }
      } catch (err) {
        setStatus('error')
        setMessage('An error occurred during verification. Please try again.')
        console.error('Verification error:', err)
      }
    }

    verify()
  }, [token, refresh])

  const handleContinue = () => {
    // Clear URL parameters and go to main app
    window.history.replaceState({}, '', '/')
    onComplete()
  }

  return (
    <div className="verify-email-container">
      <div className="verify-email-card">
        {status === 'verifying' && (
          <>
            <div className="verify-email-icon loading">
              <div className="spinner"></div>
            </div>
            <h1>Verifying Email...</h1>
            <p>Please wait while we verify your email address.</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="verify-email-icon success">&#10003;</div>
            <h1>Email Verified!</h1>
            <p>{message}</p>
            <button className="verify-email-btn" onClick={handleContinue}>
              Continue to Chat
            </button>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="verify-email-icon error">&#10007;</div>
            <h1>Verification Failed</h1>
            <p>{message}</p>
            <button className="verify-email-btn secondary" onClick={handleContinue}>
              Go to App
            </button>
          </>
        )}
      </div>
    </div>
  )
}

VerifyEmail.propTypes = {
  token: PropTypes.string,
  onComplete: PropTypes.func.isRequired,
}

export default VerifyEmail
