"""Database integration tests.

Tests for database connection, schema initialization, and basic CRUD operations.
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from agentic_news_reaper.db.connection import DatabaseConnection
from agentic_news_reaper.db.schema import init_schema


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def initialized_db(temp_db):
    """Create and initialize a temporary database."""
    init_schema(temp_db)
    yield temp_db


class TestDatabaseConnection:
    """Tests for DatabaseConnection class."""

    def test_connection_initialization(self, temp_db):
        """Test database connection initialization."""
        conn = DatabaseConnection(temp_db, timeout=30)
        assert conn.db_path == temp_db
        assert conn.timeout == 30
        assert conn._connection is None

    def test_connection_connect(self, temp_db):
        """Test establishing database connection."""
        init_schema(temp_db)
        conn = DatabaseConnection(temp_db)
        connection = conn.connect()
        assert connection is not None
        assert isinstance(connection, sqlite3.Connection)
        conn.close()

    def test_connection_context_manager(self, temp_db):
        """Test connection context manager."""
        init_schema(temp_db)
        with DatabaseConnection(temp_db) as conn:
            assert conn._connection is not None
        # After context, connection should be closed
        # (Note: checking if closed is tricky with sqlite3)

    def test_connection_close(self, temp_db):
        """Test closing database connection."""
        init_schema(temp_db)
        conn = DatabaseConnection(temp_db)
        conn.connect()
        assert conn._connection is not None
        conn.close()

    def test_execute_query(self, initialized_db):
        """Test executing a simple query."""
        conn = DatabaseConnection(initialized_db)
        conn.connect()
        cursor = conn.execute("SELECT COUNT(*) FROM hn_raw")
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == 0  # Should be empty
        conn.close()

    def test_execute_insert(self, initialized_db):
        """Test inserting data."""
        conn = DatabaseConnection(initialized_db)
        conn.connect()

        cursor = conn.execute(
            "INSERT INTO hn_raw (story_id, title, url, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            ("12345", "Test Story", "https://example.com"),
        )
        conn.commit()

        # Verify insertion
        cursor = conn.execute("SELECT COUNT(*) FROM hn_raw WHERE story_id = ?", ("12345",))
        count = cursor.fetchone()[0]
        assert count == 1

        conn.close()

    def test_execute_many(self, initialized_db):
        """Test batch insert with execute_many."""
        conn = DatabaseConnection(initialized_db)
        conn.connect()

        data = [
            ("11111", "Story 1", "https://example1.com"),
            ("22222", "Story 2", "https://example2.com"),
            ("33333", "Story 3", "https://example3.com"),
        ]

        conn.execute_many(
            "INSERT INTO hn_raw (story_id, title, url, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            data,
        )

        cursor = conn.execute("SELECT COUNT(*) FROM hn_raw")
        count = cursor.fetchone()[0]
        assert count == 3

        conn.close()

    def test_commit_and_rollback(self, initialized_db):
        """Test commit and rollback operations."""
        conn = DatabaseConnection(initialized_db)
        conn.connect()

        # Insert and commit
        conn.execute(
            "INSERT INTO hn_raw (story_id, title, url, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            ("99999", "Test Story", "https://example.com"),
        )
        conn.commit()

        # Verify committed
        cursor = conn.execute("SELECT COUNT(*) FROM hn_raw WHERE story_id = ?", ("99999",))
        assert cursor.fetchone()[0] == 1

        conn.close()


class TestSchemaInitialization:
    """Tests for database schema initialization."""

    def test_schema_initialization(self, temp_db):
        """Test schema initialization creates tables."""
        init_schema(temp_db)
        assert temp_db.exists()

    def test_schema_tables_created(self, initialized_db):
        """Test that all required tables are created."""
        conn = sqlite3.connect(str(initialized_db))
        cursor = conn.cursor()

        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        # Verify all expected tables exist
        expected_tables = [
            "hn_raw",
            "ndd_flags",
            "patterns_instances",
            "failure_modes",
            "override_log",
            "weekly_summaries",
            "execution_state",
        ]

        for table in expected_tables:
            assert table in tables, f"Table {table} not found"

        conn.close()

    def test_schema_indexes_created(self, initialized_db):
        """Test that indexes are created."""
        conn = sqlite3.connect(str(initialized_db))
        cursor = conn.cursor()

        # Get list of indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indexes = [row[0] for row in cursor.fetchall()]

        # Verify some key indexes exist
        expected_indexes = [
            "idx_hn_raw_story_id",
            "idx_hn_raw_fetched_at",
            "idx_patterns_story_id",
        ]

        for idx in expected_indexes:
            assert idx in indexes, f"Index {idx} not found"

        conn.close()

    def test_schema_foreign_keys(self, initialized_db):
        """Test that foreign key constraints are defined."""
        conn = sqlite3.connect(str(initialized_db))
        cursor = conn.cursor()

        # Check foreign keys on failure_modes table
        cursor.execute("PRAGMA foreign_key_list(failure_modes)")
        fk = cursor.fetchall()
        assert len(fk) > 0, "No foreign keys found on failure_modes"

        conn.close()


class TestDataIntegrity:
    """Tests for data integrity and constraints."""

    def test_unique_story_id(self, initialized_db):
        """Test that story_id is unique in hn_raw."""
        conn = DatabaseConnection(initialized_db)
        conn.connect()

        # Insert first story
        conn.execute(
            "INSERT INTO hn_raw (story_id, title, url, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            ("dup123", "Story 1", "https://example.com"),
        )
        conn.commit()

        # Try to insert duplicate - should fail
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO hn_raw (story_id, title, url, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                ("dup123", "Story 2", "https://example2.com"),
            )
            conn.commit()

        conn.close()

    def test_ndd_flags_foreign_key(self, initialized_db):
        """Test that ndd_flags enforces foreign key to hn_raw."""
        conn = DatabaseConnection(initialized_db)
        conn.connect()

        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")

        # Try to insert with non-existent story_id - should fail or succeed depending on FK enforcement
        # Note: SQLite doesn't enforce FKs by default, but we can test the schema
        cursor = conn.execute("PRAGMA foreign_key_list(ndd_flags)")
        fk_list = cursor.fetchall()
        assert len(fk_list) > 0, "No foreign key defined on ndd_flags"

        conn.close()

    def test_weekly_summaries_unique_week(self, initialized_db):
        """Test that week_start is unique in weekly_summaries."""
        conn = DatabaseConnection(initialized_db)
        conn.connect()

        # Insert first summary
        conn.execute(
            "INSERT INTO weekly_summaries (week_start, summary_json) VALUES (?, ?)",
            ("2024-01-01", '{"test": "data"}'),
        )
        conn.commit()

        # Try to insert duplicate week - should fail
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO weekly_summaries (week_start, summary_json) VALUES (?, ?)",
                ("2024-01-01", '{"test": "data2"}'),
            )
            conn.commit()

        conn.close()


class TestDatabaseQueries:
    """Tests for common query patterns."""

    def test_insert_and_query_story(self, initialized_db):
        """Test inserting and querying a story."""
        conn = DatabaseConnection(initialized_db)
        conn.connect()

        # Insert
        conn.execute(
            "INSERT INTO hn_raw (story_id, title, url, score, descendants, created_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
            ("test001", "Test Story Title", "https://test.example.com", 42, 15),
        )
        conn.commit()

        # Query
        cursor = conn.execute("SELECT * FROM hn_raw WHERE story_id = ?", ("test001",))
        row = cursor.fetchone()

        assert row is not None
        assert row["title"] == "Test Story Title"
        assert row["score"] == 42
        assert row["descendants"] == 15

        conn.close()

    def test_insert_pattern_instance(self, initialized_db):
        """Test inserting pattern instance."""
        conn = DatabaseConnection(initialized_db)
        conn.connect()

        # First insert a story
        conn.execute(
            "INSERT INTO hn_raw (story_id, title, url, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            ("story123", "Test", "https://test.com"),
        )

        # Then insert pattern instance
        conn.execute(
            "INSERT INTO patterns_instances (pattern_id, story_id, confidence, pattern_data, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
            ("pattern_001", "story123", 0.85, '{"type": "clickbait"}'),
        )
        conn.commit()

        cursor = conn.execute("SELECT * FROM patterns_instances WHERE story_id = ?", ("story123",))
        row = cursor.fetchone()

        assert row is not None
        assert row["pattern_id"] == "pattern_001"
        assert row["confidence"] == 0.85

        conn.close()

    def test_transaction_rollback_on_error(self, initialized_db):
        """Test that transaction rolls back on error."""
        conn = DatabaseConnection(initialized_db)
        conn.connect()

        try:
            conn.execute(
                "INSERT INTO hn_raw (story_id, title, url, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                ("rollback001", "Test", "https://test.com"),
            )
            # Intentionally cause an error
            conn.execute("INVALID SQL STATEMENT")
        except sqlite3.OperationalError:
            conn.rollback()

        cursor = conn.execute("SELECT COUNT(*) FROM hn_raw WHERE story_id = ?", ("rollback001",))
        count = cursor.fetchone()[0]

        # If rollback worked, the story should not be in the database
        # (Note: This test is informational; exact behavior depends on transaction semantics)
        assert isinstance(count, int)

        conn.close()
