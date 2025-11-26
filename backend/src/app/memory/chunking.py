# src/app/core/memory/chunking.py

from datetime import datetime
from typing import Dict, Optional

from sqlalchemy.orm import Session

from src.app.conversation import Conversation, MessageWithTimestamp
from src.app.models.database_models import SessionSummaryModel, MemoryChunkModel


def get_latest_user_assistant_pair(
    conversation: Conversation,
) -> Optional[Dict[str, MessageWithTimestamp]]:
    """
    Find the latest [user, assistant] message pair in the conversation.

    Returns:
        {"user": MessageWithTimestamp, "assistant": MessageWithTimestamp}
        or None if we can't form a pair.
    """
    messages = conversation.messages
    if len(messages) < 2:
        return None

    # Walk backwards to find the last assistant, then the nearest user before it.
    last_assistant_idx = None
    for idx in range(len(messages) - 1, -1, -1):
        if messages[idx].role == "assistant":
            last_assistant_idx = idx
            break

    if last_assistant_idx is None:
        return None

    last_user_idx = None
    for idx in range(last_assistant_idx - 1, -1, -1):
        if messages[idx].role == "user":
            last_user_idx = idx
            break

    if last_user_idx is None:
        return None

    return {
        "user": messages[last_user_idx],
        "assistant": messages[last_assistant_idx],
    }


def create_memory_chunk(
    db: Session,
    conversation: Conversation,
    session_summary: SessionSummaryModel,
    pair: Dict[str, MessageWithTimestamp],
) -> MemoryChunkModel:
    """
    Create a MemoryChunkModel for the user–assistant pair.
    """
    user_msg = pair["user"]
    assistant_msg = pair["assistant"]

    chunk_text = f"user: {user_msg.content}\nassistant: {assistant_msg.content}"

    chunk = MemoryChunkModel(
        conversation_id=conversation.id,
        session_summary_id=session_summary.id,
        # For now we leave message links optional; MVP focuses on raw text.
        start_message_id=None,
        end_message_id=None,
        text=chunk_text,
        topic_hint=None,
        timestamp=assistant_msg.timestamp or datetime.now(),
    )
    db.add(chunk)
    db.flush()
    return chunk
