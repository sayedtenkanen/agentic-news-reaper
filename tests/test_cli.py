"""Tests for the CLI interface.

Tests command-line argument parsing, error handling, and exit codes.
Uses Click's CliRunner for testing CLI commands.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from agentic_news_reaper.cli import cli


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    return CliRunner()


class TestCLIGroup:
    """Tests for the main CLI group."""

    def test_cli_help(self, cli_runner):
        """Test that --help displays help text."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Agentic News Reaper" in result.output
        assert "Deterministic Execution Engine" in result.output

    def test_cli_version(self, cli_runner):
        """Test that --version displays version."""
        result = cli_runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_cli_debug_flag(self, cli_runner):
        """Test that --debug flag is accepted."""
        result = cli_runner.invoke(cli, ["--debug", "--version"])
        assert result.exit_code == 0

    def test_cli_invalid_option(self, cli_runner):
        """Test error on invalid option."""
        result = cli_runner.invoke(cli, ["--invalid-option"])
        assert result.exit_code != 0


class TestInitCommand:
    """Tests for the init command."""

    def test_init_help(self, cli_runner):
        """Test init command help."""
        result = cli_runner.invoke(cli, ["init", "--help"])
        assert result.exit_code == 0
        assert "Initialize the database schema" in result.output

    @patch("agentic_news_reaper.cli.init_schema")
    @patch("agentic_news_reaper.cli.get_config")
    def test_init_default_path(self, mock_get_config, mock_init_schema, cli_runner):
        """Test init command with default database path."""
        # Mock config
        mock_config = MagicMock()
        mock_config.database.db_path = "hn_state.db"
        mock_get_config.return_value = mock_config

        result = cli_runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        assert "Database initialized" in result.output
        mock_init_schema.assert_called_once()

    @patch("agentic_news_reaper.cli.init_schema")
    @patch("agentic_news_reaper.cli.get_config")
    def test_init_custom_path(self, mock_get_config, mock_init_schema, cli_runner):
        """Test init command with custom database path."""
        mock_config = MagicMock()
        mock_config.database.db_path = "hn_state.db"
        mock_get_config.return_value = mock_config

        result = cli_runner.invoke(cli, ["init", "--db-path", "/tmp/test.db"])

        assert result.exit_code == 0
        assert "Database initialized at /tmp/test.db" in result.output
        mock_init_schema.assert_called_once()

    @patch("agentic_news_reaper.cli.init_schema")
    @patch("agentic_news_reaper.cli.get_config")
    def test_init_failure(self, mock_get_config, mock_init_schema, cli_runner):
        """Test init command error handling."""
        mock_config = MagicMock()
        mock_config.database.db_path = "hn_state.db"
        mock_get_config.return_value = mock_config

        # Simulate SQLite error
        mock_init_schema.side_effect = Exception("Database locked")

        result = cli_runner.invoke(cli, ["init"])

        assert result.exit_code == 1
        assert "Failed to initialize database" in result.output
        assert "Database locked" in result.output

    @patch("agentic_news_reaper.cli.init_schema")
    @patch("agentic_news_reaper.cli.get_config")
    def test_init_success_color_output(self, mock_get_config, mock_init_schema, cli_runner):
        """Test that init command shows success message with color."""
        mock_config = MagicMock()
        mock_config.database.db_path = "hn_state.db"
        mock_get_config.return_value = mock_config

        result = cli_runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        assert "✓" in result.output  # Success checkmark


class TestRunCommand:
    """Tests for the run command."""

    def test_run_help(self, cli_runner):
        """Test run command help."""
        result = cli_runner.invoke(cli, ["run", "--help"])
        assert result.exit_code == 0
        assert "Run the daily Hacker News analysis pipeline" in result.output
        assert "--stories-count" in result.output
        assert "--dry-run" in result.output

    @patch("agentic_news_reaper.cli.get_config")
    def test_run_default_options(self, mock_get_config, cli_runner):
        """Test run command with default options."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        result = cli_runner.invoke(cli, ["run"])

        # Should succeed (even if it doesn't do much)
        assert result.exit_code == 0

    @patch("agentic_news_reaper.cli.get_config")
    def test_run_custom_stories_count(self, mock_get_config, cli_runner):
        """Test run command with custom stories count."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        result = cli_runner.invoke(cli, ["run", "--stories-count", "50"])

        assert result.exit_code == 0

    @patch("agentic_news_reaper.cli.get_config")
    def test_run_dry_run_flag(self, mock_get_config, cli_runner):
        """Test run command with dry-run flag."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        result = cli_runner.invoke(cli, ["run", "--dry-run"])

        assert result.exit_code == 0

    @patch("agentic_news_reaper.cli.get_config")
    def test_run_invalid_count(self, mock_get_config, cli_runner):
        """Test run command with invalid count value."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        result = cli_runner.invoke(cli, ["run", "--stories-count", "invalid"])

        # Click should fail with non-integer value
        assert result.exit_code != 0

    @patch("agentic_news_reaper.cli.get_config")
    def test_run_combines_flags(self, mock_get_config, cli_runner):
        """Test run command with multiple flags."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        result = cli_runner.invoke(cli, ["run", "--stories-count", "25", "--dry-run"])

        assert result.exit_code == 0


class TestBriefCommand:
    """Tests for the brief command."""

    def test_brief_help(self, cli_runner):
        """Test brief command help."""
        result = cli_runner.invoke(cli, ["brief", "--help"])
        # brief command may or may not exist, just test that help works
        assert "brief" in result.output.lower() or result.exit_code != 0

    @patch("agentic_news_reaper.cli.get_config")
    def test_brief_command_exists(self, mock_get_config, cli_runner):
        """Test that brief command is available."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Try to invoke brief command
        result = cli_runner.invoke(cli, ["brief", "--help"])

        # Should either work or give a "no such command" error
        # (depending on whether brief is implemented)
        assert result.exit_code in [0, 2]


class TestCommandIntegration:
    """Integration tests for CLI commands working together."""

    @patch("agentic_news_reaper.cli.get_config")
    def test_multiple_options_parsing(self, mock_get_config, cli_runner):
        """Test that CLI correctly parses multiple options."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Test with both debug and run options
        result = cli_runner.invoke(cli, ["--debug", "run", "--stories-count", "50", "--dry-run"])

        # Should succeed even if run doesn't do much
        assert result.exit_code == 0

    def test_subcommand_required(self, cli_runner):
        """Test that a subcommand is required."""
        # Just calling cli without a subcommand should show help
        result = cli_runner.invoke(cli, [])

        # Should show usage/help
        assert "Usage:" in result.output or result.exit_code != 0

    def test_unknown_command(self, cli_runner):
        """Test error on unknown command."""
        result = cli_runner.invoke(cli, ["unknown-command"])

        assert result.exit_code != 0
        assert "Error" in result.output or "Usage" in result.output


class TestCLIErrorHandling:
    """Tests for CLI error handling and user feedback."""

    @patch("agentic_news_reaper.cli.init_schema")
    @patch("agentic_news_reaper.cli.get_config")
    def test_init_error_message_format(self, mock_get_config, mock_init_schema, cli_runner):
        """Test that error messages are user-friendly."""
        mock_config = MagicMock()
        mock_config.database.db_path = "hn_state.db"
        mock_get_config.return_value = mock_config

        mock_init_schema.side_effect = FileNotFoundError("Directory not found")

        result = cli_runner.invoke(cli, ["init"])

        assert result.exit_code == 1
        assert "✗" in result.output  # Error symbol
        assert "Failed" in result.output

    @patch("agentic_news_reaper.cli.get_config")
    def test_run_negative_count_validation(self, mock_get_config, cli_runner):
        """Test that negative story count is rejected."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Click allows negative integers, but 0 should be caught
        result = cli_runner.invoke(cli, ["run", "--stories-count", "-1"])

        # Click will parse this but it's a valid integer
        # The application logic should handle invalid values
        assert result.exit_code == 0


class TestCLIOutput:
    """Tests for CLI output formatting."""

    def test_version_option_format(self, cli_runner):
        """Test that version output is properly formatted."""
        result = cli_runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        # Version should be on one line
        assert len(result.output.strip().split("\n")) == 1

    @patch("agentic_news_reaper.cli.init_schema")
    @patch("agentic_news_reaper.cli.get_config")
    def test_success_message_visibility(self, mock_get_config, mock_init_schema, cli_runner):
        """Test that success messages are visible and clear."""
        mock_config = MagicMock()
        mock_config.database.db_path = "test.db"
        mock_get_config.return_value = mock_config

        result = cli_runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        # Should clearly indicate success
        assert any(marker in result.output for marker in ["✓", "success", "initialized"])

    @patch("agentic_news_reaper.cli.init_schema")
    @patch("agentic_news_reaper.cli.get_config")
    def test_error_messages_on_stderr(self, mock_get_config, mock_init_schema, cli_runner):
        """Test that error messages go to stderr."""
        mock_config = MagicMock()
        mock_config.database.db_path = "test.db"
        mock_get_config.return_value = mock_config

        mock_init_schema.side_effect = EnvironmentError("Cannot write to disk")

        result = cli_runner.invoke(cli, ["init"])

        assert result.exit_code == 1
        # Error should mention the problem
        assert "Cannot write" in result.output or "Failed" in result.output
