from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

# Error message constants
ERROR_NO_MESSAGE = "Either 'message' or 'messages' with at least one user message must be provided"

# Parameter description constants
DESC_USE_DB = "Whether to use the database storage (True) or in-memory storage (False)"

from src.app.core.llm_client import LlmClient, get_llm_client, AppError, ChatMessage
from src.app.core.conversation_store import ConversationStore, Conversation, MessageWithTimestamp
from src.app.core.conversation_store import get_conversation_store
from src.app.core.database import get_db
from src.app.core.db_conversation_store import get_db_conversation_store, DbConversationStore
from src.app.models.chat import (
    ChatRequest, 
    ChatResponse, 
    ConversationMetadata, 
    ConversationsResponse, 
    ConversationDetail,
    ConversationMessage,
    ConversationUpdateRequest,
    ConversationExport
)

router = APIRouter()

# Store the latest conversation ID for convenience in testing
_latest_conversation_id: Optional[str] = None


# Original /chat endpoint removed - now using /newchat and /continue endpoints


@router.get("/conversations", response_model=ConversationsResponse)
async def list_conversations(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of conversations to return"),
    db: Session = Depends(get_db),
    use_db: bool = Query(True, description=DESC_USE_DB)
) -> ConversationsResponse:
    """
    List available conversations.
    
    Args:
        limit: Maximum number of conversations to return
        db: Database session
        use_db: Whether to use database storage or in-memory storage
        
    Returns:
        List of conversation metadata
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
            reverse=True
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
    conversation_id: str = Path(..., description="ID of the conversation to retrieve"),
    db: Session = Depends(get_db),
    use_db: bool = Query(True, description=DESC_USE_DB)
) -> ConversationDetail:
    """
    Get detailed information about a conversation, including all messages.
    
    Args:
        conversation_id: ID of the conversation to retrieve
        db: Database session
        use_db: Whether to use database storage or in-memory storage
        
    Returns:
        Conversation details including all messages
        
    Raises:
        HTTPException: If the conversation is not found
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
            timestamp=msg.timestamp.isoformat()
        )
        for msg in conversation.messages
    ]
    
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at.isoformat(),
        updated_at=conversation.updated_at.isoformat(),
        messages=messages
    )


@router.post("/newchat", response_model=ChatResponse)
async def new_chat(
    req: ChatRequest,
    llm: LlmClient = Depends(get_llm_client),
    db: Session = Depends(get_db),
    use_db: bool = Query(True, description=DESC_USE_DB)
) -> ChatResponse:
    """
    Create a new conversation and send the first message.
    This endpoint always creates a new conversation regardless of any conversation_id passed.
    
    Args:
        req: The chat request with user message
        llm: LLM client injected by FastAPI's dependency system
        conversation_store: Conversation store for managing chat history
        
    Returns:
        ChatResponse with the assistant's reply and conversation ID
        
    Raises:
        HTTPException: If there's an error calling the LLM
    """
    global _latest_conversation_id
    
    try:
        # Validate that we have a message in some form
        try:
            user_message = req.user_message
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=ERROR_NO_MESSAGE
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
        
        return ChatResponse(reply=reply, conversation_id=conversation.id)
    
    except AppError as e:
        # Convert app errors to HTTP exceptions with proper status codes
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        # Catch-all for unexpected errors
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/continue", response_model=ChatResponse)
async def continue_chat(
    req: ChatRequest,
    llm: LlmClient = Depends(get_llm_client),
    db: Session = Depends(get_db),
    use_db: bool = Query(True, description=DESC_USE_DB)
) -> ChatResponse:
    """
    Continue the most recent conversation or a specific conversation if ID is provided.
    
    Args:
        req: The chat request with user message
        llm: LLM client injected by FastAPI's dependency system
        conversation_store: Conversation store for managing chat history
        
    Returns:
        ChatResponse with the assistant's reply and conversation ID
        
    Raises:
        HTTPException: If there's an error calling the LLM or no conversation exists
    """
    global _latest_conversation_id
    
    try:
        # Validate that we have a message in some form
        try:
            user_message = req.user_message
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=ERROR_NO_MESSAGE
            )
        
        # Get conversation ID - either from request, or use the latest one
        conversation_id = req.conversation_id or _latest_conversation_id
        
        if not conversation_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No conversation ID provided and no previous conversation exists"
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
                detail=f"Conversation {conversation_id} not found"
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
        
        return ChatResponse(reply=reply, conversation_id=conversation.id)
    
    except AppError as e:
        # Convert app errors to HTTP exceptions with proper status codes
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        # Catch-all for unexpected errors
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


def _get_or_create_conversation(
    conversation_store,  # Can be ConversationStore or DbConversationStore
    conversation_id: Optional[str],
    system_prompt: Optional[str]
) -> Conversation:
    """
    Get an existing conversation or create a new one.
    
    Args:
        conversation_store: The conversation store
        conversation_id: Optional ID of an existing conversation
        system_prompt: Optional system prompt for new conversations
        
    Returns:
        The conversation
        
    Raises:
        HTTPException: If the conversation ID is invalid
    """
    if conversation_id:
        # Try to get existing conversation
        conversation = conversation_store.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        return conversation
    else:
        # Create new conversation
        return conversation_store.create_conversation(system_prompt)


def _get_conversation_or_404(conversation_store, conversation_id: str) -> Conversation:  # Can be ConversationStore or DbConversationStore
    """
    Helper function to get a conversation or raise a 404 error if not found.
    
    Args:
        conversation_store: The conversation store
        conversation_id: ID of the conversation to retrieve
        
    Returns:
        The conversation if found
        
    Raises:
        HTTPException: If the conversation is not found
    """
    conversation = conversation_store.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )
    return conversation
