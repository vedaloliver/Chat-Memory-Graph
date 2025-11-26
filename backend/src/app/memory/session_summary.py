# src/app/core/memory/session_summary.py

from datetime import datetime
from typing import Any, Dict

from sqlalchemy.orm import Session

from src.app.conversation import Conversation
from src.app.models.database_models import SessionSummaryModel


def get_or_create_session_summary(
    db: Session,
    conversation: Conversation,
) -> SessionSummaryModel:
    """
    Get existing SessionSummaryModel for the conversation, or create one.

    MVP: one summary per conversation.
    """
    existing = (
        db.query(SessionSummaryModel)
        .filter(SessionSummaryModel.conversation_id == conversation.id)
        .first()
    )
    if existing:
        # Keep time range in sync with latest messages
        if conversation.messages:
            existing.end_time = conversation.messages[-1].timestamp
        existing.updated_at = datetime.now()
        db.flush()
        return existing

    # Create new summary
    if conversation.messages:
        start_time = conversation.messages[0].timestamp
        end_time = conversation.messages[-1].timestamp
    else:
        now = datetime.now()
        start_time = now
        end_time = now

    summary = SessionSummaryModel(
        conversation_id=conversation.id,
        start_time=start_time,
        end_time=end_time,
        summary_text=None,
        keywords=[],
        themes=[],
    )
    db.add(summary)
    db.flush()
    return summary


def update_session_summary_from_extraction(
    session_summary: SessionSummaryModel,
    summary_data: Dict[str, Any],
    conversation: Conversation,
) -> None:
    """
    Merge the LLM-provided session summary into the SessionSummaryModel.
    """
    summary_text = (summary_data or {}).get("summary_text")
    keywords = (summary_data or {}).get("keywords") or []
    themes = (summary_data or {}).get("themes") or []

    if summary_text:
        session_summary.summary_text = summary_text

    if keywords:
        existing_keywords = set(session_summary.keywords or [])
        for k in keywords:
            if k:
                existing_keywords.add(k)
        session_summary.keywords = list(existing_keywords)

    if themes:
        existing_themes = set(session_summary.themes or [])
        for t in themes:
            if t:
                existing_themes.add(t)
        session_summary.themes = list(existing_themes)

    # Keep temporal span consistent with conversation
    if conversation.messages:
        session_summary.start_time = conversation.messages[0].timestamp
        session_summary.end_time = conversation.messages[-1].timestamp

    session_summary.updated_at = datetime.now()
