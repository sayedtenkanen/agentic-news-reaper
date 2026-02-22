"""Non-Determinism Detector (NDD) Agent.

Detects and flags posts with multiple possible interpretations,
ambiguous titles, or mixed sentiment that could lead to non-deterministic behavior.
"""

from dataclasses import dataclass

from agentic_news_reaper.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AmbiguityFlag:
    """Represents an ambiguity flag for a story."""

    story_id: str
    title: str
    ambiguity_score: float
    reason: str


class NonDeterminismDetector:
    """Detects non-determinism in Hacker News posts."""

    def __init__(self, ambiguity_threshold: float = 0.78):
        """Initialize the NDD agent.

        Args:
            ambiguity_threshold: Threshold for flagging ambiguous content (0.0-1.0).
        """
        self.ambiguity_threshold = ambiguity_threshold
        logger.info("NDD initialized", threshold=ambiguity_threshold)

    def analyze(self, story_id: str, title: str, comments_count: int = 0) -> AmbiguityFlag | None:
        """Analyze a story for non-determinism.

        Args:
            story_id: Unique HN story ID.
            title: Story title.
            comments_count: Number of comments on the story.

        Returns:
            AmbiguityFlag if ambiguity detected, else None.
        """
        ambiguity_score = self._compute_ambiguity_score(title, comments_count)

        if ambiguity_score >= self.ambiguity_threshold:
            reason = self._generate_reason(title, ambiguity_score)
            flag = AmbiguityFlag(
                story_id=story_id,
                title=title,
                ambiguity_score=ambiguity_score,
                reason=reason,
            )
            logger.info(
                "ambiguity_detected",
                story_id=story_id,
                score=ambiguity_score,
                reason=reason,
            )
            return flag

        return None

    def _compute_ambiguity_score(self, title: str, comments_count: int) -> float:
        """Compute ambiguity score for a title.

        Args:
            title: Story title.
            comments_count: Number of comments.

        Returns:
            Ambiguity score between 0.0 and 1.0.
        """
        # Simple heuristics for demo
        score = 0.0

        # Check for clickbait indicators
        clickbait_words = ["shocking", "you won't believe", "this one", "unbelievable"]
        title_lower = title.lower()
        for word in clickbait_words:
            if word in title_lower:
                score += 0.3

        # Check for question marks (often ambiguous)
        if "?" in title:
            score += 0.2

        # Check for multiple interpretations (all caps or mixed case)
        if title.isupper():
            score += 0.15
        elif sum(1 for c in title if c.isupper()) > len(title) * 0.4:
            score += 0.1

        # High comment ratio might indicate controversy
        if comments_count > 100:
            score += 0.1

        return min(score, 1.0)

    def _generate_reason(self, title: str, score: float) -> str:
        """Generate a human-readable reason for the ambiguity flag.

        Args:
            title: Story title.
            score: Ambiguity score.

        Returns:
            Explanation string.
        """
        if "?" in title:
            return "Title contains question mark (potential ambiguity)"
        if title.isupper():
            return "Title in all caps (possible sensationalism)"
        if any(word in title.lower() for word in ["shocking", "you won't believe"]):
            return "Title contains clickbait indicators"
        return f"High ambiguity score ({score:.2f})"
