"""Pack many images into one numbered grid so Claude reads 1 image instead of N.

Reading one 1500px sheet costs roughly the same as one slide, so a 12-slide
carousel review drops from ~12 image reads to 1.

Usage:
  python contact_sheet.py <folder-or-images...> [-o sheet.jpg] [--cols 4] [--cell 360]
"""
import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def collect(inputs):
    paths = []
    for item in inputs:
        p = Path(item)
        if p.is_dir():
            paths += sorted(f for f in p.iterdir() if f.suffix.lower() in EXTS)
        elif p.suffix.lower() in EXTS:
            paths.append(p)
    return paths


def label_font(size):
    for name in ("arialbd.ttf", "DejaVuSans-Bold.ttf", "Arial Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def build(paths, out, cols, cell):
    if not paths:
        sys.exit("no images found")
    cols = min(cols, len(paths))
    rows = math.ceil(len(paths) / cols)
    # Cells keep the first image's aspect ratio (slides in one post share it).
    w0, h0 = Image.open(paths[0]).size
    cw, ch = cell, round(cell * h0 / w0)
    sheet = Image.new("RGB", (cols * cw, rows * ch), "white")
    draw = ImageDraw.Draw(sheet)
    font = label_font(max(14, cell // 12))
    for i, path in enumerate(paths):
        img = Image.open(path).convert("RGB")
        img.thumbnail((cw, ch))
        x, y = (i % cols) * cw, (i // cols) * ch
        sheet.paste(img, (x + (cw - img.width) // 2, y + (ch - img.height) // 2))
        draw.rectangle([x, y, x + cw - 1, y + ch - 1], outline="white", width=2)
        tag = str(i + 1)
        tw = draw.textlength(tag, font=font)
        draw.rectangle([x, y, x + tw + 12, y + font.size + 10], fill="black")
        draw.text((x + 6, y + 4), tag, fill="yellow", font=font)
    sheet.save(out, quality=80)
    print(f"{out}  {len(paths)} images  {sheet.width}x{sheet.height}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("-o", "--out", default="contact_sheet.jpg")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--cell", type=int, default=360, help="cell width in px")
    a = ap.parse_args()
    build(collect(a.inputs), a.out, a.cols, a.cell)
