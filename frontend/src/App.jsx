import { useState, useEffect, useRef } from 'react'
import toast from 'react-hot-toast'
import ChatHeader from './components/ChatHeader'
import MessageList from './components/MessageList'
import InputBox from './components/InputBox'
import TypingIndicator from './components/TypingIndicator'
import websocketService from './services/websocket'
import './App.css'

function App() {
  const [messages, setMessages] = useState([])
  const [connectionStatus, setConnectionStatus] = useState('connecting')
  const [isTyping, setIsTyping] = useState(false)
  const streamingMessageRef = useRef(null)
  const hasConnectedOnce = useRef(false)

  useEffect(() => {
    // Connect to WebSocket
    websocketService.connect()

    // Handle incoming messages and get cleanup function
    const cleanupMessageHandler = websocketService.onMessage(message => {
      // Skip connection system messages (they're redundant with connection status)
      if (message.type === 'system' && message.system_type === 'connection') {
        return
      }

      // Handle typing indicator
      if (message.type === 'typing') {
        setIsTyping(message.is_typing)
        return
      }

      // Handle AI streaming chunks
      if (message.type === 'ai_stream') {
        if (!streamingMessageRef.current) {
          // Create new streaming message
          const newMessage = {
            id: Date.now() + Math.random(),
            type: 'message',
            content: message.content,
            sender: 'assistant',
            timestamp: null,
          }
          streamingMessageRef.current = newMessage
          setMessages(prev => [...prev, newMessage])
        } else {
          // Append to existing streaming message
          // Capture the current ref value to avoid race conditions
          const currentStreamingMessage = streamingMessageRef.current
          if (currentStreamingMessage) {
            setMessages(prev =>
              prev
                .filter(msg => msg != null)
                .map(msg =>
                  msg.id === currentStreamingMessage.id
                    ? { ...msg, content: msg.content + message.content }
                    : msg
                )
            )
          }
        }
        return
      }

      // Handle AI stream end
      if (message.type === 'ai_stream_end') {
        streamingMessageRef.current = null
        setIsTyping(false)
        return
      }

      // Handle regular messages
      if (message && message.content) {
        setMessages(prev => [
          ...prev,
          {
            ...message,
            id: Date.now() + Math.random(), // Simple unique ID
          },
        ])
      }
    })

    // Handle connection status changes and get cleanup function
    const cleanupConnectionHandler = websocketService.onConnectionChange(status => {
      setConnectionStatus(status)

      // Only show toast notifications after the initial connection
      // This prevents spam on page load/refresh
      if (status === 'connected') {
        if (hasConnectedOnce.current) {
          // Reconnection after disconnect
          toast.success('Reconnected to chat server')
        }
        hasConnectedOnce.current = true
      } else if (status === 'disconnected' && hasConnectedOnce.current) {
        // Only show disconnect if we had connected before
        toast.error('Disconnected from chat server')
      } else if (status === 'failed') {
        toast.error('Connection failed - please refresh the page')
      } else if (status === 'error' && hasConnectedOnce.current) {
        toast.error('Connection error - attempting to reconnect...')
      }
    })

    // Cleanup on unmount
    return () => {
      cleanupMessageHandler()
      cleanupConnectionHandler()
      websocketService.disconnect()
    }
  }, [])

  const handleSendMessage = content => {
    const message = {
      content,
      sender: 'user',
      timestamp: new Date().toISOString(),
    }

    websocketService.sendMessage(message)
  }

  return (
    <div className="app">
      <ChatHeader status={connectionStatus} />
      <MessageList messages={messages} isTyping={isTyping} TypingIndicator={TypingIndicator} />
      <InputBox onSendMessage={handleSendMessage} disabled={connectionStatus !== 'connected'} />
    </div>
  )
}

export default App
