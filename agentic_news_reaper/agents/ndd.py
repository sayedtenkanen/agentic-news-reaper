"""Non-Determinism Detector (NDD) Agent.

Detects and flags posts with multiple possible interpretations,
ambiguous titles, or mixed sentiment that could lead to non-deterministic behavior.
"""

from dataclasses import dataclass

from agentic_news_reaper.logging import get_logger
from agentic_news_reaper.monty_runtime import run_monty

logger = get_logger(__name__)


_NDD_MONTY_CODE = """
def analyze(title: str, comments_count: int, ambiguity_threshold: float) -> dict | None:
    score = 0.0
    clickbait_words = ["shocking", "you won't believe", "this one", "unbelievable"]
    title_lower = title.lower()
    for word in clickbait_words:
        if word in title_lower:
            score += 0.3

    if "?" in title:
        score += 0.2

    if title.isupper():
        score += 0.15
    else:
        upper_count = 0
        for c in title:
            if c.isupper():
                upper_count += 1
        if len(title) > 0 and upper_count > len(title) * 0.4:
            score += 0.1

    if comments_count > 100:
        score += 0.1

    if score > 1.0:
        score = 1.0

    if score >= ambiguity_threshold:
        if "?" in title:
            reason = "Title contains question mark (potential ambiguity)"
        elif title.isupper():
            reason = "Title in all caps (possible sensationalism)"
        else:
            found_clickbait = False
            for word in ["shocking", "you won't believe"]:
                if word in title_lower:
                    found_clickbait = True
            if found_clickbait:
                reason = "Title contains clickbait indicators"
            else:
                reason = f"High ambiguity score ({score:.2f})"
        return {"ambiguity_score": score, "reason": reason}

    return None

result = analyze(title, comments_count, ambiguity_threshold)
result
"""


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
        result = run_monty(
            _NDD_MONTY_CODE,
            inputs={
                "title": title,
                "comments_count": comments_count,
                "ambiguity_threshold": self.ambiguity_threshold,
            },
        )

        if result is None:
            return None

        ambiguity_score = result["ambiguity_score"]
        reason = result["reason"]

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
