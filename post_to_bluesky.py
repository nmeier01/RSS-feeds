import os
import requests
import feedparser
from atproto import Client, models

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

# Try to extract image URL
image_url = None
if "media_content" in latest:
    # Some Tumblr feeds use media:content
    image_url = latest.media_content[0]["url"]
elif "description" in latest and "<img" in latest.description:
    # Fallback: parse <img> tag inside description
    import re
    match = re.search(r'<img.*?src="(.*?)"', latest.description)
    if match:
        image_url = match.group(1)

# Only post if it's new
if link != last_posted_link:
    post_text = f"Lab Update: {title}\n{link}"

    if image_url:
        # Download the image
        img_data = requests.get(image_url).content
        # Upload to Bluesky
        upload = client.upload_blob(img_data, content_type="image/jpeg")
        embed = models.AppBskyEmbedImages.Main(
            images=[models.AppBskyEmbedImages.Image(
                image=upload.blob,
                alt=f"Image from {title}"
            )]
        )
        client.send_post(text=post_text, embed=embed)
    else:
        # No image, text-only post
        client.send_post(post_text)

    with open(last_posted_file, "w") as f:
        f.write(link)

    print("Posted to Bluesky (with image if available)!")
else:
    print("No new post")

