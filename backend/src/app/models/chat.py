from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# Constants for field descriptions to avoid duplication
DESC_CONVERSATION_ID = "Conversation ID"
DESC_CONVERSATION_TITLE = "Optional title for the conversation"
DESC_CREATION_TIMESTAMP = "Creation timestamp"
DESC_UPDATE_TIMESTAMP = "Last update timestamp"
DESC_MESSAGE_ROLE = "Role of the message sender: 'user', 'assistant', or 'system'"
DESC_MESSAGE_CONTENT = "Content of the message"


class ChatMessageIn(BaseModel):
    """Model for chat message input."""
    role: str = Field(..., description=DESC_MESSAGE_ROLE)
    content: str = Field(..., description=DESC_MESSAGE_CONTENT)


class ChatRequest(BaseModel):
    """Model for chat API request that supports both direct message and message list formats."""
    message: Optional[str] = Field(None, description="User message content")
    messages: Optional[List[ChatMessageIn]] = Field(None, description="List of chat messages (legacy format)")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for maintaining context")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt to use for new conversations")
    
    @property
    def user_message(self) -> str:
        """Get the user message content, supporting both formats."""
        if self.message is not None:
            return self.message
        elif self.messages and len(self.messages) > 0:
            # Find the last user message in the list
            for msg in reversed(self.messages):
                if msg.role == "user":
                    return msg.content
            # If no user message is found, use the last message
            return self.messages[-1].content
        else:
            raise ValueError("No message content provided")
            
    class Config:
        schema_extra = {
            "examples": [
                {
                    "message": "Hello, how are you?",
                    "conversation_id": None
                },
                {
                    "messages": [
                        {"role": "user", "content": "Hello, how are you?"}
                    ]
                }
            ]
        }


class ChatResponse(BaseModel):
    """Model for chat API response."""
    reply: str = Field(..., description="Assistant's reply")
    conversation_id: str = Field(..., description=f"{DESC_CONVERSATION_ID} for future reference")


class ConversationMessage(BaseModel):
    """Model for a single message in a conversation."""
    role: str = Field(..., description=DESC_MESSAGE_ROLE)
    content: str = Field(..., description=DESC_MESSAGE_CONTENT)
    timestamp: str = Field(..., description="When the message was added to the conversation")


class ConversationMetadata(BaseModel):
    """Model for conversation metadata."""
    id: str = Field(..., description=DESC_CONVERSATION_ID)
    title: Optional[str] = Field(None, description=DESC_CONVERSATION_TITLE)
    message_count: int = Field(..., description="Number of messages in the conversation")
    created_at: str = Field(..., description=DESC_CREATION_TIMESTAMP)
    updated_at: str = Field(..., description=DESC_UPDATE_TIMESTAMP)


class ConversationDetail(BaseModel):
    """Model for detailed conversation information including messages."""
    id: str = Field(..., description=DESC_CONVERSATION_ID)
    title: Optional[str] = Field(None, description=DESC_CONVERSATION_TITLE)
    created_at: str = Field(..., description=DESC_CREATION_TIMESTAMP)
    updated_at: str = Field(..., description=DESC_UPDATE_TIMESTAMP)
    messages: List[ConversationMessage] = Field(..., description="Messages in the conversation")


class ConversationsResponse(BaseModel):
    """Model for listing conversations."""
    conversations: List[ConversationMetadata] = Field(..., description="List of conversations")


class ConversationUpdateRequest(BaseModel):
    """Model for updating conversation metadata."""
    title: Optional[str] = Field(None, description="New title for the conversation")


class ConversationExport(BaseModel):
    """Model for exporting a conversation."""
    id: str = Field(..., description=DESC_CONVERSATION_ID)
    title: Optional[str] = Field(None, description=DESC_CONVERSATION_TITLE)
    created_at: str = Field(..., description=DESC_CREATION_TIMESTAMP)
    updated_at: str = Field(..., description=DESC_UPDATE_TIMESTAMP)
    messages: List[Dict[str, str]] = Field(..., description="Messages in the conversation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ErrorResponse(BaseModel):
    """Model for API error responses."""
    detail: str = Field(..., description="Error detail message")
