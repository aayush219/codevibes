import os
import sys
import time
import argparse
import requests

from dotenv import load_dotenv, find_dotenv
# Force load the .env file and override any cached terminal session variables
load_dotenv(find_dotenv(), override=True)

GRAPH_API_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def get_credentials():
    token = os.environ.get("IG_ACCESS_TOKEN")
    ig_user_id = os.environ.get("IG_USER_ID")
    if not token or not ig_user_id:
        raise RuntimeError(
            "Missing IG_ACCESS_TOKEN or IG_USER_ID environment variables. "
            "Check that your .env file exists in your main project folder."
        )
    return token, ig_user_id



def create_media_container(image_url, caption, token, ig_user_id):
    """Step 1: Tell Instagram to fetch the image and prep a media container."""
    url = f"{GRAPH_BASE}/{ig_user_id}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": token,
    }
    # Restored to the original working POST structure
    resp = requests.post(url, data=payload, timeout=30)
    
    if resp.status_code != 200:
        print("\n❌ Meta Container Creation Failed!")
        print("Response Details:", resp.text)
        
    resp.raise_for_status()
    return resp.json()["id"]


def publish_container(container_id, token, ig_user_id):
    """Step 2: Actually publish the prepped container as a live post."""
    url = f"{GRAPH_BASE}/{ig_user_id}/media_publish"
    payload = {
        "creation_id": container_id,
        "access_token": token
    }
    resp = requests.post(url, data=payload, timeout=30)
    
    if resp.status_code != 200:
        print("\n❌ Meta Publishing Failed!")
        print("Response Details:", resp.text)
        
    resp.raise_for_status()
    return resp.json()["id"]


def post_to_instagram(image_url, caption):
    """Full pipeline flow: create container, wait, and publish directly."""
    token, ig_user_id = get_credentials()

    print(f"📤 Creating media container for {image_url[:60]}...")
    container_id = create_media_container(image_url, caption, token, ig_user_id)

    # 15s pause completely bypasses Meta's broken status-tracking loop endpoint bug
    print(f"⏳ Sleeping 15s to let Meta ingest the image completely...")
    time.sleep(15)

    print(f"🚀 Publishing directly to feed...")
    media_id = publish_container(container_id, token, ig_user_id)

    print(f"✅ Published successfully! Media ID: {media_id}")
    return media_id


def main():
    parser = argparse.ArgumentParser(description="Post an image to Instagram via Graph API")
    parser.add_argument("--image-url", required=True, help="Public HTTPS URL of the image to post")
    parser.add_argument("--caption", required=True, help="Caption text for the post")
    args = parser.parse_args()

    post_to_instagram(args.image_url, args.caption)


if __name__ == "__main__":
    main()
