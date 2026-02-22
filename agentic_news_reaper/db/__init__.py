"""Database module for agentic-news-reaper.

Handles SQLite connection, schema initialization, and query operations.
"""

from .connection import DatabaseConnection
from .schema import init_schema

__all__ = ["DatabaseConnection", "init_schema"]
