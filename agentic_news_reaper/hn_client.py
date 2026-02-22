"""Hacker News API client for fetching stories and metadata.

This module provides an async HTTP client for interacting with the official
Hacker News Firebase API (https://hacker-news.firebaseio.com/v0).

Rate Limiting:
- The HN API is free but has no official rate limits.
- We implement conservative rate limiting (1 req/sec) to be respectful.
- Caching is implemented to reduce redundant API calls.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any

import httpx

from agentic_news_reaper.logging import get_logger

logger = get_logger(__name__)


class HackerNewsClient:
    """Async HTTP client for Hacker News API."""

    BASE_URL = "https://hacker-news.firebaseio.com/v0"
    DEFAULT_TIMEOUT = 30
    RATE_LIMIT_DELAY = 1.0  # seconds between requests

    def __init__(self, base_url: str = BASE_URL, timeout: int = DEFAULT_TIMEOUT):
        """Initialize HN API client.

        Args:
            base_url: Base URL for HN API (default: official Firebase API)
            timeout: HTTP request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self._last_request_time: datetime | None = None
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._cache_ttl = timedelta(hours=1)
        logger.info("HackerNewsClient initialized", base_url=base_url, timeout=timeout)

    async def get_top_stories(self, count: int = 100) -> list[int]:
        """Fetch top story IDs from HN.

        Args:
            count: Number of stories to return (HN returns top 500, we limit to 500)

        Returns:
            List of story IDs (integers)

        Raises:
            httpx.HTTPError: If API request fails
        """
        count = min(count, 500)
        url = f"{self.base_url}/topstories.json"

        try:
            logger.info("Fetching top stories", count=count)
            stories = await self._fetch(url)
            if stories is None:
                return []
            limited_stories = stories[:count]
            logger.info("Top stories fetched", count=len(limited_stories))
            return limited_stories
        except httpx.HTTPError as e:
            logger.error("Failed to fetch top stories", error=str(e))
            raise

    async def get_story(self, story_id: int) -> dict[str, Any] | None:
        """Fetch a single story by ID.

        Args:
            story_id: HN story ID

        Returns:
            Story data dict or None if not found

        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"{self.base_url}/item/{story_id}.json"

        try:
            story = await self._fetch(url)
            if story:
                logger.debug("Story fetched", story_id=story_id, title=story.get("title", ""))
            return story
        except httpx.HTTPError as e:
            logger.error("Failed to fetch story", story_id=story_id, error=str(e))
            raise

    async def get_stories_batch(self, story_ids: list[int]) -> list[dict[str, Any] | None]:
        """Fetch multiple stories concurrently with rate limiting.

        Args:
            story_ids: List of story IDs to fetch

        Returns:
            List of story data dicts (None for failed requests)
        """
        logger.info("Fetching stories batch", count=len(story_ids))

        tasks = [self.get_story(sid) for sid in story_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to None
        processed_results: list[dict[str, Any] | None] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(
                    "Failed to fetch story in batch",
                    story_id=story_ids[i],
                    error=str(result),
                )
                processed_results.append(None)
            else:
                # result is now known to be dict[str, Any] | None
                processed_results.append(result)  # type: ignore[arg-type]

        successful = sum(1 for r in processed_results if r is not None)
        logger.info(
            "Batch fetch complete", successful=successful, failed=len(story_ids) - successful
        )
        return processed_results

    async def get_user(self, username: str) -> dict[str, Any] | None:
        """Fetch user profile data.

        Args:
            username: HN username

        Returns:
            User data dict or None if not found
        """
        url = f"{self.base_url}/user/{username}.json"

        try:
            user = await self._fetch(url)
            if user:
                logger.debug("User profile fetched", username=username)
            return user
        except httpx.HTTPError as e:
            logger.error("Failed to fetch user", username=username, error=str(e))
            raise

    async def get_comments(self, story_id: int, max_depth: int = 3) -> list[dict[str, Any]]:
        """Fetch comments for a story recursively.

        Args:
            story_id: HN story ID
            max_depth: Maximum comment nesting depth to fetch

        Returns:
            List of comment dicts with nested structure
        """
        logger.info("Fetching comments for story", story_id=story_id, max_depth=max_depth)

        story = await self.get_story(story_id)
        if not story or "kids" not in story:
            return []

        comments = await self._fetch_comments_recursive(story["kids"], max_depth=max_depth)
        logger.info("Comments fetched", story_id=story_id, count=len(comments))
        return comments

    async def _fetch_comments_recursive(
        self, comment_ids: list[int], max_depth: int, current_depth: int = 0
    ) -> list[dict[str, Any]]:
        """Recursively fetch comments with depth limiting.

        Args:
            comment_ids: List of comment IDs to fetch
            max_depth: Maximum depth to recurse
            current_depth: Current recursion depth

        Returns:
            List of comment dicts
        """
        if current_depth >= max_depth or not comment_ids:
            return []

        comments = await self.get_stories_batch(comment_ids)

        results = []
        for comment in comments:
            if comment:
                # Recursively fetch nested comments if within depth limit
                if "kids" in comment and current_depth + 1 < max_depth:
                    nested = await self._fetch_comments_recursive(
                        comment["kids"], max_depth=max_depth, current_depth=current_depth + 1
                    )
                    comment["children"] = nested
                else:
                    comment["children"] = []

                results.append(comment)

        return results

    async def _fetch(self, url: str) -> Any | None:
        """Internal method to fetch from API with rate limiting and caching.

        Args:
            url: Full URL to fetch

        Returns:
            JSON response data or None if not found

        Raises:
            httpx.HTTPError: If request fails
        """
        # Check cache
        if url in self._cache:
            data, timestamp = self._cache[url]
            if datetime.utcnow() - timestamp < self._cache_ttl:
                logger.debug("Cache hit", url=url)
                return data

        # Apply rate limiting
        await self._apply_rate_limit()

        # Make request
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            logger.debug("API request", url=url)
            response = await client.get(url)

            if response.status_code == 404:
                logger.debug("Not found", url=url)
                return None

            response.raise_for_status()
            data = response.json()

            # Cache result
            self._cache[url] = (data, datetime.utcnow())

            return data

    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting to API requests."""
        if self._last_request_time:
            elapsed = (datetime.utcnow() - self._last_request_time).total_seconds()
            if elapsed < self.RATE_LIMIT_DELAY:
                await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)

        self._last_request_time = datetime.utcnow()

    def clear_cache(self) -> None:
        """Clear the response cache."""
        self._cache.clear()
        logger.info("Cache cleared")

    def set_cache_ttl(self, ttl_hours: int) -> None:
        """Set cache TTL.

        Args:
            ttl_hours: Time to live in hours
        """
        self._cache_ttl = timedelta(hours=ttl_hours)
        logger.info("Cache TTL updated", ttl_hours=ttl_hours)
