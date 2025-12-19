"""WebSocket endpoints for real-time chat functionality."""

import json
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.ai_service import ai_service
from app.services.chat_service import chat_service

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.session_id: uuid.UUID | None = None
        self.conversation_history: list[dict] = []

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New connection. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Connection closed. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        message_json = json.dumps(message)
        for connection in self.active_connections:
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

    def add_to_history(self, message: dict):
        """Add a message to in-memory conversation history."""
        self.conversation_history.append(message)
        # Keep only last 50 messages for context
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]

    async def initialize_session(self):
        """Initialize chat session and load history from database."""
        if self.session_id is None:
            self.session_id, history = await chat_service.get_or_create_session()
            self.conversation_history = history
            logger.info(f"Initialized session {self.session_id}")


manager = ConnectionManager()


@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for chat functionality.

    Handles:
    - Connection establishment
    - History loading from database
    - Message persistence
    - AI response generation
    - Message broadcasting
    """
    await manager.connect(websocket)

    try:
        # Initialize session and load history from database
        await manager.initialize_session()

        # Send connection confirmation
        await manager.send_to_client(
            websocket,
            {
                "type": "system",
                "content": "Connected to chat server",
                "timestamp": None,
                "system_type": "connection",
            },
        )

        # Send chat history to the newly connected client
        if manager.conversation_history:
            await manager.send_to_client(
                websocket,
                {
                    "type": "history",
                    "messages": manager.conversation_history,
                },
            )

        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message_data = json.loads(data)
                content = message_data.get("content", "")

                # Broadcast user message to all connected clients
                user_message = {
                    "type": "message",
                    "content": content,
                    "sender": message_data.get("sender", "user"),
                    "timestamp": message_data.get("timestamp"),
                }
                await manager.broadcast(user_message)

                # Add to in-memory history
                manager.add_to_history(user_message)

                # Save user message to database
                await chat_service.save_user_message(
                    session_id=manager.session_id,
                    content=content,
                )

                # Send typing indicator
                await manager.broadcast(
                    {
                        "type": "typing",
                        "sender": "assistant",
                        "is_typing": True,
                    }
                )

                # Generate AI response with streaming
                ai_response_content = ""
                async for chunk in ai_service.generate_response_stream(
                    content,
                    manager.conversation_history[-10:],  # Last 10 messages for context
                ):
                    ai_response_content += chunk

                    # Send streaming chunk to all clients
                    await manager.broadcast(
                        {
                            "type": "ai_stream",
                            "content": chunk,
                            "sender": "assistant",
                        }
                    )

                # Send stream end signal
                await manager.broadcast(
                    {
                        "type": "ai_stream_end",
                        "sender": "assistant",
                    }
                )

                # Add complete AI response to in-memory history
                ai_message = {
                    "type": "message",
                    "content": ai_response_content,
                    "sender": "assistant",
                    "timestamp": None,
                }
                manager.add_to_history(ai_message)

                # Save AI response to database
                await chat_service.save_assistant_message(
                    session_id=manager.session_id,
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
