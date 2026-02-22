"""Database connection management for SQLite."""

import sqlite3
from pathlib import Path

from agentic_news_reaper.logging import get_logger

logger = get_logger(__name__)


class DatabaseConnection:
    """Manages SQLite database connections and operations."""

    def __init__(self, db_path: str | Path, timeout: int = 30) -> None:
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file.
            timeout: Connection timeout in seconds.
        """
        self.db_path = Path(db_path)
        self.timeout = timeout
        self._connection: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        """
        Establish database connection.

        Returns:
            SQLite connection object.
        """
        try:
            self._connection = sqlite3.connect(str(self.db_path), timeout=self.timeout)
            self._connection.row_factory = sqlite3.Row
            logger.info("database_connected", db_path=str(self.db_path))
            return self._connection
        except sqlite3.Error as e:
            logger.error("database_connection_failed", error=str(e))
            raise

    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            logger.info("database_closed")

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute SQL query.

        Args:
            query: SQL query string.
            params: Query parameters.

        Returns:
            Cursor object with results.
        """
        if not self._connection:
            self.connect()
        if not self._connection:
            raise ValueError("Database connection not established")
        try:
            cursor = self._connection.cursor()
            cursor.execute(query, params)
            return cursor
        except sqlite3.Error as e:
            logger.error("query_execution_failed", query=query, error=str(e))
            raise

    def execute_many(self, query: str, params_list: list) -> None:
        """
        Execute multiple SQL queries.

        Args:
            query: SQL query string.
            params_list: List of parameter tuples.
        """
        if not self._connection:
            self.connect()
        if not self._connection:
            raise ValueError("Database connection not established")
        try:
            cursor = self._connection.cursor()
            cursor.executemany(query, params_list)
            self._connection.commit()
        except sqlite3.Error as e:
            self._connection.rollback()
            logger.error("batch_execution_failed", error=str(e))
            raise

    def commit(self) -> None:
        """Commit transaction."""
        if self._connection:
            self._connection.commit()

    def rollback(self) -> None:
        """Rollback transaction."""
        if self._connection:
            self._connection.rollback()

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
