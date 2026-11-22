"""Side-by-side frame sheet: one frame per graphic/treatment class from the render next to the matching
reference frame from references/frames/ (same class). Classes come from graphic_detect.py + OCR zones.
Usage: python -I frame_compare.py qa_workdir out.jpg   (run after qa_compare.py, which made frames + graphics.json)"""
import sys, os, json, glob
from PIL import Image, ImageDraw
SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); wd, out = sys.argv[1], sys.argv[2]
G = json.load(open(os.path.join(wd, "graphics.json"))); O = {r["file"]: r for r in json.load(open(os.path.join(wd, "ocr.json")))}
def cls(g):
    if g["tier_chart"]: return "tier_chart"
    if g["price_badge"]: return "price_badge"
    lines = O.get(g["file"], {}).get("lines", [])
    if any(l["cy_pct"] >= 75 and l["conf"] > 80 for l in lines): return "bottom_text"
    if any(l["cy_pct"] < 75 and l["conf"] > 80 for l in lines): return "label"
    if g["vignette"]: return "vignette"
    return "plain"
picked = {}
for g in G: picked.setdefault(cls(g), g)
rows = []
for c, g in picked.items():
    refs = sorted(glob.glob(os.path.join(SK, "references", "frames", f"{c}_*.jpg")))
    rows.append((c, os.path.join(wd, "frames", g["file"]), refs[0] if refs else None))
S = Image.new("RGB", (2 * 640, len(rows) * 376), "black"); d = ImageDraw.Draw(S)
for i, (c, mine, ref) in enumerate(rows):
    for j, p in enumerate((ref, mine)):
        if p and os.path.exists(p): im = Image.open(p).convert("RGB").resize((640, 360)); S.paste(im, (j * 640, i * 376 + 16))
    d.text((4, i * 376 + 2), f"{c}: reference (left) vs render (right)", fill="yellow")
S.save(out, quality=88); print(out, [r[0] for r in rows])
