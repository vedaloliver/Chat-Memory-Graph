"""
Shim for backwards compatibility.

The real implementation lives in:
    src/app/conversation/db_conversation_store.py
"""

from src.app.conversation.db_conversation_store import (
    DbConversationStore,
    get_db_conversation_store,
)

__all__ = ["DbConversationStore", "get_db_conversation_store"]
