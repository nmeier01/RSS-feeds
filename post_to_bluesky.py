import os
import feedparser
import requests
from atproto import Client, models
from bs4 import BeautifulSoup
import html
import re

# Environment variables
RSS_FEED_URL = os.getenv("RSS_FEED_URL")
BSKY_HANDLE = os.getenv("BSKY_HANDLE")
BSKY_APP_PASSWORD = os.getenv("BSKY_APP_PASSWORD")

# HTML cleaner function
def html_cleaner(html_chunk):
    no_tags = BeautifulSoup(html_chunk, "html.parser")
    text_to_post = no_tags.get_text()
    return html.unescape(text_to_post).strip()

# Extract images function
def extract_images(entry):
    urls = []

    # Method 1: media_content field
    if "media_content" in entry:
        urls.extend([m["url"] for m in entry.media_content])

    # Method 2: <img> tags in description
    if "description" in entry and "<img" in entry.description:
        urls.extend(re.findall(r'<img.*?src="(.*?)"', entry.description))

    # Deduplicate while keeping order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return unique_urls[:4]

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

image_urls = extract_images(latest)

if link != last_posted_link:
    post_text = f"Tumblr Update: {title}"

    # Bluesky allows up to 300 chars
    if len(post_text) > 300:
        post_text = post_text[:297] + "..."

    embed = None
    if image_urls:
        images = []
        for url in image_urls:
            try:
                response = requests.get(url)
                response.raise_for_status()
                upload = client.upload_blob(response.content)
                images.append(
                    models.AppBskyEmbedImages.Image(
                        image=upload.blob,
                        alt=f"Image from {title}"
                    )
                )
            except Exception as e:
                print(f"Failed to upload image {url}: {e}")

        if images:
            embed = models.AppBskyEmbedImages.Main(images=images)

    # Construct full post record (no 100-char cutoff)
    record = models.AppBskyFeedPost.Record(
        text=post_text,
        embed=embed,
        created_at=client.get_current_time_iso()
    )

    client.com.atproto.repo.create_record(
        models.ComAtprotoRepoCreateRecord.Data(
            repo=client.me.did,
            collection="app.bsky.feed.post",
            data=record.model_dump()
    )
    )

    with open(last_posted_file, "w") as f:
        f.write(link)

    print("Posted to Bluesky")
else:
    print("No new post")



