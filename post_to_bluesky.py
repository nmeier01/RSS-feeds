import os
import feedparser
from atproto import Client


# Environment variables
RSS_FEED_URL = os.getenv("RSS_FEED_URL")
BSKY_HANDLE = os.getenv("BSKY_HANDLE")
BSKY_APP_PASSWORD = os.getenv("BSKY_APP_PASSWORD")


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
title = latest.title
link = latest.link


# Only post if it's new
if link != last_posted_link:
    post_text = f"📢 New Lab Update: {title}\n{link}"
    client.send_post(post_text)
    with open(last_posted_file, "w") as f:
        f.write(link)
    print("✅ Posted to Bluesky!")
else:
    print("No new post. Skipping.")