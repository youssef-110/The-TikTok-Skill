# TikTok Studio

A Claude Code skill that runs a TikTok account the way a growth team would. It audits your posts, finds what actually works, plans the next posts as tests, finds images, renders carousel slides, reviews them, opens the publish form, and learns from the results.

It was built and tested on a real 52K-follower photo-carousel account. The first audit pulled 74 posts in one text read and found that the account's best format was getting ignored while a weaker one got most of the posting slots. That kind of finding is the point.

## Why it exists

Asking an AI agent to "look at my TikTok" usually burns through tokens. It screenshots pages, reads slides one by one, and pastes signed upload URLs into the chat. This skill is built around not doing that:

| Task | Naive approach | TikTok Studio |
| --- | --- | --- |
| Read 74 posts from TikTok Studio | scroll and screenshot, or read raw API JSON at ~3K tokens per post | one in-page script, one compact text table |
| Review an 11-slide carousel | 11 image reads | 1 contact sheet |
| Watch a video | not possible, or a paid API | 1 frame grid plus duration, fps and audio stats |
| Upload 31 slides | ~40K tokens of signed URLs in the chat | a few hundred tokens, uploads run from disk |
| Re-check last week's numbers | scrape again | `perf_log.py report` |

## What it does

The skill runs as a loop: audit, decide, create, review, publish, learn.

1. **Audit.** Pulls your post list from TikTok Studio, logs views, likes and comments to a CSV, and ranks posts against your account average. It compares the covers of your best and worst posts in one image and writes 3 to 5 findings, each backed by numbers.
2. **Decide.** Builds a posting plan where every post tests one change, such as a new cover, a different hour or a different slide count. Change four things at once and you learn nothing.
3. **Create.** Searches for images and shows you 24 candidates in one grid, then pulls full-size originals for the picks. It renders slides in two styles: designed listicles, or TikTok-native centred text over a still. It writes the hook, slide copy, caption and hashtags.
4. **Review.** Checks every slide in one image for clipped text, contrast and thumbnail strength, then makes the files TikTok-safe: JPEG, within 1080x1920, under 20 MB, at most 35 slides.
5. **Publish.** Uploads the slides and opens the TikTok publish form through the Higgsfield connector. You review and submit it. The skill never posts on its own.
6. **Learn.** Re-imports your stats a few days later and keeps a "What works" list in your account config, so the next plan starts from evidence.

It also analyzes short videos. `video_frames.py` turns a file or a TikTok/YouTube link into a frame grid, and `--hook` looks at only the first 3 seconds.

## Install

```bash
git clone https://github.com/youssef-110/The-TikTok-Skill.git ~/.claude/skills/tiktok-studio
pip install pillow yt-dlp
```

Video analysis also needs ffmpeg: `winget install ffmpeg`, `brew install ffmpeg` or `apt install ffmpeg`.

Restart Claude Code. The skill loads when you ask for anything TikTok related, or with `/tiktok-studio`.

## Requirements

| Need | For |
| --- | --- |
| Claude Code | running the skill |
| Python 3.10+ and Pillow | all scripts |
| A browser tool signed in to TikTok (Claude's built-in browser or Claude in Chrome) | the audit |
| ffmpeg, yt-dlp | video analysis |
| Higgsfield MCP connector with TikTok connected | publishing only. Everything else works without it |

## First run

Say "audit my TikTok". The skill copies `config/account.example.md` to `config/account.md` and asks you five questions: niche, audience, posting window, formats and any sponsor rules. Then it opens TikTok Studio and starts.

Other things to try:

- "Make tomorrow's two posts based on what works."
- "Review the slides in ~/posts/monday before I post them."
- "Analyze this video: https://www.tiktok.com/@someone/video/..."
- "Find 20 dark moody paintings for a carousel about attachment styles."
- "Open the publish form for post 2."

## Scripts

They work on their own too, without Claude.

| Script | What it does |
| --- | --- |
| `contact_sheet.py` | Packs many images into one numbered grid |
| `video_frames.py` | Turns a video file or URL into a frame grid plus stats |
| `render_slides.py` | Renders a carousel from a JSON spec, in designed or TikTok-native text style |
| `prep_images.py` | Converts slides to TikTok-safe JPEGs and warns about limits |
| `perf_log.py` | Logs post metrics, imports the Studio scrape, reports what wins by type, hour and slide count |
| `fetch_images.py` | Downloads a list of image URLs |
| `higgsfield_put.py` | Uploads slides to Higgsfield presigned URLs from a saved result file |

Example slide spec:

```json
{
  "size": [1080, 1440],
  "slides": [
    {"type": "hook", "bg": "art/cover.jpg", "text": "How to spot a liar in 10 seconds..", "scale": 0.085},
    {"type": "tips", "bg": "art/wall.jpg", "title": "Watch the Hands",
     "bullets": ["People hide their hands when they hide the truth.", "Look for sudden stillness."]}
  ]
}
```

## Layout

```
SKILL.md                    the loop and the token rules Claude follows
config/account.example.md   template for your account rules
references/                 analyze, viral-playbook, images, publish
scripts/                    the seven scripts above
data/                       your logged metrics (created on first audit, git-ignored)
```

## Privacy

Your account rules live in `config/account.md` and your numbers in `data/`. Both are in `.gitignore`. Delete them before you share your copy of the folder.

The skill reads TikTok Studio through your own signed-in browser. It never asks for your password, never signs in for you, and never submits a post.

## Honest limits

- TikTok Studio's page layout changes. If the scrape returns 0 rows, the date format or row structure moved, and the snippet in `references/analyze.md` needs a small fix.
- The Studio list has views, likes and comments only. Saves and shares need each post's analytics page.
- `viral-playbook.md` is a starting point. After about 8 logged posts your own data wins, and the skill is told to follow it.
- Images found online are often copyrighted. Use public-domain or generated art for sponsored posts.

## Contributing

Issues and pull requests are welcome, especially fixes for Studio layout changes, new slide styles and support for other publishing connectors. Keep scripts dependency-light: Pillow and the standard library.

## License

MIT
