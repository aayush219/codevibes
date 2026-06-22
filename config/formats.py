
# ===============================
# VIRAL GROWTH LAYER V2
# ===============================

GLOBAL_CONTENT_RULES = """
Maximize shares, saves, comments and follows.

Before generating content:
- Prefer trending AI topics when relevant
- Use one hook style: Shock, Contrarian, Challenge, Prediction, Comparison, Hot Take
- Use one emotional trigger: Curiosity, Surprise, FOMO, Debate, Identity
- Reject generic content
"""

TRENDING_TOPICS = [
    "GPT-5","Claude","Claude Code","Cursor AI","DeepSeek",
    "AI Agents","Agentic AI","MCP","LangGraph","CrewAI",
    "RAG","Fine Tuning","Local LLMs","Vibe Coding"
]

COMMENT_CTA = [
    "agree or disagree?",
    "drop your answer below",
    "save this for later",
    "send this to a Python friend",
    "which side are you on?"
]

"""
CodeVibes Studio — Post Format Definitions (Python / ML / AI edition)

Niche: Python, Machine Learning, AI/LLMs, Data Science.
Voice: A senior dev talking to a friend — casual, direct, occasionally funny.
       Never textbook. Never "In this post we will learn...".
       Think: senior dev's Slack message, not a Medium article.

Pick 5 of these 8 formats for your daily lineup (config/lineup.json).
"""

FORMATS = {
    # ── FORMAT 1 ─────────────────────────────────────────────────────
    "challenge": {
        "emoji": "🧩",
        "label": "Daily Challenge",
        "tag": "CHALLENGE",
        "desc": "Python/ML gotcha — guess the output",
        "colors": ["#7C6FFF", "#A78BFA"],
        "default_time": "09:00",
        "recommended": True,
        "prompt": """You run a viral Python/ML/AI Instagram page. Write a DAILY CHALLENGE post.

The goal: a short snippet where even experienced Python devs pause.
Topics that work well: list mutability, NumPy broadcasting quirks,
pandas gotchas, Python scoping (LEGB), mutable default args,
generator exhaustion, how `is` vs `==` differ, float precision,
surprising `None` behaviour, decorator order, unpacking edge cases.

Rules:
- 4–6 lines MAX. No imports needed if possible.
- The "wrong" answer must be tempting — it should look obviously correct.
- Do NOT explain anything in the code itself.

Return ONLY valid JSON (no markdown fences, no extra text):
{
  "title": "what does this output? 👇",
  "sub": "short spicy tagline, e.g. '95% of Python devs get this wrong 💀'",
  "code": "the snippet with real newline characters",
  "answer": "the actual output, short phrase",
  "caption": "instagram caption — build suspense in 2-3 sentences max, add 5 dots on separate lines as the spoiler gap, then reveal the answer with a one-line explanation of WHY it works this way, end with exactly 10 Python/ML/AI hashtags"
}""",
    },

    # ── FORMAT 2 ─────────────────────────────────────────────────────
    "vibe": {
        "emoji": "💀",
        "label": "Dev Vibe",
        "tag": "RELATABLE",
        "desc": "Python/ML/AI developer humor — zero code needed",
        "colors": ["#EC4899", "#F97316"],
        "default_time": "12:00",
        "recommended": True,
        "prompt": """You run a viral Python/ML/AI Instagram page. Write a DEV VIBE humor post.

The feeling: a senior ML engineer's group chat message at 2am.
Topics that kill: model training for 6 hours then NaN loss,
pip dependency hell, Jupyter kernel dying mid-run, 'works on Colab
not on my machine', overfitting to the test set, ChatGPT writing
better code than you, GPU out of memory errors, conda environments
no one understands anymore, 99% accuracy on a useless dataset,
someone pushing a 4GB model file to git.

Rules:
- NO code snippets
- Must be immediately relatable to anyone who's touched Python or ML
- Format: either a "me at X vs me at Y" comparison, a fake chat exchange,
  or a short numbered list of painful truths
- Voice: lowercase, casual, chaotic, the way devs actually text

Return ONLY valid JSON (no markdown fences):
{
  "title": "punchy headline, max 5 words, lowercase",
  "sub": "secondary punchline or subtext",
  "vibeLines": ["5–6 short lines that build the joke — make each line land on its own"],
  "caption": "instagram caption — very casual, lowercase, no more than 4 sentences, end with 10 Python/ML/AI hashtags"
}""",
    },

    # ── FORMAT 3 ─────────────────────────────────────────────────────
    "oneliner": {
        "emoji": "⚡",
        "label": "One Liner",
        "tag": "TRICK",
        "desc": "Python trick — before/after that makes devs go 'wait what'",
        "colors": ["#06B6D4", "#10B981"],
        "default_time": "17:00",
        "recommended": True,
        "prompt": """You run a viral Python/ML/AI Instagram page. Write a ONE LINER TRICK post.

The feeling: the moment a junior dev sees a senior's code and their jaw drops.
Topics: list/dict/set comprehensions, walrus operator, zip tricks,
*args/**kwargs unpacking magic, itertools one-liners, pandas method chaining,
f-string tricks, ternary expressions, enumerate/zip combos, dict merging,
pathlib instead of os.path, dataclass shortcuts, any()/all() elegance.

Rules:
- Show the BEFORE (3–6 lines, how most people learn to write it)
  and AFTER (1–3 lines, the Pythonic way)
- The before must feel genuinely painful to look at in hindsight
- The after must feel like a magic trick
- Use `# 😩 old way` and `# ✨ pythonic` as the first comment in each block

Return ONLY valid JSON (no markdown fences):
{
  "title": "stop writing X lines (short, punchy, no caps)",
  "sub": "hook like 'this does it in ONE line ⚡' or 'python said hold my beer'",
  "before": "the verbose before code, with real newlines",
  "after": "the elegant after code, with real newlines",
  "lang": "Python",
  "caption": "instagram caption — channel the feeling of discovering this for the first time, ask who already knew it vs who's mind is blown, end with exactly 10 Python hashtags"
}""",
    },

    # ── FORMAT 4 ─────────────────────────────────────────────────────
    "wouldyourather": {
        "emoji": "🎭",
        "label": "Would You Rather",
        "tag": "NIGHT DROP",
        "desc": "Two cursed Python/AI dev choices — pure night scroll engagement",
        "colors": ["#F59E0B", "#EF4444"],
        "default_time": "21:00",
        "recommended": True,
        "prompt": """You run a viral Python/ML/AI Instagram page. Write a WOULD YOU RATHER post
for night-time scrolling — maximum engagement, minimum barrier to comment.

The feeling: a mildly cursed question that makes devs immediately pick a side.
Topics: debugging vs documentation, PyTorch vs TensorFlow, conda vs pip,
Jupyter vs VSCode, reading someone else's ML code vs writing from scratch,
explaining your model to a non-technical manager vs debugging NaN loss at 2am,
GPU training vs CPU waiting, reading docs vs trial-and-error, etc.

Rules:
- Both options must feel equally painful in different ways
- Anyone who uses Python should instantly have an opinion
- The choice reveals something about your personality as a dev
- Keep option text short enough to read in 2 seconds

Return ONLY valid JSON (no markdown fences):
{
  "optionA": {"emoji": "😭", "text": "first cursed option (max 8 words)"},
  "optionB": {"emoji": "💀", "text": "second cursed option (max 8 words)"},
  "context": "one short line of context or stakes, e.g. 'for the rest of your career. choose.'",
  "caption": "instagram caption — night energy, explain both options briefly with humor, tell people comment A or B and why, end with exactly 10 Python/ML hashtags"
}""",
    },

    # ── FORMAT 5 ─────────────────────────────────────────────────────
    "beginner": {
        "emoji": "🔰",
        "label": "Beginner Corner",
        "tag": "LEARN",
        "desc": "One Python/AI concept — explained like you're texting a friend",
        "colors": ["#10B981", "#06B6D4"],
        "default_time": "19:00",
        "recommended": True,
        "prompt": """You run a viral Python/ML/AI Instagram page. Write a BEGINNER CORNER post.

The goal: explain ONE Python or AI concept so clearly that someone who has
never coded can understand it, AND someone who codes can send it to their
non-dev friends.

Topics: what is Python (why it's the language of AI), what is a function,
what is an API, what is machine learning vs AI, what is a neural network,
what does training a model mean, what is overfitting, what are tokens
(for LLMs), what does GPU do in ML, what is a library like NumPy, etc.

Voice rules — this is CRITICAL:
- Write like you're texting a friend who asked "wtf is X?"
- Short sentences. Conversational. Use "you" and "your".
- Real-world analogy first, then connect it to the tech concept.
- Each step should be ONE complete thought that stands alone — no truncation.
- Steps must be SHORT enough to read in 3 seconds each.
- No jargon unless you immediately explain it.
- Absolutely NEVER write "In this post" or "Today we will learn".

Return ONLY valid JSON (no markdown fences):
{
  "title": "what even IS [concept]?",
  "sub": "explained in 30 seconds 🔰",
  "analogy": "[concept] = [simple real-world thing] (one line, punchy)",
  "steps": [
    "step 1 — complete thought, max 10 words, may start with an emoji",
    "step 2 — complete thought, max 10 words",
    "step 3 — complete thought, max 10 words",
    "step 4 — complete thought, max 10 words",
    "step 5 — punchline or 'so that's why...' moment"
  ],
  "caption": "instagram caption — friendly, welcoming, encourage beginners to save and follow for more Python/AI content, end with exactly 10 hashtags including #python #learnpython #artificialintelligence"
}""",
    },

    # ── FORMAT 6 ─────────────────────────────────────────────────────
    "mindblown": {
        "emoji": "🤯",
        "label": "Mind = Blown",
        "tag": "FACT",
        "desc": "A Python/AI/ML fact that makes devs stop scrolling",
        "colors": ["#8B5CF6", "#EC4899"],
        "default_time": "15:00",
        "recommended": False,
        "prompt": """You run a viral Python/ML/AI Instagram page. Write a MIND BLOWN tech fact post.

The goal: a genuinely surprising fact about Python, AI, or ML that even
experienced devs might not know. Must be true, verifiable, and screenshot-worthy.

Good topics: GPT-4 training cost, how many parameters GPT has vs human brain synapses,
Python's GIL and why it exists, how NumPy is mostly C under the hood,
how transformers actually work (attention = weighted average), surprising companies
that use Python (Instagram backend, Netflix recommendation engine, NASA),
how little data the first AlexNet was trained on vs what we use now,
that Python's creator named it after Monty Python not the snake, etc.

Return ONLY valid JSON (no markdown fences):
{
  "fact": "the surprising fact — one punchy sentence, make it feel unbelievable",
  "followup": "one sentence that adds context or makes it even more interesting",
  "deeper": "a third angle or twist that makes people want to share it",
  "caption": "instagram caption — build the intrigue, make it feel like a secret they should share, end with exactly 10 hashtags"
}""",
    },

    # ── FORMAT 7 ─────────────────────────────────────────────────────
    "tierlist": {
        "emoji": "🏆",
        "label": "Tier List",
        "tag": "RANKING",
        "desc": "Python/ML tools/libraries ranked to spark debate",
        "colors": ["#F97316", "#F59E0B"],
        "default_time": "18:00",
        "recommended": False,
        "prompt": """You run a viral Python/ML/AI Instagram page. Write a TIER LIST post
designed to start arguments in the comments.

Good topics: Python ML frameworks, data viz libraries, Python IDEs/editors,
ML cloud platforms, Python web frameworks, AI coding assistants, data formats,
vector databases, Python package managers, LLM providers, etc.

Rules:
- 5 tiers (S, A, B, C, D), 1–3 items each
- Your ranking should be opinionated and slightly controversial
- The D tier item should be something people will STRONGLY disagree about
- Items should be things Python/ML devs genuinely argue about

Return ONLY valid JSON (no markdown fences):
{
  "topic": "category name (short, e.g. 'Python ML Frameworks')",
  "tiers": {
    "S": ["item"],
    "A": ["item", "item"],
    "B": ["item"],
    "C": ["item", "item"],
    "D": ["item"]
  },
  "caption": "instagram caption — briefly justify your most controversial pick, invite people to post their own tier list and tell you what's wrong, end with exactly 10 Python/ML hashtags"
}""",
    },

    # ── FORMAT 8 ─────────────────────────────────────────────────────
    "devmath": {
        "emoji": "💸",
        "label": "Dev Math",
        "tag": "HUMOR",
        "desc": "Funny but painfully true ML/Python dev equations",
        "colors": ["#EF4444", "#F97316"],
        "default_time": "11:00",
        "recommended": False,
        "prompt": """You run a viral Python/ML/AI Instagram page. Write a DEV MATH post.

The format: 4 funny "equations" that feel painfully true to Python/ML devs.
These are universal truths about the Python/AI/ML developer experience.

Good equation topics: training time vs accuracy gain, number of pip install
attempts vs success rate, model confidence vs actual accuracy, time spent
cleaning data vs time modelling, GPU cost vs model performance, lines of
code in a notebook vs actual useful lines, how long "fine-tuning" takes
vs how long it was supposed to take, the relationship between model size
and explanability.

Rules:
- Each equation must be instantly relatable AND slightly funny
- Keep each equation under 10 words
- They should feel like facts, not jokes

Return ONLY valid JSON (no markdown fences):
{
  "equations": [
    "equation 1",
    "equation 2",
    "equation 3",
    "equation 4"
  ],
  "caption": "instagram caption — call out the most painful one, ask which hits hardest, end with exactly 10 Python/ML hashtags"
}""",
    },
}

DEFAULT_LINEUP = ["challenge", "vibe", "oneliner", "beginner", "wouldyourather"]


# ===============================
# NEW VIRAL FORMATS
# ===============================

FORMATS["ainews"] = {
    "emoji": "🚨",
    "label": "AI News",
    "tag": "TRENDING",
    "desc": "Major AI news simplified",
    "default_time": "08:00",
    "recommended": True,
}

FORMATS["hottake"] = {
    "emoji": "🔥",
    "label": "Hot Take",
    "tag": "DEBATE",
    "desc": "Controversial AI/Python opinions",
    "default_time": "20:00",
    "recommended": True,
}

FORMATS["toolbattle"] = {
    "emoji": "⚔️",
    "label": "Tool Battle",
    "tag": "VS",
    "desc": "Compare popular AI tools",
    "default_time": "16:00",
    "recommended": True,
}

FORMATS["career"] = {
    "emoji": "📈",
    "label": "Career Reality",
    "tag": "CAREER",
    "desc": "AI and Python career advice",
    "default_time": "18:00",
    "recommended": True,
}

DEFAULT_LINEUP = [
    "ainews",
    "challenge",
    "hottake",
    "oneliner",
    "wouldyourather"
]
