# Finding and making slide images

Goal: one consistent mood per post, art with clear space for text (usually the bottom 40%), no watermarks.

## Fastest tested path: Bing Images (no login, Oct 2026)

1. Open `bing.com/images/search?q=<words>&qft=+filterui:imagesize-large` (add `+filterui:aspect-tall` for 9:16 covers; "phone wallpaper 4k" in the query finds tall high-res stills).
2. One `javascript_tool` call returns short thumbnail ids (~60 chars each):
   ```js
   await new Promise(r=>setTimeout(r,2000));
   const m=[...document.querySelectorAll('a.iusc')].slice(0,24).map(a=>JSON.parse(a.getAttribute('m')));
   m.map((x,i)=>`${String(i+1).padStart(2,'0')}\t${x.turl.split('&')[0]}`).join('\n')
   ```
3. Write them to `urls.txt` with `&w=400` appended, `fetch_images.py urls.txt`, `contact_sheet.py` → one read, pick by number.
4. For the picks only, re-run the search and return `m[i].murl` (the original). Thumbnails cap at 474 px, so never publish them.
5. Check resolution in the `fetch_images.py` output. Needs at least ~700 px on the short side; prefer sources that already match the slide ratio (3:4 or 9:16).

## Option A: find art (Pinterest and similar)

1. Search in the browser with mood words, not topic words: "dark renaissance painting woman", "moody gothic roses oil painting", "surreal dark art portrait".
2. Collect image URLs in one call instead of screenshots:
   ```js
   [...document.images].filter(i => i.naturalWidth >= 474).map(i => i.src.replace(/\/\d+x\//, '/originals/')).slice(0, 40)
   ```
   (Pinterest thumbnails use `/236x/` or `/474x/` in the URL; `/originals/` is full size. Fall back to `/736x/` if originals 404.)
3. Download with a short Python script into a fresh folder (`candidates/`), one file per URL, skipping failures.
4. `python scripts/contact_sheet.py candidates -o picks.jpg --cols 8 --cell 160` and Read once. Pick by number.
5. Reject: watermarks, visible text, faces cut at the eyes, low resolution (under 700 px wide), art that clashes with the rest.

Rights: found art is often copyrighted. Prefer public-domain paintings (museum collections such as The Met Open Access, Rijksmuseum, Art Institute of Chicago are free to use) or generated art for anything sponsored. Tell the user when a pick has unclear rights.

## Option B: generate art

Higgsfield `generate_image` (or any image tool the user has). Keep a style suffix in `config/account.md` so every image matches, for example:
"dark oil painting, renaissance style, muted colours, dramatic chiaroscuro lighting, empty dark lower third, no text, 3:4".

Generate 4 variants per slot, sheet them, pick. Higgsfield output is PNG: run `prep_images.py` before TikTok.

## Option C: stills from shows and films (story/chat formats)

Use recognizable characters only as small reaction images in story formats, and follow any rules in the account config. Grab frames from a video file with `video_frames.py`, then crop.

## Matching art to slides

- Cover: strongest image, ideally a face or eyes, simple background.
- Point slides: one image per point, mood over literal meaning.
- Keep the same palette across the post. If one pick is off, re-tint it rather than swap the whole set.

## Final check

Render, then one contact sheet of the full post. Look for one image that breaks the mood or makes text hard to read.
