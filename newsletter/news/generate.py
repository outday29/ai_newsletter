"""
Generate a newsletters
"""

import datetime

from newsletter.llm.together_llm import Model, TogetherLLM
from newsletter.news.news import Newsletter
from newsletter.news.summarize import Summarizer
from newsletter.scraper.reddit import load_reddit_preferences, reddit_scraper
from newsletter.settings import settings


def generate_default_newsletter_name() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")


def generate_newsletter(
    name: str, filter_model: Model, summary_model: Model
) -> Newsletter:
    preferences = load_reddit_preferences()
    res = reddit_scraper.scrape_with_preferences(preferences=preferences)

    all_post_list = []
    for subreddit_name, post_list in res.items():
        filepath = settings.storage.raw_data_folder / f"{subreddit_name}.json"
        post_list.save(filepath)
        all_post_list.extend(post_list)

    summarizer = Summarizer(llm=TogetherLLM())
    summary = summarizer.summarize_post_list(
        post_list=all_post_list,
        summary_model=summary_model,
        filter_model=filter_model,
        newsletter_name=name,
    )
    summary.save()
    return summary
