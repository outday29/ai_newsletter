FILTER_PROMPT = """
Below is a JSON data holding simplified information about a social media post. The top level field refer to the information for the post, such as votes specify how many upvotes. The comments sections hold a list of objects containing information about each comment as well as replies to comments, if any. 

Post:

{post}

Your task is to detect whether the content of the post matches any of user interests. If so, reply with "Relevant". Else reply with "Not relevant".

User interests:

```
{user_interests}
```

Wrap your final response (i.e. "Relevant" or "Not relevant") with <answer></answer> tag.
"""

SUMMARIZE_PROMPT = """
Summarize the following social media post contents and the overall responses accurately into a paragraph. Ensure that the summary captures the main points and tone of both the original post and the replies.

Do not mention anything about the votes or specific users in the summary.
The summary needs both a title and a body.

Wrap title in <title></title>.
Wrap body in <body></body>.

Post: 

{post}

Summary:

"""
