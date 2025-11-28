"""AI service for handling LLM API interactions with streaming support."""

import logging
import os
from typing import AsyncGenerator

from litellm import acompletion

from app.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """Service for interacting with AI APIs via LiteLLM."""

    def __init__(self):
        """Initialize the AI service with the configured provider."""
        self.provider = settings.ai_provider
        self.model = settings.selected_model

        # Set API keys in environment for LiteLLM
        if settings.anthropic_api_key:
            os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
        if settings.openai_api_key:
            os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        if settings.google_api_key:
            os.environ["GOOGLE_API_KEY"] = settings.google_api_key

        # Validate configuration
        if not self._has_valid_api_key():
            logger.warning(
                f"No API key configured for provider '{self.provider}'. "
                "AI functionality will be disabled."
            )
            self.enabled = False
        else:
            self.enabled = True
            logger.info(
                f"AI service initialized with provider: {self.provider}, model: {self.model}"
            )

    def _has_valid_api_key(self) -> bool:
        """Check if a valid API key exists for the selected provider."""
        key_map = {
            "anthropic": settings.anthropic_api_key,
            "openai": settings.openai_api_key,
            "google": settings.google_api_key,
        }
        return bool(key_map.get(self.provider, False))

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
        if not self.enabled:
            yield f"Error: AI service is not configured. Please set API key for {self.provider}."
            return

        try:
            # Build messages list with system message
            system_prompt = (
                "You are a helpful assistant in a chat application. "
                "Provide clear, concise, and friendly responses."
            )
            messages = [{"role": "system", "content": system_prompt}]

            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history:
                    role = "user" if msg.get("sender") == "user" else "assistant"
                    messages.append({"role": role, "content": msg.get("content", "")})

            # Add current message
            messages.append({"role": "user", "content": message})

            # Stream the response using LiteLLM
            response = await acompletion(
                model=self.model,
                messages=messages,
                stream=True,
                max_tokens=1024,
            )

            async for chunk in response:
                if hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            yield f"Error: Failed to generate response - {str(e)}"


# Global AI service instance
ai_service = AIService()
