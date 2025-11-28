"""WebSocket endpoints for real-time chat functionality."""

import json
import logging
from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New connection. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
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


manager = ConnectionManager()


@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for chat functionality.

    Handles:
    - Connection establishment
    - Message broadcasting
    - Connection cleanup
    """
    await manager.connect(websocket)

    try:
        # Send welcome message only to this client
        await websocket.send_text(
            json.dumps(
                {
                    "type": "system",
                    "content": "Connected to chat server",
                    "timestamp": None,
                    "system_type": "connection",
                }
            )
        )

        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message_data = json.loads(data)

                # Broadcast user message to all connected clients
                user_message = {
                    "type": "message",
                    "content": message_data.get("content", ""),
                    "sender": message_data.get("sender", "user"),
                    "timestamp": message_data.get("timestamp"),
                }
                await manager.broadcast(user_message)

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
