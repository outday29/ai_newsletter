from datetime import datetime
from typing import Optional

from newspaper import Article
from newspaper.configuration import Configuration

from newsletter.scraper.post import Content


class Webpage(Content):
    _type: str = "webpage"
    title: Optional[str] = None
    content: Optional[str] = None  # TODO: Might need to support multimodal
    created_time: Optional[datetime] = None
    url: Optional[str] = None
    authors: Optional[list[str]] = None


def scrape_webpage(url: str) -> Webpage:
    custom_config = Configuration()
    custom_config.browser_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
    article = Article(url=url, config=custom_config)
    article.download()
    article.parse()
    return Webpage(
        title=article.title,
        content=article.text,
        created_time=article.publish_date,
        url=article.url,
        authors=article.authors,
    )
