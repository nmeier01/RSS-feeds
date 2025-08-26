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
    no_tags = BeautifulSoup(html_chunk,'html.parser')
    text_to_post = no_tags.get_text()
    return html.unescape(text_to_post).strip()



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

    return unique_urls[:4]  # Bluesky max = 4


    
client = Client()
client.login(BSKY_HANDLE, BSKY_APP_PASSWORD)

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
    post_text = f"Update from Tumblr: {title}"
    
    max_len = 300
    if len(post_text)>max_len:
        post_text = post_text[:max_len-1]+"…"
        
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

    with open(last_posted_file, "w") as f:
        f.write(link)

    print("Posted to Bluesky")


    
else:
    print("No new post.")

#     if image_url:
#         # Download the image
#         img_data = requests.get(image_url).content
#         # Upload to Bluesky
#         upload = client.upload_blob(img_data)
#         embed = models.AppBskyEmbedImages.Main(
#             images=[models.AppBskyEmbedImages.Image(
#                 image=upload.blob,
#                 alt=f"Image from {title}"
#             )]
#         )
#         client.send_post(text=post_text, embed=embed)
#     else:
#         # No image, text-only post
#         client.send_post(post_text)

#     with open(last_posted_file, "w") as f:
#         f.write(link)

#     print("Posted to Bluesky (with image if available)!")
# else:
#     print("No new post")



 













