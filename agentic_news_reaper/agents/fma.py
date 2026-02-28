"""Failure Mode Analyzer (FMA) agent.

Analyzes execution patterns and predicts failure modes by computing risk scores
based on engagement, spam, and sentiment drift metrics.
"""

from dataclasses import dataclass

from agentic_news_reaper.logging import get_logger
from agentic_news_reaper.monty_runtime import run_monty

logger = get_logger(__name__)


_FMA_MONTY_CODE = """
def analyze(
    comment_count: int,
    spam_score: float,
    sentiment_variance: float,
    engagement_weight: float,
    spam_weight: float,
    sentiment_weight: float,
    low_engagement_threshold: float,
    high_spam_threshold: float,
) -> dict:
    if comment_count >= low_engagement_threshold:
        engagement_risk = 0.0
    else:
        engagement_risk = 1.0 - (comment_count / low_engagement_threshold)
        if engagement_risk < 0.0:
            engagement_risk = 0.0

    spam_risk = spam_score
    if spam_risk > 1.0:
        spam_risk = 1.0
    if spam_risk < 0.0:
        spam_risk = 0.0

    sentiment_drift = sentiment_variance
    if sentiment_drift > 1.0:
        sentiment_drift = 1.0
    if sentiment_drift < 0.0:
        sentiment_drift = 0.0

    risk_score = (
        engagement_risk * engagement_weight
        + spam_risk * spam_weight
        + sentiment_drift * sentiment_weight
    )
    if risk_score > 1.0:
        risk_score = 1.0
    if risk_score < 0.0:
        risk_score = 0.0

    mitigations = []
    if engagement_risk > 0.7:
        mitigations.append("add_to_watchlist")
    if spam_risk > high_spam_threshold:
        mitigations.append("flag_for_review")
    if sentiment_drift > 0.8:
        mitigations.append("auto_defer")

    if mitigations:
        mitigation = ";".join(mitigations)
    else:
        mitigation = "proceed_normally"

    reasons = []
    if engagement_risk > 0.7:
        reasons.append(f"low engagement ({comment_count} comments)")
    if spam_risk > 0.6:
        reasons.append(f"spam risk ({spam_risk:.2f})")
    if sentiment_drift > 0.7:
        reasons.append(f"high sentiment variance ({sentiment_drift:.2f})")

    if reasons:
        reason = "; ".join(reasons)
    else:
        reason = "Low overall risk"

    return {
        "risk_score": risk_score,
        "engagement_risk": engagement_risk,
        "spam_risk": spam_risk,
        "sentiment_drift": sentiment_drift,
        "mitigation": mitigation,
        "reason": reason,
    }

result = analyze(
    comment_count,
    spam_score,
    sentiment_variance,
    engagement_weight,
    spam_weight,
    sentiment_weight,
    low_engagement_threshold,
    high_spam_threshold,
)
result
"""


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
        result = run_monty(
            _FMA_MONTY_CODE,
            inputs={
                "comment_count": comment_count,
                "spam_score": spam_score,
                "sentiment_variance": sentiment_variance,
                "engagement_weight": self.engagement_weight,
                "spam_weight": self.spam_weight,
                "sentiment_weight": self.sentiment_weight,
                "low_engagement_threshold": float(self.LOW_ENGAGEMENT_THRESHOLD),
                "high_spam_threshold": self.HIGH_SPAM_THRESHOLD,
            },
        )

        engagement_risk = result["engagement_risk"]
        spam_risk = result["spam_risk"]
        sentiment_drift = result["sentiment_drift"]
        risk_score = result["risk_score"]
        mitigation = result["mitigation"]
        reason = result["reason"]

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
            risk_score=risk_score,
            engagement_risk=engagement_risk,
            spam_risk=spam_risk,
            sentiment_drift=sentiment_drift,
            mitigation=mitigation,
            reason=reason,
        )
