# src/app/core/memory_service.py
"""
Backwards-compatibility shim for the memory pipeline.

The actual implementation now lives under:
    src.app.core.memory

This module re-exports the main entrypoint so existing imports like:

    from src.app.core.memory_service import update_memory_after_turn

continue to work.
"""

from src.app.memory import update_memory_after_turn

__all__ = ["update_memory_after_turn"]
