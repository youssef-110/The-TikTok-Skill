"""PUT local slides to the presigned URLs from a saved Higgsfield media_upload result.

Keeps the ~3K-token signed URLs out of the conversation: request uploads with 20
filenames per media_upload call (large results are saved to a file), then:

  python higgsfield_put.py <result.json> <slide1.jpg> <slide2.jpg> ... [-o ids.json]

Slides are matched to uploads in order (extra uploads are left unused).
Prints one short line per file and writes [{"file","media_id","url"}] to -o
(default: ids.json next to the result), ready for media_confirm and tiktok_prepare_publish.
"""
import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path


def put(url, data, content_type):
    for extra in ({"If-None-Match": "*"}, {}):
        # Cloudflare in front of upload.higgsfield.ai rejects Python's default user agent (error 1010).
        req = urllib.request.Request(url, data=data, method="PUT",
                                     headers={"Content-Type": content_type, "User-Agent": "curl/8.9.1", **extra})
        try:
            return urllib.request.urlopen(req, timeout=60).status
        except urllib.error.HTTPError as e:
            # Retry once without If-None-Match in case it is not part of the signature.
            if e.code != 403 or not extra:
                return e.code
    return 403


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("result")
    ap.add_argument("files", nargs="+")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    text = Path(a.result).read_text(encoding="utf-8-sig")
    data = json.loads(text)
    # Saved tool results may wrap the JSON as [{"type":"text","text":"{...}"}].
    if isinstance(data, list):
        data = json.loads(data[0]["text"])
    uploads = data["uploads"]
    if len(a.files) > len(uploads):
        raise SystemExit(f"{len(a.files)} files but only {len(uploads)} upload slots")
    out, failed = [], 0
    for f, u in zip(a.files, uploads):
        status = put(u["upload_url"], Path(f).read_bytes(), u.get("content_type", "image/jpeg"))
        failed += status != 200
        print(f"{status}  {Path(f).name}  {u['media_id']}")
        out.append({"file": Path(f).name, "media_id": u["media_id"], "url": u["url"]})
    dest = Path(a.out or Path(a.result).with_name("ids.json"))
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"{'ALL OK' if not failed else f'{failed} FAILED'} -> {dest}")
