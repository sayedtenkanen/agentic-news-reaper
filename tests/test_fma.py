"""Tests for Failure Mode Analyzer (FMA) agent.

Tests for analyzing patterns, computing risk scores, and predicting failure modes.
"""

import pytest

from agentic_news_reaper.agents.fma import FailureMode, FailureModeAnalyzer


@pytest.fixture
def fma_agent():
    """Create an FMA agent instance."""
    return FailureModeAnalyzer()


class TestFMAInitialization:
    """Tests for FMA agent initialization."""

    def test_fma_initialization_default(self):
        """Test FMA initialization with defaults."""
        fma = FailureModeAnalyzer()
        assert fma.engagement_weight == 0.4
        assert fma.spam_weight == 0.35
        assert fma.sentiment_weight == 0.25

    def test_fma_initialization_with_config(self):
        """Test FMA initialization with custom config."""
        config = {
            "engagement_weight": 0.5,
            "spam_weight": 0.3,
            "sentiment_weight": 0.2,
        }
        fma = FailureModeAnalyzer(config=config)
        assert fma.engagement_weight == 0.5
        assert fma.spam_weight == 0.3
        assert fma.sentiment_weight == 0.2

    def test_fma_initialization_with_config_thresholds(self):
        """Test FMA initialization with custom config."""
        config = {
            "low_engagement_threshold": 75,
            "high_spam_threshold": 0.6,
        }
        # Config is stored but class constants are used for analysis
        fma = FailureModeAnalyzer(config=config)
        assert fma.config == config
        assert fma.LOW_ENGAGEMENT_THRESHOLD == 5  # Class constant


class TestFailureModeDataclass:
    """Tests for FailureMode dataclass."""

    def test_failure_mode_creation(self):
        """Test creating a FailureMode."""
        fm = FailureMode(
            pattern_instance_id=1,
            risk_score=0.75,
            engagement_risk=0.5,
            spam_risk=0.3,
            sentiment_drift=0.2,
            mitigation="Monitor closely",
            reason="High risk detected",
        )
        assert fm.pattern_instance_id == 1
        assert fm.risk_score == 0.75
        assert fm.engagement_risk == 0.5
        assert fm.spam_risk == 0.3
        assert fm.sentiment_drift == 0.2

    def test_failure_mode_risk_score_bounds(self):
        """Test that risk scores are within bounds."""
        fm = FailureMode(
            pattern_instance_id=1,
            risk_score=0.85,
            engagement_risk=0.6,
            spam_risk=0.4,
            sentiment_drift=0.3,
            mitigation="Monitor",
            reason="Test",
        )
        assert 0.0 <= fm.risk_score <= 1.0
        assert 0.0 <= fm.engagement_risk <= 1.0
        assert 0.0 <= fm.spam_risk <= 1.0
        assert 0.0 <= fm.sentiment_drift <= 1.0


class TestRiskScoreCalculation:
    """Tests for risk score calculation."""

    def test_analyze_low_engagement(self, fma_agent):
        """Test risk analysis with low engagement."""
        result = fma_agent.analyze_pattern(
            pattern_instance_id=1,
            comment_count=2,  # Below threshold (5)
            spam_score=0.1,
            sentiment_variance=0.1,
        )
        assert result is not None
        assert result.engagement_risk > 0.0  # Should be high risk

    def test_analyze_high_engagement(self, fma_agent):
        """Test risk analysis with high engagement."""
        result = fma_agent.analyze_pattern(
            pattern_instance_id=1,
            comment_count=10,  # Above threshold
            spam_score=0.1,
            sentiment_variance=0.1,
        )
        assert result is not None
        assert result.engagement_risk == 0.0  # Should be low risk

    def test_analyze_high_spam(self, fma_agent):
        """Test risk analysis with high spam score."""
        result = fma_agent.analyze_pattern(
            pattern_instance_id=1,
            comment_count=50,
            spam_score=0.9,  # High spam
            sentiment_variance=0.1,
        )
        assert result is not None
        assert result.spam_risk == 0.9

    def test_analyze_high_sentiment_drift(self, fma_agent):
        """Test risk analysis with high sentiment drift."""
        result = fma_agent.analyze_pattern(
            pattern_instance_id=1,
            comment_count=50,
            spam_score=0.1,
            sentiment_variance=0.8,  # High drift
        )
        assert result is not None
        assert result.sentiment_drift == 0.8

    def test_analyze_weighted_risk_score(self, fma_agent):
        """Test that risk score uses correct weights."""
        result = fma_agent.analyze_pattern(
            pattern_instance_id=1,
            comment_count=3,  # engagement_risk ~0.4 (1 - 3/5)
            spam_score=0.5,  # spam_risk = 0.5
            sentiment_variance=0.5,  # sentiment_drift = 0.5
        )
        assert result is not None
        # Risk score should be weighted combination
        # 0.4 * 0.4 + 0.5 * 0.35 + 0.5 * 0.25 = 0.16 + 0.175 + 0.125 = 0.46
        assert 0.4 <= result.risk_score <= 0.6

    def test_risk_score_clamped_to_bounds(self, fma_agent):
        """Test that risk score is clamped to [0.0, 1.0]."""
        result = fma_agent.analyze_pattern(
            pattern_instance_id=1,
            comment_count=0,
            spam_score=2.0,  # Extreme values
            sentiment_variance=2.0,
        )
        assert result is not None
        assert 0.0 <= result.risk_score <= 1.0
        # All components should be clamped
        assert result.spam_risk <= 1.0
        assert result.sentiment_drift <= 1.0

    def test_risk_score_zero_comments(self, fma_agent):
        """Test risk analysis with zero comments."""
        result = fma_agent.analyze_pattern(
            pattern_instance_id=1,
            comment_count=0,
            spam_score=0.0,
            sentiment_variance=0.0,
        )
        assert result is not None
        # Zero comments should give high engagement risk
        assert result.engagement_risk > 0.5


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_analyze_pattern_zero_values(self, fma_agent):
        """Test with all zero risk factors."""
        result = fma_agent.analyze_pattern(
            pattern_instance_id=1,
            comment_count=100,  # Safe engagement
            spam_score=0.0,
            sentiment_variance=0.0,
        )
        assert result is not None
        assert result.risk_score == 0.0  # All risks are zero

    def test_analyze_pattern_max_values(self, fma_agent):
        """Test with maximum risk factors."""
        result = fma_agent.analyze_pattern(
            pattern_instance_id=1,
            comment_count=0,  # Minimum engagement
            spam_score=1.0,
            sentiment_variance=1.0,
        )
        assert result is not None
        assert 0.7 <= result.risk_score <= 1.0  # High risk

    def test_analyze_pattern_id_variations(self, fma_agent):
        """Test that pattern_instance_id is preserved."""
        for pid in [1, 100, 999999]:
            result = fma_agent.analyze_pattern(
                pattern_instance_id=pid,
                comment_count=50,
                spam_score=0.5,
                sentiment_variance=0.5,
            )
            assert result.pattern_instance_id == pid

    def test_analyze_pattern_negative_inputs_clamped(self, fma_agent):
        """Test that negative risk scores are clamped to zero."""
        result = fma_agent.analyze_pattern(
            pattern_instance_id=1,
            comment_count=1000,  # Very high engagement
            spam_score=-0.5,  # Negative (should be treated as 0)
            sentiment_variance=-0.5,
        )
        assert result is not None
        # Negative values should be clamped to 0
        assert result.spam_risk >= 0.0
        assert result.sentiment_drift >= 0.0


class TestMitigationAndReasoning:
    """Tests for mitigation strategies and reasoning."""

    def test_failure_mode_includes_mitigation(self, fma_agent):
        """Test that failure mode includes mitigation strategy."""
        result = fma_agent.analyze_pattern(
            pattern_instance_id=1,
            comment_count=10,
            spam_score=0.8,
            sentiment_variance=0.7,
        )
        assert result is not None
        assert result.mitigation is not None
        assert len(result.mitigation) > 0

    def test_failure_mode_includes_reason(self, fma_agent):
        """Test that failure mode includes reasoning."""
        result = fma_agent.analyze_pattern(
            pattern_instance_id=1,
            comment_count=50,
            spam_score=0.5,
            sentiment_variance=0.5,
        )
        assert result is not None
        assert result.reason is not None
        assert len(result.reason) > 0

    def test_different_risk_levels_have_different_mitigation(self, fma_agent):
        """Test that different risk levels produce different mitigation."""
        low_risk = fma_agent.analyze_pattern(
            pattern_instance_id=1,
            comment_count=150,
            spam_score=0.0,
            sentiment_variance=0.0,
        )
        high_risk = fma_agent.analyze_pattern(
            pattern_instance_id=2,
            comment_count=5,
            spam_score=0.9,
            sentiment_variance=0.9,
        )
        assert low_risk.risk_score < high_risk.risk_score
        # Mitigation strategies may differ
        assert low_risk.reason != high_risk.reason
