from pathlib import Path

import pytest

from newsletter.scraper.reddit import PostFilter, RedditScraper
from newsletter.scraper.webpage import scrape_webpage


@pytest.fixture
def mock_reddit_filter():
    return PostFilter(upvotes=100, upvote_ratio=None, recency=2)


def test_reddit_scraper(mock_reddit_filter):
    scraper = RedditScraper()
    res = scraper.scrape(
        subreddit="chatgpt",
        post_filter=mock_reddit_filter,
        limit=10,
    )
    res.save(Path("test.json"))


def test_webpage_scraper():
    res = scrape_webpage(
        url="https://techcrunch.com/2024/08/02/character-ai-ceo-noam-shazeer-returns-to-google/?_guc_consent_skip=1722665586"
    )
    from pprint import pprint

    pprint(f"{res=}")
