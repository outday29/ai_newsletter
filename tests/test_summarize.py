import time
from pathlib import Path

import pytest

from newsletter.llm.together_llm import TogetherLLM
from newsletter.news.summarize import Summarizer
from newsletter.scraper.reddit import RedditPostList


@pytest.fixture()
def mock_post_list() -> RedditPostList:
    return RedditPostList.from_path(Path("tests") / "test_data" / "chatgpt.json")


@pytest.fixture()
def mock_summarizer() -> Summarizer:
    return Summarizer(llm=TogetherLLM())


def test_filter(mock_post_list, mock_summarizer):
    res = mock_summarizer.filter_post(
        post=mock_post_list.posts[0],
        model_name="meta-llama/Meta-Llama-3-70B-Instruct-Turbo",
    )

    from pprint import pprint

    pprint(f"{res=}")


def test_summarize(mock_post_list, mock_summarizer):
    res = mock_summarizer.summarize_post(
        post=mock_post_list.posts[0],
        model_name="meta-llama/Meta-Llama-3-70B-Instruct-Turbo",
    )

    from pprint import pprint

    pprint(f"{res=}")


def test_summarize_post_list(mock_post_list, mock_summarizer):
    # Record time
    start = time.perf_counter()
    res = mock_summarizer.summarize_post_list(
        post_list=mock_post_list,
        model_name="meta-llama/Meta-Llama-3-70B-Instruct-Turbo",
        newsletter_name="test_newsletter",
    )

    res.save()

    from pprint import pprint

    pprint(f"{res=}")
    end = time.perf_counter()
    print(f"Elapsed time: {end - start:.2f} seconds")
