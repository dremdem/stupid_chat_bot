import { useState, useEffect, useRef, useCallback } from 'react'
import toast from 'react-hot-toast'
import ChatHeader from './components/ChatHeader'
import MessageList from './components/MessageList'
import InputBox from './components/InputBox'
import TypingIndicator from './components/TypingIndicator'
import SessionSidebar from './components/SessionSidebar'
import LoginPrompt from './components/LoginPrompt'
import websocketService from './services/websocket'
import { fetchSessions, createSession, deleteSession } from './services/sessionsApi'
import './App.css'

function App() {
  const [messages, setMessages] = useState([])
  const [connectionStatus, setConnectionStatus] = useState('connecting')
  const [isTyping, setIsTyping] = useState(false)
  const [sessions, setSessions] = useState([])
  const [currentSessionId, setCurrentSessionId] = useState(null)
  const [sessionsLoading, setSessionsLoading] = useState(true)
  const [userInitialized, setUserInitialized] = useState(false)
  const [limitInfo, setLimitInfo] = useState(null)
  const [showLoginPrompt, setShowLoginPrompt] = useState(false)
  const [limitExceededMessage, setLimitExceededMessage] = useState('')
  const streamingMessageRef = useRef(null)
  const hasConnectedOnce = useRef(false)

  // Load sessions on mount (also initializes user cookie)
  useEffect(() => {
    const loadSessions = async () => {
      try {
        setSessionsLoading(true)
        // This fetch request will set the user cookie if not present
        const data = await fetchSessions()
        setSessions(data.sessions)
        // Mark user as initialized (cookie is now set)
        setUserInitialized(true)
        // If we have sessions but no current session selected, select the first one
        if (data.sessions.length > 0) {
          // Find default session or use first
          const defaultSession = data.sessions.find(s => s.metadata?.is_default)
          setCurrentSessionId(prev => prev || defaultSession?.id || data.sessions[0].id)
        }
      } catch (error) {
        console.error('Failed to load sessions:', error)
        toast.error('Failed to load conversations')
        // Still mark as initialized so we can show error state
        setUserInitialized(true)
      } finally {
        setSessionsLoading(false)
      }
    }

    loadSessions()
  }, [])

  // Handle WebSocket connection and messages
  // Only connect after user is initialized (cookie is set)
  useEffect(() => {
    // Don't connect until user is initialized (cookie set by sessions API)
    if (!userInitialized) {
      return
    }

    // Connect to WebSocket with current session
    websocketService.connect(currentSessionId)

    // Handle incoming messages
    const cleanupMessageHandler = websocketService.onMessage(message => {
      // Handle system messages (includes limit_info on connection)
      if (message.type === 'system' && message.system_type === 'connection') {
        if (message.limit_info) {
          setLimitInfo(message.limit_info)
          // Show modal if limit already exhausted on connection (e.g., page reload)
          if (!message.limit_info.can_send && message.limit_info.user_role === 'anonymous') {
            setLimitExceededMessage(
              "You've reached your message limit as an anonymous user. " +
                'Please sign in to continue chatting with more messages!'
            )
            setShowLoginPrompt(true)
          }
        }
        return
      }

      // Handle limit updates
      if (message.type === 'limit_update') {
        if (message.limit_info) {
          setLimitInfo(message.limit_info)
          // Show modal when limit is exhausted for anonymous users
          if (!message.limit_info.can_send && message.limit_info.user_role === 'anonymous') {
            setLimitExceededMessage(
              "You've reached your message limit as an anonymous user. " +
                'Please sign in to continue chatting with more messages!'
            )
            setShowLoginPrompt(true)
          }
        }
        return
      }

      // Handle limit exceeded
      if (message.type === 'limit_exceeded') {
        setLimitInfo(message.limit_info)
        setLimitExceededMessage(message.content)
        if (message.login_required) {
          setShowLoginPrompt(true)
        }
        toast.error(message.content)
        return
      }

      // Handle history messages from server
      if (message.type === 'history') {
        const historyMessages = message.messages.map((msg, index) => ({
          ...msg,
          id: `history-${index}-${Date.now()}`,
        }))
        setMessages(historyMessages)
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
            id: Date.now() + Math.random(),
          },
        ])
      }
    })

    // Handle connection status changes
    const cleanupConnectionHandler = websocketService.onConnectionChange(status => {
      setConnectionStatus(status)

      if (status === 'connected') {
        if (hasConnectedOnce.current) {
          toast.success('Reconnected to chat server')
        }
        hasConnectedOnce.current = true
      } else if (status === 'disconnected' && hasConnectedOnce.current) {
        toast.error('Disconnected from chat server')
      } else if (status === 'failed') {
        toast.error('Connection failed - please refresh the page')
      } else if (status === 'error' && hasConnectedOnce.current) {
        toast.error('Connection error - attempting to reconnect...')
      }
    })

    // Cleanup on unmount or session change
    return () => {
      cleanupMessageHandler()
      cleanupConnectionHandler()
      websocketService.disconnect()
    }
  }, [currentSessionId, userInitialized])

  const handleSelectSession = useCallback(
    sessionId => {
      if (sessionId === currentSessionId) return

      // Clear messages and switch session
      setMessages([])
      streamingMessageRef.current = null
      setCurrentSessionId(sessionId)
    },
    [currentSessionId]
  )

  const handleCreateSession = useCallback(async () => {
    try {
      const newSession = await createSession()
      setSessions(prev => [newSession, ...prev])
      handleSelectSession(newSession.id)
      toast.success('New conversation created')
    } catch (error) {
      console.error('Failed to create session:', error)
      toast.error('Failed to create conversation')
    }
  }, [handleSelectSession])

  const handleDeleteSession = useCallback(
    async sessionId => {
      try {
        await deleteSession(sessionId)
        setSessions(prev => prev.filter(s => s.id !== sessionId))

        // If we deleted the current session, switch to another
        if (sessionId === currentSessionId) {
          const remaining = sessions.filter(s => s.id !== sessionId)
          if (remaining.length > 0) {
            handleSelectSession(remaining[0].id)
          }
        }

        toast.success('Conversation deleted')
      } catch (error) {
        console.error('Failed to delete session:', error)
        toast.error(error.message || 'Failed to delete conversation')
      }
    },
    [currentSessionId, sessions, handleSelectSession]
  )

  const handleSendMessage = content => {
    const message = {
      content,
      sender: 'user',
      timestamp: new Date().toISOString(),
    }

    websocketService.sendMessage(message)
  }

  // Check if sending is disabled
  const isSendDisabled = connectionStatus !== 'connected' || (limitInfo && !limitInfo.can_send)

  return (
    <div className="app-container">
      <SessionSidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={handleSelectSession}
        onCreateSession={handleCreateSession}
        onDeleteSession={handleDeleteSession}
        isLoading={sessionsLoading}
      />
      <div className="app">
        <ChatHeader status={connectionStatus} limitInfo={limitInfo} />
        <MessageList messages={messages} isTyping={isTyping} TypingIndicator={TypingIndicator} />
        <InputBox
          onSendMessage={handleSendMessage}
          disabled={isSendDisabled}
          limitInfo={limitInfo}
        />
      </div>

      {/* Login prompt modal */}
      <LoginPrompt
        isOpen={showLoginPrompt}
        onClose={() => setShowLoginPrompt(false)}
        message={limitExceededMessage}
        limitInfo={limitInfo}
      />
    </div>
  )
}

export default App
