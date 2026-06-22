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

    # ── Titles
    title = post.get("title", "what does this output? 👇")
    f_title = F_BOLD(50)
    tl_lines = wrap_mixed(title, f_title, cw * 0.88, draw)
    ty = cy + int(ch * 0.09)
    for tl in tl_lines:
        draw_mixed_centered(img, draw, mid, ty, tl, f_title, (255, 255, 255, 255))
        ty += 58
    sub = post.get("sub", "")
    f_sub = F_BOLD(29)
    draw_mixed_centered(img, draw, mid, ty + 2, sub, f_sub, (*c1, 255))
    header_bottom = ty + 44

    # ── Code block: size dynamically from line count
    code_lines = [l for l in post.get("code", "").split("\n")]
    CODE_LINE_H, DOT_H, PAD_TOP, PAD_BOT = 42, 50, 16, 16
    block_h = DOT_H + PAD_TOP + len(code_lines) * CODE_LINE_H + PAD_BOT
    # Clamp so it doesn't overflow into the CTA
    CTA_H, CTA_GAP, BOTTOM_GAP = 80, 14, 12
    max_block_h = (cy + ch) - header_bottom - CTA_H - CTA_GAP - BOTTOM_GAP - 8
    if block_h > max_block_h:
        block_h = max_block_h

    bx, bw = cx + int(cw * 0.04), int(cw * 0.92)
    # Stretch block to fill available space (no dead gap)
    stretch_h = (cy + ch) - header_bottom - CTA_H - CTA_GAP - BOTTOM_GAP - 8 - 8
    block_h = max(block_h, stretch_h)
    block_y = header_bottom + 8
    blk = Image.new("RGBA", (bw, block_h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(blk)
    bd.rounded_rectangle([0, 0, bw-1, block_h-1], radius=20,
                          fill=(0, 0, 0, 140), outline=(255, 255, 255, 16), width=2)
    img.alpha_composite(blk, (bx, block_y))

    dots = [(c1, (124,111,255)), ((245,158,11),(245,158,11)), ((16,185,129),(16,185,129))]
    for i, (col, _) in enumerate(dots):
        dx, dy = bx + 34 + i * 34, block_y + 26
        draw.ellipse([dx-8, dy-8, dx+8, dy+8], fill=(*col, 255))

    f_code = F_MONO(30)
    yy = block_y + DOT_H + PAD_TOP
    for line in code_lines:
        if yy > block_y + block_h - PAD_BOT - 4:
            break
        col = syntax_color(line)
        draw_mixed(img, draw, bx + 28, yy, line[:42], f_code, (*col, 255))
        yy += CODE_LINE_H

    # ── CTA pill anchored above bottom bar
    cta_y = (cy + ch) - CTA_H - BOTTOM_GAP
    pill = Image.new("RGBA", (bw, CTA_H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle([0, 0, bw-1, CTA_H-1], radius=22,
                          fill=(255, 255, 255, 8), outline=(*c1, 100), width=2)
    img.alpha_composite(pill, (bx, cta_y))
    f_ans = F_BOLD(26)
    draw_mixed_centered(img, draw, mid, cta_y + CTA_H//2 - 18,
                        "💬 comment your answer first 👇", f_ans, (*c2, 255))

    draw_bottom_bar(img, draw, "challenge")
    return img


def render_vibe(post, handle, fmt_meta):
    img, draw, (c1, c2), (cx, cy, cw, ch) = base_canvas("vibe")
    draw_top_bar(img, draw, "vibe", handle, fmt_meta)
    mid = S // 2

    # Big skull centered, with a subtle glow halo
    skull_y = cy + int(ch * 0.09)
    skull_size = 104
    glow = ctx_glow = Image.new("RGBA", (skull_size + 40, skull_size + 40), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([0, 0, skull_size + 39, skull_size + 39], fill=(*c1, 22))
    img.alpha_composite(glow, (mid - (skull_size + 40)//2, skull_y - 20))
    draw_mixed_centered_block(img, draw, mid, skull_y, "💀", None, None, emoji_size=skull_size)

    title = post.get("title", "")
    f_title = F_BOLD(52)
    t_lines = wrap_mixed(title, f_title, cw * 0.86, draw)
    ty = skull_y + skull_size + 18
    for tl in t_lines:
        draw_mixed_centered(img, draw, mid, ty, tl, f_title, (255, 255, 255, 255))
        ty += 60

    sub = post.get("sub", "")
    f_sub = F_BOLD(29)
    draw_mixed_centered(img, draw, mid, ty + 4, sub, f_sub, (*c1, 255))
    bubble_top = ty + 50

    # ── Text bubble: left-aligned text for readability
    vlines = post.get("vibeLines", [])
    LINE_H = 46
    EMOJI_ROW_H = 70   # emoji row + bottom margin
    max_bubble_h = (cy + ch) - bubble_top - EMOJI_ROW_H - 12
    bubble_content_h = sum(LINE_H if l else 22 for l in vlines)
    # Stretch to fill available space — no dead gap
    bubble_h = max(bubble_content_h + 32, max_bubble_h)
    bubble_h = min(bubble_h, max_bubble_h)
    bubble_w = int(cw * 0.88)

    bubble = Image.new("RGBA", (bubble_w, bubble_h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bubble)
    bd.rounded_rectangle([0, 0, bubble_w-1, bubble_h-1], radius=20,
                          fill=(0, 0, 0, 100), outline=(255, 255, 255, 12), width=1)
    img.alpha_composite(bubble, (cx + int(cw * 0.06), bubble_top))

    f_v = F_MONO(30)
    # Left-align inside bubble for better code/text readability
    text_lx = cx + int(cw * 0.06) + 24
    yy = bubble_top + 16
    for line in vlines:
        if yy > bubble_top + bubble_h - 12:
            break
        if line == "":
            yy += 22
            continue
        col = c1 if line.startswith("...") else (210, 206, 255)
        draw_mixed(img, draw, text_lx, yy, line, f_v, (*col, 255))
        yy += LINE_H

    # ── Reaction emojis row — anchored 14px above bottom bar
    emojis = ["😭", "😂", "💀", "🫠"]
    emoji_y = (cy + ch) - 58
    ex = mid - (len(emojis) * 86) // 2
    for i, e in enumerate(emojis):
        draw_mixed_centered_block(img, draw, ex + i * 86 + 30, emoji_y, e, None, None, emoji_size=44)

    draw_bottom_bar(img, draw, "vibe")
    return img


def _wrap_code_line(line, max_chars=38):
    """Wrap a long code line at natural break points (spaces/operators)."""
    if len(line) <= max_chars:
        return [line]
    leading = len(line) - len(line.lstrip())
    cont_indent = " " * (leading + 2)
    BREAK_CHARS = [" ", ",", ".", "(", "[", "+", "|", "="]
    result = []
    current = line
    while len(current) > max_chars:
        budget = max_chars if not result else max(20, max_chars - len(cont_indent))
        segment = current[:budget]
        best_break = -1
        for ch in BREAK_CHARS:
            pos = segment.rfind(ch)
            if pos > max(5, len(cont_indent) + 4):
                best_break = max(best_break, pos + (1 if ch == " " else 0))
        if best_break > 0:
            result.append(current[:best_break])
            current = cont_indent + current[best_break:].lstrip(" ")
        else:
            result.append(current[:budget])
            current = cont_indent + current[budget:]
    if current:
        result.append(current)
    return result


def _expand_code_lines(raw_code, max_chars=38):
    result = []
    for line in raw_code.split("\n"):
        result.extend(_wrap_code_line(line, max_chars))
    return result


def render_oneliner(post, handle, fmt_meta):
    img, draw, (c1, c2), (cx, cy, cw, ch) = base_canvas("oneliner")
    draw_top_bar(img, draw, "oneliner", handle, fmt_meta)
    mid = S // 2

    # ── Header
    title = post.get("title", "stop writing 8 lines")
    f_title = F_BOLD(44)
    tl_lines = wrap_mixed(title, f_title, cw * 0.88, draw)
    ty = cy + int(ch * 0.07)
    for tl in tl_lines:
        draw_mixed_centered(img, draw, mid, ty, tl, f_title, (255, 255, 255, 255))
        ty += 54
    sub = post.get("sub", "")
    f_sub = F_BOLD(27)
    draw_mixed_centered(img, draw, mid, ty + 4, sub, f_sub, (*c1, 255))
    header_bottom = ty + 44

    # ── Measure both code blocks
    before_raw = post.get("before", "")
    after_raw  = post.get("after", "")
    before_lines = _expand_code_lines(before_raw, 38)
    after_lines  = _expand_code_lines(after_raw,  38)

    LABEL_H, CODE_H, PAD = 44, 34, 14
    ARROW_H, LANG_H = 52, 56
    BMARGIN = 12

    before_h = LABEL_H + len(before_lines) * CODE_H + PAD
    after_h  = LABEL_H + len(after_lines)  * CODE_H + PAD
    available = (cy + ch) - header_bottom - ARROW_H - LANG_H - BMARGIN - 16
    total = before_h + after_h
    if total > available:
        ratio = available / total
        before_h = max(80, int(before_h * ratio))
        after_h  = max(60, int(after_h  * ratio))
        CODE_H   = max(26, int(CODE_H * ratio))

    bx = cx + int(cw * 0.04)
    bw = int(cw * 0.92)

    # ── Before block
    before_y = header_bottom + 8
    blk1 = Image.new("RGBA", (bw, before_h), (0, 0, 0, 0))
    bd1  = ImageDraw.Draw(blk1)
    bd1.rounded_rectangle([0, 0, bw-1, before_h-1], radius=18,
                           fill=(0, 0, 0, 130), outline=(255, 255, 255, 14), width=1)
    img.alpha_composite(blk1, (bx, before_y))
    draw_mixed(img, draw, bx + 24, before_y + 14, "😩 before", F_BOLD(22), (130, 130, 165, 255))
    f_code = F_MONO(26)
    yy = before_y + LABEL_H
    for line in before_lines:
        if yy > before_y + before_h - 8:
            break
        draw_mixed(img, draw, bx + 24, yy, line, f_code, (130, 130, 165, 255))
        yy += CODE_H

    # ── Arrow
    arrow_y = before_y + before_h + 6
    draw_mixed_centered_block(img, draw, mid, arrow_y + 2, "⬇️", None, None, emoji_size=38)

    # ── After block
    after_y = arrow_y + ARROW_H
    blk2 = Image.new("RGBA", (bw, after_h), (0, 0, 0, 0))
    bd2  = ImageDraw.Draw(blk2)
    bd2.rounded_rectangle([0, 0, bw-1, after_h-1], radius=18,
                           fill=(*c1, 20), outline=(*c1, 160), width=2)
    img.alpha_composite(blk2, (bx, after_y))
    draw_mixed(img, draw, bx + 24, after_y + 14, "✨ after", F_BOLD(22), (*c1, 255))
    yy = after_y + LABEL_H
    for line in after_lines:
        if yy > after_y + after_h - 8:
            break
        draw_mixed(img, draw, bx + 24, yy, line, f_code, (224, 222, 255, 255))
        yy += CODE_H

    # ── Lang badge
    lang = post.get("lang", "Python")
    f_lang = F_MONO_BOLD(23)
    bbox  = draw.textbbox((0, 0), lang, font=f_lang)
    lw    = bbox[2] - bbox[0]
    lang_y = after_y + after_h + 14
    pw, ph = lw + 50, 44
    pill = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle([0, 0, pw-1, ph-1], radius=22, fill=(*c1, 40))
    img.alpha_composite(pill, (mid - pw//2, lang_y))
    draw.text((mid - lw//2, lang_y + 10), lang, font=f_lang, fill=(*c1, 255))

    draw_bottom_bar(img, draw, "oneliner")
    return img


def render_wouldyourather(post, handle, fmt_meta):
    img, draw, (c1, c2), (cx, cy, cw, ch) = base_canvas("wouldyourather")
    draw_top_bar(img, draw, "wouldyourather", handle, fmt_meta)
    mid = S // 2

    # ── Header label
    f_h = F_BOLD(28)
    draw_mixed_centered(img, draw, mid, cy + int(ch * 0.07), "WOULD YOU RATHER…", f_h, (*c1, 255))

    optA = post.get("optionA", {"emoji": "😭", "text": "Option A"})
    optB = post.get("optionB", {"emoji": "💀", "text": "Option B"})

    # ── Fixed layout constants so both boxes are equal height
    VS_D    = 88        # VS circle diameter
    CTXT_H  = 50        # height for context text at bottom
    GAP_TOP = 12        # gap between header and option A
    GAP_VS  = 10        # gap between option A and VS
    GAP_B   = 10        # gap between VS and option B
    GAP_CTX = 8         # gap between option B and context

    available = (cy + ch) - (cy + int(ch * 0.07) + 36) - GAP_TOP - VS_D - GAP_VS - GAP_B - GAP_CTX - CTXT_H - 16
    opt_h = available // 2  # both options same height

    # Clamp to sensible min/max
    opt_h = max(180, min(opt_h, 260))

    EMOJI_SZ = min(74, opt_h // 2)
    ow = int(cw * 0.92)
    ox = cx + int(cw * 0.04)

    optA_y = cy + int(ch * 0.07) + 40 + GAP_TOP

    def draw_option(opt, oy, color):
        box = Image.new("RGBA", (ow, opt_h), (0, 0, 0, 0))
        bd  = ImageDraw.Draw(box)
        bd.rounded_rectangle([0, 0, ow-1, opt_h-1], radius=22,
                               fill=(*color, 28), outline=(*color, 130), width=2)
        img.alpha_composite(box, (ox, oy))
        # Emoji vertically centered in top half
        emoji_center_y = oy + opt_h // 4
        draw_mixed_centered_block(img, draw, mid, emoji_center_y - EMOJI_SZ//2,
                                  opt.get("emoji", "🤔"), None, None, emoji_size=EMOJI_SZ)
        # Text vertically centered in bottom half
        f_txt = F_BOLD(29)
        wrapped = wrap_mixed(opt.get("text", ""), f_txt, ow * 0.80, draw)
        total_th = len(wrapped) * 38
        ty = oy + opt_h // 2 + (opt_h // 2 - total_th) // 2
        for wl in wrapped:
            draw_mixed_centered(img, draw, mid, ty, wl, f_txt, (255, 255, 255, 255))
            ty += 38

    draw_option(optA, optA_y, c1)

    vs_y = optA_y + opt_h + GAP_VS
    vs_circle = Image.new("RGBA", (VS_D, VS_D), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vs_circle)
    vd.ellipse([0, 0, VS_D-1, VS_D-1], fill=(22, 20, 38, 235), outline=(*c1, 210), width=3)
    img.alpha_composite(vs_circle, (mid - VS_D//2, vs_y))
    f_vs = F_BOLD(34)
    bbox = draw.textbbox((0, 0), "VS", font=f_vs)
    draw.text((mid - (bbox[2]-bbox[0])//2, vs_y + VS_D//2 - (bbox[3]-bbox[1])//2 - 2),
              "VS", font=f_vs, fill=(255, 255, 255, 255))

    optB_y = vs_y + VS_D + GAP_B
    draw_option(optB, optB_y, c2)

    context = post.get("context", "comment A or B 👇")
    f_ctx = F_REGULAR(25)
    ctx_y = optB_y + opt_h + GAP_CTX
    draw_mixed_centered(img, draw, mid, ctx_y + 8, context, f_ctx, (120, 118, 148, 255))

    draw_bottom_bar(img, draw, "wouldyourather")
    return img


def render_beginner(post, handle, fmt_meta):
    img, draw, (c1, c2), (cx, cy, cw, ch) = base_canvas("beginner")
    draw_top_bar(img, draw, "beginner", handle, fmt_meta)
    mid = S // 2

    # ── Header section
    f_h = F_BOLD(27)
    draw_mixed_centered(img, draw, mid, cy + int(ch * 0.06), "🔰  BEGINNER CORNER", f_h, (*c1, 255))

    title = post.get("title", "")
    f_title = F_BOLD(44)
    t_wrapped = wrap_mixed(title, f_title, cw * 0.84, draw)
    ty = cy + int(ch * 0.13)
    for tl in t_wrapped:
        draw_mixed_centered(img, draw, mid, ty, tl, f_title, (255, 255, 255, 255))
        ty += 54

    sub = post.get("sub", "")
    f_sub = F_BOLD(27)
    draw_mixed_centered(img, draw, mid, ty + 4, sub, f_sub, (*c2, 255))
    analogy_top = ty + 50

    # ── Analogy pill
    analogy = post.get("analogy", "")
    apw = int(cw * 0.86)
    aph = 58
    apill = Image.new("RGBA", (apw, aph), (0, 0, 0, 0))
    ad = ImageDraw.Draw(apill)
    ad.rounded_rectangle([0, 0, apw-1, aph-1], radius=20,
                          fill=(*c1, 25), outline=(*c1, 100), width=2)
    img.alpha_composite(apill, (mid - apw//2, analogy_top))
    f_an = F_BOLD(25)
    draw_mixed_centered(img, draw, mid, analogy_top + aph//2 - 16, analogy, f_an, (*c1, 255))

    # ── Steps: distribute evenly in remaining space
    steps = post.get("steps", [])
    steps_top = analogy_top + aph + 16
    steps_bottom = (cy + ch) - 14  # right to the bottom of card
    available_h = steps_bottom - steps_top
    step_slot = available_h // max(len(steps), 1) if steps else 72
    step_slot = max(56, min(step_slot, 90))

    f_num  = F_BOLD(24)
    f_step = F_REGULAR(25)
    text_x = cx + int(cw * 0.1) + 44
    max_tw = cx + cw - text_x - 28

    for i, step in enumerate(steps):
        sy = steps_top + i * step_slot + step_slot // 2
        if sy > steps_bottom - 16:
            break

        circ_x = cx + int(cw * 0.1)
        CIRC = 46
        circle_img = Image.new("RGBA", (CIRC, CIRC), (0, 0, 0, 0))
        cd = ImageDraw.Draw(circle_img)
        cd.ellipse([0, 0, CIRC-1, CIRC-1], fill=(*c2, 55), outline=(*c2, 180), width=2)
        img.alpha_composite(circle_img, (circ_x - CIRC//2, sy - CIRC//2))
        num_text = str(i + 1)
        bbox = draw.textbbox((0, 0), num_text, font=f_num)
        draw.text((circ_x - (bbox[2]-bbox[0])//2, sy - (bbox[3]-bbox[1])//2 - 2),
                   num_text, font=f_num, fill=(*c2, 255))

        wrapped_step = wrap_mixed(step, f_step, max_tw, draw)
        block_h = len(wrapped_step) * 32
        text_top = sy - block_h // 2
        for j, line in enumerate(wrapped_step):
            draw_mixed(img, draw, text_x, text_top + j * 32, line, f_step, (224, 222, 255, 255))

    draw_bottom_bar(img, draw, "beginner")
    return img


def render_mindblown(post, handle, fmt_meta):
    img, draw, (c1, c2), (cx, cy, cw, ch) = base_canvas("mindblown")
    draw_top_bar(img, draw, "mindblown", handle, fmt_meta)
    mid = S // 2

    # Pre-measure to centre content vertically in the card
    f_fact = F_BOLD(38)
    f_fu   = F_REGULAR(26)
    f_dp   = F_REGULAR(24)

    fact     = post.get("fact", "")
    followup = post.get("followup", "")
    deeper   = post.get("deeper", "")

    fact_lines = wrap_mixed(fact, f_fact, cw * 0.86, draw)
    fu_lines   = wrap_mixed(followup, f_fu, cw * 0.80, draw)
    dp_lines   = wrap_mixed(deeper, f_dp, cw * 0.78, draw)

    EMOJI_H  = 96
    LABEL_H  = 30
    CTA_H    = 56

    # Measure total content height
    total_h = (EMOJI_H + 10 + LABEL_H + 14
               + len(fact_lines) * 50
               + 16 + len(fu_lines) * 34
               + 12 + len(dp_lines) * 30
               + 24 + CTA_H)

    # Vertically centre with 40% top bias
    start_y = cy + int((ch - total_h) * 0.40)
    start_y = max(cy + 14, start_y)

    y = start_y
    draw_mixed_centered_block(img, draw, mid, y, "🤯", None, None, emoji_size=EMOJI_H)
    y += EMOJI_H + 10

    f_label = F_BOLD(26)
    draw_mixed_centered(img, draw, mid, y, "MIND = BLOWN", f_label, (*c1, 255))
    y += LABEL_H + 14

    for wl in fact_lines:
        draw_mixed_centered(img, draw, mid, y, wl, f_fact, (255, 255, 255, 255))
        y += 50

    y += 16
    for wl in fu_lines:
        draw_mixed_centered(img, draw, mid, y, wl, f_fu, (145, 143, 180, 255))
        y += 34

    y += 12
    for wl in dp_lines:
        draw_mixed_centered(img, draw, mid, y, wl, f_dp, (*c2, 255))
        y += 30

    # CTA immediately below content
    cta_y = y + 24
    cta_y = min(cta_y, (cy + ch) - CTA_H - 16)
    CTA_W = int(cw * 0.82)
    cta = Image.new("RGBA", (CTA_W, CTA_H), (0, 0, 0, 0))
    cd  = ImageDraw.Draw(cta)
    cd.rounded_rectangle([0, 0, CTA_W-1, CTA_H-1], radius=20,
                          fill=(*c1, 45), outline=(*c1, 130), width=1)
    img.alpha_composite(cta, (mid - CTA_W//2, cta_y))
    f_cta = F_BOLD(24)
    draw_mixed_centered(img, draw, mid, cta_y + CTA_H//2 - 16,
                        "share with someone 👇", f_cta, (*c1, 255))

    draw_bottom_bar(img, draw, "mindblown")
    return img


def render_tierlist(post, handle, fmt_meta):
    img, draw, (c1, c2), (cx, cy, cw, ch) = base_canvas("tierlist")
    draw_top_bar(img, draw, "tierlist", handle, fmt_meta)
    mid = S // 2

    # ── Header
    f_h = F_BOLD(27)
    draw_mixed_centered(img, draw, mid, cy + int(ch * 0.06), "🏆 TIER LIST", f_h, (*c1, 255))

    topic = post.get("topic", "")
    f_topic = F_BOLD(40)
    t_lines = wrap_mixed(topic, f_topic, cw * 0.88, draw)
    ty = cy + int(ch * 0.13)
    for tl in t_lines:
        draw_mixed_centered(img, draw, mid, ty, tl, f_topic, (255, 255, 255, 255))
        ty += 48
    rows_top = ty + 10

    # ── Rows: dynamically sized to fill card
    tiers = post.get("tiers", {})
    n = len(tiers)
    FOOTER_H = 48
    rows_bottom = (cy + ch) - FOOTER_H - 8
    available_h = rows_bottom - rows_top
    # Stretch to fill all space — no unused gap
    row_slot = available_h // n if n else 80
    row_slot = max(62, row_slot)
    GAP = 6
    row_h = row_slot - GAP

    f_tier = F_BOLD(36)
    f_item = F_REGULAR(26)

    for i, (tier_label, items) in enumerate(tiers.items()):
        col  = TIER_COLORS.get(tier_label, c1)
        rw   = int(cw * 0.92)
        ry   = rows_top + i * row_slot
        # Draw row with proper rounded corners using composited layer
        row_img = Image.new("RGBA", (rw, row_h), (0, 0, 0, 0))
        rd = ImageDraw.Draw(row_img)
        rd.rounded_rectangle([0, 0, rw-1, row_h-1], radius=14,
                               fill=(*col, 32), outline=(*col, 100), width=2)
        img.alpha_composite(row_img, (cx + int(cw * 0.04), ry))

        # Tier letter
        bbox = draw.textbbox((0, 0), tier_label, font=f_tier)
        lh = bbox[3] - bbox[1]
        draw.text((cx + int(cw * 0.04) + 22, ry + row_h//2 - lh//2 - 2),
                   tier_label, font=f_tier, fill=(*col, 255))

        # Items text with separator dots
        items_text = "  ·  ".join(items)
        # Truncate to fit — use wrap then take first line
        it_lines = wrap_mixed(items_text, f_item, rw - 110, draw)
        it_text  = it_lines[0] if it_lines else items_text
        bbox2 = draw.textbbox((0, 0), it_text, font=f_item)
        ih = bbox2[3] - bbox2[1]
        draw.text((cx + int(cw * 0.04) + 90, ry + row_h//2 - ih//2 - 2),
                   it_text, font=f_item, fill=(224, 222, 255, 255))

    # ── Footer
    f_f = F_REGULAR(24)
    draw_mixed_centered(img, draw, mid, rows_bottom + 12,
                        "drop your tier list 👇 let's fight", f_f, (110, 110, 145, 255))

    draw_bottom_bar(img, draw, "tierlist")
    return img


def render_devmath(post, handle, fmt_meta):
    img, draw, (c1, c2), (cx, cy, cw, ch) = base_canvas("devmath")
    draw_top_bar(img, draw, "devmath", handle, fmt_meta)
    mid = S // 2

    # ── Header
    f_h = F_BOLD(27)
    draw_mixed_centered(img, draw, mid, cy + int(ch * 0.06), "💸 DEV MATH", f_h, (*c1, 255))

    f_title = F_BOLD(34)
    header_lines = ["math they don't teach", "in CS class 📐"]
    hy = cy + int(ch * 0.13)
    for hl in header_lines:
        draw_mixed_centered(img, draw, mid, hy, hl, f_title, (255, 255, 255, 255))
        hy += 44
    rows_top = hy + 14

    # ── Equation rows: evenly distributed in remaining space
    equations = post.get("equations", [])
    n = len(equations)
    BMARGIN = 14
    rows_bottom = (cy + ch) - BMARGIN
    available_h = rows_bottom - rows_top
    # Stretch rows to fill all available space
    row_slot = available_h // n if n else 80
    row_slot = max(72, row_slot)  # no cap — fill the space
    GAP = 8
    row_h = row_slot - GAP

    f_eq = F_MONO_BOLD(27)
    for i, eq in enumerate(equations):
        col  = c1 if i % 2 == 0 else c2
        rw   = int(cw * 0.90)
        ry   = rows_top + i * row_slot

        row_img = Image.new("RGBA", (rw, row_h), (0, 0, 0, 0))
        rd = ImageDraw.Draw(row_img)
        rd.rounded_rectangle([0, 0, rw-1, row_h-1], radius=14,
                               fill=(255, 255, 255, 8 if i % 2 == 0 else 4),
                               outline=(*col, 55), width=2)
        img.alpha_composite(row_img, (cx + int(cw * 0.05), ry))

        eq_lines = wrap_mixed(eq, f_eq, rw * 0.88, draw)
        total_h  = len(eq_lines) * 34
        eqy = ry + row_h//2 - total_h//2
        for wl in eq_lines:
            draw_mixed_centered(img, draw, mid, eqy, wl, f_eq, (224, 222, 255, 255))
            eqy += 34

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
