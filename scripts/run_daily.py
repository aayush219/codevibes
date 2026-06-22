"""
CodeVibes Studio — Daily Orchestrator
The single entry point that runs once a day (triggered by GitHub Actions).
For each format in today's lineup, it:
  1. Generates content via Claude (generate_content.py)
  2. Renders the Instagram image (render_image.py)
  3. Publishes the image to a public URL (image_host.py)
  4. Posts it to Instagram (post_to_instagram.py)
  5. Logs the result to output/post_log.csv

DRY RUN MODE: set DRY_RUN=true to generate + render everything WITHOUT
actually posting to Instagram. Use this to review content before going live,
or while you're still setting up Instagram API access.

Usage:
    python run_daily.py                  # full run: generate, render, post
    python run_daily.py --dry-run        # generate + render only, skip posting
    python run_daily.py --format vibe    # just one format (for testing)
"""

import os
import sys
import json
import csv
import argparse
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))

from formats import FORMATS, DEFAULT_LINEUP
from generate_content import generate_one, get_client
from render_image import render_post

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
OUTPUT_DIR = os.path.join(REPO_ROOT, "output")
LOG_PATH = os.path.join(OUTPUT_DIR, "post_log.csv")


def load_config():
    with open(os.path.join(REPO_ROOT, "config", "lineup.json")) as f:
        return json.load(f)


def log_result(format_id, status, detail=""):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    file_exists = os.path.isfile(LOG_PATH)
    with open(LOG_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp_utc", "format", "status", "detail"])
        writer.writerow([datetime.now(timezone.utc).isoformat(), format_id, status, detail])


def run_one_format(format_id, handle, client, dry_run, repo_full_name, today_str):
    print(f"\n{'=' * 50}\n{format_id.upper()}\n{'=' * 50}")

    # 1. Generate content
    print("⚡ Generating content with Claude...")
    post_data = generate_one(client, format_id, handle)
    print(f"  ✅ Got: {post_data.get('title') or post_data.get('fact') or post_data.get('topic') or format_id}")

    # 2. Render image
    print("🎨 Rendering image...")
    image_path = os.path.join(OUTPUT_DIR, f"{today_str}_{format_id}.png")
    render_post(post_data, format_id, handle, image_path)
    print(f"  ✅ Saved: {image_path}")

    caption = post_data.get("caption", "")

    if dry_run:
        print("🔍 DRY RUN — skipping Instagram publish.")
        log_result(format_id, "dry_run_ok", image_path)
        return {"format": format_id, "status": "dry_run", "image": image_path, "caption": caption}

    # 3. Publish image to a public URL (via repo image-host + GitHub raw URL)
    print("☁️  Publishing image to public host...")
    from image_host import publish_image_to_repo, get_raw_github_url, git_commit_and_push

    dest_subpath = f"{today_str}/{format_id}.png"
    publish_image_to_repo(image_path, REPO_ROOT, dest_subpath)
    pushed = git_commit_and_push(REPO_ROOT, message=f"Add {format_id} image for {today_str}")
    image_url = get_raw_github_url(repo_full_name, "main", f"image-host/{dest_subpath}")
    print(f"  ✅ Public URL: {image_url}")

    if pushed:
        print("  ⏳ Waiting 10s for GitHub raw CDN to catch up...")
        import time
        time.sleep(10)

    # 4. Post to Instagram
    print("📤 Posting to Instagram...")
    from post_to_instagram import post_to_instagram

    try:
        media_id = post_to_instagram(image_url, caption)
        log_result(format_id, "posted", media_id)
        return {"format": format_id, "status": "posted", "media_id": media_id, "image_url": image_url}
    except Exception as e:
        print(f"  ❌ Failed to post: {e}")
        log_result(format_id, "failed", str(e))
        return {"format": format_id, "status": "failed", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Run the full daily CodeVibes pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Generate + render only, skip Instagram posting")
    parser.add_argument("--format", help="Run only one format (for testing)")
    parser.add_argument("--repo-full-name", default=os.environ.get("GITHUB_REPOSITORY", ""),
                         help="owner/repo, used to build the public image URL")
    args = parser.parse_args()

    dry_run = args.dry_run or os.environ.get("DRY_RUN", "").lower() == "true"

    config = load_config()
    handle = config.get("page_handle", "codevibes.dev")
    lineup = [args.format] if args.format else config.get("lineup", DEFAULT_LINEUP)
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print(f"📅 Running CodeVibes daily pipeline for {today_str}")
    print(f"   Page: @{handle}")
    print(f"   Lineup: {', '.join(lineup)}")
    print(f"   Mode: {'DRY RUN (no posting)' if dry_run else 'LIVE'}")

    client = get_client()
    results = []
    for format_id in lineup:
        try:
            result = run_one_format(format_id, handle, client, dry_run, args.repo_full_name, today_str)
            results.append(result)
        except Exception as e:
            print(f"❌ {format_id} failed entirely: {e}")
            log_result(format_id, "error", str(e))
            results.append({"format": format_id, "status": "error", "error": str(e)})

    print(f"\n{'=' * 50}\nSUMMARY\n{'=' * 50}")
    for r in results:
        icon = "✅" if r["status"] in ("posted", "dry_run") else "❌"
        print(f"{icon} {r['format']}: {r['status']}")

    failed = [r for r in results if r["status"] in ("failed", "error")]
    if failed:
        print(f"\n⚠️  {len(failed)} format(s) failed. Check output/post_log.csv for details.")
        sys.exit(1)

    print(f"\n🎉 Done! {len(results)} posts processed.")


if __name__ == "__main__":
    main()
