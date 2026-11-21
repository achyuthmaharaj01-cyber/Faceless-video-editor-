#!/usr/bin/env python3
"""Contact sheet of search candidates so the agent can look at them before choosing.

Usage: thumb_sheet.py CANDIDATES_JSON OUT_JPG
CANDIDATES_JSON: [{"thumb": url_or_path, "label": "..."}]. Thumbnails are fetched with the system proxy settings.
"""
import io
import json
import sys
import urllib.request

from PIL import Image, ImageDraw

items = json.load(open(sys.argv[1]))
cols, cw, ch, lh = 4, 360, 240, 34
rows = max(1, (len(items) + cols - 1) // cols)
sheet = Image.new("RGB", (cols * cw, rows * (ch + lh)), (20, 20, 20))
d = ImageDraw.Draw(sheet)
ua = {"User-Agent": "faceless-video-studio/0.1 (thumbnail preview)"}
for i, it in enumerate(items):
    x, y = (i % cols) * cw, (i // cols) * (ch + lh)
    try:
        src = it["thumb"]
        data = urllib.request.urlopen(urllib.request.Request(src, headers=ua), timeout=20).read() if src.startswith("http") else open(src, "rb").read()
        im = Image.open(io.BytesIO(data)).convert("RGB")
        im.thumbnail((cw, ch))
        sheet.paste(im, (x + (cw - im.width) // 2, y + lh + (ch - im.height) // 2))
    except Exception as e:  # show the failure on the sheet instead of hiding it
        d.text((x + 8, y + lh + 8), f"thumbnail failed: {str(e)[:40]}", fill=(255, 90, 90))
    d.text((x + 6, y + 4), f"[{i}] {it.get('label', '')}"[:58], fill=(255, 220, 90))
sheet.save(sys.argv[2], quality=80)
print(json.dumps({"sheet": sys.argv[2], "items": len(items)}))
