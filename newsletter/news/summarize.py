import datetime
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from newsletter.llm.base import BaseLLM
from newsletter.llm.exception import (
    LLMRateLimitError,
    LLMServiceUnavailableError,
)
from newsletter.logger import logger
from newsletter.news.news import News, Newsletter
from newsletter.news.prompts import FILTER_PROMPT, SUMMARIZE_PROMPT
from newsletter.scraper.post import Post, PostList
from newsletter.settings import settings

NOT_RELEVANT_WORD = "not relevant"
RELEVANT_WORD = "relevant"
answer_pattern = re.compile(r"<answer>(.*?)</answer>")
title_pattern = re.compile(r"<title>(.*?)</title>")
body_pattern = re.compile(r"<body>(.*?)</body>")


def extract_relevance(text):
    # Use the precompiled regex to find the text within the <answer> tag
    match = answer_pattern.search(text)
    if match:
        # Get the content inside the <answer> tag
        content = match.group(1).strip()
        if content.lower() == NOT_RELEVANT_WORD:
            return False
        elif content.lower() == RELEVANT_WORD:
            return True
    # Return None if no match or if content is neither "Relevant" nor "Not relevant"
    return None


def extract_summary(text) -> Optional[tuple[str, str]]:
    # Use the precompiled regex to find the text within the <title> and <body> tags
    match = title_pattern.search(text)
    if match:
        title = match.group(1).strip()
    else:
        return None
    match = body_pattern.search(text)
    if match:
        body = match.group(1).strip()
    else:
        return None
    return title, body


class Summarizer(BaseModel):
    llm: BaseLLM

    def _format_filter_prompt(self, post: Post) -> str:
        return FILTER_PROMPT.format(
            post=post.model_dump_json(indent=2),
            user_interests=settings.storage.get_user_interest_prompt(),
        )

    def _format_summary_prompt(self, post: Post) -> str:
        return SUMMARIZE_PROMPT.format(
            post=post.model_dump_json(indent=2),
        )

    def filter_post(
        self, post: Post, model_names: list[str], num_retries: int = 1
    ) -> Optional[bool]:
        model_index_to_use = 0
        for _ in range(num_retries + 1):
            prompt = self._format_filter_prompt(post=post)
            try:
                output = self.llm.generate(
                    prompt=prompt, model_name=model_names[model_index_to_use]
                )
                logger.debug(f"Filter llm output: {output}")
                relevance = extract_relevance(output)
                if relevance is None:
                    logger.info("Failed to filter post. Retrying...")
                    continue
                return relevance

            except LLMRateLimitError:
                logger.info("Hitting rate limit error, waiting for 15 seconds.")
                time.sleep(15)
                continue

            except LLMServiceUnavailableError:
                logger.info(
                    f"LLM model {model_names[model_index_to_use]} unavailable (exception: {e}), using other LLM"
                )
                time.sleep(3)
                model_index_to_use = min(model_index_to_use + 1, len(model_names) - 1)
                continue

        return None

    def summarize_post(
        self, post: Post, model_name: list[str], num_retries: int = 1
    ) -> Optional[News]:
        model_index_to_use = 0
        for _ in range(num_retries + 1):
            prompt = self._format_summary_prompt(post=post)
            try:
                output = self.llm.generate(
                    prompt=prompt, model_name=model_name[model_index_to_use]
                )
                result = extract_summary(output)
                if result is None:
                    logger.info("Failed to summarize post. Retrying...")
                    continue

            except LLMRateLimitError:
                logger.info("Hitting rate limit error, waiting for 15 seconds.")
                time.sleep(15)
                continue

            except LLMServiceUnavailableError as e:
                logger.info(
                    f"LLM model {model_name[model_index_to_use]} unavailable (exception: {e}), using other LLM"
                )
                time.sleep(3)
                model_index_to_use = min(model_index_to_use + 1, len(model_name) - 1)
                continue

            return News(title=result[0], description=result[1], sources=[post.url])

        logger.info("All summarization attempts failed, returning None")
        return None

    def summarize_post_list(
        self,
        post_list: PostList,
        filter_model: list[str],
        summary_model: list[str],
        newsletter_name: Optional[str] = None,
    ) -> Newsletter:
        if newsletter_name is None:
            newsletter_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

        filtered_post = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_results = {
                executor.submit(
                    self.filter_post, post=post, model_names=filter_model
                ): post
                for post in post_list.posts
            }

            for future_result in as_completed(future_results):
                if future_result.exception() is not None:
                    logger.error(
                        f"{future_results[future_result]} failed to get filter result due to exception {future_result.exception()}. Skipping"
                    )

                else:
                    result = future_result.result()

                    if result is None:
                        logger.debug(
                            f"{future_results[future_result]=} failed to get filter result. Skipping"
                        )

                    elif result is True:
                        filtered_post.append(future_results[future_result])

                    elif result is not False:
                        logger.debug(f"Unknown filter result {result=}, skipping")

        news_list = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_results = {
                executor.submit(
                    self.summarize_post, post=post, model_name=summary_model
                ): post
                for post in filtered_post
            }

            for future in as_completed(future_results):
                result = future.result()
                if future.exception() is not None:
                    logger.error(
                        f"{future.post} failed to get summary result due to exception {future.exception()}. Skipping"
                    )

                elif result is not None:
                    news_list.append(result)

                else:
                    logger.debug(
                        f"{future_results[future]} failed to get summary result. Skipping"
                    )

        return Newsletter(
            news=news_list,
            name=newsletter_name,
            created_at=datetime.datetime.now(),
            path=Path(settings.storage.newsletter_folder) / f"{newsletter_name}.json",
        )
