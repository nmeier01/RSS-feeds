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
    no_tags = BeautifulSoup(html_chunk,'html.parser')
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


image_urls = extract_images(latest)

if link != last_posted_link:
    post_text = f"Tumblr Update: {title}"

    if image_urls:
        images = []
        for url in image_urls:
            try:
                response = requests.get(url)
                response.raise_for_status()
                upload = client.upload_blob(response.content)
                images.append(models.AppBskyEmbedImages.Image(
                    image=upload.blob,
                    alt=f"Image from {title}"
                ))
            except Exception as e:
                print(f"Failed to upload image {url}: {e}")

        embed = models.AppBskyEmbedImages.Main(images=images)
        client.send_post(text=post_text, embed=embed)
    else:
        client.send_post(post_text)

    with open(last_posted_file, "w") as f:
        f.write(link)

    print("Posted to Bluesky")
else:
    print("No new post")
