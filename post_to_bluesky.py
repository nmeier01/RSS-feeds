import os
import feedparser
import requests
from atproto import Client, models
from bs4 import BeautifulSoup
import html

# ---- Clean Tumblr text (remove HTML tags, decode entities) ----
def clean_text(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text()
    return html.unescape(text).strip()

# ---- Build safe Bluesky text ----
def build_post_text(title: str) -> str:
    MAX_LEN = 300
    if len(title) > MAX_LEN:
        return title[:MAX_LEN - 1] + "…"
    return title

# ---- Main ----
def main():
    # Load env vars
    RSS_FEED_URL = os.getenv("RSS_FEED_URL")
    BSKY_HANDLE = os.getenv("BSKY_HANDLE")
    BSKY_APP_PASSWORD = os.getenv("BSKY_APP_PASSWORD")


    # Parse Tumblr RSS
    feed = feedparser.parse(tumblr_rss)
    latest = feed.entries[0]

    # Clean and prepare text
    title = clean_text(latest.title)
    description = clean_text(getattr(latest, "description", ""))

    # Prefer title; fallback to description if no title
    raw_text = title if title else description

    post_text = build_post_text(raw_text)

    # Collect any images in the post
    image_urls = []
    if "media_content" in latest:
        image_urls = [m["url"] for m in latest.media_content if m["medium"] == "image"]

    # Login to Bluesky
    client = Client()
    client.login(bsky_handle, bsky_password)

    # If images exist, upload them
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
                        alt=f"Image from Tumblr post"
                    )
                )
            except Exception as e:
                print(f"⚠️ Failed to fetch/upload image {url}: {e}")

        if images:
            embed = models.AppBskyEmbedImages.Main(images=images)
            client.send_post(text=post_text, embed=embed)
        else:
            client.send_post(post_text)
    else:
        client.send_post(post_text)

if __name__ == "__main__":
    main()

