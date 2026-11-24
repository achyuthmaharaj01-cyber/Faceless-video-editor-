"""Resolve photo shots (scene "photo", p.theme) to real images: fetch the chosen pool candidates, make 1920x1080 render-ready JPEGs
(cover crop, or inset on a blurred darkened copy when the photo is not ~16:9; optional baked vignette), write p.src + credit.
Usage: python -I assign_photos.py shots.json pool.json chosen.json project_dir
  chosen.json = {"theme": [pool_index, ...]}   (the images you picked by eye from the contact sheets; used in order, cycling)
Shots whose theme has no chosen image are converted back to p.fallback (a 3D scene dict) if the plan gave one, else reported."""
import sys, os, json, io, csv, re, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import photo_pool as PP
import numpy as np
from PIL import Image, ImageOps, ImageFilter
shots_p, pool_p, chosen_p, P = sys.argv[1:5]
D = json.load(open(shots_p)); POOL = json.load(open(pool_p)); CH = json.load(open(chosen_p))
raw = os.path.join(P, "assets", "raw"); med = os.path.join(P, "assets", "media"); os.makedirs(raw, exist_ok=True); os.makedirs(med, exist_ok=True)
log = os.path.join(P, "assets", "LICENSES.csv"); used = {}; made = {}
def prep(src, dst, vig):
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    if im.width / im.height >= 1.62: out = ImageOps.fit(im, (1920, 1080), Image.LANCZOS, centering=(0.5, 0.45))
    else:
        bg = ImageOps.fit(im, (1920, 1080), Image.LANCZOS).filter(ImageFilter.GaussianBlur(40)).point(lambda v: int(v * 0.62))
        fg = im.resize((min(1920, int(im.width * 1080 / im.height)), 1080), Image.LANCZOS); bg.paste(fg, ((1920 - fg.width) // 2, 0)); out = bg
    if vig:
        yy, xx = np.mgrid[0:1080, 0:1920]; r = np.sqrt(((xx - 960) / 960) ** 2 + ((yy - 540) / 540) ** 2) / 1.2
        t = np.clip((r - 0.55) / 0.55, 0, 1); k = 1 - 0.58 * (t * t * (3 - 2 * t)); out = Image.fromarray((np.asarray(out).astype(np.float32) * k[..., None]).clip(0, 255).astype("uint8"))
    # soft bottom scrim so the white lowercase captions (86 % of frame height) stay readable on light photos
    yy = np.linspace(0, 1, 1080)[:, None]; t = np.clip((yy - 0.58) / 0.42, 0, 1); k = 1 - 0.52 * (t * t * (3 - 2 * t))
    out = Image.fromarray((np.asarray(out).astype(np.float32) * k[..., None]).clip(0, 255).astype("uint8"))
    out.save(dst, quality=90)
n_ok = 0; miss = []
for s in D["shots"]:
    if s["scene"] != "photo": continue
    p = s["p"]; th = p["theme"]; lst = CH.get(th) or []
    if not p.get("motion"): p["motion"] = "push" if n_ok % 2 == 0 else "pull"   # alternate (style: 60 % push-in / 40 % pull-out)
    if not lst:
        miss.append((s["id"], th)); continue
    if p.get("pick") is not None: idx = lst[p["pick"] % len(lst)]
    else: k = used.get(th, 0); used[th] = k + 1; idx = lst[k % len(lst)]
    key = (th, idx); r = POOL[th][idx]
    if key not in made:
        fn = f"{th}_{idx}"; rawf = os.path.join(raw, fn + ".jpg")
        if not os.path.exists(rawf): open(rawf, "wb").write(PP.get_bytes(r["url"]))
        made[key] = fn
    fn = made[key]; dst = os.path.join(med, f"{fn}{'_v' if p.get('vig') else ''}.jpg")
    if not os.path.exists(dst): prep(os.path.join(raw, fn + ".jpg"), dst, p.get("vig"))
    p["src"] = f"assets/media/{os.path.basename(dst)}"; p["credit"] = {k: r[k] for k in ("title", "author", "license", "page", "provider")}; n_ok += 1
    new = not os.path.exists(log)
    if not any(fn in row for row in (open(log).read().splitlines() if os.path.exists(log) else [])):
        with open(log, "a", newline="") as fh:
            w = csv.writer(fh)
            if new: w.writerow(["file", "shot", "provider", "title", "author", "license", "license_url", "source_page", "download_url", "fetched_utc", "attribution_required"])
            w.writerow([f"assets/raw/{fn}.jpg", s["id"], r["provider"], r["title"], r["author"], r["license"], r["license_url"], r["page"], r["url"], time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "yes" if re.search(r"by", r["license"] or "", re.I) and not re.search("pd|cc0", r["license"] or "", re.I) else "no"])
# photo shots without an image fall back to their 3D scene
for sid, th in miss:
    s = next(x for x in D["shots"] if x["id"] == sid); fb = s["p"].get("fallback")
    if fb: s["scene"] = fb["scene"]; s["p"] = fb.get("p", {}); s["bg"] = fb.get("bg", s["bg"]); print("fallback to 3D:", sid, th, "->", s["scene"])
    else: print("NO IMAGE and no fallback:", sid, th)
json.dump(D, open(shots_p, "w")); print(f"{n_ok} photo shots resolved; {len(miss)} without image")
