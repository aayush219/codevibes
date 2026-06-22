"""
CodeVibes Studio — Instagram Poster
Publishes a single image + caption to Instagram using the Instagram Graph API.

REQUIRES (see SETUP.md for full walkthrough):
  - An Instagram Professional (Business or Creator) account
  - That account linked to a Facebook Page
  - A Meta app with the instagram_basic + instagram_content_publish permissions
  - A long-lived Page Access Token
  - Your Instagram Business Account ID (IG_USER_ID)
  - A public HTTPS URL where the generated image can be fetched from
    (the Graph API requires a URL, not a local file upload — see image_host.py)

Usage:
    python post_to_instagram.py --image path/to/image.png --caption "caption text" --image-url https://your-host/image.png
"""

import os
import sys
import time
import argparse
import requests

GRAPH_API_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def get_credentials():
    token = os.environ.get("IG_ACCESS_TOKEN")
    ig_user_id = os.environ.get("IG_USER_ID")
    if not token or not ig_user_id:
        raise RuntimeError(
            "Missing IG_ACCESS_TOKEN or IG_USER_ID environment variables. "
            "See SETUP.md section 'Instagram API Setup' for how to obtain these."
        )
    return token, ig_user_id


def create_media_container(image_url, caption, token, ig_user_id):
    """Step 1: tell Instagram to fetch the image and prep a media container."""
    url = f"{GRAPH_BASE}/{ig_user_id}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": token,
    }
    resp = requests.post(url, data=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "id" not in data:
        raise RuntimeError(f"Failed to create media container: {data}")
    return data["id"]


def wait_for_container_ready(container_id, token, max_wait=60):
    """Poll the container status until FINISHED (Instagram needs to fetch+process the image)."""
    url = f"{GRAPH_BASE}/{container_id}"
    waited = 0
    while waited < max_wait:
        resp = requests.get(url, params={"fields": "status_code", "access_token": token}, timeout=15)
        resp.raise_for_status()
        status = resp.json().get("status_code")
        if status == "FINISHED":
            return True
        if status == "ERROR":
            raise RuntimeError(f"Media container failed processing: {resp.json()}")
        time.sleep(3)
        waited += 3
    raise TimeoutError(f"Container {container_id} not ready after {max_wait}s")


def publish_container(container_id, token, ig_user_id):
    """Step 2: actually publish the prepped container as a live post."""
    url = f"{GRAPH_BASE}/{ig_user_id}/media_publish"
    payload = {"creation_id": container_id, "access_token": token}
    resp = requests.post(url, data=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "id" not in data:
        raise RuntimeError(f"Failed to publish container: {data}")
    return data["id"]


def post_to_instagram(image_url, caption):
    """
    Full flow: create container -> wait for ready -> publish.
    image_url MUST be a publicly accessible HTTPS URL (Instagram fetches it server-side).
    Returns the published media ID.
    """
    token, ig_user_id = get_credentials()

    print(f"📤 Creating media container for {image_url[:60]}...")
    container_id = create_media_container(image_url, caption, token, ig_user_id)

    print(f"⏳ Waiting for Instagram to process the image...")
    wait_for_container_ready(container_id, token)

    print(f"🚀 Publishing...")
    media_id = publish_container(container_id, token, ig_user_id)

    print(f"✅ Published! Media ID: {media_id}")
    return media_id


def main():
    parser = argparse.ArgumentParser(description="Post an image to Instagram via Graph API")
    parser.add_argument("--image-url", required=True, help="Public HTTPS URL of the image to post")
    parser.add_argument("--caption", required=True, help="Caption text for the post")
    args = parser.parse_args()

    post_to_instagram(args.image_url, args.caption)


if __name__ == "__main__":
    main()
