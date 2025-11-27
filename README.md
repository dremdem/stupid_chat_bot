# Stupid Chat Bot

The most stupid chat bot with AI - a simple, straightforward chat application that connects users with an AI assistant.

## Use Cases

This chat bot is designed for casual, collaborative interactions:

- **Multi-user chat without authentication** - No login required, just jump in and start chatting
- **Anonymous or named participation** - Users can choose a display name or stay anonymous
- **AI responds when mentioned/tagged** - The AI will answer when specifically called upon using @mentions or tags
- **Persistent history while users are online** - Chat history is maintained as long as at least one user remains connected

## Tech Stack

### Backend
- **FastAPI** - Modern, fast Python web framework for building APIs
  - Async support for handling multiple concurrent connections
  - Automatic API documentation with Swagger/OpenAPI
  - WebSocket support for real-time chat functionality
  - Type hints and data validation with Pydantic

### Frontend
- **React** - Component-based UI library
  - Modern hooks-based architecture
  - Efficient virtual DOM for smooth updates
  - Rich ecosystem of chat-related libraries

### AI Integration
- LLM API integration (OpenAI, Anthropic, or similar)
- Streaming response support for real-time message generation

## Architecture

### High-Level Overview

```mermaid
graph TB
    subgraph Frontend["React Frontend"]
        UI["Chat UI"]
        Flow["Message Flow"]
        State["State Mgmt"]
    end

    subgraph Backend["FastAPI Backend"]
        WS["WebSocket"]
        Logic["Chat Logic"]
        Proxy["AI Proxy"]
    end

    subgraph AI["AI Service (LLM API)"]
        Model["Claude/GPT"]
        Stream["Streaming"]
    end

    subgraph Storage["Storage Layer"]
        History["Chat History"]
        Sessions["User Sessions"]
        Meta["Metadata"]
    end

    Frontend <-->|HTTP/WS| Backend
    Backend <-->|HTTP API| AI
    Backend --> Storage
```

### Component Details

#### Frontend Components
- **ChatContainer** - Main container managing chat state
- **MessageList** - Scrollable message history with virtualization
- **MessageBubble** - Individual message display with markdown support
- **InputBox** - User input with auto-resize and keyboard shortcuts
- **TypingIndicator** - Animated indicator shown when AI is generating any response
- **ChatHeader** - Title, status, and controls

#### Backend Services
- **WebSocket Manager** - Handles real-time connections
- **Chat Service** - Business logic for message processing
- **AI Client** - Wrapper for LLM API calls with streaming
- **History Manager** - Storage and retrieval of conversations

## Fancy Chat Component

For the "most fancy" chat experience, we recommend:

### UI Features
- **Smooth Animations**
  - Message entrance animations (fade + slide)
  - Typing indicator with animated dots
  - Smooth auto-scroll to latest message

- **Rich Message Rendering**
  - Markdown support (code blocks, lists, links)
  - Syntax highlighting for code snippets
  - LaTeX rendering for mathematical expressions
  - Image/file preview support

- **Modern Design**
  - Gradient backgrounds or subtle patterns
  - Glass morphism effects for message bubbles
  - Dark/light theme toggle
  - Custom emoji reactions
  - Avatar support

### Recommended Libraries
- **react-markdown** - Markdown rendering
- **highlight.js** or **prism-react-renderer** - Code syntax highlighting
- **framer-motion** - Smooth animations
- **react-window** or **react-virtuoso** - Efficient list virtualization for long chats
- **emoji-mart** - Emoji picker
- **react-hot-toast** - Notifications

### Example Component Structure
```jsx
<ChatContainer>
  <ChatHeader title="Stupid Chat Bot" status="online" />
  <MessageList>
    {messages.map(msg => (
      <MessageBubble
        key={msg.id}
        content={msg.content}
        sender={msg.sender}
        timestamp={msg.timestamp}
        animated={true}
      />
    ))}
    <TypingIndicator visible={isAiTyping} />
  </MessageList>
  <InputBox
    onSend={handleSendMessage}
    placeholder="Type your message..."
    maxLength={2000}
  />
</ChatContainer>
```

## Implementation Phases

### Phase 1: Foundation Setup (Week 1)
**Goal**: Basic project structure and development environment

- [ ] Initialize repository structure
  ```
  stupid_chat_bot/
  ├── backend/
  │   ├── app/
  │   │   ├── main.py
  │   │   ├── api/
  │   │   ├── services/
  │   │   └── models/
  │   ├── requirements.txt
  │   └── .env.example
  ├── frontend/
  │   ├── src/
  │   │   ├── components/
  │   │   ├── services/
  │   │   └── App.jsx
  │   ├── package.json
  │   └── vite.config.js
  └── docker-compose.yml
  ```

- [ ] Set up FastAPI backend skeleton
  - Basic app structure with CORS
  - Health check endpoint
  - Environment configuration

- [ ] Set up React frontend with Vite
  - Project scaffolding
  - Basic routing (if needed)
  - Dev server configuration

- [ ] Create Docker setup for local development
- [ ] Set up linting and formatting (Black, ESLint, Prettier)

**Deliverables**:
- Running backend on `http://localhost:8000`
- Running frontend on `http://localhost:5173`
- Docker containers for both services

---

### Phase 2: Basic Chat Functionality (Week 2)
**Goal**: Simple non-AI chat working end-to-end

- [ ] Backend: WebSocket endpoint
  - Connection management
  - Message broadcasting
  - Basic error handling

- [ ] Frontend: Basic chat UI
  - Simple message list
  - Input box
  - Send/receive messages via WebSocket

- [ ] Frontend: Message state management
  - Local state or Context API
  - Message history array
  - Auto-scroll to bottom

- [ ] Basic styling with CSS/Tailwind
  - Message bubbles (user vs bot)
  - Responsive layout
  - Mobile-friendly design

**Deliverables**:
- Users can type and see messages in real-time
- Messages are broadcast to all connected users

---

### Phase 3: AI Integration (Week 3)
**Goal**: Connect to LLM and stream responses

- [ ] Backend: AI service integration
  - Choose AI provider (OpenAI, Anthropic, etc.)
  - Implement API client with streaming
  - Environment variable configuration for API keys

- [ ] Backend: Chat endpoint with AI
  - Process user messages
  - Stream AI responses via WebSocket
  - Handle API errors gracefully

- [ ] Frontend: Handle streaming responses
  - Display partial messages as they arrive
  - Typing indicator during generation
  - Stop generation button

- [ ] Frontend: Message formatting
  - Markdown rendering
  - Code syntax highlighting
  - Copy button for code blocks

**Deliverables**:
- Functional AI chat bot
- Streaming responses visible in real-time
- Proper error messages for API failures

---

### Phase 4: Enhanced UI/UX (Week 4)
**Goal**: Make it "fancy" with animations and polish

- [ ] Frontend: Implement fancy components
  - Smooth message animations (framer-motion)
  - Gradient backgrounds or themes
  - Glass morphism effects
  - Custom scrollbar

- [ ] Frontend: Rich features
  - Theme toggle (dark/light)
  - Emoji picker
  - Message reactions
  - Timestamp formatting

- [ ] Frontend: Better input handling
  - Auto-resize textarea
  - Keyboard shortcuts (Enter to send, Shift+Enter for newline)
  - Character counter
  - Disabled state during sending

- [ ] Polish and refinements
  - Loading states
  - Empty state design
  - Error state designs
  - Toast notifications

**Deliverables**:
- Polished, animated chat interface
- Smooth user experience
- Professional-looking design

---

### Phase 5: Persistence & History (Week 5)
**Goal**: Save and retrieve chat history

- [ ] Backend: Database setup
  - Choose database (PostgreSQL, SQLite, or MongoDB)
  - Set up ORM (SQLAlchemy or motor)
  - Create chat message schema

- [ ] Backend: History API
  - Save messages to database
  - Retrieve conversation history
  - Pagination for long chats

- [ ] Backend: Session management
  - Create/retrieve chat sessions
  - Multi-conversation support
  - Session metadata

- [ ] Frontend: History features
  - Load previous messages on mount
  - Infinite scroll for history
  - Sidebar with past conversations
  - Clear/delete conversation

**Deliverables**:
- Messages persist across page refreshes
- Users can access conversation history
- Multiple chat sessions supported

---

### Phase 6: Testing & Deployment (Week 6)
**Goal**: Production-ready application

- [ ] Backend: Testing
  - Unit tests for services
  - Integration tests for API endpoints
  - WebSocket connection tests

- [ ] Frontend: Testing
  - Component tests with React Testing Library
  - E2E tests with Playwright/Cypress
  - Accessibility testing

- [ ] Performance optimization
  - Message list virtualization
  - Image lazy loading
  - Bundle size optimization
  - Backend response caching

- [ ] Deployment setup
  - Choose hosting (Railway, Render, Vercel, AWS, etc.)
  - CI/CD pipeline
  - Environment variable management
  - SSL/HTTPS configuration

- [ ] Documentation
  - API documentation (auto-generated by FastAPI)
  - User guide
  - Deployment guide
  - Contributing guidelines

**Deliverables**:
- Tested, production-ready application
- Deployed and accessible online
- Complete documentation

---

## Optional Enhancements (Post-MVP)

### Advanced Features
- **Multi-modal Support**: Image upload and analysis
- **Voice Input**: Speech-to-text integration
- **File Attachments**: Document upload and processing
- **Search**: Full-text search across chat history
- **Export**: Download conversations as PDF/TXT

### User Features
- **Authentication**: User accounts and login
- **Profiles**: Customizable user profiles and avatars
- **Sharing**: Share conversations via link
- **Favorites**: Bookmark important messages
- **Multi-language**: i18n support

### System Features
- **Rate Limiting**: Prevent API abuse
- **Analytics**: Usage tracking and metrics
- **Admin Panel**: Monitor system health
- **API Rate Limits**: Manage AI API costs
- **Caching**: Redis for session and response caching

## Getting Started

### Prerequisites
- Python 3.12
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- Node.js 18+
- Docker (optional)

### Development Setup

(To be completed in Phase 1)

### Environment Variables

(To be completed in Phase 1)

## Contributing

This is the "stupid chat bot" - contributions are welcome! Please feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## License

MIT License - see [LICENSE](LICENSE) file for details
