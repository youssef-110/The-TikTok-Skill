"""Make slides TikTok-safe before upload: JPEG, fits 1080x1920, under 20 MB, max 35.

TikTok photo posts reject PNG and oversize images (sometimes only after
posting), so run this on every folder before media_upload.

Usage:
  python prep_images.py <folder> [-o out_folder] [--ratio 3:4|9:16|keep]
  --ratio crops to that aspect (center crop) before fitting; default keep.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps

EXTS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_W, MAX_H, MAX_BYTES, MAX_COUNT = 1080, 1920, 20 * 1024 * 1024, 35


def crop_to(img, ratio):
    rw, rh = map(int, ratio.split(":"))
    target = rw / rh
    w, h = img.size
    if w / h > target:
        nw = round(h * target)
        return img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    nh = round(w / target)
    return img.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))


def prep(src, dst, ratio):
    files = sorted(f for f in Path(src).iterdir() if f.suffix.lower() in EXTS)
    if not files:
        sys.exit("no images found")
    if len(files) > MAX_COUNT:
        print(f"WARNING: {len(files)} images, TikTok allows {MAX_COUNT}. Only the first {MAX_COUNT} are written.")
    Path(dst).mkdir(parents=True, exist_ok=True)
    for i, f in enumerate(files[:MAX_COUNT], 1):
        img = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
        if ratio != "keep":
            img = crop_to(img, ratio)
        img.thumbnail((MAX_W, MAX_H), Image.LANCZOS)
        out = Path(dst) / f"{i:02d}.jpg"
        q = 92
        img.save(out, quality=q, optimize=True)
        while out.stat().st_size > MAX_BYTES and q > 50:
            q -= 10
            img.save(out, quality=q, optimize=True)
        print(f"{f.name} -> {out.name}  {img.width}x{img.height}  {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("-o", "--out")
    ap.add_argument("--ratio", default="keep")
    a = ap.parse_args()
    prep(a.src, a.out or str(Path(a.src) / "ready"), a.ratio)
