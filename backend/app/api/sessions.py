"""REST API endpoints for session management."""

import logging
import uuid

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.chat_service import chat_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


# --- Request/Response Models ---


class SessionResponse(BaseModel):
    """Response model for a single session."""

    id: str
    title: str
    metadata: dict
    created_at: str
    updated_at: str


class SessionListResponse(BaseModel):
    """Response model for session list."""

    sessions: list[SessionResponse]
    total: int
    limit: int
    offset: int


class CreateSessionRequest(BaseModel):
    """Request model for creating a session."""

    title: str = Field(default="New Chat", max_length=200)


class UpdateSessionRequest(BaseModel):
    """Request model for updating a session."""

    title: str = Field(max_length=200)


class MessageResponse(BaseModel):
    """Response model for a single message."""

    type: str
    sender: str
    content: str


class SessionHistoryResponse(BaseModel):
    """Response model for session history."""

    session_id: str
    messages: list[MessageResponse]
    count: int


# --- Endpoints ---


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> SessionListResponse:
    """
    List all chat sessions.

    Returns sessions ordered by most recent activity (updated_at desc).
    """
    sessions, total = await chat_service.list_sessions(limit=limit, offset=offset)

    return SessionListResponse(
        sessions=[SessionResponse(**s) for s in sessions],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(request: CreateSessionRequest) -> SessionResponse:
    """
    Create a new chat session.

    Returns the created session.
    """
    session = await chat_service.create_new_session(title=request.title)

    return SessionResponse(**session)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: uuid.UUID) -> SessionResponse:
    """
    Get a specific session by ID.

    Returns 404 if session not found.
    """
    session = await chat_service.get_session(session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(**session)


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: uuid.UUID,
    request: UpdateSessionRequest,
) -> SessionResponse:
    """
    Update a session's title.

    Returns 404 if session not found.
    """
    session = await chat_service.update_session_title(session_id, request.title)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(**session)


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: uuid.UUID) -> None:
    """
    Delete a session and all its messages.

    Returns 404 if session not found.
    Returns 400 if attempting to delete the default session.
    """
    # First check if session exists
    session = await chat_service.get_session(session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check if it's the default session
    if session.get("metadata", {}).get("is_default"):
        raise HTTPException(status_code=400, detail="Cannot delete the default session")

    deleted = await chat_service.delete_session(session_id)

    if not deleted:
        raise HTTPException(status_code=400, detail="Failed to delete session")


@router.get("/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=100),
) -> SessionHistoryResponse:
    """
    Get conversation history for a specific session.

    Returns messages ordered from oldest to newest.
    """
    result = await chat_service.get_session_with_history(session_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")

    session_id, history = result

    messages = [
        MessageResponse(
            type=msg.get("type", "message"),
            sender=msg.get("sender", "unknown"),
            content=msg.get("content", ""),
        )
        for msg in history[:limit]
    ]

    return SessionHistoryResponse(
        session_id=str(session_id),
        messages=messages,
        count=len(messages),
    )
