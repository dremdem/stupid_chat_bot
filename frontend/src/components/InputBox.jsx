import { useState, useRef, useEffect } from 'react'
import PropTypes from 'prop-types'
import './InputBox.css'

const MAX_CHARS = 2000

/**
 * InputBox component - handles user message input
 */
function InputBox({ onSendMessage, disabled }) {
  const [message, setMessage] = useState('')
  const textareaRef = useRef(null)

  // Auto-resize textarea based on content
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`
    }
  }, [message])

  const handleSubmit = e => {
    e.preventDefault()
    if (message.trim() && !disabled) {
      onSendMessage(message)
      setMessage('')
    }
  }

  const handleKeyDown = e => {
    // Send on Enter, new line on Shift+Enter
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleChange = e => {
    const newValue = e.target.value
    if (newValue.length <= MAX_CHARS) {
      setMessage(newValue)
    }
  }

  const charCount = message.length
  const isNearLimit = charCount > MAX_CHARS * 0.8

  return (
    <form className="input-box" onSubmit={handleSubmit}>
      <div className="input-wrapper">
        <textarea
          ref={textareaRef}
          className="message-input"
          value={message}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
          disabled={disabled}
          rows={1}
        />
        <div className="input-footer">
          <span className={`char-counter ${isNearLimit ? 'warning' : ''}`}>
            {charCount}/{MAX_CHARS}
          </span>
          <button type="submit" className="send-button" disabled={disabled || !message.trim()}>
            Send
          </button>
        </div>
      </div>
    </form>
  )
}

InputBox.propTypes = {
  onSendMessage: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
}

export default InputBox
