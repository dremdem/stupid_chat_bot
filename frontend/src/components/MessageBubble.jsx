import PropTypes from 'prop-types'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import './MessageBubble.css'
import 'highlight.js/styles/github-dark.css'

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
  const isAssistant = sender === 'assistant'
  const isUser = sender === 'user'
  const bubbleClass = `message-bubble ${isAssistant ? 'assistant' : 'user'}`

  return (
    <div className={bubbleClass}>
      <div className="message-sender">{isAssistant ? 'AI Assistant' : 'You'}</div>
      <div className="message-content">
        {isAssistant ? (
          <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
            {content}
          </ReactMarkdown>
        ) : (
          content
        )}
      </div>
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
