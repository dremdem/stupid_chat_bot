/* eslint-disable react-refresh/only-export-components */
/**
 * Authentication context for managing user authentication state.
 */
import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import PropTypes from 'prop-types'
import {
  getCurrentUser,
  getProviders,
  initiateOAuthLogin,
  logout as logoutApi,
  refreshTokens,
} from '../services/authApi'

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [providers, setProviders] = useState([])
  const [error, setError] = useState(null)

  // Check authentication status on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        setIsLoading(true)
        setError(null)

        // Try to get current user
        const { user: currentUser, authenticated } = await getCurrentUser()

        if (authenticated && currentUser) {
          setUser(currentUser)
          setIsAuthenticated(true)
        } else {
          // Try to refresh token
          const refreshResult = await refreshTokens()
          if (refreshResult && refreshResult.user) {
            setUser(refreshResult.user)
            setIsAuthenticated(true)
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

  const value = {
    user,
    isAuthenticated,
    isLoading,
    providers,
    error,
    loginWithProvider,
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
