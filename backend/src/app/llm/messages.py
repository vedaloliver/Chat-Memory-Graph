# src/app/core/llm/messages.py

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """
    Internal chat message model used throughout the app.

    Mirrors the OpenAI API shape: role + content.
    """
    role: str  # "user", "assistant", "system"
    content: str
