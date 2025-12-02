from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

# Error message constants
ERROR_NO_MESSAGE = (
    "Either 'message' or 'messages' with at least one user message must be provided"
)

# Parameter description constants
DESC_USE_DB = (
    "Whether to use the database storage (True) or in-memory storage (False)"
)

from src.app.llm import LlmClient, get_llm_client, AppError, ChatMessage
from src.app.conversation import Conversation, get_conversation_store
from src.app.conversation.db_conversation_store import (
    get_db_conversation_store,
    DbConversationStore,
)
from src.app.db.session import get_db

from src.app.memory import update_memory_after_turn
from src.app.core.logging_utils import get_logger
from src.app.models.chat import (
    ChatRequest,
    ChatResponse,
    ConversationMetadata,
    ConversationsResponse,
    ConversationDetail,
    ConversationMessage
)

router = APIRouter()
logger = get_logger(__name__)

# Store the latest conversation ID for convenience in testing
_latest_conversation_id: Optional[str] = None


@router.get("/conversations", response_model=ConversationsResponse)
async def list_conversations(
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Maximum number of conversations to return",
    ),
    db: Session = Depends(get_db),
    use_db: bool = Query(True, description=DESC_USE_DB),
) -> ConversationsResponse:
    """
    List available conversations.
    """
    if use_db:
        # Use SQLAlchemy store
        conversation_store = get_db_conversation_store(db)
        conversations = conversation_store.list_conversations(limit=limit)

        # Convert to metadata objects
        metadata_list = [
            ConversationMetadata(
                id=conv.id,
                title=conv.title,
                message_count=len(conv.messages),
                created_at=conv.created_at.isoformat(),
                updated_at=conv.updated_at.isoformat(),
            )
            for conv in conversations
        ]
    else:
        # Use in-memory store (legacy)
        conversation_store = get_conversation_store()
        all_conversations = conversation_store._conversations.values()

        # Sort conversations by updated_at (most recent first)
        sorted_conversations = sorted(
            all_conversations,
            key=lambda c: c.updated_at,
            reverse=True,
        )[:limit]

        # Convert to metadata objects
        metadata_list = [
            ConversationMetadata(
                id=conv.id,
                title=conv.title,
                message_count=len(conv.messages),
                created_at=conv.created_at.isoformat(),
                updated_at=conv.updated_at.isoformat(),
            )
            for conv in sorted_conversations
        ]

    return ConversationsResponse(conversations=metadata_list)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str = Path(
        ..., description="ID of the conversation to retrieve"
    ),
    db: Session = Depends(get_db),
    use_db: bool = Query(True, description=DESC_USE_DB),
) -> ConversationDetail:
    """
    Get detailed information about a conversation, including all messages.
    """
    if use_db:
        conversation_store = get_db_conversation_store(db)
    else:
        conversation_store = get_conversation_store()

    conversation = _get_conversation_or_404(conversation_store, conversation_id)

    # Convert the conversation to the response model
    messages = [
        ConversationMessage(
            role=msg.role,
            content=msg.content,
            timestamp=msg.timestamp.isoformat(),
        )
        for msg in conversation.messages
    ]

    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at.isoformat(),
        updated_at=conversation.updated_at.isoformat(),
        messages=messages,
    )


@router.post("/newchat", response_model=ChatResponse)
async def new_chat(
    req: ChatRequest,
    llm: LlmClient = Depends(get_llm_client),
    db: Session = Depends(get_db),
    use_db: bool = Query(True, description=DESC_USE_DB),
) -> ChatResponse:
    """
    Create a new conversation and send the first message.
    This endpoint always creates a new conversation regardless of any conversation_id passed.
    """
    global _latest_conversation_id

    try:
        # Validate that we have a message in some form
        try:
            user_message = req.user_message
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=ERROR_NO_MESSAGE,
            )

        # Select the appropriate store
        if use_db:
            conversation_store = get_db_conversation_store(db)
        else:
            conversation_store = get_conversation_store()

        # Always create a new conversation
        conversation = conversation_store.create_conversation(req.system_prompt)

        # Add the new user message to the conversation
        conversation.add_message(ChatMessage(role="user", content=user_message))

        # Get reply from LLM using full conversation history
        reply = await llm.chat(conversation.messages)

        # Add the assistant's reply to the conversation history
        conversation.add_message(ChatMessage(role="assistant", content=reply))

        # Update the conversation in the store
        conversation_store.update_conversation(conversation)

        # Store the latest conversation ID for convenience in testing
        _latest_conversation_id = conversation.id

        # Fire the memory update pipeline (best-effort; errors are logged inside)
        await update_memory_after_turn(db=db, llm=llm, conversation=conversation)

        return ChatResponse(reply=reply, conversation_id=conversation.id)

    except AppError as e:
        # Convert app errors to HTTP exceptions with proper status codes
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except HTTPException:
        # Let explicit HTTPExceptions bubble through
        raise
    except Exception as e:
        logger.exception("Unexpected error in /newchat: %s", e)
        # Catch-all for unexpected errors
        raise HTTPException(
            status_code=500, detail=f"Unexpected error: {str(e)}"
        )


@router.post("/continue", response_model=ChatResponse)
async def continue_chat(
    req: ChatRequest,
    llm: LlmClient = Depends(get_llm_client),
    db: Session = Depends(get_db),
    use_db: bool = Query(True, description=DESC_USE_DB),
) -> ChatResponse:
    """
    Continue the most recent conversation or a specific conversation if ID is provided.
    """
    global _latest_conversation_id

    try:
        # Validate that we have a message in some form
        try:
            user_message = req.user_message
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=ERROR_NO_MESSAGE,
            )

        # Get conversation ID - either from request, or use the latest one
        conversation_id = req.conversation_id or _latest_conversation_id

        if not conversation_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "No conversation ID provided and no previous conversation exists"
                ),
            )

        # Select the appropriate store
        if use_db:
            conversation_store = get_db_conversation_store(db)
        else:
            conversation_store = get_conversation_store()

        # Try to get existing conversation
        conversation = conversation_store.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found",
            )

        # Add the new user message to the conversation
        conversation.add_message(ChatMessage(role="user", content=user_message))

        # Get reply from LLM using full conversation history
        reply = await llm.chat(conversation.messages)

        # Add the assistant's reply to the conversation history
        conversation.add_message(ChatMessage(role="assistant", content=reply))

        # Update the conversation in the store
        conversation_store.update_conversation(conversation)

        # Store the latest conversation ID for convenience in testing
        _latest_conversation_id = conversation.id

        # Fire the memory update pipeline (best-effort; errors are logged inside)
        await update_memory_after_turn(db=db, llm=llm, conversation=conversation)

        return ChatResponse(reply=reply, conversation_id=conversation.id)

    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in /continue: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Unexpected error: {str(e)}"
        )


def _get_or_create_conversation(
    conversation_store,  # Can be ConversationStore or DbConversationStore
    conversation_id: Optional[str],
    system_prompt: Optional[str],
) -> Conversation:
    """
    Get an existing conversation or create a new one.
    """
    if conversation_id:
        # Try to get existing conversation
        conversation = conversation_store.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found",
            )
        return conversation
    else:
        # Create new conversation
        return conversation_store.create_conversation(system_prompt)


def _get_conversation_or_404(
    conversation_store, conversation_id: str
) -> Conversation:  # Can be ConversationStore or DbConversationStore
    """
    Helper function to get a conversation or raise a 404 error if not found.
    """
    conversation = conversation_store.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    return conversation
