"""Theme-based photo pool for the hybrid (photo + 3D) mode.
  search : python -I photo_pool.py search themes.json pool.json [--n 18] [--min-w 1000]
           themes.json = {"theme": ["query", ...], ...}; each query = ONE Openverse request (anonymous limit 20/min, 200/day),
           so requests are spaced 3.2 s. Keeps licence-OK results (CC0/PDM/CC BY/CC BY-SA/...), width >= --min-w, no svg/tif.
  sheets : python -I photo_pool.py sheets pool.json outdir [--per 8] [--cols 4]
           numbered contact sheets (thumbnails from Openverse's own thumb endpoint) for choosing by eye.
  fetch  : python -I photo_pool.py fetch pool.json theme idx dest.jpg [--log LICENSES.csv --shot sNNN]
           downloads one chosen candidate (full image) and appends the licence log row.
Pool entries keep provider/author/licence/page URL for CREDITS."""
import sys, os, json, re, time, io, argparse, csv
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import source_assets as SA
from PIL import Image, ImageDraw

def search(themes, out, n, min_w):
    pool = json.load(open(out)) if os.path.exists(out) else {}
    seen = {r["url"] for v in pool.values() for r in v}
    for th, qs in themes.items():
        if th in pool and pool[th]: print("skip (have)", th); continue
        res = []
        for q in qs:
            for attempt in range(3):
                time.sleep(3.2)
                try: res += SA.openverse(q, "image", n); break
                except Exception as e: print("  !", th, q, str(e)[:80]); time.sleep(8)
        keep = []
        for r in res:
            u = r.get("url") or ""
            if not u or u in seen or not SA.lic_ok(r.get("license")): continue
            if (r.get("w") or 0) < min_w or re.search(r"\.(svg|tif|tiff|pdf|gif)(\?|$)", u, re.I): continue
            if "wikimedia" in u: continue   # upload.wikimedia.org rate-limits shared cloud IPs (429)
            seen.add(u); keep.append({k: r.get(k) for k in ("provider", "title", "author", "license", "license_url", "page", "url", "thumb", "w", "h")})
        pool[th] = keep; json.dump(pool, open(out, "w"), indent=1); print(f"{th:18} {len(keep):3} usable of {len(res)}")
    return pool

def get_bytes(url): return SA.get(url, tries=3)

def sheets(pool, outdir, per, cols):
    os.makedirs(outdir, exist_ok=True); th_list = [t for t, v in pool.items() if v]; Wt, Ht = 300, 190; files = []
    # one sheet = several themes stacked; each theme row shows its first `per` candidates
    rows_per_sheet = 5; chunks = [th_list[i:i + rows_per_sheet] for i in range(0, len(th_list), rows_per_sheet)]
    for ci, chunk in enumerate(chunks):
        S = Image.new("RGB", (per * Wt, len(chunk) * (Ht + 18)), "black"); d = ImageDraw.Draw(S)
        for ri, th in enumerate(chunk):
            for k, r in enumerate(pool[th][:per]):
                try:
                    im = Image.open(io.BytesIO(get_bytes(r["thumb"] or r["url"]))).convert("RGB"); im.thumbnail((Wt - 4, Ht - 2))
                except Exception: im = Image.new("RGB", (Wt - 4, Ht - 2), "#552")
                x = k * Wt; y = ri * (Ht + 18); S.paste(im, (x + 2, y + 18)); d.text((x + 3, y + 3), f"{th}#{k}  {r['license']}  {r['w']}x{r['h']}", fill="yellow")
        f = os.path.join(outdir, f"pool_sheet_{ci:02d}.jpg"); S.save(f, quality=82); files.append(f)
    print("\n".join(files))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("a"); ap.add_argument("b"); ap.add_argument("c", nargs="?"); ap.add_argument("d", nargs="?")
    ap.add_argument("--n", type=int, default=18); ap.add_argument("--min-w", type=int, default=1000); ap.add_argument("--per", type=int, default=8); ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--log"); ap.add_argument("--shot", default="")
    x = ap.parse_args()
    if x.cmd == "search": search(json.load(open(x.a)), x.b, x.n, x.min_w)
    elif x.cmd == "sheets": sheets(json.load(open(x.a)), x.b, x.per, x.cols)
    elif x.cmd == "fetch":
        pool = json.load(open(x.a)); r = pool[x.b][int(x.c)]; meta = dict(r)
        os.makedirs(os.path.dirname(x.d) or ".", exist_ok=True); open(x.d, "wb").write(get_bytes(r["url"]))
        if x.log:
            new = not os.path.exists(x.log)
            with open(x.log, "a", newline="") as fh:
                w = csv.writer(fh)
                if new: w.writerow(["file", "shot", "provider", "title", "author", "license", "license_url", "source_page", "download_url", "fetched_utc", "attribution_required"])
                w.writerow([x.d, x.shot, r["provider"], r["title"], r["author"], r["license"], r["license_url"], r["page"], r["url"], time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "yes" if re.search(r"by", r["license"] or "", re.I) and not re.search("pd|cc0", r["license"] or "", re.I) else "no"])
        print("saved", x.d, r["license"], "|", r["title"])
