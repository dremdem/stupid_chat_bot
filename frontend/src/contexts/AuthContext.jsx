/* eslint-disable react-refresh/only-export-components */
/**
 * Authentication context for managing user authentication state.
 */
import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'
import PropTypes from 'prop-types'
import {
  getCurrentUser,
  getProviders,
  initiateOAuthLogin,
  logout as logoutApi,
  refreshTokens,
  register as registerApi,
  login as loginApi,
} from '../services/authApi'

const AuthContext = createContext()

// Refresh tokens 5 minutes before access token expires (25 minutes)
const TOKEN_REFRESH_INTERVAL = 25 * 60 * 1000

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isBlocked, setIsBlocked] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [providers, setProviders] = useState([])
  const [error, setError] = useState(null)
  const refreshIntervalRef = useRef(null)

  // Check authentication status on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        setIsLoading(true)
        setError(null)

        // Try to get current user
        const { user: currentUser, authenticated, blocked } = await getCurrentUser()

        if (blocked) {
          setIsBlocked(true)
          setUser(null)
          setIsAuthenticated(false)
        } else if (authenticated && currentUser) {
          setUser(currentUser)
          setIsAuthenticated(true)
          setIsBlocked(false)
        } else {
          // Try to refresh token
          const refreshResult = await refreshTokens()
          if (refreshResult && refreshResult.blocked) {
            setIsBlocked(true)
            setUser(null)
            setIsAuthenticated(false)
          } else if (refreshResult && refreshResult.user) {
            setUser(refreshResult.user)
            setIsAuthenticated(true)
            setIsBlocked(false)
          }
        }

        // Get available providers
        const availableProviders = await getProviders()
        setProviders(availableProviders)
      } catch (err) {
        console.error('Auth check failed:', err)
        setError(err.message)
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [])

  // Set up periodic token refresh when authenticated
  useEffect(() => {
    // Clear any existing interval
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current)
      refreshIntervalRef.current = null
    }

    // Only set up refresh interval if authenticated
    if (isAuthenticated) {
      refreshIntervalRef.current = setInterval(async () => {
        try {
          const result = await refreshTokens()
          if (result && result.blocked) {
            // User was blocked
            setIsBlocked(true)
            setUser(null)
            setIsAuthenticated(false)
          } else if (result && result.user) {
            setUser(result.user)
          } else {
            // Refresh failed, user needs to re-login
            setUser(null)
            setIsAuthenticated(false)
          }
        } catch (err) {
          console.error('Periodic token refresh failed:', err)
          // Don't logout on network errors, just log and try again next interval
        }
      }, TOKEN_REFRESH_INTERVAL)
    }

    // Cleanup on unmount or when isAuthenticated changes
    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current)
        refreshIntervalRef.current = null
      }
    }
  }, [isAuthenticated])

  // Login with OAuth provider
  const loginWithProvider = useCallback(async (provider, redirectUrl = null) => {
    try {
      setError(null)
      const authUrl = await initiateOAuthLogin(provider, redirectUrl || window.location.href)
      // Redirect to OAuth provider
      window.location.href = authUrl
    } catch (err) {
      console.error(`OAuth login failed:`, err)
      setError(err.message)
      throw err
    }
  }, [])

  // Logout
  const logout = useCallback(async () => {
    try {
      setError(null)
      await logoutApi()
      setUser(null)
      setIsAuthenticated(false)
    } catch (err) {
      console.error('Logout failed:', err)
      setError(err.message)
      // Still clear local state even if API call fails
      setUser(null)
      setIsAuthenticated(false)
    }
  }, [])

  // Refresh tokens (called periodically or when needed)
  const refresh = useCallback(async () => {
    try {
      const result = await refreshTokens()
      if (result && result.user) {
        setUser(result.user)
        setIsAuthenticated(true)
        return true
      }
      return false
    } catch (err) {
      console.error('Token refresh failed:', err)
      setUser(null)
      setIsAuthenticated(false)
      return false
    }
  }, [])

  // Check if a specific provider is available
  const isProviderAvailable = useCallback(
    provider => {
      return providers.includes(provider)
    },
    [providers]
  )

  // Register with email and password
  const registerWithEmail = useCallback(async (email, password, displayName = null) => {
    try {
      setError(null)
      setIsLoading(true)
      const result = await registerApi(email, password, displayName)
      if (result && result.user) {
        setUser(result.user)
        setIsAuthenticated(true)
        return result
      }
      throw new Error('Registration failed')
    } catch (err) {
      console.error('Registration failed:', err)
      setError(err.message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Login with email and password
  const loginWithEmail = useCallback(async (email, password) => {
    try {
      setError(null)
      setIsLoading(true)
      const result = await loginApi(email, password)
      if (result && result.user) {
        setUser(result.user)
        setIsAuthenticated(true)
        return result
      }
      throw new Error('Login failed')
    } catch (err) {
      console.error('Login failed:', err)
      setError(err.message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const value = {
    user,
    isAuthenticated,
    isBlocked,
    isLoading,
    providers,
    error,
    loginWithProvider,
    loginWithEmail,
    registerWithEmail,
    logout,
    refresh,
    isProviderAvailable,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

AuthProvider.propTypes = {
  children: PropTypes.node.isRequired,
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
