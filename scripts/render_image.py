"""
CodeVibes Studio — Image Renderer
Renders Instagram-ready 1080x1080 PNGs for each post format using Pillow.
Visual style: dark glassmorphism, gradient glows, bold sans-serif type,
real color emoji (via Noto Color Emoji bitmap compositing).

Usage:
    from render_image import render_post
    render_post(post_dict, "challenge", "your.handle", "output.png")
"""

import os
import re
import random
from PIL import Image, ImageDraw, ImageFont

S = 1080  # Instagram square canvas size

FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "fonts")
EMOJI_FONT_PATH = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

FORMAT_COLORS = {
    "challenge": ((124, 111, 255), (167, 139, 250)),
    "vibe": ((236, 72, 153), (249, 115, 22)),
    "oneliner": ((6, 182, 212), (16, 185, 129)),
    "wouldyourather": ((245, 158, 11), (239, 68, 68)),
    "beginner": ((16, 185, 129), (6, 182, 212)),
    "mindblown": ((139, 92, 246), (236, 72, 153)),
    "tierlist": ((249, 115, 22), (245, 158, 11)),
    "devmath": ((239, 68, 68), (249, 115, 22)),
}

TIER_COLORS = {
    "S": (255, 215, 0), "A": (16, 185, 129), "B": (124, 111, 255),
    "C": (245, 158, 11), "D": (239, 68, 68),
}


# ── FONTS ───────────────────────────────────────────────────────────

def _font(paths, size):
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def F_BOLD(size):
    return _font([
        os.path.join(FONT_DIR, "Inter-ExtraBold.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ], size)


def F_REGULAR(size):
    return _font([
        os.path.join(FONT_DIR, "Inter-Regular.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ], size)


def F_MONO(size):
    return _font([
        os.path.join(FONT_DIR, "JetBrainsMono-Regular.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ], size)


def F_MONO_BOLD(size):
    return _font([
        os.path.join(FONT_DIR, "JetBrainsMono-Bold.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    ], size)


# ── EMOJI-AWARE TEXT RENDERING ──────────────────────────────────────
# Noto Color Emoji is a fixed-size bitmap-strike (CBDT/CBLC) font, so
# Pillow can't scale it cleanly through normal draw.text(). We render
# each emoji glyph separately at native size then LANCZOS-resize it,
# compositing it inline with regular text runs.

_EMOJI_FONT_CACHE = {}
_EMOJI_GLYPH_CACHE = {}

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF"
    "\U00002B00-\U00002BFF"
    "\U0000FE0F"
    "]+",
    flags=re.UNICODE,
)


def _get_emoji_font():
    if "f" not in _EMOJI_FONT_CACHE:
        try:
            _EMOJI_FONT_CACHE["f"] = ImageFont.truetype(EMOJI_FONT_PATH, 109)
        except Exception:
            _EMOJI_FONT_CACHE["f"] = None
    return _EMOJI_FONT_CACHE["f"]


def _render_emoji_glyph(char, target_size):
    cache_key = (char, target_size)
    if cache_key in _EMOJI_GLYPH_CACHE:
        return _EMOJI_GLYPH_CACHE[cache_key]
    font = _get_emoji_font()
    if font is None:
        return None
    canvas = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    try:
        d.text((0, 0), char, font=font, embedded_color=True)
    except Exception:
        return None
    bbox = canvas.getbbox()
    if not bbox:
        return None
    canvas = canvas.crop(bbox)
    scale = target_size / max(canvas.size)
    new_size = (max(1, int(canvas.size[0] * scale)), max(1, int(canvas.size[1] * scale)))
    resized = canvas.resize(new_size, Image.LANCZOS)
    _EMOJI_GLYPH_CACHE[cache_key] = resized
    return resized


def split_text_emoji(text):
    parts, last_end = [], 0
    for m in EMOJI_PATTERN.finditer(text):
        if m.start() > last_end:
            parts.append((text[last_end:m.start()], False))
        parts.append((m.group(), True))
        last_end = m.end()
    if last_end < len(text):
        parts.append((text[last_end:], False))
    return parts if parts else [(text, False)]


def measure_mixed(draw, text, font, emoji_size=None):
    emoji_size = emoji_size or font.size
    total_w, max_h = 0, 0
    for chunk, is_emoji in split_text_emoji(text):
        if not chunk:
            continue
        if is_emoji:
            for ch in chunk:
                glyph = _render_emoji_glyph(ch, emoji_size)
                if glyph:
                    total_w += glyph.size[0] + int(emoji_size * 0.1)
                    max_h = max(max_h, glyph.size[1])
        else:
            bbox = draw.textbbox((0, 0), chunk, font=font)
            total_w += bbox[2] - bbox[0]
            max_h = max(max_h, bbox[3] - bbox[1])
    return total_w, max_h


def draw_mixed(img, draw, x, y, text, font, fill, emoji_size=None):
    """Left-aligned draw of mixed text+emoji starting at top-left (x, y). Returns width drawn."""
    emoji_size = emoji_size or int(font.size * 1.05)
    cursor_x = x
    for chunk, is_emoji in split_text_emoji(text):
        if not chunk:
            continue
        if is_emoji:
            for ch in chunk:
                glyph = _render_emoji_glyph(ch, emoji_size)
                if glyph:
                    paste_y = y - int((glyph.size[1] - font.size) * 0.18)
                    img.alpha_composite(glyph, (int(cursor_x), int(paste_y)))
                    cursor_x += glyph.size[0] + int(emoji_size * 0.1)
        else:
            draw.text((cursor_x, y), chunk, font=font, fill=fill)
            bbox = draw.textbbox((0, 0), chunk, font=font)
            cursor_x += bbox[2] - bbox[0]
    return cursor_x - x


def draw_mixed_centered(img, draw, center_x, y, text, font, fill, emoji_size=None):
    """Draw mixed text+emoji horizontally centered at center_x, top at y."""
    total_w, _ = measure_mixed(draw, text, font, emoji_size)
    draw_mixed(img, draw, center_x - total_w // 2, y, text, font, fill, emoji_size)
    return total_w


def draw_mixed_centered_block(img, draw, center_x, y, text, font, fill, emoji_size=None, line_height=None):
    """Draw single emoji centered as a standalone block (for big hero emoji)."""
    emoji_size = emoji_size or font.size
    glyph = _render_emoji_glyph(text, emoji_size)
    if glyph:
        img.alpha_composite(glyph, (center_x - glyph.size[0] // 2, y))
        return glyph.size[1]
    return 0


def wrap_mixed(text, font, max_width, draw):
    """Word-wrap mixed text+emoji to fit max_width, returns list of line strings."""
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        tw, _ = measure_mixed(draw, test, font)
        if tw > max_width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


# ── BACKGROUND / CHROME HELPERS ─────────────────────────────────────

def draw_blob(base_img, x, y, radius, color, alpha=60):
    blob_size = radius * 2
    blob = Image.new("RGBA", (blob_size, blob_size), (0, 0, 0, 0))
    bd = ImageDraw.Draw(blob)
    steps = 50
    for i in range(steps, 0, -1):
        r = int(radius * i / steps)
        a = int(alpha * (1 - i / steps) ** 1.5)
        bd.ellipse(
            [blob_size // 2 - r, blob_size // 2 - r, blob_size // 2 + r, blob_size // 2 + r],
            fill=(*color, a),
        )
    base_img.alpha_composite(blob, (x - radius, y - radius))


def draw_grain(img, density=0.012):
    px = img.load()
    w, h = img.size
    for _ in range(int(w * h * density)):
        x, y = random.randint(0, w - 1), random.randint(0, h - 1)
        a = random.randint(0, 12)
        r, g, b, _ = px[x, y]
        px[x, y] = (min(255, r + a), min(255, g + a), min(255, b + a), 255)


def syntax_color(line):
    stripped = line.strip()
    if stripped.startswith("#") or stripped.startswith("//"):
        return (90, 90, 122)
    if any(k in line for k in ["console", "print", "log"]):
        return (6, 182, 212)
    if any(k in line for k in ["const ", "let ", "var ", "def ", "return", "for ", "if ", "function"]):
        return (167, 139, 250)
    if "'" in line or '"' in line or "`" in line:
        return (16, 185, 129)
    if any(c.isdigit() for c in line):
        return (245, 158, 11)
    return (224, 222, 255)


def base_canvas(format_id):
    c1, c2 = FORMAT_COLORS.get(format_id, FORMAT_COLORS["challenge"])
    img = Image.new("RGBA", (S, S), (8, 8, 15, 255))

    grad = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    top, bottom = (8, 8, 15), (13, 12, 30)
    for y in range(S):
        t = y / S
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        gd.line([(0, y), (S, y)], fill=(r, g, b, 255))
    img.alpha_composite(grad)

    draw_blob(img, int(S * 0.15), int(S * 0.15), int(S * 0.45), c1, alpha=55)
    draw_blob(img, int(S * 0.85), int(S * 0.8), int(S * 0.4), c2, alpha=45)
    draw_blob(img, int(S * 0.5), int(S * 0.5), int(S * 0.3), c1, alpha=18)
    draw_grain(img, density=0.01)

    draw = ImageDraw.Draw(img)
    cx, cy, cw, ch = int(S * 0.05), int(S * 0.1), int(S * 0.9), int(S * 0.8)
    card = Image.new("RGBA", (cw, ch), (255, 255, 255, 10))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=36, outline=(255, 255, 255, 18), width=2)
    img.alpha_composite(card, (cx, cy))

    return img, draw, (c1, c2), (cx, cy, cw, ch)


def draw_top_bar(img, draw, format_id, handle, fmt_meta):
    c1, c2 = FORMAT_COLORS.get(format_id, FORMAT_COLORS["challenge"])
    tag = fmt_meta.get("tag", format_id.upper())
    emoji = fmt_meta.get("emoji", "")
    font = F_BOLD(26)

    label = f"{emoji} {tag}".strip()
    tw, th = measure_mixed(draw, label, font)
    pad_x, pad_y = 26, 14
    px, py = 40, 36
    pw, ph = tw + pad_x * 2, th + pad_y * 2

    pill = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle([0, 0, pw - 1, ph - 1], radius=ph // 2, fill=(*c1, 60), outline=(*c1, 130), width=2)
    img.alpha_composite(pill, (px, py))
    draw_mixed(img, draw, px + pad_x, py + pad_y, label, font, (255, 255, 255, 255))

    handle_text = f"@{handle}"
    hfont = F_MONO_BOLD(24)
    hbbox = draw.textbbox((0, 0), handle_text, font=hfont)
    hw = hbbox[2] - hbbox[0]
    draw.text((S - 40 - hw, 44), handle_text, font=hfont, fill=(*c1, 255))


def draw_bottom_bar(img, draw, format_id):
    c1, c2 = FORMAT_COLORS.get(format_id, FORMAT_COLORS["challenge"])
    bar_y = int(S * 0.955)
    overlay = Image.new("RGBA", (S, S - bar_y), (255, 255, 255, 6))
    img.alpha_composite(overlay, (0, bar_y))
    draw.line([(0, bar_y), (S, bar_y)], fill=(255, 255, 255, 14), width=2)
    mid = S // 2
    dot_y = bar_y + (S - bar_y) // 2
    for i, col in enumerate([c1, c2, (255, 255, 255)]):
        alpha = 255 if i < 2 else 70
        draw.ellipse([mid - 35 + i * 35 - 4, dot_y - 4, mid - 35 + i * 35 + 4, dot_y + 4], fill=(*col, alpha))


def render_code_block(img, draw, code_lines, box, dot_colors=None):
    bx, by, bw, bh = box
    block = Image.new("RGBA", (bw, bh), (0, 0, 0, 140))
    bd = ImageDraw.Draw(block)
    bd.rounded_rectangle([0, 0, bw - 1, bh - 1], radius=22, outline=(255, 255, 255, 16), width=2)
    img.alpha_composite(block, (bx, by))

    dots = dot_colors or [(124, 111, 255), (245, 158, 11), (16, 185, 129)]
    for i, col in enumerate(dots):
        cx_, cy_ = bx + 34 + i * 34, by + 30
        draw.ellipse([cx_ - 8, cy_ - 8, cx_ + 8, cy_ + 8], fill=(*col, 255))

    font = F_MONO(30)
    y = by + 58
    for line in code_lines:
        if y > by + bh - 30:
            break
        col = syntax_color(line)
        draw_mixed(img, draw, bx + 30, y, line[:42], font, (*col, 255))
        y += 42


# ── FORMAT RENDERERS ─────────────────────────────────────────────────

def render_challenge(post, handle, fmt_meta):
    img, draw, (c1, c2), (cx, cy, cw, ch) = base_canvas("challenge")
    draw_top_bar(img, draw, "challenge", handle, fmt_meta)
    mid = S // 2

    title = post.get("title", "what does this output? 👇")
    f_title = F_BOLD(50)
    draw_mixed_centered(img, draw, mid, cy + int(ch * 0.10), title, f_title, (255, 255, 255, 255))

    sub = post.get("sub", "")
    f_sub = F_BOLD(30)
    draw_mixed_centered(img, draw, mid, cy + int(ch * 0.19), sub, f_sub, (*c1, 255))

    code = post.get("code", "")
    box = (cx + int(cw * 0.05), cy + int(ch * 0.27), int(cw * 0.9), int(ch * 0.46))
    render_code_block(img, draw, code.split("\n"), box)

    ay = cy + int(ch * 0.82)
    pill_w, pill_h = int(cw * 0.9), int(ch * 0.1)
    pill = Image.new("RGBA", (pill_w, pill_h), (255, 255, 255, 10))
    pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle([0, 0, pill_w - 1, pill_h - 1], radius=20, outline=(*c1, 90), width=2)
    img.alpha_composite(pill, (cx + int(cw * 0.05), ay))
    f_ans = F_BOLD(26)
    draw_mixed_centered(img, draw, mid, ay + pill_h // 2 - 16, "💬 comment your answer first 👇", f_ans, (*c2, 255))

    draw_bottom_bar(img, draw, "challenge")
    return img


def render_vibe(post, handle, fmt_meta):
    img, draw, (c1, c2), (cx, cy, cw, ch) = base_canvas("vibe")
    draw_top_bar(img, draw, "vibe", handle, fmt_meta)
    mid = S // 2

    draw_mixed_centered_block(img, draw, mid, cy + int(ch * 0.13), "💀", None, None, emoji_size=110)

    title = post.get("title", "")
    f_title = F_BOLD(52)
    draw_mixed_centered(img, draw, mid, cy + int(ch * 0.34), title, f_title, (255, 255, 255, 255))

    sub = post.get("sub", "")
    f_sub = F_BOLD(30)
    draw_mixed_centered(img, draw, mid, cy + int(ch * 0.44), sub, f_sub, (*c1, 255))

    vlines = post.get("vibeLines", [])
    vby, vbh = cy + int(ch * 0.51), int(ch * 0.32)
    bubble_w = int(cw * 0.86)
    bubble = Image.new("RGBA", (bubble_w, vbh), (0, 0, 0, 100))
    bd = ImageDraw.Draw(bubble)
    bd.rounded_rectangle([0, 0, bubble_w - 1, vbh - 1], radius=24, outline=(255, 255, 255, 14), width=2)
    img.alpha_composite(bubble, (cx + int(cw * 0.07), vby))

    f_v = F_MONO(30)
    yy = vby + 28
    for line in vlines:
        if line == "":
            yy += 30
            continue
        col = c1 if line.startswith("...") else (196, 192, 255)
        draw_mixed_centered(img, draw, mid, yy, line, f_v, (*col, 255))
        yy += 44

    emojis = ["😭", "😂", "💀", "🫠"]
    start_x = mid - (len(emojis) * 88) // 2
    for i, e in enumerate(emojis):
        draw_mixed_centered_block(img, draw, start_x + i * 88 + 25, cy + int(ch * 0.88), e, None, None, emoji_size=46)

    draw_bottom_bar(img, draw, "vibe")
    return img


def render_oneliner(post, handle, fmt_meta):
    img, draw, (c1, c2), (cx, cy, cw, ch) = base_canvas("oneliner")
    draw_top_bar(img, draw, "oneliner", handle, fmt_meta)
    mid = S // 2

    title = post.get("title", "stop writing 8 lines")
    f_title = F_BOLD(46)
    draw_mixed_centered(img, draw, mid, cy + int(ch * 0.08), title, f_title, (255, 255, 255, 255))

    sub = post.get("sub", "")
    f_sub = F_BOLD(28)
    draw_mixed_centered(img, draw, mid, cy + int(ch * 0.17), sub, f_sub, (*c1, 255))

    before, after = post.get("before", ""), post.get("after", "")

    bx, bw = cx + int(cw * 0.04), int(cw * 0.92)
    before_y, before_h = cy + int(ch * 0.23), int(ch * 0.32)
    block1 = Image.new("RGBA", (bw, before_h), (0, 0, 0, 130))
    bd1 = ImageDraw.Draw(block1)
    bd1.rounded_rectangle([0, 0, bw - 1, before_h - 1], radius=20, outline=(255, 255, 255, 16), width=2)
    img.alpha_composite(block1, (bx, before_y))
    draw_mixed(img, draw, bx + 26, before_y + 18, "😩 before", F_BOLD(24), (140, 140, 170, 255))
    f_code = F_MONO(28)
    yy = before_y + 60
    for line in before.split("\n"):
        if yy > before_y + before_h - 24:
            break
        draw_mixed(img, draw, bx + 26, yy, line[:44], f_code, (138, 138, 170, 255))
        yy += 38

    arrow_y = before_y + before_h + 8
    draw_mixed_centered_block(img, draw, mid, arrow_y, "⬇️", None, None, emoji_size=46)

    after_y, after_h = arrow_y + 56, int(ch * 0.20)
    block2 = Image.new("RGBA", (bw, after_h), (0, 0, 0, 0))
    bd2 = ImageDraw.Draw(block2)
    bd2.rounded_rectangle([0, 0, bw - 1, after_h - 1], radius=20, fill=(*c1, 24), outline=(*c1, 140), width=2)
    img.alpha_composite(block2, (bx, after_y))
    draw_mixed(img, draw, bx + 26, after_y + 16, "✨ after", F_BOLD(24), (*c1, 255))
    yy = after_y + 56
    for line in after.split("\n"):
        if yy > after_y + after_h - 20:
            break
        draw_mixed(img, draw, bx + 26, yy, line[:44], f_code, (224, 222, 255, 255))
        yy += 38

    lang = post.get("lang", "JavaScript")
    f_lang = F_MONO_BOLD(24)
    bbox = draw.textbbox((0, 0), lang, font=f_lang)
    lw = bbox[2] - bbox[0]
    lang_y = cy + int(ch * 0.91)
    pill = Image.new("RGBA", (lw + 50, 50), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle([0, 0, lw + 49, 49], radius=25, fill=(*c1, 40))
    img.alpha_composite(pill, (mid - (lw + 50) // 2, lang_y))
    draw.text((mid - lw // 2, lang_y + 13), lang, font=f_lang, fill=(*c1, 255))

    draw_bottom_bar(img, draw, "oneliner")
    return img


def render_wouldyourather(post, handle, fmt_meta):
    img, draw, (c1, c2), (cx, cy, cw, ch) = base_canvas("wouldyourather")
    draw_top_bar(img, draw, "wouldyourather", handle, fmt_meta)
    mid = S // 2

    f_h = F_BOLD(28)
    draw_mixed_centered(img, draw, mid, cy + int(ch * 0.08), "WOULD YOU RATHER…", f_h, (*c1, 255))

    optA = post.get("optionA", {"emoji": "😭", "text": "Option A"})
    optB = post.get("optionB", {"emoji": "💀", "text": "Option B"})

    def draw_option(opt, oy, color):
        ox, ow, oh = cx + int(cw * 0.04), int(cw * 0.92), int(ch * 0.28)
        box = Image.new("RGBA", (ow, oh), (*color, 30))
        bd = ImageDraw.Draw(box)
        bd.rounded_rectangle([0, 0, ow - 1, oh - 1], radius=28, outline=(*color, 110), width=3)
        img.alpha_composite(box, (ox, oy))

        draw_mixed_centered_block(img, draw, mid, oy + int(oh * 0.12), opt.get("emoji", "🤔"), None, None, emoji_size=84)

        f_txt = F_BOLD(30)
        wrapped = wrap_mixed(opt.get("text", ""), f_txt, ow * 0.78, draw)
        ty = oy + int(oh * 0.62)
        for wl in wrapped:
            draw_mixed_centered(img, draw, mid, ty, wl, f_txt, (255, 255, 255, 255))
            ty += 40

    optA_y = cy + int(ch * 0.16)
    draw_option(optA, optA_y, c1)

    vs_y = optA_y + int(ch * 0.28) + 14
    vs_size = 100
    vs_circle = Image.new("RGBA", (vs_size, vs_size), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vs_circle)
    vd.ellipse([0, 0, vs_size - 1, vs_size - 1], fill=(30, 28, 45, 230), outline=(*c1, 200), width=3)
    img.alpha_composite(vs_circle, (mid - vs_size // 2, vs_y))
    f_vs = F_BOLD(36)
    bbox = draw.textbbox((0, 0), "VS", font=f_vs)
    draw.text((mid - (bbox[2] - bbox[0]) // 2, vs_y + vs_size // 2 - 22), "VS", font=f_vs, fill=(255, 255, 255, 255))

    optB_y = vs_y + 100 + 14
    draw_option(optB, optB_y, c2)

    context = post.get("context", "comment A or B 👇")
    f_ctx = F_REGULAR(26)
    draw_mixed_centered(img, draw, mid, cy + int(ch * 0.945), context, f_ctx, (110, 110, 140, 255))

    draw_bottom_bar(img, draw, "wouldyourather")
    return img


def render_beginner(post, handle, fmt_meta):
    img, draw, (c1, c2), (cx, cy, cw, ch) = base_canvas("beginner")
    draw_top_bar(img, draw, "beginner", handle, fmt_meta)
    mid = S // 2

    f_h = F_BOLD(28)
    draw_mixed_centered(img, draw, mid, cy + int(ch * 0.07), "🔰  BEGINNER CORNER", f_h, (*c1, 255))

    title = post.get("title", "")
    f_title = F_BOLD(46)
    wrapped = wrap_mixed(title, f_title, cw * 0.8, draw)
    ty = cy + int(ch * 0.15)
    for wl in wrapped:
        draw_mixed_centered(img, draw, mid, ty, wl, f_title, (255, 255, 255, 255))
        ty += 56

    sub = post.get("sub", "")
    f_sub = F_BOLD(28)
    draw_mixed_centered(img, draw, mid, ty + 6, sub, f_sub, (*c2, 255))

    analogy = post.get("analogy", "")
    apy, apw = ty + 60, int(cw * 0.82)
    apill = Image.new("RGBA", (apw, 64), (0, 0, 0, 0))
    ad = ImageDraw.Draw(apill)
    ad.rounded_rectangle([0, 0, apw - 1, 63], radius=20, fill=(*c1, 28), outline=(*c1, 90), width=2)
    img.alpha_composite(apill, (mid - apw // 2, apy))
    f_an = F_BOLD(26)
    draw_mixed_centered(img, draw, mid, apy + 18, analogy, f_an, (*c1, 255))

    steps = post.get("steps", [])
    sy = apy + 100
    f_num, f_step = F_BOLD(26), F_REGULAR(27)
    for i, step in enumerate(steps):
        if sy > cy + int(ch * 0.92):
            break
        circle_x = cx + int(cw * 0.1)
        circle_d = 52
        circle_img = Image.new("RGBA", (circle_d, circle_d), (0, 0, 0, 0))
        circ_d = ImageDraw.Draw(circle_img)
        circ_d.ellipse([0, 0, circle_d - 1, circle_d - 1], fill=(*c2, 60), outline=(*c2, 180), width=2)
        img.alpha_composite(circle_img, (circle_x - circle_d // 2, sy - circle_d // 2))
        num_text = str(i + 1)
        bbox = draw.textbbox((0, 0), num_text, font=f_num)
        draw.text((circle_x - (bbox[2] - bbox[0]) // 2, sy - (bbox[3] - bbox[1]) // 2 - 4),
                   num_text, font=f_num, fill=(*c2, 255))
        step_text = step if len(step) <= 46 else step[:46].rsplit(" ", 1)[0]
        draw_mixed(img, draw, circle_x + 50, sy - 16, step_text, f_step, (224, 222, 255, 255))
        sy += 76

    draw_bottom_bar(img, draw, "beginner")
    return img


def render_mindblown(post, handle, fmt_meta):
    img, draw, (c1, c2), (cx, cy, cw, ch) = base_canvas("mindblown")
    draw_top_bar(img, draw, "mindblown", handle, fmt_meta)
    mid = S // 2

    draw_mixed_centered_block(img, draw, mid, cy + int(ch * 0.13), "🤯", None, None, emoji_size=110)

    f_label = F_BOLD(28)
    draw_mixed_centered(img, draw, mid, cy + int(ch * 0.31), "MIND = BLOWN", f_label, (*c1, 255))

    fact = post.get("fact", "")
    f_fact = F_BOLD(38)
    wrapped = wrap_mixed(fact, f_fact, cw * 0.84, draw)
    fy = cy + int(ch * 0.40)
    for wl in wrapped:
        draw_mixed_centered(img, draw, mid, fy, wl, f_fact, (255, 255, 255, 255))
        fy += 50

    followup = post.get("followup", "")
    f_fu = F_REGULAR(27)
    wrapped2 = wrap_mixed(followup, f_fu, cw * 0.78, draw)
    fy += 16
    for wl in wrapped2:
        draw_mixed_centered(img, draw, mid, fy, wl, f_fu, (140, 140, 176, 255))
        fy += 38

    deeper = post.get("deeper", "")
    f_dp = F_REGULAR(25)
    draw_mixed_centered(img, draw, mid, fy + 16, deeper, f_dp, (*c2, 255))

    cta_y = cy + int(ch * 0.85)
    cta_w, cta_h = int(cw * 0.8), 60
    cta = Image.new("RGBA", (cta_w, cta_h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cta)
    cd.rounded_rectangle([0, 0, cta_w - 1, cta_h - 1], radius=18, fill=(*c1, 50))
    img.alpha_composite(cta, (cx + int(cw * 0.1), cta_y))
    f_cta = F_BOLD(25)
    draw_mixed_centered(img, draw, mid, cta_y + 17, "share with someone 👇", f_cta, (*c1, 255))

    draw_bottom_bar(img, draw, "mindblown")
    return img


def render_tierlist(post, handle, fmt_meta):
    img, draw, (c1, c2), (cx, cy, cw, ch) = base_canvas("tierlist")
    draw_top_bar(img, draw, "tierlist", handle, fmt_meta)
    mid = S // 2

    f_h = F_BOLD(28)
    draw_mixed_centered(img, draw, mid, cy + int(ch * 0.06), "🏆 TIER LIST", f_h, (*c1, 255))

    topic = post.get("topic", "")
    f_topic = F_BOLD(42)
    draw_mixed_centered(img, draw, mid, cy + int(ch * 0.13), topic, f_topic, (255, 255, 255, 255))

    tiers = post.get("tiers", {})
    ty, row_h = cy + int(ch * 0.23), int(ch * 0.12)
    f_tier, f_item = F_BOLD(38), F_REGULAR(27)

    for tier_label, items in tiers.items():
        col = TIER_COLORS.get(tier_label, c1)
        row_w, row_h2 = int(cw * 0.94), int(row_h * 0.85)
        row = Image.new("RGBA", (row_w, row_h2), (*col, 35))
        rd = ImageDraw.Draw(row)
        rd.rounded_rectangle([0, 0, row_w - 1, row_h2 - 1], radius=16, outline=(*col, 90), width=2)
        img.alpha_composite(row, (cx + int(cw * 0.03), ty))

        draw.text((cx + int(cw * 0.03) + 30, ty + row_h2 // 2 - 24), tier_label, font=f_tier, fill=(*col, 255))
        items_text = "  ·  ".join(items)
        draw.text((cx + int(cw * 0.03) + 110, ty + row_h2 // 2 - 16), items_text[:38], font=f_item, fill=(224, 222, 255, 255))

        ty += row_h

    f_f = F_REGULAR(25)
    draw_mixed_centered(img, draw, mid, cy + int(ch * 0.93), "drop your tier list 👇 let's fight", f_f, (110, 110, 140, 255))

    draw_bottom_bar(img, draw, "tierlist")
    return img


def render_devmath(post, handle, fmt_meta):
    img, draw, (c1, c2), (cx, cy, cw, ch) = base_canvas("devmath")
    draw_top_bar(img, draw, "devmath", handle, fmt_meta)
    mid = S // 2

    f_h = F_BOLD(28)
    draw_mixed_centered(img, draw, mid, cy + int(ch * 0.06), "💸 DEV MATH", f_h, (*c1, 255))

    f_title = F_BOLD(36)
    for i, line in enumerate(["math they don't teach", "in CS class 📐"]):
        draw_mixed_centered(img, draw, mid, cy + int(ch * 0.14) + i * 46, line, f_title, (255, 255, 255, 255))

    equations = post.get("equations", [])
    ey, row_h = cy + int(ch * 0.32), int(ch * 0.155)
    f_eq = F_MONO_BOLD(28)
    for i, eq in enumerate(equations):
        col = c1 if i % 2 == 0 else c2
        box_w, box_h = int(cw * 0.9), int(row_h * 0.82)
        box = Image.new("RGBA", (box_w, box_h), (255, 255, 255, 10 if i % 2 == 0 else 6))
        bd = ImageDraw.Draw(box)
        bd.rounded_rectangle([0, 0, box_w - 1, box_h - 1], radius=16, outline=(*col, 50), width=2)
        img.alpha_composite(box, (cx + int(cw * 0.05), ey))

        wrapped = wrap_mixed(eq, f_eq, cw * 0.78, draw)
        ty = ey + box_h // 2 - (len(wrapped) * 36) // 2
        for wl in wrapped:
            draw_mixed_centered(img, draw, mid, ty, wl, f_eq, (224, 222, 255, 255))
            ty += 36

        ey += row_h

    draw_bottom_bar(img, draw, "devmath")
    return img


RENDERERS = {
    "challenge": render_challenge,
    "vibe": render_vibe,
    "oneliner": render_oneliner,
    "wouldyourather": render_wouldyourather,
    "beginner": render_beginner,
    "mindblown": render_mindblown,
    "tierlist": render_tierlist,
    "devmath": render_devmath,
}


def render_post(post, format_id, handle, output_path, fmt_meta=None):
    """
    Render a single post to a 1080x1080 PNG.

    post: dict with format-specific fields (title, code, caption, etc.)
    format_id: one of the keys in RENDERERS
    handle: instagram handle string (without @)
    output_path: where to save the PNG
    fmt_meta: optional dict with 'emoji' and 'tag' (else loaded from config/formats.py)
    """
    renderer = RENDERERS.get(format_id)
    if renderer is None:
        raise ValueError(f"Unknown format_id: {format_id}")

    meta = fmt_meta or {}
    if "emoji" not in meta or "tag" not in meta:
        try:
            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))
            from formats import FORMATS as F
            meta = {**F.get(format_id, {}), **meta}
        except ImportError:
            meta.setdefault("emoji", "✨")
            meta.setdefault("tag", format_id.upper())

    img = renderer(post, handle, meta)
    img.convert("RGB").save(output_path, "PNG", quality=95)
    return output_path


if __name__ == "__main__":
    samples = {
        "challenge": {
            "title": "what does this output? 👇", "sub": "90% get this wrong 😈",
            "code": "const x = [1, 2, 3]\nconst y = x\ny.push(4)\nconsole.log(x.length)",
        },
        "vibe": {
            "title": "me reviewing my own PR", "sub": "after 2 weeks away 💀",
            "vibeLines": ["who wrote this??", "", "...git blame...", "", "oh no"],
        },
        "oneliner": {
            "title": "stop writing 8 lines", "sub": "this does it in ONE ⚡", "lang": "JavaScript",
            "before": "// 😩 old way\nlet max = nums[0]\nfor (let i=1;i<nums.length;i++){\n  if (nums[i]>max) max=nums[i]\n}",
            "after": "// ✨ one liner\nconst max = Math.max(...nums)",
        },
        "wouldyourather": {
            "optionA": {"emoji": "😭", "text": "debug with no Stack Overflow"},
            "optionB": {"emoji": "💀", "text": "code forever with no autocomplete"},
            "context": "both are cursed. choose wisely.",
        },
        "beginner": {
            "title": "what even IS an API?", "sub": "explained in 30 seconds 🔰",
            "analogy": "API = a waiter at a restaurant",
            "steps": ["you (the app) want food (data)", "the waiter (API) takes your order", "kitchen (server) makes it", "waiter brings it back to you", "you never enter the kitchen 🍽️"],
        },
        "mindblown": {
            "fact": "Python was named after Monty Python, not the snake",
            "followup": "Guido van Rossum wrote it while reading MP scripts",
            "deeper": "The snake logo came years later",
        },
        "tierlist": {
            "topic": "CSS Frameworks",
            "tiers": {"S": ["Tailwind"], "A": ["Bootstrap"], "B": ["Bulma", "Foundation"], "C": ["Pure CSS"], "D": ["3am custom CSS"]},
        },
        "devmath": {
            "equations": ["1 hour estimate = 3 days actual", "10 min fix = new bug created", "works locally = broken in prod", "final_v2 + 1 = final_FINAL_v2_REAL"],
        },
    }
    out_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(out_dir, exist_ok=True)
    for fmt_id, post in samples.items():
        path = os.path.join(out_dir, f"sample_{fmt_id}.png")
        render_post(post, fmt_id, "codevibes.dev", path)
        print(f"✅ {fmt_id} -> {path}")
