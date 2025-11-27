import { useState, useEffect } from 'react';
import ChatHeader from './components/ChatHeader';
import MessageList from './components/MessageList';
import InputBox from './components/InputBox';
import websocketService from './services/websocket';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('connecting');

  useEffect(() => {
    // Connect to WebSocket
    websocketService.connect();

    // Handle incoming messages
    websocketService.onMessage((message) => {
      setMessages((prev) => [
        ...prev,
        {
          ...message,
          id: Date.now() + Math.random(), // Simple unique ID
        },
      ]);
    });

    // Handle connection status changes
    websocketService.onConnectionChange((status) => {
      setConnectionStatus(status);
    });

    // Cleanup on unmount
    return () => {
      websocketService.disconnect();
    };
  }, []);

  const handleSendMessage = (content) => {
    const message = {
      content,
      sender: 'user',
      timestamp: new Date().toISOString(),
    };

    websocketService.sendMessage(message);
  };

  return (
    <div className="app">
      <ChatHeader status={connectionStatus} />
      <MessageList messages={messages} />
      <InputBox
        onSendMessage={handleSendMessage}
        disabled={connectionStatus !== 'connected'}
      />
    </div>
  );
}

export default App;
