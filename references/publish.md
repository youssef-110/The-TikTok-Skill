# Publishing (Higgsfield TikTok tools)

## Steps

1. `tiktok_accounts` → take the `active` account's `connector_id`. `error` → `tiktok_reconnect`. None → `tiktok_connect`.
2. `python scripts/prep_images.py <slides> -o <slides>/ready --ratio 3:4`.
3. Upload without putting signed URLs into the conversation (each is ~3K tokens):
   - Call `media_upload` with **exactly 20 filenames** per call, padding with dummy names if needed. A 20-file result is too big to inline, so the harness saves it to a file and returns the path. Smaller batches get inlined and cost ~40K tokens.
   - `python scripts/higgsfield_put.py <saved-result-file> <slides in order...> -o ids.json` does the PUTs from disk and prints one line per file. It sends a curl user agent because Cloudflare blocks Python's default one (`error code: 1010`).
   - `media_confirm` with `type: "image"` and the media_ids (max 20 per call).
   - Public URL per slide: the `url` field in ids.json.
4. `tiktok_prepare_publish`:
   - `media_type: "PHOTO"`, `photo_images` in slide order, `photo_cover_index: 0`
   - `mode: "DIRECT_POST"` (music only works there) or `"UPLOAD_TO_DRAFT"`
   - `title` max 150 chars, `description` max 4000
   - `commercial_content_disclosure` only when the account rules say so
5. The user reviews, picks music and submits in the form. Never call the final publish step yourself.
6. `tiktok_publish_status` if the user asks whether it went live.

## Limits (rejections can arrive after posting)

| | Photo | Video |
|---|---|---|
| Format | JPEG or WebP. PNG is rejected | MP4, WebM, MOV |
| Size | each ≤ 20 MB, fits 1080x1920 | ≤ 1 GB, ≥ 360 px both sides |
| Count / length | up to 35 images | 3-600 s, 23-60 fps |

## Timing

Publish forms expire about 2 hours after they open. Upload and open the form a few minutes before the posting time, not in a batch hours early.

## Before calling tiktok_prepare_publish

- [ ] Review step done (contact sheet read, no clipped text)
- [ ] `prep_images.py` ran with no warnings
- [ ] Title and description follow every rule in `config/account.md` (hashtags, mentions, disclosure)
- [ ] Inside the posting window
