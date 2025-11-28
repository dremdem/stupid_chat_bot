import { useEffect, useRef } from 'react'
import PropTypes from 'prop-types'
import MessageBubble from './MessageBubble'
import './MessageList.css'

/**
 * MessageList component - displays the list of chat messages
 */
function MessageList({ messages }) {
  const messagesEndRef = useRef(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="message-list">
      {messages.length === 0 ? (
        <div className="empty-state">
          <p>No messages yet. Start a conversation!</p>
        </div>
      ) : (
        messages.map((message, index) => (
          <MessageBubble key={message.id || index} message={message} />
        ))
      )}
      <div ref={messagesEndRef} />
    </div>
  )
}

MessageList.propTypes = {
  messages: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      content: PropTypes.string.isRequired,
      sender: PropTypes.string,
      timestamp: PropTypes.string,
      type: PropTypes.string,
    })
  ).isRequired,
}

export default MessageList
