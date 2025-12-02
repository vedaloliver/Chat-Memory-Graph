# src/app/core/llm/chat_client.py

from typing import Sequence

from .base_client import BaseOpenAIClient
from .messages import ChatMessage
from .errors import AppError


class ChatLlmClient:
    """
    High-level chat client for normal assistant behaviour.

    Wraps BaseOpenAIClient and exposes a simple `chat(messages)` method.
    """

    def __init__(self, base_client: BaseOpenAIClient) -> None:
        self._base = base_client

    @classmethod
    def from_base(cls, base_client: BaseOpenAIClient) -> "ChatLlmClient":
        return cls(base_client)

    async def chat(self, messages: Sequence[ChatMessage]) -> str:
        """
        Sends the full chat history to the LLM and returns the assistant reply text.

        Raises:
            AppError if the response has no choices.
        """
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        response = await self._base.create_chat_completion(openai_messages)

        if not getattr(response, "choices", None) or len(response.choices) == 0:
            raise AppError("LLM returned empty response", 502)

        return response.choices[0].message.content
