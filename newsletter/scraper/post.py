"""
Common object for online posts.
Support Reddit, X, and others.
"""

from __future__ import annotations

import abc
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, SerializeAsAny


class Content(BaseModel, abc.ABC):
    pass


class Video(Content):
    url: str
    _type: str = "video"


class Image(Content):
    url: str
    _type: str = "image"


class Text(Content):
    text: str
    _type: str = "text"


class Poll(Content):
    _type: str = "poll"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    description: Optional[str] = None
    total_votes: int
    result: dict[str, int]  # A mapping from choice to votes.


class ForumContent(BaseModel):
    contents: SerializeAsAny[list[Content]] = Field(default_factory=list)

    def add(self, content: Content):
        self.contents.append(content)


class Comment(BaseModel):
    author: Optional[str] = None
    content: Optional[ForumContent] = None
    upvotes: Optional[int] = None
    downvotes: Optional[int] = None
    created_utc: Optional[int] = None
    url: Optional[str] = None
    comments: Optional[list[ForumContent]] = None


class Post(BaseModel):
    title: Optional[str] = None
    content: Optional[ForumContent] = None
    upvotes: Optional[int] = None
    downvotes: Optional[int] = None
    author: Optional[str] = None
    created_utc: Optional[int] = None
    url: Optional[str] = None
    comments: Optional[list[Comment]] = None

    @property
    def upvote_ratio(self) -> float:
        return self.upvotes / (self.upvotes + self.downvotes)


class PostList(BaseModel):
    source: str
    posts: list[Post]

    @classmethod
    def from_post_lists(cls, source: str, post_lists: list[PostList]) -> PostList:
        return cls(
            source=source,
            posts=[post for post_list in post_lists for post in post_list.posts],
        )
