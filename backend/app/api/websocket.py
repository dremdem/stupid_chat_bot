"""WebSocket endpoints for real-time chat functionality."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
import logging

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
        logger.info(
            f"Connection closed. Total connections: {len(self.active_connections)}"
        )

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
            json.dumps({
                "type": "system",
                "content": "Connected to chat server",
                "timestamp": None,
                "system_type": "connection"
            })
        )

        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message_data = json.loads(data)

                # Echo back for now (Phase 2 requirement)
                # In Phase 3, this will be replaced with AI integration
                response = {
                    "type": "message",
                    "content": message_data.get("content", ""),
                    "sender": message_data.get("sender", "user"),
                    "timestamp": message_data.get("timestamp")
                }

                # Broadcast to all connected clients
                await manager.broadcast(response)

                # Echo bot response (for Phase 2 testing)
                if message_data.get("content"):
                    echo_response = {
                        "type": "message",
                        "content": f"Echo: {message_data.get('content')}",
                        "sender": "bot",
                        "timestamp": None
                    }
                    await manager.broadcast(echo_response)

            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                await websocket.send_text(
                    json.dumps({
                        "type": "error",
                        "content": "Invalid message format"
                    })
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
