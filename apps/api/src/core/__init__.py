"""Core module for configuration, database, and shared utilities."""

from src.core.config import settings
from src.core.database import get_db, init_db

__all__ = ["settings", "get_db", "init_db"]
