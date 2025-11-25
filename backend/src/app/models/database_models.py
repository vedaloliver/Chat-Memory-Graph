"""
SQLAlchemy models for database storage.
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from typing import List, Dict, Any, Optional

from src.app.core.database import Base


class ConversationModel(Base):
    """SQLAlchemy model for storing conversations."""
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    meta_data = Column(JSON, default=dict)  # Renamed from metadata to avoid SQLAlchemy conflict
    
    # Relationship to messages (one-to-many)
    messages = relationship("MessageModel", back_populates="conversation", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.meta_data  # Use meta_data field but keep metadata in the dictionary
        }


class MessageModel(Base):
    """SQLAlchemy model for storing chat messages."""
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(50), nullable=False)  # system, user, assistant
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    
    # Relationship to conversation (many-to-one)
    conversation = relationship("ConversationModel", back_populates="messages")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }



