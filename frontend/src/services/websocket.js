/**
 * WebSocket service for real-time chat communication
 */

class WebSocketService {
  constructor() {
    this.ws = null;
    this.messageHandlers = [];
    this.connectionHandlers = [];
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 2000;
  }

  /**
   * Connect to the WebSocket server
   * @param {string} url - WebSocket server URL
   */
  connect(url = 'ws://localhost:8000/ws/chat') {
    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.notifyConnectionHandlers('connected');
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.notifyMessageHandlers(message);
        } catch (error) {
          console.error('Error parsing message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.notifyConnectionHandlers('error');
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.notifyConnectionHandlers('disconnected');
        this.attemptReconnect(url);
      };
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      this.notifyConnectionHandlers('error');
    }
  }

  /**
   * Attempt to reconnect to the WebSocket server
   * @param {string} url - WebSocket server URL
   */
  attemptReconnect(url) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(
        `Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`
      );
      setTimeout(() => this.connect(url), this.reconnectDelay);
    } else {
      console.error('Max reconnection attempts reached');
      this.notifyConnectionHandlers('failed');
    }
  }

  /**
   * Send a message through the WebSocket
   * @param {Object} message - Message object to send
   */
  sendMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  /**
   * Register a handler for incoming messages
   * @param {Function} handler - Callback function to handle messages
   */
  onMessage(handler) {
    this.messageHandlers.push(handler);
  }

  /**
   * Register a handler for connection status changes
   * @param {Function} handler - Callback function to handle connection changes
   */
  onConnectionChange(handler) {
    this.connectionHandlers.push(handler);
  }

  /**
   * Notify all message handlers
   * @param {Object} message - Message to distribute
   */
  notifyMessageHandlers(message) {
    this.messageHandlers.forEach((handler) => handler(message));
  }

  /**
   * Notify all connection handlers
   * @param {string} status - Connection status
   */
  notifyConnectionHandlers(status) {
    this.connectionHandlers.forEach((handler) => handler(status));
  }

  /**
   * Disconnect from the WebSocket server
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Check if WebSocket is connected
   * @returns {boolean} Connection status
   */
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }
}

export default new WebSocketService();
