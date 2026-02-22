"""Database schema initialization and management.

This module handles creating and managing the SQLite database schema
for persisting Hacker News data, agent outputs, and execution state.
"""

import sqlite3
from pathlib import Path

from agentic_news_reaper.logging import get_logger

logger = get_logger(__name__)

# SQL schema definition
SCHEMA_SQL = """
-- Raw Hacker News items
CREATE TABLE IF NOT EXISTS hn_raw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    url TEXT,
    author TEXT,
    score INTEGER DEFAULT 0,
    descendants INTEGER DEFAULT 0,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Non-Determinism Detector results
CREATE TABLE IF NOT EXISTS ndd_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id TEXT NOT NULL,
    ambiguity_score REAL NOT NULL,
    reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(story_id) REFERENCES hn_raw(story_id)
);

-- Execution Pattern instances
CREATE TABLE IF NOT EXISTS patterns_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id TEXT NOT NULL,
    story_id TEXT NOT NULL,
    confidence REAL NOT NULL,
    pattern_data TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(story_id) REFERENCES hn_raw(story_id)
);

-- Failure Mode Analysis results
CREATE TABLE IF NOT EXISTS failure_modes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_instance_id INTEGER NOT NULL,
    risk_score REAL NOT NULL,
    engagement_risk REAL,
    spam_risk REAL,
    sentiment_drift REAL,
    mitigation TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(pattern_instance_id) REFERENCES patterns_instances(id)
);

-- Human Override log
CREATE TABLE IF NOT EXISTS override_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id TEXT NOT NULL,
    pattern_instance_id INTEGER,
    decision TEXT NOT NULL,
    reason TEXT,
    operator_id TEXT,
    decision_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(story_id) REFERENCES hn_raw(story_id),
    FOREIGN KEY(pattern_instance_id) REFERENCES patterns_instances(id)
);

-- Weekly summaries
CREATE TABLE IF NOT EXISTS weekly_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start DATE NOT NULL UNIQUE,
    summary_json TEXT NOT NULL,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- System state and execution tracking
CREATE TABLE IF NOT EXISTS execution_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_date DATE NOT NULL UNIQUE,
    status TEXT DEFAULT 'pending',
    started_at DATETIME,
    completed_at DATETIME,
    error_message TEXT,
    metadata TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_hn_raw_story_id ON hn_raw(story_id);
CREATE INDEX IF NOT EXISTS idx_hn_raw_fetched_at ON hn_raw(fetched_at);
CREATE INDEX IF NOT EXISTS idx_ndd_flags_story_id ON ndd_flags(story_id);
CREATE INDEX IF NOT EXISTS idx_patterns_story_id ON patterns_instances(story_id);
CREATE INDEX IF NOT EXISTS idx_patterns_pattern_id ON patterns_instances(pattern_id);
CREATE INDEX IF NOT EXISTS idx_failure_modes_pattern ON failure_modes(pattern_instance_id);
CREATE INDEX IF NOT EXISTS idx_override_log_story_id ON override_log(story_id);
CREATE INDEX IF NOT EXISTS idx_execution_state_date ON execution_state(execution_date);
"""


def init_schema(db_path: Path) -> None:
    """Initialize database schema.

    Creates all necessary tables if they don't exist.

    Args:
        db_path: Path to SQLite database file.

    Raises:
        sqlite3.Error: If schema initialization fails.
    """
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.executescript(SCHEMA_SQL)
        conn.commit()
        conn.close()
        logger.info("Database schema initialized", db_path=str(db_path))
    except sqlite3.Error as e:
        logger.error("Failed to initialize schema", error=str(e), db_path=str(db_path))
        raise


def get_schema() -> str:
    """Get the schema SQL string.

    Returns:
        The complete schema SQL definition.
    """
    return SCHEMA_SQL
