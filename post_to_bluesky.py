import os
import feedparser
from atproto import Client, models
from bs4 import BeautifulSoup
import html

# Environment variables
RSS_FEED_URL = os.getenv("RSS_FEED_URL")
BSKY_HANDLE = os.getenv("BSKY_HANDLE")
BSKY_APP_PASSWORD = os.getenv("BSKY_APP_PASSWORD")

# HTML cleaner function
def html_cleaner(html_chunk):
    no_tags = BeautifulSoup(html_chunk, "html.parser")
    text_to_post = no_tags.get_text()
    return html.unescape(text_to_post).strip()

# Initialize Bluesky client
client = Client()
client.login(BSKY_HANDLE, BSKY_APP_PASSWORD)

# Parse RSS feed
feed = feedparser.parse(RSS_FEED_URL)

# Read last posted link
last_posted_file = "last_posted.txt"
last_posted_link = ""
if os.path.exists(last_posted_file):
    with open(last_posted_file, "r") as f:
        last_posted_link = f.read().strip()

# Get the newest item
latest = feed.entries[0]
title = html_cleaner(latest.title)
link = latest.link

if link != last_posted_link:
    post_text = f"Tumblr Update: {title}"

    # Limit to 300 characters
    if len(post_text) > 300:
        post_text = post_text[:297] + "..."

    # Create post record (no images)
    client.com.atproto.repo.create_record(
        data=models.ComAtprotoRepoCreateRecord.Data(
            repo=client.me.did,
            collection="app.bsky.feed.post",
            record=models.AppBskyFeedPost.Record(
                text=post_text,
                created_at=client.get_current_time_iso()
            ).model_dump()
        )
    )

    # Save last posted link
    with open(last_posted_file, "w") as f:
        f.write(link)

    print("Posted to Bluesky")
else:
    print("No new post")
