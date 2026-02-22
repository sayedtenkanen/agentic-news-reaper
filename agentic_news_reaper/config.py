"""Configuration management for agentic-news-reaper.

Loads settings from environment variables and .env files.
Provides typed configuration objects for all system components.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    db_path: str = Field(
        default="hn_state.db",
        description="Path to SQLite database file",
        validation_alias="ANR_DB_PATH",
    )
    schema_path: str = Field(
        default="schema.sql",
        description="Path to database schema SQL file",
        validation_alias="ANR_SCHEMA_PATH",
    )

    class Config:
        env_prefix = "ANR_"
        case_sensitive = False


class HackerNewsConfig(BaseSettings):
    """Hacker News API configuration."""

    api_base_url: str = Field(
        default="https://hacker-news.firebaseio.com/v0",
        description="HN Firebase API base URL",
        validation_alias="ANR_HN_API_BASE_URL",
    )
    top_stories_count: int = Field(
        default=100,
        description="Number of top stories to fetch",
        validation_alias="ANR_HN_STORIES_COUNT",
    )
    timeout_seconds: int = Field(
        default=30,
        description="HTTP request timeout in seconds",
        validation_alias="ANR_HN_TIMEOUT",
    )

    class Config:
        env_prefix = "ANR_"
        case_sensitive = False


class AgentConfig(BaseSettings):
    """Multi-agent system configuration."""

    # Non-Determinism Detector (NDD)
    ndd_ambiguity_threshold: float = Field(
        default=0.78,
        description="Title ambiguity threshold for NDD (0.0-1.0)",
        validation_alias="ANR_NDD_AMBIGUITY_THRESHOLD",
    )

    # Human Override Detector (HOD)
    hod_override_threshold: float = Field(
        default=0.9,
        description="Risk threshold requiring human override (0.0-1.0)",
        validation_alias="ANR_HOD_OVERRIDE_THRESHOLD",
    )

    # Execution Pattern Miner (EPM)
    epm_min_confidence: float = Field(
        default=0.5,
        description="Minimum confidence for pattern matching (0.0-1.0)",
        validation_alias="ANR_EPM_MIN_CONFIDENCE",
    )

    class Config:
        env_prefix = "ANR_"
        case_sensitive = False


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        validation_alias="ANR_LOG_LEVEL",
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or text)",
        validation_alias="ANR_LOG_FORMAT",
    )

    class Config:
        env_prefix = "ANR_"
        case_sensitive = False


class AppConfig(BaseSettings):
    """Root application configuration."""

    debug: bool = Field(
        default=False,
        description="Enable debug mode",
        validation_alias="ANR_DEBUG",
    )
    env: str = Field(
        default="development",
        description="Environment (development, staging, production)",
        validation_alias="ANR_ENV",
    )

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    hacker_news: HackerNewsConfig = Field(default_factory=HackerNewsConfig)
    agents: AgentConfig = Field(default_factory=AgentConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    class Config:
        env_prefix = "ANR_"
        case_sensitive = False

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> "AppConfig":
        """Load configuration from environment and optional .env file.

        Args:
            env_file: Optional path to .env file to load first.

        Returns:
            AppConfig instance with all settings loaded.
        """
        if env_file and env_file.exists():
            from dotenv import load_dotenv

            load_dotenv(env_file)

        return cls()


def get_config() -> AppConfig:
    """Get application configuration (singleton pattern).

    Returns:
        AppConfig instance loaded from environment.
    """
    return AppConfig.from_env(env_file=Path(".env"))
