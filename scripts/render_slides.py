"""Render a carousel from a JSON spec: background art + bottom gradient + text.

No browser needed. Output is TikTok-ready JPEG (default 1080x1440, 3:4).

Spec (JSON):
{
  "size": [1080, 1440],
  "tag": "PSYCHOLOGY",                      # small top-left label, optional
  "accent": "#E8C47A",                      # label colour
  "slides": [
    {"type": "cover", "bg": "art/01.jpg", "title": "9 tricks ...", "sub": "backed by research"},
    {"type": "point", "bg": "art/02.jpg", "title": "Say their name",
     "sections": [["HOW", "Use it once or twice."], ["WHY IT WORKS", "..."]]},
    {"type": "end", "bg": "art/11.jpg", "title": "Save this", "sections": [["", "Send it to a friend."]]}
  ]
}
Point slides get an automatic "01 / 09" counter. bg paths are relative to the spec.

Native style (looks like TikTok's own text tool: centred white text with a soft shadow):
    {"type": "hook", "bg": "still.jpg", "text": "How to piss off a Narcissist..", "y": 0.5, "dim": 0.1, "focus": 0.3}
    {"type": "tips", "bg": "wall.jpg", "title": "Give Zero Reaction", "bullets": ["...", "..."], "dim": 0.45}
"y" is the text centre as a fraction of height, "dim" darkens the image (0-1),
"focus" is the horizontal crop centre (0 = left, 0.5 = middle) when the image is wider than the slide.

Usage:  python render_slides.py spec.json [-o out_folder]
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

BOLD = ("Poppins-Bold.ttf", "Montserrat-Bold.ttf", "segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf")
REGULAR = ("Poppins-Regular.ttf", "segoeui.ttf", "arial.ttf", "DejaVuSans.ttf")
# Closest system match to TikTok's in-app text (TikTok Sans / Proxima semibold).
NATIVE = ("TikTokSans-SemiBold.ttf", "ProximaNova-Semibold.otf", "seguisb.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf")


def font(names, size):
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            pass
    return ImageFont.load_default(size)


def wrap(draw, text, fnt, width):
    lines, line = [], ""
    for word in text.split():
        test = f"{line} {word}".strip()
        if draw.textlength(test, font=fnt) <= width:
            line = test
        else:
            lines.append(line)
            line = word
    return lines + [line] if line else lines


def balanced(draw, text, fnt, width):
    # Narrow the box until the last line holds 2+ words, so no orphan "IT" line.
    lines = wrap(draw, text, fnt, width)
    for shrink in range(1, 9):
        if len(lines) < 2 or len(lines[-1].split()) > 1:
            break
        trial = wrap(draw, text, fnt, width * (1 - shrink * 0.05))
        if len(trial) > len(lines):
            break
        lines = trial
    return lines


def background(path, size, dim):
    img = ImageOps.fit(Image.open(path).convert("RGB"), size, Image.LANCZOS)
    w, h = size
    # Bottom gradient: transparent at `dim` of the height, ~92% black at the bottom.
    grad = Image.new("L", (1, h))
    for y in range(h):
        t = max(0.0, (y - h * dim) / (h * (1 - dim)))
        grad.putpixel((0, y), int(235 * min(1.0, t * 1.3)))
    black = Image.new("RGB", size, "black")
    return Image.composite(black, img, grad.resize(size))


def plain_bg(path, size, dim, focus):
    img = ImageOps.fit(Image.open(path).convert("RGB"), size, Image.LANCZOS, centering=(focus, 0.5))
    return ImageEnhance.Brightness(img).enhance(1 - dim)


def native_text(img, blocks, y_center, width):
    """blocks: [(text, font, gap_after_px)]. Draws centred, shadowed lines around y_center."""
    W, H = img.size
    d = ImageDraw.Draw(img)
    laid = [(balanced(d, t, f, width), f, gap) for t, f, gap in blocks]
    total = sum(len(ls) * int(f.size * 1.22) + gap for ls, f, gap in laid)
    y = int(H * y_center - total / 2)
    shadow = Image.new("L", img.size, 0)
    sd = ImageDraw.Draw(shadow)
    pos = []
    for lines, f, gap in laid:
        for ln in lines:
            x = (W - d.textlength(ln, font=f)) / 2
            pos.append((x, y, ln, f))
            sd.text((x + 2, y + 3), ln, font=f, fill=200)
            y += int(f.size * 1.22)
        y += gap
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    img.paste(Image.new("RGB", img.size, "black"), mask=shadow)
    for x, y, ln, f in pos:
        d.text((x, y), ln, font=f, fill="white", stroke_width=1, stroke_fill=(40, 40, 40))
    return img


def text_block(draw, lines, fnt, x, y, fill, gap=1.18):
    for ln in lines:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += int(fnt.size * gap)
    return y


def render(spec_path, out_dir):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8-sig"))
    base = Path(spec_path).parent
    W, H = spec.get("size", [1080, 1440])
    accent = spec.get("accent", "#E8C47A")
    pad = int(W * 0.07)
    points = [s for s in spec["slides"] if s["type"] == "point"]
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    n = 0
    for i, s in enumerate(spec["slides"], 1):
        if s["type"] in ("hook", "tips"):
            img = plain_bg(base / s["bg"], (W, H), s.get("dim", 0.1 if s["type"] == "hook" else 0.45), s.get("focus", 0.5))
            if s["type"] == "hook":
                blocks = [(s["text"], font(NATIVE, int(W * s.get("scale", 0.075))), 0)]
            else:
                body = font(NATIVE, int(W * 0.047))
                blocks = [(s["title"], font(NATIVE, int(W * 0.055)), int(W * 0.06))]
                blocks += [("• " + b, body, int(W * 0.045)) for b in s["bullets"]]
            native_text(img, blocks, s.get("y", 0.5), W * 0.8)
            out = Path(out_dir) / f"{i:02d}.jpg"
            img.save(out, quality=92)
            print(out)
            continue
        cover = s["type"] == "cover"
        img = background(base / s["bg"], (W, H), 0.25 if cover else 0.45)
        d = ImageDraw.Draw(img)
        small = font(BOLD, int(W * 0.022))
        if spec.get("tag") and not cover:
            d.text((pad, pad), spec["tag"], font=small, fill="white")
        if s["type"] == "point":
            n += 1
            label = f"{n:02d} / {len(points):02d}"
            d.text((W - pad - d.textlength(label, font=small), pad), label, font=small, fill="white")
        title_f = font(BOLD, int(W * (0.085 if cover else 0.06)))
        body_f = font(REGULAR, int(W * 0.033))
        head_f = font(BOLD, int(W * 0.022))
        title = balanced(d, s["title"].upper(), title_f, W - 2 * pad)
        if cover:
            y = int(H * 0.40) - len(title) * title_f.size // 2
            for ln in title:
                d.text(((W - d.textlength(ln, font=title_f)) / 2, y), ln, font=title_f, fill="white",
                       stroke_width=2, stroke_fill="black")
                y += int(title_f.size * 1.1)
            if s.get("sub"):
                y += 20
                d.text(((W - d.textlength(s["sub"], font=body_f)) / 2, y), s["sub"], font=body_f, fill="white")
            hint = s.get("swipe", "SWIPE →")
            d.text(((W - d.textlength(hint, font=small)) / 2, H - pad * 1.5), hint, font=small, fill="white")
        else:
            # Measure the block first, then draw it bottom-aligned.
            blocks = [(h, wrap(d, b, body_f, W - 2 * pad)) for h, b in s.get("sections", [])]
            height = len(title) * int(title_f.size * 1.25) + 36
            height += sum((head_f.size + 14 if h else 0) + len(b) * int(body_f.size * 1.18) + 24 for h, b in blocks)
            y = H - pad - height
            y = text_block(d, title, title_f, pad, y, "white", 1.25) + 36
            for head, body in blocks:
                if head:
                    d.text((pad, y), head.upper(), font=head_f, fill=accent)
                    y += head_f.size + 14
                y = text_block(d, body, body_f, pad, y, "white") + 24
        out = Path(out_dir) / f"{i:02d}.jpg"
        img.save(out, quality=92)
        print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("-o", "--out", default="slides")
    a = ap.parse_args()
    render(a.spec, a.out)
