# src/app/core/llm/factory.py

from typing import Sequence, Dict, Any, Optional

from src.app.core.config import get_settings

from .base_client import BaseOpenAIClient
from .chat_client import ChatLlmClient
from .memory_client import MemoryLlmClient
from .messages import ChatMessage


class LlmClient:
    """
    Facade that combines chat + memory behaviours.

    This gives the rest of the app a single object with:
      - chat(messages)
      - extract_memory(chunk_text, existing_summary)
    """

    def __init__(self, base_client: BaseOpenAIClient) -> None:
        self._chat_client = ChatLlmClient.from_base(base_client)
        self._memory_client = MemoryLlmClient.from_base(base_client)

    async def chat(self, messages: Sequence[ChatMessage]) -> str:
        return await self._chat_client.chat(messages)

    async def extract_memory(
        self,
        chunk_text: str,
        existing_summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await self._memory_client.extract_memory(chunk_text, existing_summary)


def get_llm_client() -> LlmClient:
    """
    Factory used by FastAPI dependency injection.
    """
    settings = get_settings()

    base = BaseOpenAIClient(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        use_azure=settings.use_azure,
        azure_endpoint=settings.azure_endpoint,
        azure_api_version=settings.azure_api_version,
    )

    return LlmClient(base)
