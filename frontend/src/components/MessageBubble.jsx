import PropTypes from 'prop-types'
import { motion } from 'framer-motion'
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
      <motion.div
        className="message-bubble system"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="message-content">{content}</div>
      </motion.div>
    )
  }

  // Regular chat messages
  const isAssistant = sender === 'assistant'
  const bubbleClass = `message-bubble ${isAssistant ? 'assistant' : 'user'}`

  return (
    <motion.div
      className={bubbleClass}
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
    >
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
    </motion.div>
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
