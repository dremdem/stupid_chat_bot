"""AI service for handling LLM API interactions with streaming support."""

import logging
from typing import AsyncGenerator

from anthropic import AsyncAnthropic

from app.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """Service for interacting with AI APIs."""

    def __init__(self):
        """Initialize the AI service with the configured provider."""
        self.provider = settings.ai_provider
        if self.provider == "anthropic":
            if not settings.anthropic_api_key:
                logger.warning(
                    "ANTHROPIC_API_KEY not set. AI functionality will be disabled."
                )
                self.client = None
            else:
                self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        else:
            logger.error(f"Unsupported AI provider: {self.provider}")
            self.client = None

    async def generate_response_stream(
        self, message: str, conversation_history: list[dict] | None = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response from the AI.

        Args:
            message: The user's message
            conversation_history: Optional list of previous messages for context

        Yields:
            Chunks of the AI's response as they are generated
        """
        if not self.client:
            yield "Error: AI service is not configured. Please set ANTHROPIC_API_KEY."
            return

        try:
            # Build messages list
            messages = []

            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history:
                    role = "user" if msg.get("sender") == "user" else "assistant"
                    messages.append({"role": role, "content": msg.get("content", "")})

            # Add current message
            messages.append({"role": "user", "content": message})

            # Stream the response
            async with self.client.messages.stream(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=messages,
                system="You are a helpful assistant in a chat application. Provide clear, concise, and friendly responses.",
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            yield f"Error: Failed to generate response - {str(e)}"


# Global AI service instance
ai_service = AIService()
