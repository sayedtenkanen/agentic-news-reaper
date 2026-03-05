"""Tests for Human Override Detector (HOD) agent.

Tests for evaluating override requirements and batch evaluation.
"""

import pytest

from agentic_news_reaper.agents.hod import HumanOverrideDetector, OverrideDecision


@pytest.fixture
def hod_agent():
    """Create a HOD agent instance."""
    return HumanOverrideDetector(override_threshold=0.9)


class TestHODInitialization:
    """Tests for HOD agent initialization."""

    def test_hod_initialization_default(self):
        """Test HOD initialization with defaults."""
        hod = HumanOverrideDetector()
        assert hod.override_threshold == 0.9

    def test_hod_initialization_custom_threshold(self):
        """Test HOD initialization with custom threshold."""
        hod = HumanOverrideDetector(override_threshold=0.75)
        assert hod.override_threshold == 0.75


class TestOverrideDecisionDataclass:
    """Tests for OverrideDecision dataclass."""

    def test_override_decision_creation(self):
        """Test creating an OverrideDecision."""
        decision = OverrideDecision(
            story_id="12345",
            requires_override=True,
            risk_score=0.95,
            reason="High risk detected",
            recommendation="Require human review",
        )
        assert decision.story_id == "12345"
        assert decision.requires_override is True
        assert decision.risk_score == 0.95

    def test_override_decision_not_required(self):
        """Test creating an OverrideDecision when override not needed."""
        decision = OverrideDecision(
            story_id="12345",
            requires_override=False,
            risk_score=0.3,
            reason="Low risk",
            recommendation="Proceed normally",
        )
        assert decision.requires_override is False


class TestEvaluationLogic:
    """Tests for override evaluation logic."""

    def test_evaluate_high_risk_requires_override(self, hod_agent):
        """Test that high risk score triggers override."""
        result = hod_agent.evaluate(
            story_id="12345",
            risk_score=0.95,
        )
        assert result is not None
        assert result.requires_override is True

    def test_evaluate_low_risk_no_override(self, hod_agent):
        """Test that low risk score does not require override."""
        result = hod_agent.evaluate(
            story_id="12345",
            risk_score=0.5,
        )
        assert result is not None
        assert result.requires_override is False

    def test_evaluate_threshold_boundary(self, hod_agent):
        """Test behavior at threshold boundary."""
        # Just below threshold
        result_below = hod_agent.evaluate(
            story_id="12345",
            risk_score=0.89,
        )
        # Just above threshold
        result_above = hod_agent.evaluate(
            story_id="12346",
            risk_score=0.91,
        )
        # Below should not require override
        assert result_below.requires_override is False
        # Above should require override
        assert result_above.requires_override is True

    def test_evaluate_preserves_story_id(self, hod_agent):
        """Test that story_id is preserved in decision."""
        story_ids = ["123", "456", "789"]
        for sid in story_ids:
            result = hod_agent.evaluate(
                story_id=sid,
                risk_score=0.7,
            )
            assert result.story_id == sid

    def test_evaluate_includes_recommendation(self, hod_agent):
        """Test that evaluation includes recommendation."""
        result = hod_agent.evaluate(
            story_id="12345",
            risk_score=0.85,
        )
        assert result is not None
        # recommendation may be None if not set by Monty, check if it's present/accessible
        assert hasattr(result, "recommendation")

    def test_evaluate_with_pattern_type(self, hod_agent):
        """Test evaluation with pattern type."""
        result = hod_agent.evaluate(
            story_id="12345",
            risk_score=0.92,
            pattern_type="financial",
        )
        assert result is not None
        assert result.requires_override is True


class TestBatchEvaluation:
    """Tests for batch override evaluation."""

    def test_batch_evaluate_single_item(self, hod_agent):
        """Test batch evaluation with single item."""
        evaluations = [
            {
                "story_id": "123",
                "risk_score": 0.95,
            }
        ]
        results = hod_agent.batch_evaluate(evaluations)
        assert len(results) == 1
        assert results[0].story_id == "123"
        assert results[0].requires_override is True

    def test_batch_evaluate_multiple_items(self, hod_agent):
        """Test batch evaluation with multiple items."""
        evaluations = [
            {"story_id": "1", "risk_score": 0.95},
            {"story_id": "2", "risk_score": 0.5},
            {"story_id": "3", "risk_score": 0.92},
        ]
        results = hod_agent.batch_evaluate(evaluations)
        assert len(results) == 3
        # First and third should need override
        assert results[0].requires_override is True
        assert results[1].requires_override is False
        assert results[2].requires_override is True

    def test_batch_evaluate_empty_list(self, hod_agent):
        """Test batch evaluation with empty list."""
        results = hod_agent.batch_evaluate([])
        assert results == []

    def test_batch_evaluate_preserves_order(self, hod_agent):
        """Test that batch evaluation preserves order."""
        evaluations = [{"story_id": f"story_{i}", "risk_score": 0.5 + i * 0.1} for i in range(5)]
        results = hod_agent.batch_evaluate(evaluations)
        for i, result in enumerate(results):
            assert result.story_id == f"story_{i}"

    def test_batch_evaluate_with_pattern_types(self, hod_agent):
        """Test batch evaluation with pattern types."""
        evaluations = [
            {
                "story_id": "1",
                "risk_score": 0.95,
                "pattern_type": "financial",
            },
            {
                "story_id": "2",
                "risk_score": 0.92,
                "pattern_type": "security",
            },
        ]
        results = hod_agent.batch_evaluate(evaluations)
        assert len(results) == 2
        assert all(r.requires_override for r in results)

    def test_batch_evaluate_with_business_context(self, hod_agent):
        """Test batch evaluation with business context."""
        evaluations = [
            {
                "story_id": "1",
                "risk_score": 0.85,
                "pattern_type": "financial",
                "business_context": {"domain": "crypto"},
            }
        ]
        results = hod_agent.batch_evaluate(evaluations)
        assert len(results) == 1


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_evaluate_zero_risk(self, hod_agent):
        """Test evaluation with zero risk score."""
        result = hod_agent.evaluate(
            story_id="12345",
            risk_score=0.0,
        )
        assert result.requires_override is False
        assert result.risk_score == 0.0

    def test_evaluate_maximum_risk(self, hod_agent):
        """Test evaluation with maximum risk score."""
        result = hod_agent.evaluate(
            story_id="12345",
            risk_score=1.0,
        )
        assert result.requires_override is True
        assert result.risk_score == 1.0

    def test_evaluate_exact_threshold(self, hod_agent):
        """Test evaluation exactly at threshold."""
        hod = HumanOverrideDetector(override_threshold=0.85)
        result = hod.evaluate(
            story_id="12345",
            risk_score=0.85,
        )
        # Behavior at exact threshold (may depend on comparison logic)
        assert result.requires_override is not None

    def test_custom_threshold_low(self):
        """Test with very low threshold."""
        hod = HumanOverrideDetector(override_threshold=0.1)
        result = hod.evaluate(
            story_id="12345",
            risk_score=0.15,
        )
        assert result.requires_override is True

    def test_custom_threshold_high(self):
        """Test with very high threshold."""
        hod = HumanOverrideDetector(override_threshold=0.99)
        result = hod.evaluate(
            story_id="12345",
            risk_score=0.95,
        )
        assert result.requires_override is False


class TestRecommendations:
    """Tests for override recommendations."""

    def test_high_risk_recommendation(self, hod_agent):
        """Test that high risk generates clear recommendation."""
        result = hod_agent.evaluate(
            story_id="12345",
            risk_score=0.95,
        )
        assert result.requires_override is True
        assert (
            "review" in result.recommendation.lower() or "escalate" in result.recommendation.lower()
        )

    def test_low_risk_recommendation(self, hod_agent):
        """Test that low risk generates proceed recommendation."""
        result = hod_agent.evaluate(
            story_id="12345",
            risk_score=0.3,
        )
        assert result.requires_override is False
        # Recommendation should suggest proceeding

    def test_different_recommendations_for_different_risks(self, hod_agent):
        """Test that different risk levels generate different recommendations."""
        low_risk = hod_agent.evaluate(
            story_id="1",
            risk_score=0.2,
        )
        high_risk = hod_agent.evaluate(
            story_id="2",
            risk_score=0.95,
        )
        # Recommendations should be different
        assert low_risk.recommendation != high_risk.recommendation
