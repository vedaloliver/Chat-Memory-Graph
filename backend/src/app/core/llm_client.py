# src/app/core/llm_client.py
"""
Backwards-compatibility shim.

Previously, LLM functionality lived in this module.
It now lives under src.app.core.llm, but we re-export the
public API so existing imports keep working:

    from src.app.core.llm_client import LlmClient, get_llm_client, AppError, ChatMessage
"""

from src.app.llm import (  # type: ignore[assignment]
    AppError,
    ChatMessage,
    LlmClient,
    get_llm_client,
)

__all__ = [
    "AppError",
    "ChatMessage",
    "LlmClient",
    "get_llm_client",
]
