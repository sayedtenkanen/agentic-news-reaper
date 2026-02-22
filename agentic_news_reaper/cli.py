"""Command-line interface for agentic-news-reaper.

Provides commands for initializing the database, running the pipeline,
and generating weekly briefs.
"""

import sys
from pathlib import Path

import click

from agentic_news_reaper import __version__
from agentic_news_reaper.config import get_config
from agentic_news_reaper.db.schema import init_schema
from agentic_news_reaper.logging import configure_logging, get_logger

logger = get_logger(__name__)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.version_option(version=__version__, prog_name="agentic-news-reaper")
def cli(debug: bool) -> None:
    """Agentic News Reaper - Deterministic Execution Engine for News Analysis."""
    configure_logging(debug=debug)
    if debug:
        logger.info("debug mode enabled")


@cli.command()
@click.option(
    "--db-path",
    type=click.Path(),
    default=None,
    help="Path to SQLite database (default: hn_state.db)",
)
def init(db_path: Path | None) -> None:
    """Initialize the database schema."""
    config = get_config()

    if db_path:
        db_file = Path(db_path)
    else:
        db_file = Path(config.database.db_path)

    try:
        init_schema(db_file)
        click.secho(f"✓ Database initialized at {db_file}", fg="green")
        logger.info("database initialized", db_path=str(db_file))
    except Exception as e:
        click.secho(f"✗ Failed to initialize database: {e}", fg="red", err=True)
        logger.error("database initialization failed", error=str(e))
        sys.exit(1)


@cli.command()
@click.option(
    "--stories-count",
    type=int,
    default=100,
    help="Number of top stories to fetch from HN",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Run without persisting to database",
)
def run(stories_count: int, dry_run: bool) -> None:
    """Run the daily Hacker News analysis pipeline.

    This executes all agents in sequence:
    1. Fetch top stories from Hacker News
    2. Detect non-determinism (NDD)
    3. Mine execution patterns (EPM)
    4. Analyze failure modes (FMA)
    5. Check for human overrides (HOD)
    """
    _ = get_config()

    logger.info(
        "pipeline started",
        stories_count=stories_count,
        dry_run=dry_run,
    )

    try:
        # TODO: Implement pipeline execution
        click.echo("Pipeline execution not yet implemented.")
        logger.warning("pipeline execution not implemented")
    except Exception as e:
        click.secho(f"✗ Pipeline failed: {e}", fg="red", err=True)
        logger.error("pipeline execution failed", error=str(e))
        sys.exit(1)


@cli.command()
@click.option(
    "--week",
    type=str,
    default=None,
    help="Week to generate brief for (YYYY-W##, default: current week)",
)
@click.option(
    "--output",
    type=click.Path(),
    default=None,
    help="Output file path for the brief (default: stdout)",
)
def brief(week: str | None, output: str | None) -> None:
    """Generate a weekly founder brief.

    Aggregates all patterns, signals, and decisions from the week
    into a concise executive summary.
    """
    _ = get_config()

    logger.info("brief generation started", week=week, output=output)

    try:
        # TODO: Implement brief generation
        click.echo("Brief generation not yet implemented.")
        logger.warning("brief generation not implemented")
    except Exception as e:
        click.secho(f"✗ Brief generation failed: {e}", fg="red", err=True)
        logger.error("brief generation failed", error=str(e))
        sys.exit(1)


@cli.command()
def schema() -> None:
    """Display the database schema."""
    from agentic_news_reaper.db.schema import get_schema

    click.echo(get_schema())


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
