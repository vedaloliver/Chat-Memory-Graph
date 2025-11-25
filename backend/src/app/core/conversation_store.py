"""
In-memory conversation context store for managing chat histories.
"""
from typing import Dict, List, Optional, Any
from uuid import uuid4
from datetime import datetime

from pydantic import BaseModel, Field

from src.app.core.llm_client import ChatMessage


class MessageWithTimestamp(ChatMessage):
    """ChatMessage with added timestamp for conversation history."""
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
        """
        Add a message to the conversation history.
        
        Args:
            message: The message to add
        """
        # Convert to MessageWithTimestamp if it's a regular ChatMessage
        if isinstance(message, MessageWithTimestamp):
            timestamped_message = message
        else:
            timestamped_message = MessageWithTimestamp(
                role=message.role,
                content=message.content,
                timestamp=datetime.now()
            )
            
        self.messages.append(timestamped_message)
        self.updated_at = datetime.now()
        
        # Auto-generate a title from the first user message if not set
        if not self.title and message.role == "user" and len(self.messages) <= 2:
            # Use the first few words of the first user message as the title
            words = message.content.split()
            title_words = words[:5] if len(words) > 5 else words
            self.title = " ".join(title_words) + ("..." if len(words) > 5 else "")
    
    def update_metadata(self, title: Optional[str] = None) -> None:
        """
        Update conversation metadata.
        
        Args:
            title: New title for the conversation
        """
        if title is not None:
            self.title = title
        
        self.updated_at = datetime.now()


class ConversationStore:
    """
    Manages in-memory storage and retrieval of conversation histories.
    
    This class provides methods for creating, retrieving, and updating
    conversations, allowing the application to maintain context across
    multiple chat interactions.
    """
    
    def __init__(self, max_conversations: int = 1000):
        """
        Initialize the conversation store.
        
        Args:
            max_conversations: Maximum number of conversations to store in memory
        """
        self._conversations: Dict[str, Conversation] = {}
        self.max_conversations = max_conversations
    
    def create_conversation(self, system_prompt: Optional[str] = None) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            system_prompt: Optional system prompt to initialize the conversation with
            
        Returns:
            A new Conversation instance
        """
        conversation = Conversation()
        
        # Add system prompt if provided
        if system_prompt:
            conversation.add_message(ChatMessage(role="system", content=system_prompt))
            
        self._conversations[conversation.id] = conversation
        self._enforce_limit()
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Retrieve a conversation by ID.
        
        Args:
            conversation_id: The ID of the conversation to retrieve
            
        Returns:
            The Conversation if found, None otherwise
        """
        return self._conversations.get(conversation_id)
    
    def update_conversation(self, conversation: Conversation) -> None:
        """
        Update a conversation in the store.
        
        Args:
            conversation: The updated conversation
        """
        self._conversations[conversation.id] = conversation
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation by ID.
        
        Args:
            conversation_id: The ID of the conversation to delete
            
        Returns:
            True if the conversation was found and deleted, False otherwise
        """
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False
    
    def _enforce_limit(self) -> None:
        """
        Remove oldest conversations if store exceeds maximum size.
        """
        if len(self._conversations) > self.max_conversations:
            # Sort by updated_at and remove oldest
            sorted_conversations = sorted(
                self._conversations.items(),
                key=lambda item: item[1].updated_at
            )
            # Remove oldest conversations
            to_remove = len(self._conversations) - self.max_conversations
            for i in range(to_remove):
                del self._conversations[sorted_conversations[i][0]]


# Singleton instance
_conversation_store: Optional[ConversationStore] = None


def get_conversation_store(max_conversations: int = 1000) -> ConversationStore:
    """
    Get or create the singleton conversation store instance.
    
    Args:
        max_conversations: Maximum number of conversations to store
        
    Returns:
        ConversationStore instance
    """
    global _conversation_store
    if _conversation_store is None:
        _conversation_store = ConversationStore(max_conversations=max_conversations)
    return _conversation_store
