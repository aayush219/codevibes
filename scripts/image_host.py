"""
CodeVibes Studio — Image Hosting Helper
The Instagram Graph API requires a PUBLIC HTTPS URL for the image — it
cannot accept a local file upload directly. The simplest free solution
that works inside GitHub Actions: commit the generated image to a
public "image-host" folder in this same repo, then use the raw
GitHub URL (raw.githubusercontent.com) as the image_url.

This script is called automatically by the GitHub Actions workflow
(see .github/workflows/daily_post.yml) — you generally don't need to
run it manually.

Alternative hosting options (swap this module if you prefer):
  - Cloudflare R2 / AWS S3 with public read access
  - Imgur API (free, simple, but rate-limited)
  - Your own server / Render / Railway static file route
"""

import os
import sys
import shutil
import subprocess


def get_raw_github_url(repo_full_name, branch, file_path):
    """Build a raw.githubusercontent.com URL for a file already pushed to the repo."""
    return f"https://raw.githubusercontent.com/{repo_full_name}/{branch}/{file_path}"


def publish_image_to_repo(local_image_path, repo_root, dest_subpath):
    """
    Copy an image into <repo_root>/image-host/<dest_subpath> so it can be
    committed and pushed by the GitHub Actions workflow (which handles
    git add/commit/push as a separate step — see daily_post.yml).
    """
    dest_dir = os.path.join(repo_root, "image-host")
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, dest_subpath)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    shutil.copy(local_image_path, dest_path)
    return dest_path


def git_commit_and_push(repo_root, message="Add generated post images"):
    """Commit and push the image-host folder. Used inside CI where git is preconfigured."""
    subprocess.run(["git", "add", "image-host/"], cwd=repo_root, check=True)
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=repo_root
    )
    if result.returncode == 0:
        print("No changes to commit.")
        return False
    subprocess.run(["git", "commit", "-m", message], cwd=repo_root, check=True)
    subprocess.run(["git", "push"], cwd=repo_root, check=True)
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Publish a local image to the repo's public image-host folder")
    parser.add_argument("--image", required=True, help="Local path to the image file")
    parser.add_argument("--repo-root", default=".", help="Path to the git repo root")
    parser.add_argument("--dest", required=True, help="Destination subpath within image-host/, e.g. '2026-06-18/challenge.png'")
    parser.add_argument("--repo-full-name", required=True, help="e.g. 'yourusername/codevibes-studio'")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--push", action="store_true", help="Also git add/commit/push")
    args = parser.parse_args()

    dest_path = publish_image_to_repo(args.image, args.repo_root, args.dest)
    print(f"Copied to: {dest_path}")

    if args.push:
        pushed = git_commit_and_push(args.repo_root)
        if pushed:
            print("Pushed to remote.")

    url = get_raw_github_url(args.repo_full_name, args.branch, f"image-host/{args.dest}")
    print(f"PUBLIC_URL={url}")
