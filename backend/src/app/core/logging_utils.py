import logging
import os

_logger_configured = False


def _configure_root_logger() -> None:
    """Configure the root logger once with a sensible default format."""
    global _logger_configured
    if _logger_configured:
        return

    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    _logger_configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a module-level logger with shared configuration.

    Usage:
        from src.app.core.logging_utils import get_logger
        logger = get_logger(__name__)
    """
    _configure_root_logger()
    return logging.getLogger(name)
