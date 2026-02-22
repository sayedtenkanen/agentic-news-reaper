"""Failure Mode Analyzer (FMA) agent.

Analyzes execution patterns and predicts failure modes by computing risk scores
based on engagement, spam, and sentiment drift metrics.
"""

from dataclasses import dataclass

from agentic_news_reaper.logging import get_logger

logger = get_logger(__name__)


@dataclass
class FailureMode:
    """Represents a predicted failure mode."""

    pattern_instance_id: int
    risk_score: float
    engagement_risk: float
    spam_risk: float
    sentiment_drift: float
    mitigation: str
    reason: str


class FailureModeAnalyzer:
    """Analyzes failure modes for execution patterns.

    Risk Model:
    - Engagement Risk = (low comment count) * weight₁
    - Spam Risk = (high URL blacklist score) * weight₂
    - Sentiment Drift = (sentiment polarity variance) * weight₃
    """

    # Risk weights (configurable)
    ENGAGEMENT_WEIGHT = 0.4
    SPAM_WEIGHT = 0.35
    SENTIMENT_WEIGHT = 0.25

    # Risk thresholds
    LOW_ENGAGEMENT_THRESHOLD = 5  # Minimum comments
    HIGH_SPAM_THRESHOLD = 0.7

    def __init__(self, config: dict | None = None) -> None:
        """Initialize FMA agent.

        Args:
            config: Optional configuration dictionary for thresholds and weights.
        """
        self.config = config or {}
        self.engagement_weight = self.config.get("engagement_weight", self.ENGAGEMENT_WEIGHT)
        self.spam_weight = self.config.get("spam_weight", self.SPAM_WEIGHT)
        self.sentiment_weight = self.config.get("sentiment_weight", self.SENTIMENT_WEIGHT)

    def analyze_pattern(
        self,
        pattern_instance_id: int,
        comment_count: int,
        spam_score: float,
        sentiment_variance: float,
    ) -> FailureMode:
        """Analyze failure modes for a pattern instance.

        Args:
            pattern_instance_id: ID of the pattern instance to analyze.
            comment_count: Number of comments on the story.
            spam_score: Spam risk score (0.0-1.0).
            sentiment_variance: Sentiment polarity variance (0.0-1.0).

        Returns:
            FailureMode object with risk scores and mitigation.
        """
        # Calculate individual risk components
        engagement_risk = self._calculate_engagement_risk(comment_count)
        spam_risk = min(1.0, spam_score)
        sentiment_drift = min(1.0, sentiment_variance)

        # Calculate weighted composite risk score
        risk_score = (
            engagement_risk * self.engagement_weight
            + spam_risk * self.spam_weight
            + sentiment_drift * self.sentiment_weight
        )

        # Determine mitigation strategy
        mitigation = self._recommend_mitigation(engagement_risk, spam_risk, sentiment_drift)

        # Build reason string
        reason = self._build_reason(engagement_risk, spam_risk, sentiment_drift, comment_count)

        logger.info(
            "pattern_analyzed",
            pattern_instance_id=pattern_instance_id,
            risk_score=risk_score,
            engagement_risk=engagement_risk,
            spam_risk=spam_risk,
            sentiment_drift=sentiment_drift,
        )

        return FailureMode(
            pattern_instance_id=pattern_instance_id,
            risk_score=min(1.0, risk_score),
            engagement_risk=engagement_risk,
            spam_risk=spam_risk,
            sentiment_drift=sentiment_drift,
            mitigation=mitigation,
            reason=reason,
        )

    def _calculate_engagement_risk(self, comment_count: int) -> float:
        """Calculate engagement risk based on comment count.

        Args:
            comment_count: Number of comments.

        Returns:
            Engagement risk score (0.0-1.0).
        """
        if comment_count >= self.LOW_ENGAGEMENT_THRESHOLD:
            return 0.0
        # Linear interpolation: 0 comments = 1.0 risk, threshold = 0.0 risk
        return max(0.0, 1.0 - (comment_count / self.LOW_ENGAGEMENT_THRESHOLD))

    def _recommend_mitigation(
        self, engagement_risk: float, spam_risk: float, sentiment_drift: float
    ) -> str:
        """Recommend mitigation strategy based on risks.

        Args:
            engagement_risk: Engagement risk score.
            spam_risk: Spam risk score.
            sentiment_drift: Sentiment drift score.

        Returns:
            Mitigation recommendation string.
        """
        mitigations = []

        if engagement_risk > 0.7:
            mitigations.append("add_to_watchlist")
        if spam_risk > self.HIGH_SPAM_THRESHOLD:
            mitigations.append("flag_for_review")
        if sentiment_drift > 0.8:
            mitigations.append("auto_defer")

        if not mitigations:
            return "proceed_normally"

        return ";".join(mitigations)

    def _build_reason(
        self,
        engagement_risk: float,
        spam_risk: float,
        sentiment_drift: float,
        comment_count: int,
    ) -> str:
        """Build a human-readable reason for the risk assessment.

        Args:
            engagement_risk: Engagement risk score.
            spam_risk: Spam risk score.
            sentiment_drift: Sentiment drift score.
            comment_count: Number of comments.

        Returns:
            Human-readable reason string.
        """
        reasons = []

        if engagement_risk > 0.7:
            reasons.append(f"low engagement ({comment_count} comments)")
        if spam_risk > 0.6:
            reasons.append(f"spam risk ({spam_risk:.2f})")
        if sentiment_drift > 0.7:
            reasons.append(f"high sentiment variance ({sentiment_drift:.2f})")

        if not reasons:
            return "Low overall risk"

        return "; ".join(reasons)
