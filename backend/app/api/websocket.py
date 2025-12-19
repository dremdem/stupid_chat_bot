"""WebSocket endpoints for real-time chat functionality."""

import json
import logging
import uuid

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.services.ai_service import ai_service
from app.services.chat_service import chat_service

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self):
        # Map of session_id -> list of connections
        self.session_connections: dict[uuid.UUID, list[WebSocket]] = {}
        # Map of websocket -> (session_id, conversation_history)
        self.connection_sessions: dict[WebSocket, tuple[uuid.UUID, list[dict]]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        session_id: uuid.UUID,
        history: list[dict],
    ):
        """Accept and register a new WebSocket connection for a session."""
        await websocket.accept()

        # Track connection for this session
        if session_id not in self.session_connections:
            self.session_connections[session_id] = []
        self.session_connections[session_id].append(websocket)

        # Track session info for this connection
        self.connection_sessions[websocket] = (session_id, history)

        logger.info(
            f"New connection for session {session_id}. "
            f"Session connections: {len(self.session_connections[session_id])}"
        )

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.connection_sessions:
            session_id, _ = self.connection_sessions[websocket]

            # Remove from session connections
            if session_id in self.session_connections:
                if websocket in self.session_connections[session_id]:
                    self.session_connections[session_id].remove(websocket)

                # Clean up empty session lists
                if not self.session_connections[session_id]:
                    del self.session_connections[session_id]

            # Remove connection tracking
            del self.connection_sessions[websocket]

            logger.info(f"Connection closed for session {session_id}")

    async def broadcast_to_session(self, session_id: uuid.UUID, message: dict):
        """Broadcast a message to all connections in a session."""
        message_json = json.dumps(message)

        if session_id not in self.session_connections:
            return

        for connection in self.session_connections[session_id]:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")

    async def send_to_client(self, websocket: WebSocket, message: dict):
        """Send a message to a specific client."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending to client: {e}")

    def get_session_info(self, websocket: WebSocket) -> tuple[uuid.UUID, list[dict]] | None:
        """Get session info for a connection."""
        return self.connection_sessions.get(websocket)

    def add_to_history(self, websocket: WebSocket, message: dict):
        """Add a message to the connection's conversation history."""
        if websocket not in self.connection_sessions:
            return

        session_id, history = self.connection_sessions[websocket]
        history.append(message)

        # Keep only last 50 messages for context
        if len(history) > 50:
            history = history[-50:]

        self.connection_sessions[websocket] = (session_id, history)


manager = ConnectionManager()


@router.websocket("/ws/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: uuid.UUID | None = Query(default=None),
):
    """
    WebSocket endpoint for chat functionality.

    Query Parameters:
        session_id: Optional session UUID. If not provided, uses the default session.

    Handles:
    - Connection establishment
    - Session-based history loading
    - Message persistence
    - AI response generation
    - Session-scoped message broadcasting
    """
    try:
        # Get session and history
        if session_id:
            # Use specified session
            result = await chat_service.get_session_with_history(session_id)
            if result is None:
                # Session not found - fall back to default
                logger.warning(f"Session {session_id} not found, using default")
                session_id, history = await chat_service.get_or_create_session()
            else:
                session_id, history = result
        else:
            # Use default session
            session_id, history = await chat_service.get_or_create_session()

        # Register connection
        await manager.connect(websocket, session_id, history)

        # Send connection confirmation with session info
        await manager.send_to_client(
            websocket,
            {
                "type": "system",
                "content": "Connected to chat server",
                "session_id": str(session_id),
                "timestamp": None,
                "system_type": "connection",
            },
        )

        # Send chat history to the newly connected client
        if history:
            await manager.send_to_client(
                websocket,
                {
                    "type": "history",
                    "session_id": str(session_id),
                    "messages": history,
                },
            )

        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message_data = json.loads(data)
                content = message_data.get("content", "")

                # Get current session info
                session_info = manager.get_session_info(websocket)
                if session_info is None:
                    continue

                current_session_id, current_history = session_info

                # Broadcast user message to all connections in this session
                user_message = {
                    "type": "message",
                    "content": content,
                    "sender": message_data.get("sender", "user"),
                    "timestamp": message_data.get("timestamp"),
                }
                await manager.broadcast_to_session(current_session_id, user_message)

                # Add to in-memory history
                manager.add_to_history(websocket, user_message)

                # Save user message to database
                await chat_service.save_user_message(
                    session_id=current_session_id,
                    content=content,
                )

                # Send typing indicator to session
                await manager.broadcast_to_session(
                    current_session_id,
                    {
                        "type": "typing",
                        "sender": "assistant",
                        "is_typing": True,
                    },
                )

                # Get updated history for context
                session_info = manager.get_session_info(websocket)
                _, current_history = session_info if session_info else (None, [])

                # Generate AI response with streaming
                ai_response_content = ""
                async for chunk in ai_service.generate_response_stream(
                    content,
                    current_history[-10:],  # Last 10 messages for context
                ):
                    ai_response_content += chunk

                    # Send streaming chunk to all clients in session
                    await manager.broadcast_to_session(
                        current_session_id,
                        {
                            "type": "ai_stream",
                            "content": chunk,
                            "sender": "assistant",
                        },
                    )

                # Send stream end signal
                await manager.broadcast_to_session(
                    current_session_id,
                    {
                        "type": "ai_stream_end",
                        "sender": "assistant",
                    },
                )

                # Add complete AI response to in-memory history
                ai_message = {
                    "type": "message",
                    "content": ai_response_content,
                    "sender": "assistant",
                    "timestamp": None,
                }
                manager.add_to_history(websocket, ai_message)

                # Save AI response to database
                await chat_service.save_assistant_message(
                    session_id=current_session_id,
                    content=ai_response_content,
                    meta={"provider": ai_service.provider, "model": ai_service.model},
                )

            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                await websocket.send_text(
                    json.dumps({"type": "error", "content": "Invalid message format"})
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
