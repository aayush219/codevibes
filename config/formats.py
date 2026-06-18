"""
CodeVibes Studio — Post Format Definitions
Each format has a unique visual identity, color palette, and AI prompt.
Pick 5 of these 8 formats for your daily lineup (see config/lineup.json).
"""

FORMATS = {
    "challenge": {
        "emoji": "🧩",
        "label": "Daily Challenge",
        "tag": "CHALLENGE",
        "desc": "Short code snippet — guess the output",
        "colors": ["#7C6FFF", "#A78BFA"],
        "default_time": "09:00",
        "recommended": True,
        "prompt": """You run a viral coding Instagram page. Create a DAILY CHALLENGE post.

Rules:
- ONE short, surprising code snippet (4-6 lines) where the output is genuinely tricky
- Topics: JS type coercion, Python gotchas, async quirks, scope/closures, reference vs value
- Casual tone. No tutorials. Just the puzzle.

Return ONLY valid JSON, no markdown fences:
{
  "title": "what does this output? 👇",
  "sub": "short tagline like '90% get this wrong 😈'",
  "code": "the code snippet with real newline characters",
  "answer": "short answer phrase",
  "caption": "full instagram caption: casual tone, build suspense, use a dot-by-dot spoiler gap before revealing the answer, end with exactly 10 relevant hashtags"
}""",
    },
    "vibe": {
        "emoji": "💀",
        "label": "Dev Vibe",
        "tag": "RELATABLE",
        "desc": "Meme / relatable humor, no code required",
        "colors": ["#EC4899", "#F97316"],
        "default_time": "12:00",
        "recommended": True,
        "prompt": """You run a viral coding Instagram page. Create a DEV VIBE meme post.

Rules:
- NO code required
- Relatable developer humor: git blame, 3am code, standup hell, merge conflicts, "it works on my machine"
- Format like a tweet, text convo, or "me vs" comparison
- Vibe: chaotic, real, funny — devs should want to tag a friend

Return ONLY valid JSON, no markdown fences:
{
  "title": "punchy headline, max 5 words",
  "sub": "secondary punchline",
  "vibeLines": ["array of 5-6 short lines that build the joke"],
  "caption": "full instagram caption: very casual, lowercase, relatable, end with exactly 10 hashtags"
}""",
    },
    "oneliner": {
        "emoji": "⚡",
        "label": "One Liner",
        "tag": "TRICK",
        "desc": "Before/after — messy code vs one elegant line",
        "colors": ["#06B6D4", "#10B981"],
        "default_time": "17:00",
        "recommended": True,
        "prompt": """You run a viral coding Instagram page. Create a ONE LINER TRICK post.

Rules:
- Show a clear BEFORE (messy, multi-line, "the way everyone learns first")
  and AFTER (one elegant, genuinely impressive line)
- Must be a real, non-obvious trick — not basic syntax
- Languages: Python, JS, bash, SQL — keep it practical
- Vibe: "why didn't I know this earlier"

Return ONLY valid JSON, no markdown fences:
{
  "title": "stop writing X lines (short, punchy)",
  "sub": "hook like 'this does it in ONE ⚡'",
  "before": "before code with a // 😩 old way comment, real newlines",
  "after": "after one-liner with a // ✨ comment, real newlines",
  "lang": "language name",
  "caption": "full instagram caption: hype the discovery moment, ask who already knew it, end with exactly 10 hashtags"
}""",
    },
    "wouldyourather": {
        "emoji": "🎭",
        "label": "Would You Rather",
        "tag": "NIGHT DROP",
        "desc": "Two cursed dev choices — forced pick in comments",
        "colors": ["#F59E0B", "#EF4444"],
        "default_time": "21:00",
        "recommended": True,
        "prompt": """You run a viral coding Instagram page. Create a WOULD YOU RATHER post
designed for night-time scrolling — easy to understand, zero technical
knowledge required to participate, instant gut-reaction opinion.

Rules:
- Two equally cursed/funny developer-life choices
- Must be answerable in 2 seconds, no thinking required
- Funny, relatable, slightly absurd is good

Return ONLY valid JSON, no markdown fences:
{
  "optionA": {"emoji": "😭", "text": "first cursed option"},
  "optionB": {"emoji": "💀", "text": "second cursed option"},
  "context": "short subtext like 'both are cursed. choose.'",
  "caption": "full instagram caption: casual night energy, explain both options briefly, tell people to comment A or B, end with exactly 10 hashtags"
}""",
    },
    "beginner": {
        "emoji": "🔰",
        "label": "Beginner Corner",
        "tag": "LEARN",
        "desc": "One concept explained simply, for total beginners",
        "colors": ["#10B981", "#06B6D4"],
        "default_time": "19:00",
        "recommended": True,
        "prompt": """You run a viral coding Instagram page. Create a BEGINNER CORNER post
that explains ONE simple programming concept using a real-world analogy,
aimed at someone who has never coded before.

Rules:
- Pick ONE concept (API, variable, function, loop, database, etc.)
- Use a real-world analogy a non-coder instantly understands
- Keep it to 4-5 short steps
- Warm, welcoming tone — never condescending

Return ONLY valid JSON, no markdown fences:
{
  "title": "What even IS [concept]?",
  "sub": "explained in 30 seconds 🔰",
  "analogy": "[concept] = real world thing analogy",
  "steps": ["array of 4-5 short, simple steps explaining the analogy"],
  "caption": "full instagram caption: welcoming to total beginners, encourage them to save + follow for more, end with exactly 10 hashtags"
}""",
    },
    "mindblown": {
        "emoji": "🤯",
        "label": "Mind = Blown",
        "tag": "FACT",
        "desc": "A tech fact or concept that breaks your brain",
        "colors": ["#8B5CF6", "#EC4899"],
        "default_time": "15:00",
        "recommended": False,
        "prompt": """You run a viral coding Instagram page. Create a MIND BLOWN tech-fact post.

Rules:
- A genuinely surprising, true fact about programming/tech history or behavior
- Must be screenshot/share-worthy
- Keep it simple enough for a non-developer to also find interesting

Return ONLY valid JSON, no markdown fences:
{
  "fact": "the surprising fact, one punchy sentence",
  "followup": "one supporting sentence with more detail",
  "deeper": "a short third twist or extra detail",
  "caption": "full instagram caption: build on the fact, ask people to tag someone who didn't know, end with exactly 10 hashtags"
}""",
    },
    "tierlist": {
        "emoji": "🏆",
        "label": "Tier List",
        "tag": "RANKING",
        "desc": "Rank tools/frameworks devs always argue about",
        "colors": ["#F97316", "#F59E0B"],
        "default_time": "18:00",
        "recommended": False,
        "prompt": """You run a viral coding Instagram page. Create a TIER LIST post designed
to start arguments in the comments.

Rules:
- Pick ONE category devs genuinely disagree about (frameworks, editors, languages, tools)
- 5 tiers: S, A, B, C, D
- 1-2 items per tier, keep it spicy/debatable

Return ONLY valid JSON, no markdown fences:
{
  "topic": "category name",
  "tiers": {"S": ["item"], "A": ["item"], "B": ["item","item"], "C": ["item"], "D": ["item"]},
  "caption": "full instagram caption: justify a couple picks, invite people to post their own tier list, end with exactly 10 hashtags"
}""",
    },
    "devmath": {
        "emoji": "💸",
        "label": "Dev Math",
        "tag": "HUMOR",
        "desc": "Funny but true equations about developer life",
        "colors": ["#EF4444", "#F97316"],
        "default_time": "11:00",
        "recommended": False,
        "prompt": """You run a viral coding Instagram page. Create a DEV MATH post:
funny, relatable "equations" about developer life.

Rules:
- 4 short equation-style lines, e.g. "1 hour estimate = 3 days actual"
- Must be true-feeling and broadly relatable, even to non-devs
- Punchy, no explanation needed

Return ONLY valid JSON, no markdown fences:
{
  "equations": ["equation 1", "equation 2", "equation 3", "equation 4"],
  "caption": "full instagram caption: ask which one hits hardest, end with exactly 10 hashtags"
}""",
    },
}

# Default daily lineup — 5 formats, ordered by recommended posting time
DEFAULT_LINEUP = ["challenge", "vibe", "oneliner", "beginner", "wouldyourather"]
