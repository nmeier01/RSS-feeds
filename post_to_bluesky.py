import os
import requests
import feedparser
from atproto import Client, models
from bs4 import BeautifulSoup
import html
import re

# github secrets
RSS_FEED_URL = os.getenv("RSS_FEED_URL")
BSKY_HANDLE = os.getenv("BSKY_HANDLE")
BSKY_APP_PASSWORD = os.getenv("BSKY_APP_PASSWORD")

def html_cleaner(html_chunk):
    """Strip HTML and unescape entities"""
    no_tags = BeautifulSoup(html_chunk, 'html.parser')
    text_to_post = no_tags.get_text()
    return html.unescape(text_to_post)

def extract_images(entry):
    """Extract up to 4 unique image URLs from RSS entry"""
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

    return unique_urls[:4]  # Bluesky max = 4

def get_already_posted_links(client, handle, limit=20):
    #Fetch recent Bluesky posts and extract URLs
    feed_response = client.get_author_feed(actor=handle, limit=limit)
    already_posted_links = set()

    for post in feed_response.feed:
        record = post.post.record
        if hasattr(record, "text") and isinstance(record.text, str):
            matches = re.findall(r'https?://\S+', record.text)
            already_posted_links.update(matches)

    return already_posted_links

############ main script #############
feed = feedparser.parse(RSS_FEED_URL)   

client = Client()
client.login(BSKY_HANDLE, BSKY_APP_PASSWORD)

latest = feed.entries[0]
title = html_cleaner(latest.title)
link = latest.link

# Get recent Bluesky posts
already_posted_links = get_already_posted_links(client, BSKY_HANDLE, limit=20)

if link not in already_posted_links:
    post_text = f"Update from Tumblr: {title}\n{link}"

    image_urls = extract_images(latest)

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

    print("Posted to Bluesky")
else:
    print("Already cross-posted.")
