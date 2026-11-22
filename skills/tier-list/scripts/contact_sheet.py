"""Contact sheet of sourced media per shot (raw files) so Claude can review picks.
Usage: python -I contact_sheet.py shotlist.json project_dir out.jpg"""
import sys, os, json, subprocess, io
from PIL import Image, ImageDraw
SL = json.load(open(sys.argv[1])); P = sys.argv[2]; out = sys.argv[3]
items = [(f"s{i:03d} {s.get('line_type','')} | {s.get('text', s.get('query',''))[:34]}", s.get("raw")) for i, s in enumerate(SL["shots"]) if s.get("raw")]
items += [(f"entry{j} {k}", e.get(k)) for j, e in enumerate(SL.get("entries", [])) for k in ("face_raw", "item_raw") if e.get(k)]
cols = 6; Wt, Ht = 320, 180; rows = (len(items) + cols - 1) // cols
S = Image.new("RGB", (cols * Wt, rows * (Ht + 16)), "black"); d = ImageDraw.Draw(S)
for n, (lab, f) in enumerate(items):
    p = os.path.join(P, f)
    try:
        if p.lower().endswith((".webm", ".ogv", ".mp4", ".mov")):
            r = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "quiet", "-ss", "1", "-i", p, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True); im = Image.open(io.BytesIO(r.stdout))
        else: im = Image.open(p)
        im = im.convert("RGB"); im.thumbnail((Wt, Ht))
    except Exception: im = Image.new("RGB", (Wt, Ht), "gray")
    x = (n % cols) * Wt; y = (n // cols) * (Ht + 16); S.paste(im, (x + (Wt - im.width) // 2, y + 16)); d.text((x + 2, y + 2), lab, fill="yellow")
S.save(out, quality=85); print(out, len(items))
