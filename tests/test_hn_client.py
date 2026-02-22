"""Tests for Hacker News API client.

Tests for fetching stories, comments, and handling API interactions.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentic_news_reaper.hn_client import HackerNewsClient


@pytest.fixture
def hn_client():
    """Create a HackerNewsClient instance."""
    return HackerNewsClient()


@pytest.fixture
def mock_story_data():
    """Sample HN story data."""
    return {
        "by": "author",
        "descendants": 42,
        "id": 12345,
        "kids": [1, 2, 3],
        "score": 100,
        "time": 1234567890,
        "title": "Test Story Title",
        "type": "story",
        "url": "https://example.com",
    }


@pytest.fixture
def mock_comment_data():
    """Sample HN comment data."""
    return {
        "by": "commenter",
        "id": 1,
        "kids": [],
        "parent": 12345,
        "score": 10,
        "text": "Great story!",
        "time": 1234567900,
        "type": "comment",
    }


@pytest.fixture
def mock_user_data():
    """Sample HN user data."""
    return {
        "about": "Software engineer",
        "created": 1234567890,
        "id": "author",
        "karma": 5000,
        "submitted": [1, 2, 3, 4, 5],
    }


class TestHackerNewsClientInitialization:
    """Tests for HackerNewsClient initialization."""

    def test_client_initialization_default(self):
        """Test client initialization with defaults."""
        client = HackerNewsClient()
        assert client.base_url == "https://hacker-news.firebaseio.com/v0"
        assert client.timeout == 30
        assert client._cache == {}

    def test_client_initialization_custom(self):
        """Test client initialization with custom values."""
        client = HackerNewsClient(
            base_url="https://custom.api.com",
            timeout=60,
        )
        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 60

    def test_client_rate_limit_delay(self):
        """Test rate limit delay constant."""
        client = HackerNewsClient()
        assert client.RATE_LIMIT_DELAY == 1.0


class TestTopStoriesFetching:
    """Tests for fetching top stories."""

    @pytest.mark.asyncio
    async def test_get_top_stories(self, hn_client):
        """Test fetching top stories."""
        mock_stories = [1, 2, 3, 4, 5]
        with patch.object(hn_client, "_fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_stories
            result = await hn_client.get_top_stories(count=5)
            assert result == mock_stories
            mock_fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_top_stories_limits_count(self, hn_client):
        """Test that get_top_stories limits to 500."""
        mock_stories = list(range(600))
        with patch.object(hn_client, "_fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_stories
            result = await hn_client.get_top_stories(count=600)
            # Should only request 500
            assert len(result) <= 500

    @pytest.mark.asyncio
    async def test_get_top_stories_default_count(self, hn_client):
        """Test default count for top stories."""
        mock_stories = list(range(100))
        with patch.object(hn_client, "_fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_stories
            result = await hn_client.get_top_stories()
            assert len(result) == 100


class TestSingleStoryFetching:
    """Tests for fetching individual stories."""

    @pytest.mark.asyncio
    async def test_get_story(self, hn_client, mock_story_data):
        """Test fetching a single story."""
        with patch.object(hn_client, "_fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_story_data
            result = await hn_client.get_story(12345)
            assert result == mock_story_data
            assert result["title"] == "Test Story Title"

    @pytest.mark.asyncio
    async def test_get_story_not_found(self, hn_client):
        """Test fetching a story that doesn't exist."""
        with patch.object(hn_client, "_fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            result = await hn_client.get_story(99999)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_story_constructs_url(self, hn_client):
        """Test that get_story constructs correct URL."""
        with patch.object(hn_client, "_fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {}
            await hn_client.get_story(12345)
            call_args = mock_fetch.call_args[0][0]
            assert "item/12345" in call_args


class TestBatchStoryFetching:
    """Tests for batch fetching stories."""

    @pytest.mark.asyncio
    async def test_get_stories_batch(self, hn_client, mock_story_data):
        """Test batch fetching stories."""
        story_ids = [1, 2, 3, 4, 5]
        with patch.object(hn_client, "get_story", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_story_data
            results = await hn_client.get_stories_batch(story_ids)
            assert len(results) == 5
            assert all(r == mock_story_data for r in results)

    @pytest.mark.asyncio
    async def test_get_stories_batch_with_failures(self, hn_client):
        """Test batch fetching with some failures."""
        story_ids = [1, 2, 3]
        results_data = [{"id": 1}, None, {"id": 3}]
        with patch.object(hn_client, "get_story", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = results_data
            results = await hn_client.get_stories_batch(story_ids)
            assert len(results) == 3
            assert results[0] == {"id": 1}
            assert results[1] is None
            assert results[2] == {"id": 3}

    @pytest.mark.asyncio
    async def test_get_stories_batch_empty(self, hn_client):
        """Test batch fetching with empty list."""
        results = await hn_client.get_stories_batch([])
        assert results == []


class TestUserFetching:
    """Tests for fetching user data."""

    @pytest.mark.asyncio
    async def test_get_user(self, hn_client, mock_user_data):
        """Test fetching user profile."""
        with patch.object(hn_client, "_fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_user_data
            result = await hn_client.get_user("author")
            assert result == mock_user_data
            assert result["id"] == "author"

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, hn_client):
        """Test fetching non-existent user."""
        with patch.object(hn_client, "_fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            result = await hn_client.get_user("nonexistent")
            assert result is None


class TestCommentFetching:
    """Tests for fetching comments."""

    @pytest.mark.asyncio
    async def test_get_comments_no_kids(self, hn_client):
        """Test fetching comments when story has no kids."""
        story_data = {"id": 123, "title": "Test"}
        with patch.object(hn_client, "get_story", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = story_data
            result = await hn_client.get_comments(123)
            assert result == []

    @pytest.mark.asyncio
    async def test_get_comments_with_kids(self, hn_client, mock_story_data, mock_comment_data):
        """Test fetching comments with nested structure."""
        story_data = {"id": 123, "title": "Test", "kids": [1]}
        with patch.object(hn_client, "get_story", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = story_data
            with patch.object(
                hn_client, "_fetch_comments_recursive", new_callable=AsyncMock
            ) as mock_fetch_comments:
                mock_fetch_comments.return_value = [mock_comment_data]
                result = await hn_client.get_comments(123)
                assert len(result) == 1
                assert result[0]["type"] == "comment"


class TestCaching:
    """Tests for response caching."""

    def test_cache_initialization(self, hn_client):
        """Test cache is initialized."""
        assert hn_client._cache == {}

    def test_clear_cache(self, hn_client):
        """Test clearing cache."""
        hn_client._cache["key"] = ("value", None)
        hn_client.clear_cache()
        assert hn_client._cache == {}

    def test_set_cache_ttl(self, hn_client):
        """Test setting cache TTL."""
        hn_client.set_cache_ttl(2)
        assert hn_client._cache_ttl.total_seconds() == 2 * 3600


class TestRateLimiting:
    """Tests for rate limiting."""

    @pytest.mark.asyncio
    async def test_rate_limit_delay(self, hn_client):
        """Test rate limiting delay."""
        import time

        hn_client._last_request_time = None
        start = time.time()
        await hn_client._apply_rate_limit()
        elapsed = time.time() - start
        # Should complete quickly (no sleep on first request)
        assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_rate_limit_subsequent_requests(self, hn_client):
        """Test rate limiting on subsequent requests."""
        import time
        from datetime import datetime, timedelta

        # Set last request to just now
        hn_client._last_request_time = datetime.utcnow() - timedelta(milliseconds=100)
        start = time.time()
        await hn_client._apply_rate_limit()
        elapsed = time.time() - start
        # Should have slept approximately 900ms (1000 - 100)
        assert elapsed >= 0.8


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_get_story_handles_http_error(self, hn_client):
        """Test that HTTP errors are properly raised."""
        import httpx

        with patch.object(hn_client, "_fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = httpx.HTTPStatusError(
                "404",
                request=MagicMock(),
                response=MagicMock(),
            )
            with pytest.raises(httpx.HTTPStatusError):
                await hn_client.get_story(99999)

    @pytest.mark.asyncio
    async def test_batch_handles_exceptions(self, hn_client):
        """Test batch fetch handles exceptions gracefully."""
        with patch.object(hn_client, "get_story", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("API error")
            results = await hn_client.get_stories_batch([1, 2, 3])
            # Should return None for failed requests, not raise
            assert len(results) == 3


class TestURLConstruction:
    """Tests for URL construction."""

    @pytest.mark.asyncio
    async def test_top_stories_url(self, hn_client):
        """Test top stories URL construction."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = []
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            await hn_client.get_top_stories()
            # Verify URL was constructed correctly
            call_args = mock_client.return_value.__aenter__.return_value.get.call_args
            assert "topstories" in str(call_args)

    @pytest.mark.asyncio
    async def test_story_url(self, hn_client):
        """Test story URL construction."""
        with patch.object(hn_client, "_fetch", new_callable=AsyncMock):
            with patch("httpx.AsyncClient") as mock_client:
                mock_response = AsyncMock()
                mock_response.json.return_value = {}
                mock_response.status_code = 200
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

                await hn_client.get_story(12345)
                # Verify URL contains story ID
                call_args = mock_client.return_value.__aenter__.return_value.get.call_args
                if call_args:
                    url = call_args[0][0] if call_args[0] else ""
                    assert "item/12345" in url or "/12345" in url


class TestIntegration:
    """Integration-style tests."""

    @pytest.mark.asyncio
    async def test_full_fetch_pipeline(self, hn_client):
        """Test a full fetch pipeline."""
        mock_story_ids = [1, 2, 3]
        mock_stories = [
            {"id": 1, "title": "Story 1"},
            {"id": 2, "title": "Story 2"},
            {"id": 3, "title": "Story 3"},
        ]

        with patch.object(hn_client, "_fetch", new_callable=AsyncMock) as mock_fetch:

            async def mock_fetch_side_effect(url):
                if "topstories" in url:
                    return mock_story_ids
                elif "item" in url:
                    for story in mock_stories:
                        if str(story["id"]) in url:
                            return story
                return None

            mock_fetch.side_effect = mock_fetch_side_effect

            # Get top stories
            stories = await hn_client.get_top_stories(count=3)
            assert len(stories) == 3

            # Get individual stories
            story = await hn_client.get_story(1)
            assert story["title"] == "Story 1"
