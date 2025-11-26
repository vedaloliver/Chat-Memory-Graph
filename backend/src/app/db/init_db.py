# src/app/db/init_db.py
"""
Initialize the database by creating all tables.
Intended to be called at application startup or from a small CLI shim.
"""

from .session import Base, engine


def init_db() -> None:
    """
    Initialize the database by creating all tables.
    """
    # Import models here to ensure they are registered with Base
    from src.app.models.database_models import (  # noqa: F401
        ConversationModel,
        MessageModel,
    )

    Base.metadata.create_all(bind=engine)
