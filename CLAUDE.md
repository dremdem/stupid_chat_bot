# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the "Stupid Chat Bot" - a simple, straightforward AI-powered chat application. The project demonstrates a clean implementation of a modern chat bot using FastAPI for the backend and React for the frontend.

## Tech Stack

- **Backend**: FastAPI (Python 3.9+)
  - WebSocket support for real-time messaging
  - AI integration with streaming responses
  - RESTful API design

- **Frontend**: React with Vite
  - Modern hooks-based components
  - Real-time WebSocket communication
  - Rich markdown and code rendering

- **AI Integration**: LLM APIs (OpenAI, Anthropic, or similar)

## Development Commands

*To be added in Phase 1 during project setup.*

Expected structure:
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Architecture

### High-Level Design
- **Frontend**: React SPA connecting via WebSocket
- **Backend**: FastAPI server handling WebSocket connections and AI proxy
- **AI Service**: External LLM API for chat responses
- **Storage**: Database for chat history (to be implemented in Phase 5)

### Key Components
- WebSocket Manager for real-time bidirectional communication
- Chat Service for message processing
- AI Client with streaming support
- Message persistence layer
- Rich UI with animations and markdown rendering

See [README.md](./README.md) for detailed architecture diagrams and component descriptions.

## Implementation Status

The project is currently in **Phase 0** (Documentation Phase). See README.md for the complete 6-phase implementation roadmap.

## Important Notes

- Follow the phased implementation approach outlined in README.md
- Prioritize simplicity ("stupid" chat bot philosophy)
- Use TypeScript for frontend in later phases
- Implement proper error handling and user feedback
- Test WebSocket connections thoroughly
- Follow security best practices for API key management
- Consider rate limiting for AI API calls
