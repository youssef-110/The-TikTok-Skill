# Analyze: account, posts, competitors, videos

## Where the numbers come from

Use the browser the user is signed in with (Claude in Chrome if the built-in browser is not signed in to TikTok). Never sign in, sign out or change settings.

| Need | Page | Read with |
|---|---|---|
| Post list + per-post views/likes/comments/shares | `tiktok.com/tiktokstudio/content` | `get_page_text` |
| Account overview, followers, traffic | `tiktok.com/tiktokstudio/analytics` | `get_page_text` |
| One post's retention, traffic sources, saves | the post's analytics page in Studio | `get_page_text` |
| Public profile (yours or a competitor's) | `tiktok.com/@handle` | `get_page_text`, then `find` for counts |

### Fast path: scrape the Studio post list in one go (tested Oct 2026)

The content list is virtualized (only visible rows exist) and its API responses carry ~3K tokens of signed URLs per post, so do not read either directly. Run these two `javascript_tool` calls instead. Times use a narrow no-break space, hence `\s`.

Call 1 (setup + first 20 scroll steps, ~20 s):
```js
window.__tt={sc:[...document.querySelectorAll('*')].filter(e=>e.scrollHeight>e.clientHeight+200&&getComputedStyle(e).overflowY!='visible').sort((a,b)=>b.scrollHeight-a.scrollHeight)[0]||document.scrollingElement,seen:new Map()};
window.__tt.sc.scrollTop=0; await new Promise(r=>setTimeout(r,1500));
window.__ttStep=async(n)=>{const t=window.__tt,re=/^[A-Z][a-z]{2} \d{1,2}(, \d{4})?,\s\d{1,2}:\d{2}\s[AP]M$/u;
 for(let i=0;i<n;i++){const L=document.body.innerText.split('\n').map(s=>s.trim()).filter(Boolean);
  L.forEach((l,j)=>{if(re.test(l)){const pin=L[j-1]==='Pinned';const d=pin?L[j-2]:L[j-1];const k=l+'|'+d.slice(0,30);
   if(!t.seen.has(k))t.seen.set(k,[l.replace(/\s/g,' '),L[j+2],L[j+3],L[j+4],pin?'PIN':'',d.slice(0,90)].join(' | '));}});
  t.sc.scrollTop+=t.sc.clientHeight*0.7;await new Promise(r=>setTimeout(r,800));}
 return t.seen.size;};
await window.__ttStep(20)
```
Repeat `await window.__ttStep(20)` until the count covers the period you need (keep each call under ~40 s). Then:
```js
[...window.__tt.seen.values()].join('\n')
```
Save the output to `data/studio-YYYY-MM-DD.txt` and run `perf_log.py import <file> --promo-word <sponsor>`. Re-importing later refreshes counts without duplicating rows.

The list has views, likes, comments only. Saves and shares need the per-post analytics page; collect them for the top and bottom posts only.

**Cover thumbnails of any post**: walk up from each `img` to the row whose text contains the post's date, take `img.src`, download with Python, contact-sheet. One sheet of 10 covers is one image read.

Page layouts change. If text extraction misses a number, use `read_page` on that region, and only then a screenshot. If a metric is not visible anywhere, record it as blank, never estimate it.

Collect per post: id, date, time, type, hook (cover text), slide count, views, likes, comments, shares, saves. Then:

```
python scripts/perf_log.py add --id <id> --date ... --time ... --type ... --hook "..." --slides N --views ... --likes ... --comments ... --shares ... --saves ...
python scripts/perf_log.py report
```

## Reading the report

- **x avg** — views versus account average. 2x+ is a winner, 0.5x and below is a miss.
- **save/1k, share/1k** — the strongest signals for carousels. A post with average views but high saves is a format to repeat with a stronger hook.
- **High views, low saves** — the hook works, the body does not deliver. Fix the middle slides.
- **Low views, high eng/1k** — content is good, the cover or posting time failed. Retest with a new cover.
- Under 8 posts, every pattern is noise. Say so.

## Visual comparison (cheap)

```
python scripts/contact_sheet.py <top-post-folder> -o top.jpg --cols 6 --cell 220
python scripts/contact_sheet.py <weak-post-folder> -o weak.jpg --cols 6 --cell 220
```

Read both. Compare: cover wording, cover contrast, text per slide, art mood consistency, slide count, ending CTA. Write differences as a table.

If slides are only online, open the post, collect image URLs with one `javascript_tool` call (`[...document.images].map(i=>i.src)`), download them with Python into a fresh folder, then sheet them.

## Competitor sweep

1. Find 5-10 accounts in the same niche (TikTok search via browser, or the user's list in `config/account.md`).
2. For each, read the profile grid as text: post view counts.
3. Mark outliers: posts at 3x+ that account's median.
4. Sheet only the outliers. Extract the structure: hook pattern, slide count, art style, CTA. Ignore the topic itself.
5. Output a table: account, outlier, views, hook pattern, structure note, idea for us.

Hand steps 1-3 to a small-model subagent when there are more than 5 accounts. Ask for a table only.

## Videos

Free first:

```
python scripts/video_frames.py <file-or-tiktok-url> -n 12 -o frames.jpg       # whole video
python scripts/video_frames.py <file-or-tiktok-url> -n 6  -o hook.jpg --hook  # first 3 s only
```

Judge from the grid: does frame 1 have motion or text in the first second, is there on-screen text, how often does the shot change, is the subject centered for the UI overlays.

Captions/speech: `yt-dlp --write-auto-subs --skip-download <url>` when available, read the text file instead of listening.

Paid, only when the user wants a final verdict on one video:
- `video_analysis_create` (Higgsfield) for a scene-by-scene breakdown. Needs an uploaded video or a YouTube URL. Warn it takes 3-5 min and long videos are less accurate.
- `virality_predictor` for hook strength and retention risk on one finished video.

Only download videos the user owns or that are public, for analysis. Do not re-upload other people's videos.
