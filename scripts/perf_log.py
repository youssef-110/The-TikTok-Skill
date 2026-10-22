"""Post performance log: store metrics once as text, analyse forever without re-scraping.

Commands:
  add     python perf_log.py add --id A --date 2026-10-23 --time 10:30 --type psych \
            --hook "9 psychology tricks to make people like you" --slides 11 \
            --views 12000 --likes 900 --comments 40 --shares 120 --saves 600 [--notes "..."]
          (re-adding an existing id updates its row)
  import  python perf_log.py import studio.txt [--year 2026] [--promo-word <sponsor>]
          lines from the Studio scrape snippet (references/analyze.md):
          "Oct 22, 9:32 PM | 333 | 13 | 0 | PIN? | caption"   (pinned rows skipped)
  report  python perf_log.py report     -> ranking + what wins, by type, hour, slide count

Rates per 1k views are what matter: saves and shares push carousels further than likes.
Log file defaults to ../data/posts.csv next to this script (override with --log).
"""
import argparse
import csv
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

FIELDS = ["id", "date", "time", "type", "hook", "slides", "views", "likes", "comments", "shares", "saves", "notes"]
DEFAULT_LOG = Path(__file__).resolve().parent.parent / "data" / "posts.csv"


def load(log):
    if not log.exists():
        return []
    with log.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save(log, rows):
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def num(row, key):
    try:
        return float(row.get(key) or 0)
    except ValueError:
        return 0.0


def score(r):
    v = max(num(r, "views"), 1)
    # Shares and saves weighted highest: strongest distribution signals for photo posts.
    return (num(r, "likes") + 2 * num(r, "comments") + 4 * num(r, "saves") + 5 * num(r, "shares")) / v * 1000


def count(text):
    # Studio shows 1.7M / 21K / 2,512.
    text = text.replace(",", "").strip().upper()
    mult = {"K": 1e3, "M": 1e6}.get(text[-1:], 1)
    return str(int(float(text.rstrip("KM") or 0) * mult))


def parse_studio(path, year, promo_word):
    rows = []
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 6 or parts[4] == "PIN":
            continue
        stamp = re.sub(r"\s+", " ", parts[0])
        if not re.search(r", \d{4},", stamp):
            stamp = stamp.replace(",", f", {year},", 1)
        dt = datetime.strptime(stamp, "%b %d, %Y, %I:%M %p")
        caption = " | ".join(parts[5:])
        pid = dt.strftime("%m%d-%H%M")
        # Batch uploads share a minute: suffix in file order (a, b, c) so ids stay stable on re-import.
        same = sum(r["id"].startswith(pid) for r in rows)
        rows.append({"id": pid + ("abcdefgh"[same - 1] if same else ""), "date": dt.strftime("%Y-%m-%d"), "time": dt.strftime("%H:%M"),
                     "type": "promo" if promo_word and promo_word in caption.lower() else "organic",
                     "hook": caption, "views": count(parts[1]), "likes": count(parts[2]), "comments": count(parts[3])})
    return rows


def rate(r, key):
    # Blank means "not collected", which must not read as zero.
    return f"{num(r, key) / max(num(r, 'views'), 1) * 1000:.1f}" if r.get(key) else "-"


def report(rows, top):
    if not rows:
        print("log empty")
        return
    rows = sorted(rows, key=lambda r: num(r, "views"), reverse=True)
    avg = sum(num(r, "views") for r in rows) / len(rows)
    median = num(rows[len(rows) // 2], "views")
    print(f"{len(rows)} posts, avg views {avg:,.0f}, median {median:,.0f}\n")
    print(f"{'id':<11}{'views':>9}{'x avg':>7}{'eng/1k':>8}{'save/1k':>8}{'share/1k':>9}  type     hook")
    shown = rows if len(rows) <= 2 * top else rows[:top] + [None] + rows[-top:]
    for r in shown:
        if r is None:
            print(f"  ... {len(rows) - 2 * top} more ...")
            continue
        print(f"{r['id']:<11}{num(r, 'views'):>9,.0f}{num(r, 'views') / avg:>7.1f}{score(r):>8.0f}"
              f"{rate(r, 'saves'):>8}{rate(r, 'shares'):>9}  {r['type']:<8} {r['hook'][:48]}")
    cuts = [("type", lambda r: r["type"]), ("hour", lambda r: (r["time"] or "??")[:2] + "h")]
    if any(r.get("slides") for r in rows):
        cuts.append(("slides", lambda r: "?" if not r.get("slides") else "<=8" if num(r, "slides") <= 8
                     else "9-15" if num(r, "slides") <= 15 else "16+"))
    for label, key in cuts:
        groups = defaultdict(list)
        for r in rows:
            groups[key(r)].append(r)
        print(f"\nby {label}:")
        for g, rs in sorted(groups.items(), key=lambda kv: -sum(num(r, "views") for r in kv[1]) / len(kv[1])):
            print(f"  {g:<8} n={len(rs):<3} avg views {sum(num(r, 'views') for r in rs) / len(rs):>9,.0f}"
                  f"  eng/1k {sum(score(r) for r in rs) / len(rs):>5.0f}")
    if len(rows) < 8:
        print("\nnote: under 8 posts, patterns are noise. Keep logging.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["add", "import", "report"])
    ap.add_argument("file", nargs="?")
    ap.add_argument("--log", type=Path, default=DEFAULT_LOG)
    ap.add_argument("--year", default=str(datetime.now().year))
    ap.add_argument("--promo-word", default="")
    ap.add_argument("--top", type=int, default=10, help="rows shown at each end of the ranking")
    for f in FIELDS:
        ap.add_argument(f"--{f}", default="")
    a = ap.parse_args()
    rows = load(a.log)
    if a.cmd == "import":
        if not a.file:
            ap.error("import needs a file")
        by_id = {r["id"]: r for r in rows}
        new = parse_studio(a.file, a.year, a.promo_word.lower())
        for r in new:
            # Keep manual fields (slides, saves, notes) and refresh the counts.
            by_id.setdefault(r["id"], {f: "" for f in FIELDS}).update({k: v for k, v in r.items() if v})
        save(a.log, sorted(by_id.values(), key=lambda r: (r["date"], r["time"])))
        print(f"imported {len(new)} posts -> {a.log}")
    elif a.cmd == "add":
        if not a.id:
            ap.error("--id required")
        new = {f: getattr(a, f) for f in FIELDS}
        old = next((r for r in rows if r["id"] == a.id), None)
        if old:
            old.update({k: v for k, v in new.items() if v})
        else:
            rows.append(new)
        save(a.log, rows)
        print(f"saved {a.id} -> {a.log}")
    else:
        report(rows, a.top)
