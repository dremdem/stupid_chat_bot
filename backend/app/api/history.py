"""REST API endpoints for chat history."""

import logging

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.chat_service import chat_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["history"])


class MessageResponse(BaseModel):
    """Response model for a single message."""

    type: str
    sender: str
    content: str


class HistoryResponse(BaseModel):
    """Response model for chat history."""

    messages: list[MessageResponse]
    count: int


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    limit: int = Query(default=50, ge=1, le=100, description="Number of messages to return"),
) -> HistoryResponse:
    """
    Get chat history from the default session.

    Returns the most recent messages from the chat history,
    ordered from oldest to newest.

    Args:
        limit: Maximum number of messages to return (1-100, default 50)

    Returns:
        HistoryResponse with list of messages and count
    """
    # Get or create session and load history
    session_id, _ = await chat_service.get_or_create_session()

    # Get history with pagination
    history = await chat_service.get_conversation_history(session_id, limit=limit)

    messages = [
        MessageResponse(
            type=msg.get("type", "message"),
            sender=msg.get("sender", "unknown"),
            content=msg.get("content", ""),
        )
        for msg in history
    ]

    logger.info(f"Retrieved {len(messages)} messages from history")

    return HistoryResponse(messages=messages, count=len(messages))
