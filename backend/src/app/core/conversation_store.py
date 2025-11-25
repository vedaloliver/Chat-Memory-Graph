"""
Shim for backwards compatibility.
All logic moved to src/app/conversation/.
"""

from src.app.conversation import (
    Conversation,
    MessageWithTimestamp,
    ConversationStore,
)

# Keep the singleton behaviour identical to before
_conversation_store: ConversationStore | None = None


def get_conversation_store(max_conversations: int = 1000) -> ConversationStore:
    global _conversation_s
