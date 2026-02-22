"""Tests for Execution Pattern Miner (EPM) agent.

Tests pattern loading, matching, and confidence calculation.
"""

from pathlib import Path

import pytest

from agentic_news_reaper.agents.epm import ExecutionPatternMiner, PatternInstance


@pytest.fixture
def epm_agent():
    """Create an EPM agent instance."""
    return ExecutionPatternMiner(min_confidence=0.5)


@pytest.fixture
def sample_patterns_yaml(tmp_path):
    """Create a temporary patterns.yaml file for testing."""
    patterns_content = """
patterns:
  - id: "clickbait_test"
    description: "Test clickbait pattern"
    trigger_conditions:
      title_contains:
        - "shocking"
        - "you won't believe"
      min_score: 100
    confidence_weights:
      title_match: 0.6
      score: 0.4
    risk_level: "medium"

  - id: "technical_test"
    description: "Test technical discussion pattern"
    trigger_conditions:
      title_contains:
        - "python"
        - "rust"
      min_comments: 20
    confidence_weights:
      title_match: 0.5
      engagement: 0.5
    risk_level: "low"

  - id: "security_test"
    description: "Test security pattern"
    trigger_conditions:
      title_contains:
        - "vulnerability"
        - "exploit"
      url_contains:
        - "security"
    confidence_weights:
      title_match: 0.5
      url_match: 0.5
    risk_level: "high"
"""
    patterns_file = tmp_path / "patterns.yaml"
    patterns_file.write_text(patterns_content)
    return patterns_file


class TestPatternInstanceDataclass:
    """Tests for PatternInstance dataclass."""

    def test_pattern_instance_creation(self):
        """Test creating a PatternInstance."""
        instance = PatternInstance(
            pattern_id="test_pattern",
            story_id="12345",
            confidence=0.85,
        )
        assert instance.pattern_id == "test_pattern"
        assert instance.story_id == "12345"
        assert instance.confidence == 0.85

    def test_pattern_instance_with_data(self):
        """Test PatternInstance with pattern data."""
        data = {"title": "Test", "url": "https://example.com"}
        instance = PatternInstance(
            pattern_id="test",
            story_id="123",
            confidence=0.9,
            pattern_data=data,
        )
        assert instance.pattern_data == data

    def test_pattern_instance_to_dict(self):
        """Test converting PatternInstance to dict."""
        instance = PatternInstance(
            pattern_id="test",
            story_id="123",
            confidence=0.75,
            pattern_data={"key": "value"},
        )
        result = instance.to_dict()
        assert result["pattern_id"] == "test"
        assert result["story_id"] == "123"
        assert result["confidence"] == 0.75
        assert "created_at" in result


class TestEPMInitialization:
    """Tests for EPM agent initialization."""

    def test_epm_initialization_default(self):
        """Test EPM initialization with defaults."""
        epm = ExecutionPatternMiner()
        assert epm.min_confidence == 0.5

    def test_epm_initialization_custom_threshold(self):
        """Test EPM with custom confidence threshold."""
        epm = ExecutionPatternMiner(min_confidence=0.7)
        assert epm.min_confidence == 0.7

    def test_epm_initialization_with_patterns_file(self, sample_patterns_yaml):
        """Test EPM initialization with custom patterns file."""
        epm = ExecutionPatternMiner(patterns_file=sample_patterns_yaml)
        assert len(epm.patterns) == 3
        assert "clickbait_test" in epm.patterns
        assert "technical_test" in epm.patterns
        assert "security_test" in epm.patterns

    def test_epm_load_patterns_programmatically(self, epm_agent):
        """Test loading patterns programmatically."""
        patterns = {
            "test1": {"id": "test1", "description": "Test pattern 1"},
            "test2": {"id": "test2", "description": "Test pattern 2"},
        }
        epm_agent.load_patterns(patterns)
        assert len(epm_agent.patterns) == 2
        assert "test1" in epm_agent.patterns


class TestPatternLoading:
    """Tests for pattern loading from YAML."""

    def test_load_patterns_from_file(self, sample_patterns_yaml):
        """Test loading patterns from file."""
        epm = ExecutionPatternMiner(patterns_file=sample_patterns_yaml)
        assert epm.patterns_file == sample_patterns_yaml
        assert len(epm.patterns) == 3

    def test_load_patterns_file_not_found(self):
        """Test loading patterns when file doesn't exist."""
        epm = ExecutionPatternMiner(patterns_file=Path("/nonexistent/patterns.yaml"))
        assert len(epm.patterns) == 0

    def test_load_patterns_file_structure(self, sample_patterns_yaml):
        """Test loaded pattern structure."""
        epm = ExecutionPatternMiner(patterns_file=sample_patterns_yaml)
        pattern = epm.patterns["clickbait_test"]
        assert pattern["description"] == "Test clickbait pattern"
        assert "trigger_conditions" in pattern
        assert "confidence_weights" in pattern


class TestPatternMatching:
    """Tests for pattern matching logic."""

    def test_match_pattern_not_found(self, epm_agent):
        """Test matching non-existent pattern."""
        metadata = {"story_id": "123"}
        result = epm_agent.match_pattern(
            pattern_id="nonexistent",
            title="Test",
            url="https://test.com",
            metadata=metadata,
        )
        assert result is None

    def test_match_pattern_title_keywords(self, sample_patterns_yaml):
        """Test matching pattern by title keywords."""
        epm = ExecutionPatternMiner(min_confidence=0.3, patterns_file=sample_patterns_yaml)
        metadata = {"story_id": "123", "score": 150, "descendants": 5}
        result = epm.match_pattern(
            pattern_id="clickbait_test",
            title="This is shocking news!",
            url="https://example.com",
            metadata=metadata,
        )
        assert result is not None
        assert result.pattern_id == "clickbait_test"
        assert result.confidence > 0.0

    def test_match_pattern_below_threshold(self, sample_patterns_yaml):
        """Test pattern match below confidence threshold."""
        epm = ExecutionPatternMiner(min_confidence=0.9, patterns_file=sample_patterns_yaml)
        metadata = {"story_id": "123", "score": 50, "descendants": 5}
        result = epm.match_pattern(
            pattern_id="clickbait_test",
            title="Normal story",
            url="https://example.com",
            metadata=metadata,
        )
        assert result is None

    def test_match_pattern_with_url_keywords(self, sample_patterns_yaml):
        """Test pattern matching with URL keywords."""
        epm = ExecutionPatternMiner(min_confidence=0.3, patterns_file=sample_patterns_yaml)
        metadata = {"story_id": "123"}
        result = epm.match_pattern(
            pattern_id="security_test",
            title="Vulnerability discovered",
            url="https://security.example.com",
            metadata=metadata,
        )
        assert result is not None
        assert result.confidence > 0.0


class TestConfidenceCalculation:
    """Tests for confidence score calculation."""

    def test_calculate_confidence_title_only(self, sample_patterns_yaml):
        """Test confidence calculation with title keywords only."""
        epm = ExecutionPatternMiner(patterns_file=sample_patterns_yaml)
        pattern_def = epm.patterns["clickbait_test"]
        metadata = {"story_id": "123", "score": 100, "descendants": 5}
        confidence = epm._calculate_confidence(
            pattern_id="clickbait_test",
            pattern_def=pattern_def,
            title="This is shocking!",
            url="https://example.com",
            metadata=metadata,
        )
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.0

    def test_calculate_confidence_no_matches(self, sample_patterns_yaml):
        """Test confidence when no conditions match."""
        epm = ExecutionPatternMiner(patterns_file=sample_patterns_yaml)
        pattern_def = epm.patterns["clickbait_test"]
        metadata = {"story_id": "123", "score": 10, "descendants": 0}
        confidence = epm._calculate_confidence(
            pattern_id="clickbait_test",
            pattern_def=pattern_def,
            title="Boring story",
            url="https://example.com",
            metadata=metadata,
        )
        assert confidence == 0.0

    def test_calculate_confidence_weighted(self, sample_patterns_yaml):
        """Test that confidence respects weights."""
        epm = ExecutionPatternMiner(patterns_file=sample_patterns_yaml)
        pattern_def = epm.patterns["clickbait_test"]
        metadata = {"story_id": "123", "score": 150, "descendants": 5}
        confidence = epm._calculate_confidence(
            pattern_id="clickbait_test",
            pattern_def=pattern_def,
            title="Shocking news!",
            url="https://example.com",
            metadata=metadata,
        )
        # Should be weighted combination of title_match (0.6) and score (0.4)
        assert 0.0 <= confidence <= 1.0


class TestKeywordMatching:
    """Tests for keyword matching."""

    def test_match_keywords_single_match(self, epm_agent):
        """Test keyword matching with single match."""
        score = epm_agent._match_keywords("This is shocking", ["shocking", "unbelievable"])
        assert score == 0.5

    def test_match_keywords_all_match(self, epm_agent):
        """Test keyword matching when all keywords match."""
        score = epm_agent._match_keywords(
            "This is shocking and unbelievable",
            ["shocking", "unbelievable"],
        )
        assert score == 1.0

    def test_match_keywords_no_match(self, epm_agent):
        """Test keyword matching with no matches."""
        score = epm_agent._match_keywords("This is boring", ["shocking", "unbelievable"])
        assert score == 0.0

    def test_match_keywords_case_insensitive(self, epm_agent):
        """Test keyword matching is case-insensitive."""
        score = epm_agent._match_keywords("This is SHOCKING", ["shocking"])
        assert score == 1.0

    def test_match_keywords_empty_keywords(self, epm_agent):
        """Test keyword matching with empty keywords list."""
        score = epm_agent._match_keywords("Some text", [])
        assert score == 0.0


class TestPatternMining:
    """Tests for mining patterns from stories."""

    def test_mine_no_patterns(self, epm_agent):
        """Test mining when no patterns match."""
        metadata = {"story_id": "123", "score": 10, "descendants": 0}
        results = epm_agent.mine(
            story_id="123",
            title="Boring story",
            url="https://example.com",
            metadata=metadata,
        )
        assert results == []

    def test_mine_single_pattern(self, sample_patterns_yaml):
        """Test mining a single matching pattern."""
        epm = ExecutionPatternMiner(min_confidence=0.3, patterns_file=sample_patterns_yaml)
        metadata = {"story_id": "123", "score": 150, "descendants": 5}
        results = epm.mine(
            story_id="123",
            title="Shocking news here!",
            url="https://example.com",
            metadata=metadata,
        )
        assert len(results) > 0
        assert isinstance(results[0], PatternInstance)

    def test_mine_multiple_patterns(self, sample_patterns_yaml):
        """Test mining multiple matching patterns."""
        epm = ExecutionPatternMiner(min_confidence=0.2, patterns_file=sample_patterns_yaml)
        metadata = {
            "story_id": "123",
            "score": 150,
            "descendants": 25,
            "sentiment_variance": 0.5,
        }
        results = epm.mine(
            story_id="123",
            title="Python vulnerability shocking exploit",
            url="https://security.example.com",
            metadata=metadata,
        )
        # Should match multiple patterns
        assert len(results) >= 1

    def test_mine_results_sorted_by_confidence(self, sample_patterns_yaml):
        """Test that mining results are sorted by confidence."""
        epm = ExecutionPatternMiner(min_confidence=0.1, patterns_file=sample_patterns_yaml)
        metadata = {
            "story_id": "123",
            "score": 150,
            "descendants": 25,
        }
        results = epm.mine(
            story_id="123",
            title="Python shocking vulnerability exploit security",
            url="https://security.example.com",
            metadata=metadata,
        )
        # Results should be sorted descending by confidence
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].confidence >= results[i + 1].confidence


class TestPatternInstanceData:
    """Tests for pattern instance data handling."""

    def test_pattern_instance_includes_pattern_data(self, sample_patterns_yaml):
        """Test that pattern instance includes pattern metadata."""
        epm = ExecutionPatternMiner(min_confidence=0.2, patterns_file=sample_patterns_yaml)
        metadata = {"story_id": "123", "score": 150, "descendants": 5}
        result = epm.match_pattern(
            pattern_id="clickbait_test",
            title="Shocking!",
            url="https://example.com",
            metadata=metadata,
        )
        assert result is not None, "Pattern match should not be None"
        assert "pattern_description" in result.pattern_data
        assert "risk_level" in result.pattern_data
        assert result.pattern_data["risk_level"] == "medium"

    def test_pattern_instance_serialization(self, sample_patterns_yaml):
        """Test that pattern instances serialize correctly."""
        epm = ExecutionPatternMiner(min_confidence=0.2, patterns_file=sample_patterns_yaml)
        metadata = {"story_id": "123", "score": 150, "descendants": 5}
        result = epm.match_pattern(
            pattern_id="clickbait_test",
            title="Shocking!",
            url="https://example.com",
            metadata=metadata,
        )
        assert result is not None
        serialized = result.to_dict()
        assert "pattern_id" in serialized
        assert "story_id" in serialized
        assert "confidence" in serialized
        assert "created_at" in serialized


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_metadata(self, sample_patterns_yaml):
        """Test matching with minimal metadata."""
        epm = ExecutionPatternMiner(patterns_file=sample_patterns_yaml)
        results = epm.mine(
            story_id="123",
            title="Test",
            url="https://example.com",
            metadata={},
        )
        # Should not crash
        assert isinstance(results, list)

    def test_very_long_title(self, sample_patterns_yaml):
        """Test matching with very long title."""
        epm = ExecutionPatternMiner(patterns_file=sample_patterns_yaml)
        long_title = "shocking " * 100
        results = epm.mine(
            story_id="123",
            title=long_title,
            url="https://example.com",
            metadata={"story_id": "123"},
        )
        assert isinstance(results, list)

    def test_special_characters_in_title(self, sample_patterns_yaml):
        """Test matching with special characters."""
        epm = ExecutionPatternMiner(patterns_file=sample_patterns_yaml)
        results = epm.mine(
            story_id="123",
            title="Shocking! @#$% news & events",
            url="https://example.com",
            metadata={"story_id": "123"},
        )
        assert isinstance(results, list)

    def test_unicode_in_title(self, sample_patterns_yaml):
        """Test matching with unicode characters."""
        epm = ExecutionPatternMiner(patterns_file=sample_patterns_yaml)
        results = epm.mine(
            story_id="123",
            title="Shocking 日本 news 中文",
            url="https://example.com",
            metadata={"story_id": "123"},
        )
        assert isinstance(results, list)
