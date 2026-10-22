"""Download images listed in a text file, one per line: "name<TAB>url" or just "url".

Saves each as <name>.jpg (RGB JPEG) in the output folder, skipping failures.
Pair with contact_sheet.py to review everything in one read.

Usage:  python fetch_images.py urls.txt [-o folder]
"""
import argparse
import io
import urllib.request
from pathlib import Path

from PIL import Image

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("urls")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    out = Path(a.out or Path(a.urls).parent)
    out.mkdir(parents=True, exist_ok=True)
    lines = [l.strip() for l in Path(a.urls).read_text(encoding="utf-8-sig").splitlines() if l.strip()]
    for i, line in enumerate(lines, 1):
        name, _, url = line.rpartition("\t")
        name = name or f"{i:02d}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=20).read()
            img = Image.open(io.BytesIO(data)).convert("RGB")
            img.save(out / f"{name}.jpg", quality=92)
            print(f"ok   {name}  {img.width}x{img.height}")
        except Exception as e:  # noqa: BLE001 - report and keep going
            print(f"FAIL {name}  {e}")
