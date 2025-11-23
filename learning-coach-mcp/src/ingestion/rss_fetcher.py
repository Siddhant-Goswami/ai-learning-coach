"""
RSS Feed Fetcher

Fetches articles from RSS feeds and returns structured content.
"""

import logging
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class RSSFetcher:
    """Fetcher for RSS feeds."""

    def __init__(self, user_agent: str = "AI Learning Coach/1.0"):
        """
        Initialize RSS fetcher.

        Args:
            user_agent: User agent string for HTTP requests
        """
        self.user_agent = user_agent

    async def fetch_feed(
        self,
        feed_url: str,
        since: Optional[datetime] = None,
        max_articles: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Fetch articles from an RSS feed.

        Args:
            feed_url: URL of the RSS feed
            since: Only fetch articles published after this timestamp (optional)
            max_articles: Maximum number of articles to return (default: 50)

        Returns:
            List of article dictionaries

        Raises:
            Exception: If feed cannot be fetched or parsed
        """
        logger.info(f"Fetching RSS feed: {feed_url}")

        try:
            # Fetch feed with custom user agent
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    feed_url,
                    headers={"User-Agent": self.user_agent},
                    timeout=30.0,
                    follow_redirects=True,
                )
                response.raise_for_status()
                feed_content = response.text

            # Parse feed
            feed = feedparser.parse(feed_content)

            if feed.bozo:  # feedparser detected malformed feed
                logger.warning(f"Feed may be malformed: {feed_url}")

            # Extract articles
            articles = []
            for entry in feed.entries[:max_articles]:
                article = self._parse_entry(entry)

                # Filter by date if specified
                if since and article.get("published_at"):
                    if article["published_at"] <= since:
                        continue

                articles.append(article)

            logger.info(f"Fetched {len(articles)} articles from {feed_url}")
            return articles

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching feed {feed_url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching feed {feed_url}: {e}", exc_info=True)
            raise

    def _parse_entry(self, entry: Any) -> Dict[str, Any]:
        """
        Parse a feed entry into article dictionary.

        Args:
            entry: feedparser entry object

        Returns:
            Article dictionary
        """
        # Extract published date
        published_at = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published_at = datetime(*entry.published_parsed[:6])
            except (ValueError, TypeError):
                logger.warning("Could not parse published date")

        # If no published date, try updated date
        if not published_at and hasattr(entry, "updated_parsed") and entry.updated_parsed:
            try:
                published_at = datetime(*entry.updated_parsed[:6])
            except (ValueError, TypeError):
                pass

        # Default to now if still no date
        if not published_at:
            published_at = datetime.now()

        # Extract content (prefer content over summary)
        content = ""
        if hasattr(entry, "content") and entry.content:
            content = entry.content[0].value
        elif hasattr(entry, "summary"):
            content = entry.summary
        elif hasattr(entry, "description"):
            content = entry.description

        # Clean HTML from content
        clean_content = self._clean_html(content)

        return {
            "title": entry.get("title", "Untitled"),
            "url": entry.get("link", ""),
            "content": clean_content,
            "raw_html": content,
            "published_at": published_at,
            "author": entry.get("author", "Unknown"),
            "tags": [tag.term for tag in entry.get("tags", [])],
        }

    def _clean_html(self, html_content: str) -> str:
        """
        Remove HTML tags and extract clean text.

        Args:
            html_content: HTML string

        Returns:
            Clean text without HTML tags
        """
        if not html_content:
            return ""

        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator=" ", strip=True)

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            logger.warning(f"Error cleaning HTML: {e}")
            return html_content

    async def validate_feed(self, feed_url: str) -> bool:
        """
        Validate that a feed URL is accessible and parseable.

        Args:
            feed_url: URL to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            articles = await self.fetch_feed(feed_url, max_articles=1)
            return len(articles) > 0
        except Exception as e:
            logger.error(f"Feed validation failed for {feed_url}: {e}")
            return False


async def fetch_multiple_feeds(
    feed_urls: List[str],
    since: Optional[datetime] = None,
    max_articles_per_feed: int = 50,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetch articles from multiple RSS feeds concurrently.

    Args:
        feed_urls: List of feed URLs to fetch
        since: Only fetch articles after this timestamp (optional)
        max_articles_per_feed: Maximum articles per feed (default: 50)

    Returns:
        Dictionary mapping feed URL to list of articles
    """
    import asyncio

    fetcher = RSSFetcher()
    results = {}

    async def fetch_one(url: str) -> tuple[str, List[Dict[str, Any]]]:
        try:
            articles = await fetcher.fetch_feed(url, since, max_articles_per_feed)
            return (url, articles)
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return (url, [])

    # Fetch all feeds concurrently
    tasks = [fetch_one(url) for url in feed_urls]
    fetch_results = await asyncio.gather(*tasks)

    for url, articles in fetch_results:
        results[url] = articles

    total_articles = sum(len(articles) for articles in results.values())
    logger.info(f"Fetched total of {total_articles} articles from {len(feed_urls)} feeds")

    return results
