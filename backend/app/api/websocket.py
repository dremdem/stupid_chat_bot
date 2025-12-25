"""WebSocket endpoints for real-time chat functionality."""

import json
import logging
import uuid

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.database import async_session_maker
from app.dependencies import USER_ID_COOKIE
from app.services.ai_service import ai_service
from app.services.chat_service import chat_service
from app.services.jwt_service import jwt_service
from app.services.message_limits import MessageLimitsService

logger = logging.getLogger(__name__)

# Cookie name for JWT access token
ACCESS_TOKEN_COOKIE = "access_token"

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self):
        # Map of session_id -> list of connections
        self.session_connections: dict[uuid.UUID, list[WebSocket]] = {}
        # Map of websocket -> (session_id, cookie_user_id, auth_user_id, conversation_history)
        self.connection_sessions: dict[
            WebSocket, tuple[uuid.UUID, str, uuid.UUID | None, list[dict]]
        ] = {}

    def register(
        self,
        websocket: WebSocket,
        session_id: uuid.UUID,
        cookie_user_id: str,
        auth_user_id: uuid.UUID | None,
        history: list[dict],
    ):
        """Register a WebSocket connection for a session (after accept)."""
        # Track connection for this session
        if session_id not in self.session_connections:
            self.session_connections[session_id] = []
        self.session_connections[session_id].append(websocket)

        # Track session info for this connection
        self.connection_sessions[websocket] = (session_id, cookie_user_id, auth_user_id, history)

        user_display = f"auth:{str(auth_user_id)[:8]}" if auth_user_id else f"anon:{cookie_user_id[:8]}"
        logger.info(
            f"New connection for session {session_id} (user: {user_display}...). "
            f"Session connections: {len(self.session_connections[session_id])}"
        )

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.connection_sessions:
            session_id, cookie_user_id, auth_user_id, _ = self.connection_sessions[websocket]

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

    def get_session_info(
        self, websocket: WebSocket
    ) -> tuple[uuid.UUID, str, uuid.UUID | None, list[dict]] | None:
        """Get session info for a connection."""
        return self.connection_sessions.get(websocket)

    def add_to_history(self, websocket: WebSocket, message: dict):
        """Add a message to the connection's conversation history."""
        if websocket not in self.connection_sessions:
            return

        session_id, cookie_user_id, auth_user_id, history = self.connection_sessions[websocket]
        history.append(message)

        # Keep only last 50 messages for context
        if len(history) > 50:
            history = history[-50:]

        self.connection_sessions[websocket] = (session_id, cookie_user_id, auth_user_id, history)


manager = ConnectionManager()


def _get_limit_exceeded_message(user_role: str) -> str:
    """Get the appropriate limit exceeded message based on user role."""
    if user_role == "anonymous":
        return (
            "You've reached your message limit as an anonymous user. "
            "Please sign in to continue chatting with more messages!"
        )
    elif user_role == "user":
        return (
            "You've reached your message limit. "
            "Please contact us at dremdem.ru for extended access."
        )
    else:
        return "You've reached your message limit."


@router.websocket("/ws/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: uuid.UUID | None = Query(default=None),
):
    """
    WebSocket endpoint for chat functionality.

    Query Parameters:
        session_id: Optional session UUID. If not provided, uses the default session.

    Cookies:
        stupidbot_user_id: Required user identifier from cookie.

    Handles:
    - Connection establishment
    - User identification from cookie
    - Session-based history loading
    - Message persistence
    - AI response generation
    - Session-scoped message broadcasting
    """
    # IMPORTANT: Accept the WebSocket FIRST before any async database operations.
    # This prevents "WebSocket closed before connection established" errors
    # if database calls fail or timeout.
    await websocket.accept()

    try:
        # Get cookie-based user_id (for anonymous users)
        cookie_user_id = websocket.cookies.get(USER_ID_COOKIE)

        if not cookie_user_id:
            # No user identity - close connection with error
            logger.warning("WebSocket connection attempted without user cookie")
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "error",
                        "content": "No user identity. Please refresh the page.",
                        "error_code": "NO_USER_ID",
                    }
                )
            )
            await websocket.close(code=4001, reason="No user identity")
            return

        # Check for JWT access_token (for authenticated users)
        auth_user_id = None
        access_token = websocket.cookies.get(ACCESS_TOKEN_COOKIE)
        if access_token:
            auth_user_id = jwt_service.get_user_id_from_token(access_token)
            if auth_user_id:
                logger.info(f"Authenticated user connected: {auth_user_id}")

        # Get session and history for this user
        actual_session_id, history = await chat_service.get_or_create_session(
            user_id=cookie_user_id,
            session_id=session_id,
        )

        # If requested session_id was provided but we got a different one,
        # it means the session didn't belong to this user
        if session_id is not None and actual_session_id != session_id:
            logger.warning(
                f"Session {session_id} not found or doesn't belong to user, "
                f"using default session {actual_session_id}"
            )

        # Get initial message limit info (use auth_user_id if authenticated)
        async with async_session_maker() as db:
            limits_service = MessageLimitsService(db)
            limit_info = await limits_service.get_limit_info(
                cookie_user_id=cookie_user_id,
                auth_user_id=auth_user_id,
            )

        # Register connection (websocket already accepted above)
        manager.register(websocket, actual_session_id, cookie_user_id, auth_user_id, history)

        # Send connection confirmation with session info and limit info
        await manager.send_to_client(
            websocket,
            {
                "type": "system",
                "content": "Connected to chat server",
                "session_id": str(actual_session_id),
                "timestamp": None,
                "system_type": "connection",
                "limit_info": limit_info.to_dict(),
            },
        )

        # Send chat history to the newly connected client
        if history:
            await manager.send_to_client(
                websocket,
                {
                    "type": "history",
                    "session_id": str(actual_session_id),
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

                current_session_id, current_cookie_user_id, current_auth_user_id, current_history = (
                    session_info
                )

                # Check message limits before processing (use auth_user_id if authenticated)
                async with async_session_maker() as db:
                    limits_service = MessageLimitsService(db)
                    can_send, limit_info = await limits_service.check_can_send(
                        cookie_user_id=current_cookie_user_id,
                        auth_user_id=current_auth_user_id,
                    )

                if not can_send:
                    # Send limit exceeded notification
                    await manager.send_to_client(
                        websocket,
                        {
                            "type": "limit_exceeded",
                            "content": _get_limit_exceeded_message(limit_info.user_role),
                            "limit_info": limit_info.to_dict(),
                            "login_required": limit_info.user_role == "anonymous",
                        },
                    )
                    continue

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
                _, _, _, current_history = session_info if session_info else (None, None, None, [])

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

                # Send updated limit info after message exchange
                async with async_session_maker() as db:
                    limits_service = MessageLimitsService(db)
                    updated_limit_info = await limits_service.get_limit_info(
                        cookie_user_id=current_cookie_user_id,
                        auth_user_id=current_auth_user_id,
                    )

                await manager.send_to_client(
                    websocket,
                    {
                        "type": "limit_update",
                        "limit_info": updated_limit_info.to_dict(),
                    },
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
        logger.error(f"WebSocket error: {e}", exc_info=True)
        # Try to send error message to client before closing
        try:
            await websocket.send_text(
                json.dumps({"type": "error", "content": f"Server error: {str(e)}"})
            )
        except Exception:
            pass  # Client may already be disconnected
        manager.disconnect(websocket)
