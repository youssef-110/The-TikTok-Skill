"""Turn a video (file or TikTok/YouTube URL) into one frame grid plus basic stats.

Lets Claude "watch" a video for the cost of one image read. Needs ffmpeg;
URLs also need yt-dlp.

Usage:
  python video_frames.py <file-or-url> [-n 12] [-o frames.jpg] [--hook]
  --hook  samples only the first 3 seconds (hook analysis)
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from contact_sheet import build  # noqa: E402


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def fetch(src, tmp):
    if Path(src).exists():
        return Path(src)
    if not shutil.which("yt-dlp"):
        sys.exit("yt-dlp not installed: pip install yt-dlp")
    out = Path(tmp) / "video.mp4"
    run(["yt-dlp", "-q", "-f", "mp4/best", "-o", str(out), src])
    return out


def probe(video):
    info = json.loads(run(["ffprobe", "-v", "quiet", "-print_format", "json",
                           "-show_format", "-show_streams", str(video)]))
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    num, den = v.get("r_frame_rate", "0/1").split("/")
    return {
        "duration_s": round(float(info["format"]["duration"]), 1),
        "size": f'{v["width"]}x{v["height"]}',
        "fps": round(int(num) / max(int(den), 1), 1),
        "has_audio": any(s["codec_type"] == "audio" for s in info["streams"]),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("-n", type=int, default=12, help="frames to sample")
    ap.add_argument("-o", "--out", default="frames.jpg")
    ap.add_argument("--hook", action="store_true")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        video = fetch(a.src, tmp)
        stats = probe(video)
        span = min(3.0, stats["duration_s"]) if a.hook else stats["duration_s"]
        step = span / a.n
        frames = []
        for i in range(a.n):
            f = Path(tmp) / f"f{i:03d}.jpg"
            run(["ffmpeg", "-v", "quiet", "-ss", f"{i * step + step / 2:.2f}",
                 "-i", str(video), "-frames:v", "1", "-vf", "scale=360:-2", str(f)])
            if f.exists():
                frames.append(f)
        build(frames, a.out, cols=4 if a.n > 6 else a.n, cell=300)
        stats["frame_interval_s"] = round(step, 2)
        print(json.dumps(stats))
