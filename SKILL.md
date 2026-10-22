---
name: tiktok-studio
description: TikTok growth studio for photo carousels and short videos. Audits an account and its posts, studies competitors and viral videos, decides what to post next, finds or generates slide images, renders carousels, writes hooks and captions, prepares the publish form, and learns from results. Built to stay cheap on tokens. Use when the user asks to analyze a TikTok account or post, plan TikTok content, make or improve carousel slides, analyze a TikTok video, find images for slides, write TikTok captions or hooks, or post to TikTok.
---

# TikTok Studio

A loop, not a one-off: **Audit → Decide → Create → Review → Publish → Learn**.
Each run makes the next one smarter because results are logged as text.

## 0. Load the account first

Read `config/account.md` (niche, audience, voice, posting window, partnership rules).
If it does not exist, copy `config/account.example.md` to `config/account.md` and fill it with the user in 5 short questions. Never guess partnership or brand rules.

Rules in `config/account.md` override everything in this skill.

## Token budget rules (always on)

These are the core of the skill. They keep a full audit under a few image reads.

1. **Text before pixels.** Read analytics and post lists with `get_page_text` or `read_page`, never screenshots. Screenshot only to judge visuals.
2. **One sheet, not N images.** Never Read slides one by one. Run `scripts/contact_sheet.py <folder>` and Read the single sheet. A 30-slide post is one read at `--cols 6 --cell 220`.
3. **Videos become one image.** `scripts/video_frames.py <file-or-url> -n 12` gives a 12-frame grid plus duration/fps/audio stats. Add `--hook` to look only at the first 3 seconds.
4. **Zoom only where needed.** If a sheet shows a problem on slide 7, Read that one slide at full size. Nothing else.
5. **Log once, analyze forever.** Put metrics into `scripts/perf_log.py add`. Next time run `perf_log.py report` instead of re-scraping.
6. **Paid analysis is opt-in.** Higgsfield `video_analysis_create` and `virality_predictor` cost credits. Offer them for a final check on a video, never for bulk.
7. **Delegate bulk.** For 10+ posts or competitor sweeps, hand collection to a subagent on a small model and ask it to return a table only.

Scripts need Python 3 + Pillow. Videos need ffmpeg; URLs need yt-dlp. Run scripts by absolute path from this skill folder.

## 1. Audit

Goal: know what already works before making anything. Full method in `references/analyze.md`.

- Pull the last 20-30 posts with views, likes, comments, shares, saves (TikTok Studio, via browser text).
- Log them with `perf_log.py add`, then `perf_log.py report`.
- Contact-sheet the top 3 and bottom 3 posts. Compare hook slide, text density, art style, slide count.
- Output: 3-5 findings, each with evidence (numbers) and one action.

## 2. Decide

Pick the next posts from evidence, not vibes. See `references/viral-playbook.md`.

- Double down: remake the format of the top post with a new topic.
- Fix: one change per test (hook wording, cover image, slide count, posting hour). Never change 4 things at once, or nothing is learned.
- Steal structure from competitors' outliers (posts at 3x+ their average), never their content.
- Write the plan as a table: id, time, type, hook, slide count, what is being tested.
- Confirm the plan with the user before making slides.

## 3. Create

**Images:** find or generate art per `references/images.md`. Review candidates as one contact sheet, pick by number.

**Slides:** write a JSON spec and run `scripts/render_slides.py spec.json -o slides/`. Cover, point and end slide types. Default 1080x1440 (3:4). For tools that make their own slides (for example a chat-template site), use those, then still run the review.

**Copy:** hook, slide text, caption and hashtags per `references/viral-playbook.md` and the account rules.

## 4. Review (before every publish)

Contact-sheet the final folder and Read it once. Check:

- Cover: readable as a thumbnail? One idea, 3-8 words, a curiosity gap or a promise?
- Every slide: text fully inside the frame, nothing clipped, contrast readable on a phone.
- Flow: does each slide make you want the next? Is there a reason to save or share at the end?
- Specs: run `scripts/prep_images.py <folder> --ratio 3:4` (JPEG, fits 1080x1920, under 20 MB, max 35).

Report problems by slide number. Fix, re-render, re-sheet.

## 5. Publish

See `references/publish.md`. Short version:
`tiktok_accounts` → `media_upload` + PUT + `media_confirm` → `tiktok_prepare_publish`.
The user reviews and submits the form. Never submit it for them. Open forms close to posting time; they expire.

## 6. Learn

24-72 hours after posting, log each post's metrics (`perf_log.py add --id X --views ...`).
Run `perf_log.py report`. Update the "What works" section in `config/account.md` with any finding that held across 3+ posts. Old guesses that failed get deleted.

## Output style

- Lead with the decision, then the evidence.
- Tables for plans and comparisons.
- Never invent metrics. If a number was not read from a source, say it is missing.
