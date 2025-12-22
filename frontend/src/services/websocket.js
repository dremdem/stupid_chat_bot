/**
 * WebSocket service for real-time chat communication
 */

class WebSocketService {
  constructor() {
    this.ws = null
    this.messageHandlers = []
    this.connectionHandlers = []
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 2000
    this.shouldReconnect = true
    this.reconnectTimeout = null
    this.currentUrl = null
    this.currentSessionId = null
  }

  /**
   * Build WebSocket URL with optional session ID
   * @param {string|null} sessionId - Optional session UUID
   * @returns {string} WebSocket URL
   */
  buildUrl(sessionId = null) {
    // Use relative URL - works in both dev (Vite proxy) and prod (nginx proxy)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const baseUrl = `${protocol}//${window.location.host}/ws/chat`
    if (sessionId) {
      return `${baseUrl}?session_id=${sessionId}`
    }
    return baseUrl
  }

  /**
   * Connect to the WebSocket server
   * @param {string|null} sessionId - Optional session UUID to connect to
   */
  connect(sessionId = null) {
    const url = this.buildUrl(sessionId)
    this.currentUrl = url
    this.currentSessionId = sessionId
    // Prevent multiple connections
    if (
      this.ws &&
      (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)
    ) {
      console.log('WebSocket already connected or connecting, skipping...')
      return
    }

    try {
      this.shouldReconnect = true
      this.ws = new WebSocket(url)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
        this.notifyConnectionHandlers('connected')
      }

      this.ws.onmessage = event => {
        try {
          const message = JSON.parse(event.data)
          this.notifyMessageHandlers(message)
        } catch (error) {
          console.error('Error parsing message:', error)
        }
      }

      this.ws.onerror = error => {
        console.error('WebSocket error:', error)
        this.notifyConnectionHandlers('error')
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.notifyConnectionHandlers('disconnected')
        // Only attempt reconnect if not explicitly disconnected
        if (this.shouldReconnect) {
          this.attemptReconnect()
        }
      }
    } catch (error) {
      console.error('Error connecting to WebSocket:', error)
      this.notifyConnectionHandlers('error')
    }
  }

  /**
   * Attempt to reconnect to the WebSocket server
   */
  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(
        `Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`
      )
      this.reconnectTimeout = setTimeout(() => {
        this.reconnectTimeout = null
        this.connect(this.currentSessionId)
      }, this.reconnectDelay)
    } else {
      console.error('Max reconnection attempts reached')
      this.notifyConnectionHandlers('failed')
    }
  }

  /**
   * Switch to a different session
   * @param {string|null} sessionId - Session UUID to switch to
   */
  switchSession(sessionId) {
    console.log(`Switching to session: ${sessionId || 'default'}`)
    this.disconnect()
    // Small delay to ensure clean disconnect before reconnecting
    setTimeout(() => {
      this.connect(sessionId)
    }, 100)
  }

  /**
   * Get current session ID
   * @returns {string|null} Current session ID
   */
  getSessionId() {
    return this.currentSessionId
  }

  /**
   * Send a message through the WebSocket
   * @param {Object} message - Message object to send
   */
  sendMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.error('WebSocket is not connected')
    }
  }

  /**
   * Register a handler for incoming messages
   * @param {Function} handler - Callback function to handle messages
   * @returns {Function} Cleanup function to remove the handler
   */
  onMessage(handler) {
    this.messageHandlers.push(handler)
    // Return cleanup function
    return () => {
      const index = this.messageHandlers.indexOf(handler)
      if (index > -1) {
        this.messageHandlers.splice(index, 1)
      }
    }
  }

  /**
   * Register a handler for connection status changes
   * @param {Function} handler - Callback function to handle connection changes
   * @returns {Function} Cleanup function to remove the handler
   */
  onConnectionChange(handler) {
    this.connectionHandlers.push(handler)
    // Return cleanup function
    return () => {
      const index = this.connectionHandlers.indexOf(handler)
      if (index > -1) {
        this.connectionHandlers.splice(index, 1)
      }
    }
  }

  /**
   * Notify all message handlers
   * @param {Object} message - Message to distribute
   */
  notifyMessageHandlers(message) {
    this.messageHandlers.forEach(handler => handler(message))
  }

  /**
   * Notify all connection handlers
   * @param {string} status - Connection status
   */
  notifyConnectionHandlers(status) {
    this.connectionHandlers.forEach(handler => handler(status))
  }

  /**
   * Disconnect from the WebSocket server
   */
  disconnect() {
    this.shouldReconnect = false

    // Clear any pending reconnect timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }

    if (this.ws) {
      if (this.ws.readyState === WebSocket.OPEN) {
        // Only close if actually open
        this.ws.close()
      } else if (this.ws.readyState === WebSocket.CONNECTING) {
        // Don't close CONNECTING sockets - causes "closed before established" error
        // Instead, nullify handlers so this stale connection doesn't interfere
        this.ws.onopen = null
        this.ws.onclose = null
        this.ws.onerror = null
        this.ws.onmessage = null
      }
      this.ws = null
    }
  }

  /**
   * Check if WebSocket is connected
   * @returns {boolean} Connection status
   */
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN
  }
}

export default new WebSocketService()
