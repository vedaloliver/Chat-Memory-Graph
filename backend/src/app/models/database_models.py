"""
SQLAlchemy models for database storage.

This file now includes:
- ConversationModel / MessageModel          (existing chat storage)
- SessionSummaryModel                       (one per ConversationModel, top layer)
- MemoryChunkModel                          (chunked dialogue segments, bottom layer)
- EntityModel                               (graph entities: people, places, concepts)
- TripleModel                               (entity–relation triples, middle layer)
- TripleSessionLinkModel                    (links triples ↔ session summaries)
- TripleChunkLinkModel                      (links triples ↔ chunks)
- TagModel                                  (simple tag model to satisfy Alembic imports)
"""

from datetime import datetime
import uuid
from typing import Dict, Any, List, Optional

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Boolean,
    Float,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.app.core.database import Base


# ---------------------------------------------------------------------------
# Core chat models
# ---------------------------------------------------------------------------


class ConversationModel(Base):
    """SQLAlchemy model for storing conversations."""
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    # Renamed from metadata to avoid SQLAlchemy conflict
    meta_data = Column(JSON, default=dict)

    # Relationship to messages (one-to-many)
    messages = relationship(
        "MessageModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )

    # LiCo-style memory relationships
    session_summary = relationship(
        "SessionSummaryModel",
        back_populates="conversation",
        uselist=False,
        cascade="all, delete-orphan",
    )
    memory_chunks = relationship(
        "MemoryChunkModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.meta_data,
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
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# LiCoMemory-style graph models
# ---------------------------------------------------------------------------


class SessionSummaryModel(Base):
    """
    High-level summary for a conversation (top layer of CogniGraph).

    MVP design: one SessionSummary per ConversationModel.
    """
    __tablename__ = "session_summaries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # One-to-one with conversations
    conversation_id = Column(
        String(36),
        ForeignKey("conversations.id"),
        nullable=False,
        unique=True,
    )

    # Time span of this session (optional – can be filled from messages)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)

    # High-level summary and indexing info
    summary_text = Column(Text, nullable=True)
    # List of strings (keywords, entities, key phrases)
    keywords = Column(JSON, default=list)
    # List of high-level tags/themes ("work", "relationship", etc.)
    themes = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Backref to ConversationModel
    conversation = relationship("ConversationModel", back_populates="session_summary")

    # Chunks that belong to this session
    memory_chunks = relationship(
        "MemoryChunkModel",
        back_populates="session_summary",
        cascade="all, delete-orphan",
    )

    # Links to triples
    triple_links = relationship(
        "TripleSessionLinkModel",
        back_populates="session_summary",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "summary_text": self.summary_text,
            "keywords": self.keywords,
            "themes": self.themes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class MemoryChunkModel(Base):
    """
    Chunked dialogue segment (bottom layer).

    MVP rule: one chunk = last user message + assistant reply pair.
    Stores text used for memory extraction and links back to messages.
    """
    __tablename__ = "memory_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    conversation_id = Column(
        String(36),
        ForeignKey("conversations.id"),
        nullable=False,
    )
    session_summary_id = Column(
        String(36),
        ForeignKey("session_summaries.id"),
        nullable=False,
    )

    # Optional: exact message boundaries this chunk covers
    start_message_id = Column(String(36), ForeignKey("messages.id"), nullable=True)
    end_message_id = Column(String(36), ForeignKey("messages.id"), nullable=True)

    # Text that was given to the memory extraction LLM
    text = Column(Text, nullable=False)

    # Optional: short topic label ("work stress", "holiday planning")
    topic_hint = Column(String(255), nullable=True)

    # When this chunk was created (e.g., time of assistant reply)
    timestamp = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    conversation = relationship("ConversationModel", back_populates="memory_chunks")
    session_summary = relationship("SessionSummaryModel", back_populates="memory_chunks")

    start_message = relationship(
        "MessageModel",
        foreign_keys=[start_message_id],
    )
    end_message = relationship(
        "MessageModel",
        foreign_keys=[end_message_id],
    )

    triple_links = relationship(
        "TripleChunkLinkModel",
        back_populates="chunk",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "session_summary_id": self.session_summary_id,
            "start_message_id": self.start_message_id,
            "end_message_id": self.end_message_id,
            "text": self.text,
            "topic_hint": self.topic_hint,
            "timestamp": self.timestamp,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class EntityModel(Base):
    """
    Entity node in the memory graph.

    Examples:
    - "Oliver" (person)
    - "Hazal" (person)
    - "work stress" (concept)
    - "PVM project" (project)
    """
    __tablename__ = "entities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canonical_name = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=True)  # person, place, project, emotion, etc.

    # Optional: alt spellings / surface forms
    aliases = Column(JSON, default=list)

    first_seen_at = Column(DateTime, default=datetime.now)
    last_seen_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("canonical_name", "entity_type", name="uq_entity_name_type"),
    )

    # Triples where this entity appears as subject or object
    subject_triples = relationship(
        "TripleModel",
        back_populates="subject_entity",
        foreign_keys="TripleModel.subject_entity_id",
    )
    object_triples = relationship(
        "TripleModel",
        back_populates="object_entity",
        foreign_keys="TripleModel.object_entity_id",
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "canonical_name": self.canonical_name,
            "entity_type": self.entity_type,
            "aliases": self.aliases,
            "first_seen_at": self.first_seen_at,
            "last_seen_at": self.last_seen_at,
        }


class TripleModel(Base):
    """
    Entity–relation triple (middle layer).

    Example:
    - subject: "Oliver"
      relation_type: "feels"
      object: "stressed about sprint deadline"
    """
    __tablename__ = "triples"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    subject_entity_id = Column(String(36), ForeignKey("entities.id"), nullable=False)
    object_entity_id = Column(String(36), ForeignKey("entities.id"), nullable=True)

    # Short relation label ("feels", "works_on", "argued_with", "moved_to")
    relation_type = Column(String(100), nullable=False)

    # Optional natural-language form ("Oliver felt overwhelmed by work")
    relation_text = Column(Text, nullable=True)

    # 0–1 importance score from LLM (optional)
    importance = Column(Float, nullable=True)

    # If this triple describes a state vs. a point event
    is_state = Column(Boolean, default=False)

    # Confidence from LLM (0–1, optional)
    confidence = Column(Float, nullable=True)

    first_seen_at = Column(DateTime, default=datetime.now)
    last_seen_at = Column(DateTime, default=datetime.now)

    # Relationships
    subject_entity = relationship(
        "EntityModel",
        foreign_keys=[subject_entity_id],
        back_populates="subject_triples",
    )
    object_entity = relationship(
        "EntityModel",
        foreign_keys=[object_entity_id],
        back_populates="object_triples",
    )

    session_links = relationship(
        "TripleSessionLinkModel",
        back_populates="triple",
        cascade="all, delete-orphan",
    )
    chunk_links = relationship(
        "TripleChunkLinkModel",
        back_populates="triple",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "subject_entity_id": self.subject_entity_id,
            "object_entity_id": self.object_entity_id,
            "relation_type": self.relation_type,
            "relation_text": self.relation_text,
            "importance": self.importance,
            "is_state": self.is_state,
            "confidence": self.confidence,
            "first_seen_at": self.first_seen_at,
            "last_seen_at": self.last_seen_at,
        }


class TripleSessionLinkModel(Base):
    """
    Many-to-many link between triples and session summaries.

    A single triple can appear in multiple sessions.
    A session summary can reference many triples.
    """
    __tablename__ = "triple_session_links"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    triple_id = Column(String(36), ForeignKey("triples.id"), nullable=False)
    session_summary_id = Column(
        String(36),
        ForeignKey("session_summaries.id"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("triple_id", "session_summary_id", name="uq_triple_session"),
    )

    triple = relationship("TripleModel", back_populates="session_links")
    session_summary = relationship("SessionSummaryModel", back_populates="triple_links")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "triple_id": self.triple_id,
            "session_summary_id": self.session_summary_id,
        }


class TripleChunkLinkModel(Base):
    """
    Many-to-many link between triples and memory chunks.

    This lets you jump from a triple to the exact evidence text,
    and from a chunk to all triples extracted from it.
    """
    __tablename__ = "triple_chunk_links"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    triple_id = Column(String(36), ForeignKey("triples.id"), nullable=False)
    chunk_id = Column(String(36), ForeignKey("memory_chunks.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("triple_id", "chunk_id", name="uq_triple_chunk"),
    )

    triple = relationship("TripleModel", back_populates="chunk_links")
    chunk = relationship("MemoryChunkModel", back_populates="triple_links")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "triple_id": self.triple_id,
            "chunk_id": self.chunk_id,
        }


# ---------------------------------------------------------------------------
# Simple Tag model (to satisfy existing Alembic imports)
# ---------------------------------------------------------------------------


class TagModel(Base):
    """
    Simple tag model.

    This is intentionally minimal: it just gives you a place to store arbitrary tags
    and satisfies the `TagModel` import in alembic/env.py.
    You can expand this later or remove it if you change the migration config.
    """
    __tablename__ = "tags"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
        }
