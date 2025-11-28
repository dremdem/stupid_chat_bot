import PropTypes from 'prop-types';
import './ChatHeader.css';

/**
 * ChatHeader component - displays the chat title and connection status
 */
function ChatHeader({ status }) {
  const getStatusColor = () => {
    switch (status) {
      case 'connected':
        return 'green';
      case 'disconnected':
      case 'failed':
        return 'red';
      case 'error':
        return 'orange';
      default:
        return 'gray';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'connected':
        return 'Connected';
      case 'disconnected':
        return 'Disconnected';
      case 'failed':
        return 'Connection Failed';
      case 'error':
        return 'Connection Error';
      default:
        return 'Connecting...';
    }
  };

  return (
    <div className="chat-header">
      <div className="chat-title">
        <h1>Stupid Chat Bot</h1>
        <p className="chat-subtitle">A simple, straightforward chat</p>
      </div>
      <div className="connection-status">
        <span className={`status-indicator ${getStatusColor()}`}></span>
        <span className="status-text">{getStatusText()}</span>
      </div>
    </div>
  );
}

ChatHeader.propTypes = {
  status: PropTypes.string.isRequired,
};

export default ChatHeader;
