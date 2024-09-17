from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional, TypeAlias
from urllib.parse import urlparse

import praw
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from newsletter.logger import logger
from newsletter.scraper.post import (
    Comment,
    ForumContent,
    Image,
    Poll,
    Post,
    PostList,
    Text,
    Video,
)
from newsletter.scraper.webpage import scrape_webpage
from newsletter.settings import settings

Submission: TypeAlias = praw.models.reddit.submission.Submission
RedditComment: TypeAlias = praw.models.reddit.comment.Comment


class Preference(BaseModel):
    subreddit_name: str
    post_filter: PostFilter


def load_reddit_preferences() -> list[Preference]:
    preference_list = TypeAdapter(list[Preference])
    preference_file = settings.storage.preferences_folder / "reddit.json"
    return preference_list.validate_json(preference_file.read_text())


def save_reddit_preferences(preferences: list[Preference]):
    preference_list = TypeAdapter(list[Preference])
    preference_file = settings.storage.preferences_folder / "reddit.json"
    preference_file.write_bytes(preference_list.dump_json(preferences, indent=2))


def init_reddit_client() -> praw.Reddit:
    reddit_client = praw.Reddit(
        client_id=settings.reddit.personal_use_script,
        client_secret=settings.reddit.client_secret.get_secret_value(),
        user_agent=settings.reddit.user_agent,
        username=settings.reddit.username,
        password=settings.reddit.password.get_secret_value(),
    )
    return reddit_client


class PostFilter(BaseModel):
    upvotes: Optional[int] = None
    upvote_ratio: Optional[float] = None
    recency: Optional[int] = None

    def to_accept(self, submission: Post) -> bool:
        if self.upvotes is not None and submission.upvotes < self.upvotes:
            return False

        if self.recency is not None:
            age = (datetime.now() - datetime.fromtimestamp(submission.created_utc)).days
            if age > self.recency:
                return False

        if (
            self.upvote_ratio is not None
            and submission.upvote_ratio < self.upvote_ratio
        ):
            return False

        return True


class RedditPostList(PostList):
    subreddit_name: str

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def from_path(cls, path: Path) -> RedditPostList:
        raw_text = path.read_text(encoding="utf-8")
        params = json.loads(raw_text)
        params["subreddit_name"] = path.parent.stem
        return RedditPostList(**params)


class RedditScraper(BaseModel):
    client: praw.Reddit = Field(default_factory=init_reddit_client)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    def scrape_with_preferences(
        self, preferences: list[Preference] | Preference, **kwargs
    ) -> dict[str, RedditPostList]:
        if isinstance(preferences, Preference):
            preferences = [preferences]

        return {
            preference.subreddit_name: self.scrape(
                subreddit=preference.subreddit_name,
                post_filter=preference.post_filter,
                **kwargs,
            )
            for preference in preferences
        }

    def scrape(
        self, subreddit: str, post_filter: PostFilter = PostFilter(), **kwargs
    ) -> RedditPostList:
        submission_list = self.client.subreddit(subreddit).hot(**kwargs)
        if submission_list is None:
            logger.warning(f"Failed to scrape subreddit {subreddit}")
            return RedditPostList(source="reddit", subreddit_name=subreddit, posts=[])

        with ThreadPoolExecutor() as executor:
            futures_to_submission = (
                executor.submit(self._parse_submission_to_post, submission)
                for submission in submission_list
            )
            submission_list = []
            for future in as_completed(futures_to_submission):
                submission_list.append(future.result())
        filtered = filter(post_filter.to_accept, submission_list)
        return RedditPostList(
            source="reddit",
            subreddit_name=subreddit,
            posts=list(filtered),
        )

    def _parse_comments(self, comments: list[RedditComment]) -> list[Comment]:
        return list(
            map(
                lambda x: Comment(
                    author=x.author.name,
                    comments=None,
                    content=ForumContent(contents=[Text(text=x.body)]),
                    created_utc=x.created_utc,
                    upvotes=x.ups,
                    url=x.permalink,
                ),
                comments,
            )
        )

    def _parse_submission_content(self, submission_obj: Submission) -> ForumContent:
        content = ForumContent()
        if hasattr(submission_obj, "poll_data"):
            content.add(
                Poll(
                    result={
                        option_obj.text: (
                            option_obj.vote_count
                            if hasattr(
                                option_obj, "vote_count"
                            )  # Object will not have vote_count if vote count is 0
                            else 0
                        )
                        for option_obj in submission_obj.poll_data.options
                    },
                    total_votes=submission_obj.poll_data.total_vote_count,
                    end_time=datetime.fromtimestamp(
                        submission_obj.poll_data.voting_end_timestamp
                        / 1000  # The submission timestamp is in milliseconds
                    ),
                )
            )

        if submission_obj.is_self:
            # No media content in this submission
            content.add(Text(text=submission_obj.selftext))

        else:
            linked_url = submission_obj.url
            parsed_url = urlparse(linked_url)
            # This submission consists of video
            if parsed_url.netloc == "v.redd.it":
                if hasattr(submission_obj, "crosspost_parent"):
                    metadata_dict = submission_obj.crosspost_parent_list[0]["media"]

                else:
                    metadata_dict = submission_obj.media

                content.add(Video(url=metadata_dict["reddit_video"]["fallback_url"]))

            # This submission consists of images.
            elif (parsed_url.netloc == "i.redd.it") or ("gallery" in parsed_url.path):
                if hasattr(submission_obj, "media_metadata"):
                    # This post has multiple images

                    for image_id, data_dict in submission_obj.media_metadata.items():
                        content.add(Image(url=data_dict["s"]["u"]))

                elif (
                    hasattr(submission_obj, "crosspost_parent")
                    and "media_metadata" in submission_obj.crosspost_parent_list[0]
                ):
                    # Crosspost children with multiple images
                    metadata_dict = submission_obj.crosspost_parent_list[0][
                        "media_metadata"
                    ]
                    logger.debug(f"{submission_obj.__dict__=}")
                    for image_id, data_dict in metadata_dict.items():
                        content.add(Image(url=data_dict["s"]["u"]))

                else:
                    content.add(Image(url=submission_obj.url))

            else:
                try:
                    article = scrape_webpage(url=linked_url)
                    content.add(article)

                except Exception as e:
                    print(e)

        return content

    def _parse_submission_to_post(self, subreddit_obj: Submission) -> Post:
        truncated_comments = filter(
            lambda x: not isinstance(x, praw.models.MoreComments)
            and x.author is not None,
            subreddit_obj.comments,
        )
        truncated_comments = sorted(
            truncated_comments, key=lambda c: c.score, reverse=True
        )[:10]
        return Post(
            author=subreddit_obj.author.name if subreddit_obj.author else None,
            comments=self._parse_comments(truncated_comments),
            content=self._parse_submission_content(subreddit_obj),
            created_utc=subreddit_obj.created_utc,
            upvotes=subreddit_obj.ups,
            downvotes=int(subreddit_obj.ups * (1 / subreddit_obj.upvote_ratio - 1)),
            title=subreddit_obj.title,
            url=subreddit_obj.permalink,
        )


reddit_scraper = RedditScraper()
