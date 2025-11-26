# src/app/core/memory/pipeline.py

from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session

from src.app.conversation.db_conversation_store import Conversation
from src.app.llm import LlmClient, AppError
from src.app.core.logging_utils import get_logger

from .chunking import get_latest_user_assistant_pair, create_memory_chunk
from .session_summary import get_or_create_session_summary, update_session_summary_from_extraction
from .entities import upsert_entities
from .triples import upsert_triples_and_links

logger = get_logger(__name__)


async def update_memory_after_turn(
    db: Session,
    llm: LlmClient,
    conversation: Conversation,
) -> None:
    """
    Main entrypoint: run after each successful chat turn.

    Best-effort: logs and swallows errors so chat doesn't break if memory fails.
    """
    pair = get_latest_user_assistant_pair(conversation)
    if not pair:
        logger.info(
            "Skipping memory update for conversation %s: "
            "could not find latest user–assistant pair",
            conversation.id,
        )
        return

    try:
        # 1) Session summary
        session_summary = get_or_create_session_summary(db, conversation)

        # 2) Chunk
        chunk = create_memory_chunk(db, conversation, session_summary, pair)

        # 3) Call memory LLM
        existing_summary_text = session_summary.summary_text or ""
        extraction = await llm.extract_memory(
            chunk_text=chunk.text,
            existing_summary=existing_summary_text,
        )

        entities_data: List[Dict[str, Any]] = extraction.get("entities") or []
        triples_data: List[Dict[str, Any]] = extraction.get("triples") or []
        summary_data: Dict[str, Any] = extraction.get("session_summary") or {}

        # 4) Entities
        entity_cache = upsert_entities(db, entities_data)

        # 5) Triples + links
        upsert_triples_and_links(
            db=db,
            triples_data=triples_data,
            entity_cache=entity_cache,
            session_summary=session_summary,
            chunk=chunk,
        )

        # 6) Update session summary content
        update_session_summary_from_extraction(
            session_summary=session_summary,
            summary_data=summary_data,
            conversation=conversation,
        )

        # Commit everything from this pipeline
        db.commit()

        logger.info(
            "Memory update complete for conversation %s: "
            "summary_id=%s chunk_id=%s entities=%d triples=%d",
            conversation.id,
            session_summary.id,
            chunk.id,
            len(entity_cache),
            len(triples_data),
        )

    except AppError as e:
        logger.error(
            "Memory LLM error for conversation %s: %s",
            conversation.id,
            e.message,
        )
        db.rollback()
    except Exception as e:
        logger.exception(
            "Unexpected error updating memory for conversation %s: %s",
            conversation.id,
            e,
        )
        db.rollback()
