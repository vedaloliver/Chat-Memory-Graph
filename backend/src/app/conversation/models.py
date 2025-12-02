# src/app/conversation/models.py

from typing import List, Optional, Dict, Any
from uuid import uuid4
from datetime import datetime

from pydantic import BaseModel, Field
from src.app.llm import ChatMessage


class MessageWithTimestamp(ChatMessage):
    """ChatMessage with added timestamp."""
    timestamp: datetime = Field(default_factory=datetime.now)


class Conversation(BaseModel):
    """Represents a conversation with history and metadata."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: Optional[str] = None
    messages: List[MessageWithTimestamp] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_message(self, message: ChatMessage) -> None:
        """Append a message and auto-update timestamps."""
        if isinstance(message, MessageWithTimestamp):
            msg = message
        else:
            msg = MessageWithTimestamp(
                role=message.role,
                content=message.content,
                timestamp=datetime.now(),
            )

        self.messages.append(msg)
        self.updated_at = datetime.now()

        # Simple auto title (first user message)
        if not self.title and msg.role == "user" and len(self.messages) <= 2:
            words = msg.content.split()
            preview = " ".join(words[:5])
            self.title = preview + ("..." if len(words) > 5 else "")

    def update_metadata(self, title: Optional[str] = None) -> None:
        if title is not None:
            self.title = title
        self.updated_at = datetime.now()
