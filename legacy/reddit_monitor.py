import asyncio
from datetime import time

import praw
from praw import reddit


class RedditMonitor:
    def __init__(self, client_id, client_secret, user_agent, username, password):
        self.reddit = praw.Reddit(
            client_id=client_id, client_secret=client_secret, user_agent=user_agent, username=username, password=password
        )

    def monitor_subreddit(self, subreddit_name, keywords, limit=None):
        subreddit = self.reddit.subreddit(subreddit_name)
        matches = []
        for submission in subreddit.new(limit=50):
            if any(keyword.lower() in submission.title.lower() for keyword in keywords):
                matches.append(
                    {
                        "title": submission.title,
                        "url": submission.url,
                        "content": submission.selftext,
                        "author": submission.author.name if submission.author else "N/A",
                        "created_utc": submission.created_utc,
                    }
                )
            if limit is not None:
                if len(matches) == limit:
                    break
        return matches
