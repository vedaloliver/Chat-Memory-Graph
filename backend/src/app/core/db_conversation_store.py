"""
SQLAlchemy-backed conversation store for managing chat histories.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import uuid4

from src.app.core.llm_client import ChatMessage
from src.app.models.database_models import ConversationModel, MessageModel
from src.app.core.conversation_store import Conversation, MessageWithTimestamp


class DbConversationStore:
    """
    Manages persistent storage and retrieval of conversation histories using SQLAlchemy.
    
    This class provides methods for creating, retrieving, and updating
    conversations in a database, allowing the application to maintain context
    across multiple chat interactions and server restarts.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the conversation store with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create_conversation(self, system_prompt: Optional[str] = None) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            system_prompt: Optional system prompt to initialize the conversation with
            
        Returns:
            A new Conversation instance
        """
        # Create conversation in database
        db_conversation = ConversationModel(
            id=str(uuid4()),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.db.add(db_conversation)
        self.db.commit()
        self.db.refresh(db_conversation)
        
        # Create Pydantic model
        conversation = Conversation(
            id=db_conversation.id,
            created_at=db_conversation.created_at,
            updated_at=db_conversation.updated_at
        )
        
        # Add system prompt if provided
        if system_prompt:
            self._add_message_to_db(db_conversation.id, "system", system_prompt)
            conversation.add_message(ChatMessage(role="system", content=system_prompt))
            
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Retrieve a conversation by ID.
        
        Args:
            conversation_id: The ID of the conversation to retrieve
            
        Returns:
            The Conversation if found, None otherwise
        """
        db_conversation = self._get_db_conversation(conversation_id)
        if not db_conversation:
            return None
        
        # Convert to Pydantic model
        conversation = Conversation(
            id=db_conversation.id,
            title=db_conversation.title,
            created_at=db_conversation.created_at,
            updated_at=db_conversation.updated_at,
            metadata=db_conversation.meta_data or {}
        )
        
        # Add messages
        for db_message in db_conversation.messages:
            conversation.messages.append(
                MessageWithTimestamp(
                    role=db_message.role,
                    content=db_message.content,
                    timestamp=db_message.timestamp
                )
            )
        
        return conversation
    
    def update_conversation(self, conversation: Conversation) -> None:
        """
        Update a conversation in the store.
        
        Args:
            conversation: The updated conversation
        """
        db_conversation = self._get_db_conversation(conversation.id)
        if not db_conversation:
            raise ValueError(f"Conversation {conversation.id} not found")
        
        # Update basic fields
        db_conversation.title = conversation.title
        db_conversation.updated_at = conversation.updated_at
        db_conversation.meta_data = conversation.metadata
        
        # Check for new messages to add
        db_messages = {(msg.role, msg.content): msg for msg in db_conversation.messages}
        
        for msg in conversation.messages:
            # If message not in database, add it
            if (msg.role, msg.content) not in db_messages:
                self._add_message_to_db(conversation.id, msg.role, msg.content, msg.timestamp)
        
        self.db.commit()
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation by ID.
        
        Args:
            conversation_id: The ID of the conversation to delete
            
        Returns:
            True if the conversation was found and deleted, False otherwise
        """
        db_conversation = self._get_db_conversation(conversation_id)
        if not db_conversation:
            return False
        
        self.db.delete(db_conversation)
        self.db.commit()
        return True
    
    def list_conversations(self, limit: int = 100, skip: int = 0) -> List[Conversation]:
        """
        List conversations, sorted by updated_at (newest first).
        
        Args:
            limit: Maximum number of conversations to return
            skip: Number of conversations to skip (for pagination)
            
        Returns:
            List of Conversation objects
        """
        db_conversations = (
            self.db.query(ConversationModel)
            .order_by(ConversationModel.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return [self._db_to_pydantic_conversation(db_conv) for db_conv in db_conversations]
    
    def _get_db_conversation(self, conversation_id: str) -> Optional[ConversationModel]:
        """
        Get a conversation from the database.
        
        Args:
            conversation_id: The ID of the conversation to retrieve
            
        Returns:
            The database conversation if found, None otherwise
        """
        return (
            self.db.query(ConversationModel)
            .filter(ConversationModel.id == conversation_id)
            .first()
        )
    
    def _add_message_to_db(
        self, 
        conversation_id: str, 
        role: str, 
        content: str, 
        timestamp: Optional[datetime] = None
    ) -> MessageModel:
        """
        Add a message to the database.
        
        Args:
            conversation_id: The ID of the conversation
            role: The role of the message sender
            content: The content of the message
            timestamp: Optional timestamp for the message
            
        Returns:
            The created message
        """
        message = MessageModel(
            conversation_id=conversation_id,
            role=role,
            content=content,
            timestamp=timestamp or datetime.now()
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def _db_to_pydantic_conversation(self, db_conversation: ConversationModel) -> Conversation:
        """
        Convert a database conversation model to a Pydantic Conversation model.
        
        Args:
            db_conversation: Database conversation model
            
        Returns:
            Pydantic Conversation model
        """
        conversation = Conversation(
            id=db_conversation.id,
            title=db_conversation.title,
            created_at=db_conversation.created_at,
            updated_at=db_conversation.updated_at,
            metadata=db_conversation.meta_data or {}
        )
        
        # Add messages
        for db_message in db_conversation.messages:
            conversation.messages.append(
                MessageWithTimestamp(
                    role=db_message.role,
                    content=db_message.content,
                    timestamp=db_message.timestamp
                )
            )
        
        return conversation


def get_db_conversation_store(db: Session) -> DbConversationStore:
    """
    Get a database-backed conversation store instance.
    
    Args:
        db: SQLAlchemy database session
        
    Returns:
        DbConversationStore instance
    """
    return DbConversationStore(db)
