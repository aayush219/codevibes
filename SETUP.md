# CodeVibes Studio — Production Setup Guide

**Your 10 minutes/day automated Instagram coding page.**

---

## What This System Does

Every day, fully automatically:

1. GitHub Actions wakes up at your scheduled times
2. Claude generates viral post content for each format
3. Python renders a 1080×1080 Instagram image (real fonts, color emoji)
4. The image is committed to your repo for a public URL
5. Instagram Graph API publishes it to your page
6. You get a log entry with the result

**Your only daily job:** spend 5–10 minutes reviewing yesterday's post_log.csv
artifact in GitHub Actions and replying to comments on Instagram.

---

## System Architecture

```
GitHub Actions (cron trigger)
    ↓
scripts/run_daily.py          ← orchestrator
    ├── generate_content.py   ← calls Claude API
    ├── render_image.py       ← renders 1080×1080 PNG with PIL
    ├── image_host.py         ← commits image to repo for public URL
    └── post_to_instagram.py  ← calls Instagram Graph API
```

---

## Section 1: Local Setup (First Time)

### 1a. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/codevibes-studio
cd codevibes-studio
pip install -r requirements.txt
sudo apt-get install fonts-noto-color-emoji   # Linux / WSL
# macOS: brew install --cask font-noto-color-emoji
```

### 1b. Configure your page

Edit `config/lineup.json`:
```json
{
  "lineup": ["challenge", "vibe", "oneliner", "beginner", "wouldyourather"],
  "page_handle": "YOUR_INSTAGRAM_HANDLE",
  "timezone": "Australia/Sydney"
}
```

Pick any 3–6 formats from:
| Format | Best time | Why |
|---|---|---|
| `challenge` | 9 AM | Drives comments (output guessing) |
| `vibe` | 12 PM | Drives shares (relatable humor) |
| `oneliner` | 5 PM | Drives saves (clean code tricks) |
| `beginner` | 7 PM | Drives follows (simple explanations) |
| `wouldyourather` | 9 PM | Drives comments (night scroll engagement) |
| `mindblown` | 3 PM | Drives shares (surprising tech facts) |
| `tierlist` | 6 PM | Drives comments (debate bait) |
| `devmath` | 11 AM | Drives shares (relatable humor) |

### 1c. Set environment variables

```bash
cp .env.example .env
# Edit .env with your keys (see Sections 2 and 3 below)
```

### 1d. Test with dry run (no Instagram posting)

```bash
DRY_RUN=true python scripts/run_daily.py --format challenge
```

You'll see a `sample_challenge.png` appear in `output/`. Check it looks right.

---

## Section 2: Anthropic API Key

1. Go to https://console.anthropic.com/
2. Click **API Keys** → **Create Key**
3. Copy the key (starts with `sk-ant-`)
4. Put it in `.env` as `ANTHROPIC_API_KEY=sk-ant-...`

**Cost estimate:** ~$0.003 per post × 5 posts/day × 30 days = **~$0.45/month**

---

## Section 3: Instagram API Setup

This is the most involved part. Read carefully. Takes ~30 minutes once.

### Step 1: Convert your Instagram account

1. Open Instagram → **Settings → Account → Switch to Professional Account**
2. Choose **Creator** or **Business** (either works)

### Step 2: Create a Facebook Page

1. Go to https://www.facebook.com/pages/create
2. Create a page for your brand (e.g. "CodeVibes Dev")
3. Connect it to your Instagram: Instagram Settings → **Linked Accounts → Facebook**

### Step 3: Create a Meta Developer App

1. Go to https://developers.facebook.com/apps/
2. Click **Create App** → choose **Business** type
3. Add the **Instagram Graph API** product to your app
4. Under **Instagram → API Setup**, generate a **User Token**
   - Select permissions: `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`

### Step 4: Get a Long-Lived Token

Short-lived tokens expire in 1 hour. You need a 60-day long-lived token:

```bash
curl -i -X GET \
  "https://graph.facebook.com/v21.0/oauth/access_token?
  grant_type=fb_exchange_token&
  client_id=YOUR_APP_ID&
  client_secret=YOUR_APP_SECRET&
  fb_exchange_token=YOUR_SHORT_LIVED_TOKEN"
```

Copy the returned `access_token`. Put it in `.env` as `IG_ACCESS_TOKEN=...`

> **Token renewal:** Set a calendar reminder every 55 days to refresh your token.
> GitHub Actions will also email you when a job fails (which would catch an expired token).

### Step 5: Get your Instagram Business Account ID

```bash
curl -i -X GET \
  "https://graph.facebook.com/v21.0/me/accounts?access_token=YOUR_LONG_LIVED_TOKEN"
```

This returns your Facebook Pages. For each page, get the linked Instagram account:

```bash
curl -i -X GET \
  "https://graph.facebook.com/v21.0/YOUR_PAGE_ID?
  fields=instagram_business_account&
  access_token=YOUR_LONG_LIVED_TOKEN"
```

The `instagram_business_account.id` value is your `IG_USER_ID`. Put it in `.env`.

### Step 6: Test the connection

```bash
python scripts/post_to_instagram.py \
  --image-url "https://raw.githubusercontent.com/YOUR_USERNAME/codevibes-studio/main/image-host/test/test.png" \
  --caption "test post — ignore 🙂"
```

(First upload a test image to your repo's `image-host/test/` folder.)

---

## Section 4: GitHub Setup (Automation)

### Step 1: Push your repo to GitHub

```bash
git init
git add .
git commit -m "Initial CodeVibes setup"
git remote add origin https://github.com/YOUR_USERNAME/codevibes-studio.git
git push -u origin main
```

Make sure the repo is **public** (needed for raw.githubusercontent.com image URLs).

### Step 2: Add GitHub Secrets

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**

Add these three secrets:

| Secret name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic key (sk-ant-...) |
| `IG_ACCESS_TOKEN` | Your 60-day IG token |
| `IG_USER_ID` | Your numeric Instagram Business Account ID |

### Step 3: Enable GitHub Actions

Go to **Actions** tab in your repo → click **Enable Actions**.

The workflow file at `.github/workflows/daily_post.yml` will start running
automatically on the cron schedule.

### Step 4: Adjust posting times for your timezone

The cron times in `daily_post.yml` are in UTC. Default config is for Sydney AEDT (UTC+11).

| Sydney AEDT | UTC | Format |
|---|---|---|
| 09:00 | 22:00 (prev day) | challenge |
| 12:00 | 01:00 | vibe |
| 17:00 | 06:00 | oneliner |
| 19:00 | 08:00 | beginner |
| 21:00 | 10:00 | wouldyourather |

Edit the `cron:` lines in `.github/workflows/daily_post.yml` if you're in a different timezone.

### Step 5: First test run

Go to **Actions → CodeVibes Daily Posts → Run workflow**
- Format: `challenge`
- Dry run: `true`

Watch it run. You'll see the generated image in the **Artifacts** section
of the completed job. If it looks good, run again with dry run = `false`.

---

## Section 5: Your 10 Minutes Daily

Here's exactly what you do each day:

**Morning (2 minutes):**
- Check GitHub Actions → confirm yesterday's posts all show green ✅
- If any failed: click the failed job, read the log, fix the issue

**Any time (5–8 minutes):**
- Open Instagram → reply to comments on the challenge post (huge for the algorithm)
- Like the best comment guesses — it encourages more people to comment tomorrow

**That's it.** The content is generated, images are rendered, posts are published,
all without you touching anything.

---

## Section 6: Changing Formats

To change which 5 formats post each day, edit `config/lineup.json`:

```json
{
  "lineup": ["mindblown", "vibe", "tierlist", "beginner", "wouldyourather"]
}
```

Then update the cron jobs in `.github/workflows/daily_post.yml` to match.
Each cron job has an `if:` condition checking the schedule string — update
those to match your new time slots.

---

## Section 7: Revenue Path to $10K/Month

| Followers | Timeline | Monthly revenue | What to do |
|---|---|---|---|
| 0–5K | Months 1–3 | $0 | Post consistently. Find which format gets most comments/saves. |
| 5K–15K | Months 3–6 | $200–800 | Add affiliate links in bio (Udemy: 10–15%). Sell a $12 cheat sheet PDF. |
| 15K–30K | Months 6–10 | $800–3K | First brand deals ($300–800/post). Start email list (Beehiiv, free). |
| 30K–75K | Months 10–16 | $3K–7K | Launch a $97 course (Gumroad). Multiple sponsors/month. |
| 75K+ | Month 16+ | $7K–15K+ | Evergreen course funnel + consistent sponsorships + community. |

**Fastest growth tactics:**
- Reply to every single comment in the first hour after posting (algorithm signal)
- Post your Challenge answer in the comments 2 hours later to revive engagement
- Use your Vibe posts to tag tool companies — they reshare, giving you free reach
- Collab with other coding accounts (DM 3 per week, offer to do a joint post)

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ANTHROPIC_API_KEY not set` | Check your GitHub Secrets are named exactly right |
| `IG_ACCESS_TOKEN expired` | Refresh your 60-day token (Section 3, Step 4) |
| `Image URL 404` | Check your repo is public and the image was committed correctly |
| `(#10) Application does not have permission` | Your Meta app needs `instagram_content_publish` permission |
| `Media container ERROR status` | Image URL is not reachable by Instagram's servers — check the raw GitHub URL works |
| Font looks wrong | Run `sudo apt-get install fonts-noto-color-emoji` on your machine |
| Posts look bad on mobile | All renders are 1080×1080 px — correct for Instagram feed |

---

## File Structure Reference

```
codevibes-studio/
├── .github/
│   └── workflows/
│       └── daily_post.yml       ← GitHub Actions (automated scheduler)
├── config/
│   ├── formats.py               ← 8 post formats with prompts + colors
│   └── lineup.json              ← which 5 formats to post + your handle
├── fonts/
│   ├── Inter-ExtraBold.ttf      ← headlines
│   ├── Inter-Regular.ttf        ← body text
│   ├── JetBrainsMono-Bold.ttf   ← code labels
│   └── JetBrainsMono-Regular.ttf← code content
├── scripts/
│   ├── run_daily.py             ← MAIN: orchestrates the full pipeline
│   ├── generate_content.py      ← calls Claude API for post content
│   ├── render_image.py          ← renders 1080×1080 PNG
│   ├── image_host.py            ← publishes image to public URL
│   └── post_to_instagram.py     ← calls Instagram Graph API
├── image-host/                  ← auto-created; holds committed post images
├── output/                      ← local only (in .gitignore); daily PNGs + log
├── .env.example                 ← copy to .env, fill in your keys
├── .gitignore
├── requirements.txt
└── SETUP.md                     ← this file
```
