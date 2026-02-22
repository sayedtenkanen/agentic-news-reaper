"""Smoke tests for agentic-news-reaper.

Basic tests to verify core functionality and imports.
"""

from agentic_news_reaper import __version__
from agentic_news_reaper.agents import (
    ExecutionPatternMiner,
    FailureModeAnalyzer,
    HumanOverrideDetector,
    NonDeterminismDetector,
)
from agentic_news_reaper.config import get_config
from agentic_news_reaper.db.schema import get_schema


def test_version():
    """Test that version is set."""
    assert __version__ == "0.1.0"


def test_config_loads():
    """Test that configuration loads without error."""
    config = get_config()
    assert config is not None
    assert config.database.db_path == "hn_state.db"
    assert config.agents.ndd_ambiguity_threshold == 0.78
    assert config.agents.hod_override_threshold == 0.9


def test_ndd_agent_initialization():
    """Test Non-Determinism Detector initialization."""
    ndd = NonDeterminismDetector(ambiguity_threshold=0.78)
    assert ndd.ambiguity_threshold == 0.78


def test_ndd_analyze_non_ambiguous():
    """Test NDD correctly identifies non-ambiguous titles."""
    ndd = NonDeterminismDetector(ambiguity_threshold=0.78)
    result = ndd.analyze(
        story_id="12345",
        title="Python 3.12 Released",
        comments_count=50,
    )
    assert result is None


def test_ndd_analyze_ambiguous():
    """Test NDD correctly identifies ambiguous titles."""
    ndd = NonDeterminismDetector(ambiguity_threshold=0.5)
    result = ndd.analyze(
        story_id="12345",
        title="You won't believe what happened next!",
        comments_count=50,
    )
    assert result is not None
    assert result.story_id == "12345"
    assert result.ambiguity_score >= 0.5


def test_epm_agent_initialization():
    """Test Execution Pattern Miner initialization."""
    epm = ExecutionPatternMiner(min_confidence=0.5)
    assert epm.min_confidence == 0.5


def test_epm_mine_empty():
    """Test EPM returns empty list for empty patterns."""
    epm = ExecutionPatternMiner()
    patterns = epm.mine(
        story_id="12345",
        title="Test Story",
        url="https://example.com",
        metadata={},
    )
    assert patterns == []


def test_fma_agent_initialization():
    """Test Failure Mode Analyzer initialization."""
    fma = FailureModeAnalyzer()
    assert fma.engagement_weight == 0.4
    assert fma.spam_weight == 0.35
    assert fma.sentiment_weight == 0.25


def test_fma_analyze_pattern():
    """Test FMA can analyze a pattern."""
    fma = FailureModeAnalyzer()
    result = fma.analyze_pattern(
        pattern_instance_id=1,
        comment_count=50,
        spam_score=0.1,
        sentiment_variance=0.2,
    )
    assert result.pattern_instance_id == 1
    assert 0.0 <= result.risk_score <= 1.0
    assert result.engagement_risk == 0.0  # 50 > threshold


def test_fma_low_engagement():
    """Test FMA detects low engagement risk."""
    fma = FailureModeAnalyzer()
    result = fma.analyze_pattern(
        pattern_instance_id=1,
        comment_count=2,
        spam_score=0.1,
        sentiment_variance=0.1,
    )
    assert result.engagement_risk > 0.5


def test_hod_agent_initialization():
    """Test Human Override Detector initialization."""
    hod = HumanOverrideDetector(override_threshold=0.9)
    assert hod.override_threshold == 0.9


def test_hod_evaluate_low_risk():
    """Test HOD correctly handles low-risk patterns."""
    hod = HumanOverrideDetector(override_threshold=0.9)
    result = hod.evaluate(
        story_id="12345",
        risk_score=0.5,
        pattern_type="general",
    )
    assert result.requires_override is False
    assert result.story_id == "12345"


def test_hod_evaluate_high_risk():
    """Test HOD correctly requires override for high-risk patterns."""
    hod = HumanOverrideDetector(override_threshold=0.9)
    result = hod.evaluate(
        story_id="12345",
        risk_score=0.95,
        pattern_type="financial",
    )
    assert result.requires_override is True
    assert "financial" in result.reason.lower() or "market" in result.reason.lower()


def test_schema_generates():
    """Test that database schema generates without error."""
    schema = get_schema()
    assert schema is not None
    assert "CREATE TABLE" in schema
    assert "hn_raw" in schema
    assert "patterns_instances" in schema
    assert "failure_modes" in schema
    assert "override_log" in schema
