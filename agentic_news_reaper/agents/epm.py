"""Execution Pattern Miner (EPM) Agent.

The EPM agent extracts repeatable execution patterns from Hacker News threads,
matching stories against known pattern templates and outputting pattern instances
with confidence scores.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from agentic_news_reaper.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PatternInstance:
    """Represents a detected execution pattern."""

    pattern_id: str
    story_id: str
    confidence: float
    pattern_data: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "pattern_id": self.pattern_id,
            "story_id": self.story_id,
            "confidence": self.confidence,
            "pattern_data": self.pattern_data,
            "created_at": self.created_at.isoformat(),
        }


class ExecutionPatternMiner:
    """Mines execution patterns from Hacker News stories.

    Pattern matching is performed against pre-defined templates stored in patterns.yaml.
    Matches are scored based on title/content heuristics and comment engagement metrics.
    """

    def __init__(self, min_confidence: float = 0.5, patterns_file: Path | None = None):
        """Initialize the EPM agent.

        Args:
            min_confidence: Minimum confidence threshold for pattern matches (0.0-1.0).
            patterns_file: Path to patterns.yaml file. If None, uses default location.
        """
        self.min_confidence = min_confidence
        self.patterns: dict[str, dict] = {}

        # Load patterns from file
        if patterns_file is None:
            patterns_file = Path(__file__).parent.parent / "templates" / "patterns.yaml"

        self.patterns_file = patterns_file
        self.load_patterns_from_file()
        logger.info(
            "ExecutionPatternMiner initialized",
            min_confidence=min_confidence,
            patterns_count=len(self.patterns),
        )

    def load_patterns_from_file(self) -> None:
        """Load pattern templates from YAML file.

        Raises:
            FileNotFoundError: If patterns file not found.
            yaml.YAMLError: If YAML parsing fails.
        """
        if not self.patterns_file.exists():
            logger.warning(
                "Patterns file not found, using empty pattern set",
                patterns_file=str(self.patterns_file),
            )
            self.patterns = {}
            return

        try:
            with open(self.patterns_file) as f:
                data = yaml.safe_load(f)

            if not data or "patterns" not in data:
                logger.warning("No patterns found in patterns file")
                self.patterns = {}
                return

            # Convert list of patterns to dict indexed by id
            self.patterns = {p["id"]: p for p in data["patterns"]}
            logger.info("Patterns loaded from file", pattern_count=len(self.patterns))
        except (yaml.YAMLError, KeyError) as e:
            logger.error("Failed to load patterns from file", error=str(e))
            self.patterns = {}
            raise

    def load_patterns(self, patterns: dict) -> None:
        """Load pattern templates programmatically.

        Args:
            patterns: Dictionary of pattern definitions (id -> pattern data).
        """
        self.patterns = patterns
        logger.info("Patterns loaded programmatically", pattern_count=len(patterns))

    def mine(
        self,
        story_id: str,
        title: str,
        url: str,
        metadata: dict[str, Any],
    ) -> list[PatternInstance]:
        """Mine patterns from a Hacker News story.

        Args:
            story_id: Unique HN story ID.
            title: Story title.
            url: Story URL.
            metadata: Additional metadata (comments, score, descendants, etc.).

        Returns:
            List of detected PatternInstance objects sorted by confidence.
        """
        instances: list[PatternInstance] = []

        logger.info(
            "Mining patterns",
            story_id=story_id,
            title=title[:50],
            pattern_count=len(self.patterns),
        )

        # Try to match each pattern
        for pattern_id, pattern_def in self.patterns.items():
            match = self.match_pattern(
                pattern_id=pattern_id,
                title=title,
                url=url,
                metadata=metadata,
                pattern_def=pattern_def,
            )
            if match:
                instances.append(match)

        # Sort by confidence (highest first)
        instances.sort(key=lambda x: x.confidence, reverse=True)

        logger.info(
            "Pattern mining complete",
            story_id=story_id,
            matched_patterns=len(instances),
        )

        return instances

    def match_pattern(
        self,
        pattern_id: str,
        title: str,
        url: str,
        metadata: dict[str, Any],
        pattern_def: dict[str, Any] | None = None,
    ) -> PatternInstance | None:
        """Match a single pattern against story data.

        Args:
            pattern_id: ID of pattern to match.
            title: Story title.
            url: Story URL.
            metadata: Story metadata.
            pattern_def: Pattern definition (optional, uses loaded patterns if not provided).

        Returns:
            PatternInstance if matched with confidence >= threshold, else None.
        """
        if pattern_def is None:
            if pattern_id not in self.patterns:
                logger.debug("Pattern not found", pattern_id=pattern_id)
                return None
            pattern_def = self.patterns[pattern_id]

        try:
            # Calculate confidence from multiple signals
            confidence = self._calculate_confidence(
                pattern_id=pattern_id,
                pattern_def=pattern_def,
                title=title,
                url=url,
                metadata=metadata,
            )

            if confidence >= self.min_confidence:
                instance = PatternInstance(
                    pattern_id=pattern_id,
                    story_id=metadata.get("story_id", "unknown"),
                    confidence=confidence,
                    pattern_data={
                        "title": title,
                        "url": url,
                        "pattern_description": pattern_def.get("description"),
                        "risk_level": pattern_def.get("risk_level"),
                    },
                )
                logger.debug(
                    "Pattern matched",
                    pattern_id=pattern_id,
                    story_id=metadata.get("story_id"),
                    confidence=confidence,
                )
                return instance

            return None
        except Exception as e:
            logger.error("Error matching pattern", pattern_id=pattern_id, error=str(e))
            return None

    def _calculate_confidence(
        self,
        pattern_id: str,
        pattern_def: dict[str, Any],
        title: str,
        url: str,
        metadata: dict[str, Any],
    ) -> float:
        """Calculate confidence score for a pattern match.

        Args:
            pattern_id: Pattern ID.
            pattern_def: Pattern definition.
            title: Story title.
            url: Story URL.
            metadata: Story metadata.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        trigger_conditions = pattern_def.get("trigger_conditions", {})
        confidence_weights = pattern_def.get("confidence_weights", {})

        # Calculate individual signals
        signals = {}

        # Title matching
        title_keywords = trigger_conditions.get("title_contains", [])
        if title_keywords:
            signals["title_match"] = self._match_keywords(title, title_keywords)
        else:
            signals["title_match"] = 0.0

        # URL matching
        url_keywords = trigger_conditions.get("url_contains", [])
        if url_keywords:
            signals["url_match"] = self._match_keywords(url, url_keywords)
        else:
            signals["url_match"] = 0.0

        url_domains = trigger_conditions.get("url_domain_patterns", [])
        if url_domains:
            signals["url_domain_match"] = self._match_keywords(url, url_domains)
        else:
            signals["url_domain_match"] = 0.0

        # Engagement signals
        comment_count = metadata.get("descendants", 0)
        min_comments = trigger_conditions.get("min_comments", 0)
        signals["engagement"] = 1.0 if comment_count >= min_comments else 0.0

        # Comment upvote ratio
        target_ratio = trigger_conditions.get("comment_upvote_ratio")
        if target_ratio is not None:
            actual_ratio = metadata.get("comment_upvote_ratio", 0.0)
            signals["upvote_ratio"] = 1.0 if actual_ratio >= target_ratio else 0.0
        else:
            signals["upvote_ratio"] = 0.0

        # Minimum score threshold
        min_score = trigger_conditions.get("min_score", 0)
        story_score = metadata.get("score", 0)
        signals["score"] = 1.0 if story_score >= min_score else 0.0

        # Sentiment variance
        sentiment_var = trigger_conditions.get("comment_sentiment_variance")
        if sentiment_var is not None:
            actual_var = metadata.get("sentiment_variance", 0.0)
            signals["sentiment"] = min(1.0, actual_var / sentiment_var)
        else:
            signals["sentiment"] = 0.0

        # Spam signal
        signals["spam"] = 1.0 if trigger_conditions.get("url_on_blacklist") else 0.0

        # Calculate weighted confidence
        weights_sum = 0.0
        weighted_sum = 0.0

        for signal_name, signal_value in signals.items():
            weight = confidence_weights.get(signal_name, 0.0)
            weighted_sum += signal_value * weight
            weights_sum += weight

        # Avoid division by zero
        if weights_sum > 0:
            confidence = weighted_sum / weights_sum
        else:
            confidence = 0.0

        return min(1.0, max(0.0, confidence))

    def _match_keywords(self, text: str, keywords: list[str]) -> float:
        """Calculate keyword match score.

        Args:
            text: Text to search in.
            keywords: Keywords to search for.

        Returns:
            Match score (0.0-1.0) based on how many keywords match.
        """
        if not keywords:
            return 0.0

        text_lower = text.lower()
        matches = sum(1 for kw in keywords if kw.lower() in text_lower)
        return min(1.0, matches / len(keywords))
