import PropTypes from 'prop-types'
import './MessageBubble.css'

/**
 * MessageBubble component - displays a single chat message
 */
function MessageBubble({ message }) {
  const { content, sender, timestamp, type } = message

  // System messages (like connection status)
  if (type === 'system') {
    return (
      <div className="message-bubble system">
        <div className="message-content">{content}</div>
      </div>
    )
  }

  // Regular chat messages
  const isBot = sender === 'bot'
  const bubbleClass = `message-bubble ${isBot ? 'bot' : 'user'}`

  return (
    <div className={bubbleClass}>
      <div className="message-sender">{isBot ? 'Bot' : 'You'}</div>
      <div className="message-content">{content}</div>
      {timestamp && (
        <div className="message-timestamp">{new Date(timestamp).toLocaleTimeString()}</div>
      )}
    </div>
  )
}

MessageBubble.propTypes = {
  message: PropTypes.shape({
    content: PropTypes.string.isRequired,
    sender: PropTypes.string,
    timestamp: PropTypes.string,
    type: PropTypes.string,
  }).isRequired,
}

export default MessageBubble
