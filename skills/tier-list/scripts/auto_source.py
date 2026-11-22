"""Auto-source every shot that has a "query" and no "raw" yet: search providers, pick the first unused
licence-OK candidate (landscape preferred for footage/stills, any shape for "face"/"cutout" roles), download
to assets/raw/, append to assets/LICENSES.csv, and write shot["raw"] + shot["source"] back into the shotlist.
Also sources entry portraits ("face_query") and item photos for badge/spec cutouts ("item_query").
Usage: python -I auto_source.py shotlist.json project_dir [--providers commons,openverse,nasa]
Review afterwards: python -I contact_sheet.py ... and replace bad picks by editing "query" + deleting "raw"."""
import sys, os, json, re, argparse, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import source_assets as SA
ap = argparse.ArgumentParser(); ap.add_argument("shotlist"); ap.add_argument("project"); ap.add_argument("--providers", default="pexels,pixabay,unsplash,openverse,nasa,archive,commons")
a = ap.parse_args(); SLp = a.shotlist; SL = json.load(open(SLp)); P = a.project
raw = os.path.join(P, "assets", "raw"); os.makedirs(raw, exist_ok=True); log = os.path.join(P, "assets", "LICENSES.csv")
cache_p = os.path.join(P, "assets", ".search_cache.json"); cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
bad_hosts = set()
used = set(s.get("source", {}).get("url") for s in SL["shots"] if s.get("source"))
def search(q, kind):
    k = f"{kind}|{q}"
    if k not in cache:
        res = []
        for f in SA.PROV:
            if f.__name__ not in a.providers.split(","): continue
            try: res += f(q, kind, 12)
            except Exception as e: print("  !", f.__name__, e)
        cache[k] = res; json.dump(cache, open(cache_p, "w"))
    return cache[k]
def pick(q, kind, role):
    c = [r for r in search(q, kind) if r.get("url") and SA.lic_ok(r.get("license")) and r["url"] not in used and urllib.parse.urlparse(r["url"]).hostname not in bad_hosts]
    if kind == "image":
        c = [r for r in c if (r.get("w") or 2000) >= 900 and not re.search(r"\.(svg|tif|tiff|pdf|djvu)(\?|$)", r["url"], re.I)]
        if role == "frame": c.sort(key=lambda r: -(1 if (r.get("w") or 16) / max(1, r.get("h") or 9) >= 1.25 else 0))
    else:
        c = [r for r in c if re.search(r"\.(webm|ogv|mp4|mov)(\?|$)", r["url"], re.I) or r["provider"] in ("pexels", "pixabay", "internet_archive")]
    return c
def fetch(r, dest_stem, shot):
    ext = re.search(r"\.(jpe?g|png|webp|gif|webm|ogv|mp4|mov)(\?|$)", r["url"], re.I); ext = (ext.group(1) if ext else ("mp4" if r["provider"] in ("pexels", "pixabay") else "jpg")).lower()
    dest = os.path.join(raw, f"{dest_stem}.{ext}")
    url = r["url"]
    if r["provider"] == "wikimedia_commons" and ext in ("jpg", "jpeg", "png", "webp") and (r.get("w") or 0) > 2600 and r.get("thumb"): url = r["thumb"]  # 1920-wide rendition
    sys.argv = ["source_assets.py", "fetch", url, dest, "--meta", json.dumps(r), "--log", log, "--shot", shot]
    try:
        import runpy; runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "source_assets.py"), run_name="__main__")
    except SystemExit as e:
        print("  !", e); return None
    except Exception as e:
        print("  ! download failed:", str(e)[:120]); used.add(r["url"]); bad_hosts.add(urllib.parse.urlparse(r["url"]).hostname); return None
    used.add(r["url"]); return os.path.relpath(dest, P)
missing = []
for i, s in enumerate(SL["shots"]):
    if s.get("raw") or not s.get("query"): continue
    kind = s.get("kind", "video" if s["type"] in ("clip_audio",) else "image")
    cands = [(kind, r) for r in pick(s["query"], kind, "frame")]
    if kind == "video": cands += [("image", r) for r in pick(s["query"], "image", "frame")]
    got = None
    for kind_, r in cands[:6]:
        got = fetch(r, f"s{i:03d}", f"s{i:03d}")
        if got: kind = kind_; break
    if not got: missing.append((i, s["query"])); continue
    s["raw"] = got; s["source"] = {k: r.get(k) for k in ("provider", "title", "author", "license", "page", "url")}; s["raw_kind"] = kind
    print(f"s{i:03d} {kind:5} {r['provider']:18} {r.get('license','')[:16]:16} {str(r.get('title'))[:60]}")
    json.dump(SL, open(SLp, "w"), indent=1)
for j, e in enumerate(SL.get("entries", [])):
    for role, key in (("face", "face_query"), ("item", "item_query")):
        if e.get(key) and not e.get(f"{role}_raw"):
            got = None
            for r in pick(e[key], "image", role)[:6]:
                got = fetch(r, f"{role}_e{j}", f"entry{j}-{role}")
                if got: break
            if not got: missing.append((f"entry{j}-{role}", e[key])); continue
            e[f"{role}_raw"] = got; e[f"{role}_source"] = {k: r.get(k) for k in ("provider", "title", "author", "license", "page")}
            print(f"entry{j} {role:5} {r['provider']:18} {r.get('license','')[:16]:16} {str(r.get('title'))[:60]}")
            json.dump(SL, open(SLp, "w"), indent=1)
json.dump(SL, open(SLp, "w"), indent=1)
print("MISSING (substitute or flag for the user):", missing if missing else "none")
