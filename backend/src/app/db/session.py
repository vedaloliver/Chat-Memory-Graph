# src/app/db/session.py
"""
Database configuration and session utilities.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Get database URL from environment variable or use default SQLite file
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()


def get_db() -> Session:
    """
    Dependency for FastAPI to get a database session.

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
