"""Human Override Detector (HOD) Agent.

Identifies moments where human approval is mandatory based on risk assessment
and business rules.
"""

from dataclasses import dataclass

from agentic_news_reaper.logging import get_logger
from agentic_news_reaper.monty_runtime import run_monty

logger = get_logger(__name__)


_HOD_MONTY_CODE = """
def evaluate(
    story_id: str,
    risk_score: float,
    pattern_type: str | None,
    override_threshold: float,
) -> dict:
    requires_override = risk_score >= override_threshold

    reason = ""
    recommendation = None

    if requires_override:
        if pattern_type == "financial":
            reason = "Potential market-impact investment decision"
            recommendation = "Review with CFO before proceeding"
        elif pattern_type == "security":
            reason = "Security or privacy-related pattern detected"
            recommendation = "Security review required"
        else:
            reason = (
                f"Risk score {risk_score:.2f} exceeds override threshold {override_threshold}"
            )
            recommendation = "Manual review recommended"
    else:
        reason = f"Risk score {risk_score:.2f} within acceptable threshold"

    return {
        "story_id": story_id,
        "requires_override": requires_override,
        "risk_score": risk_score,
        "reason": reason,
        "recommendation": recommendation,
    }

result = evaluate(story_id, risk_score, pattern_type, override_threshold)
result
"""


@dataclass
class OverrideDecision:
    """Decision output from HOD agent."""

    story_id: str
    requires_override: bool
    risk_score: float
    reason: str
    recommendation: str | None = None


class HumanOverrideDetector:
    """Detects patterns requiring human approval."""

    def __init__(self, override_threshold: float = 0.9) -> None:
        """
        Initialize HOD agent.

        Args:
            override_threshold: Risk score threshold triggering human override (0.0-1.0).
        """
        self.override_threshold = override_threshold
        logger.info(
            "HumanOverrideDetector initialized",
            threshold=override_threshold,
        )

    def evaluate(
        self,
        story_id: str,
        risk_score: float,
        pattern_type: str | None = None,
        business_context: dict | None = None,
    ) -> OverrideDecision:
        """
        Evaluate if a pattern requires human override.

        Args:
            story_id: HN story identifier.
            risk_score: Aggregated risk score (0.0-1.0).
            pattern_type: Type of pattern detected (e.g., 'financial', 'security').
            business_context: Additional business rules context.

        Returns:
            OverrideDecision with approval recommendation.
        """
        _ = business_context

        result = run_monty(
            _HOD_MONTY_CODE,
            inputs={
                "story_id": story_id,
                "risk_score": risk_score,
                "pattern_type": pattern_type,
                "override_threshold": self.override_threshold,
            },
        )

        if result["requires_override"]:
            logger.warning(
                "Override required",
                story_id=story_id,
                risk_score=risk_score,
                reason=result["reason"],
            )

        return OverrideDecision(
            story_id=result["story_id"],
            requires_override=result["requires_override"],
            risk_score=result["risk_score"],
            reason=result["reason"],
            recommendation=result["recommendation"],
        )

    def batch_evaluate(
        self,
        evaluations: list[dict],
    ) -> list[OverrideDecision]:
        """
        Evaluate multiple patterns for override requirements.

        Args:
            evaluations: List of dicts with keys: story_id, risk_score, pattern_type, business_context.

        Returns:
            List of OverrideDecision objects.
        """
        results = []
        for item in evaluations:
            decision = self.evaluate(
                story_id=item["story_id"],
                risk_score=item["risk_score"],
                pattern_type=item.get("pattern_type"),
                business_context=item.get("business_context"),
            )
            results.append(decision)
        return results
