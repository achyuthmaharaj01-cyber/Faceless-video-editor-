"""Search + download licensed media for each shot; write an asset licence log.
Providers (keyless first): Wikimedia Commons, Openverse, NASA Images. Keyed (only if env var set):
PEXELS_API_KEY, PIXABAY_API_KEY, UNSPLASH_ACCESS_KEY.
Licences accepted: CC0, Public Domain / PDM, CC BY, CC BY-SA, Pexels, Pixabay, Unsplash licences.
Rejected (logged as 'rejected'): NC, ND, 'fair use', unknown.
Usage:
  python -I source_assets.py search "<query>" [--kind image|video] [--n 8]          -> prints candidates (JSON)
  python -I source_assets.py fetch <url> <dest> --meta '<json from search>' --log assets/LICENSES.csv --shot s012
The skill drives this per shot (see SKILL.md step 3); Claude looks at the candidates and picks."""
import sys, os, json, csv, re, argparse, urllib.parse, urllib.request, urllib.error, time
UA = {"User-Agent": "tierlist-skill/1.0 (video research tool)"}
OK = re.compile(r"^(cc0|cc-?0|public domain|pd|pdm|pd-.*|cc by(-sa)?( \d\.\d)?|cc-by(-sa)?(-\d\.\d)?|pexels|pixabay|unsplash|no restrictions)", re.I)
BAD = re.compile(r"(nc|nd|non-?commercial|no ?deriv|fair use)", re.I)
_last = [0.0]
def get(url, headers=None, tries=5):
    """polite GET: >=1.5 s between requests, exponential backoff on 429/5xx"""
    for k in range(tries):
        wait = 1.5 - (time.time() - _last[0])
        if wait > 0: time.sleep(wait)
        _last[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={**UA, **(headers or {})})
            with urllib.request.urlopen(req, timeout=40) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and k < tries - 1:
                time.sleep(min(20, int(e.headers.get("Retry-After") or 0) or 6 * 2 ** k)); continue
            raise
def lic_ok(l):
    l = (l or "").strip()
    return bool(l) and bool(OK.search(l)) and not BAD.search(l.replace("cc by-sa", "").replace("CC BY-SA", ""))
def commons(q, kind, n):
    ft = "filetype:bitmap" if kind == "image" else "filetype:video"
    u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search", "gsrsearch": f"{q} {ft}",
        "gsrnamespace": 6, "gsrlimit": n, "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1920})
    d = json.loads(get(u)); out = []
    for p in (d.get("query", {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]; em = ii.get("extmetadata", {})
        v = lambda k: re.sub("<[^>]+>", "", (em.get(k) or {}).get("value", "")).strip()
        out.append({"provider": "wikimedia_commons", "title": p["title"], "url": ii.get("url"), "thumb": ii.get("thumburl"), "w": ii.get("width"), "h": ii.get("height"),
                    "mime": ii.get("mime"), "page": ii.get("descriptionurl"), "author": v("Artist")[:120], "license": v("LicenseShortName"), "license_url": v("LicenseUrl"),
                    "duration": ii.get("duration")})
    return out
def openverse(q, kind, n):
    if kind != "image": return []
    u = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode({"q": q, "page_size": n, "license_type": "commercial,modification"})
    d = json.loads(get(u))
    return [{"provider": "openverse:" + r.get("source", ""), "title": r.get("title"), "url": r.get("url"), "thumb": r.get("thumbnail"), "w": r.get("width"), "h": r.get("height"),
             "page": r.get("foreign_landing_url"), "author": r.get("creator"), "license": f"CC {r.get('license','').upper()} {r.get('license_version','')}".replace("CC PDM", "PDM").replace("CC CC0", "CC0").strip(),
             "license_url": r.get("license_url")} for r in d.get("results", [])]
def nasa(q, kind, n):
    u = "https://images-api.nasa.gov/search?" + urllib.parse.urlencode({"q": q, "media_type": "image" if kind == "image" else "video"})
    d = json.loads(get(u)); out = []
    for it in d.get("collection", {}).get("items", [])[:n]:
        m = it["data"][0]; href = it.get("links", [{}])[0].get("href")
        out.append({"provider": "nasa", "title": m.get("title"), "url": href, "thumb": href, "page": f"https://images.nasa.gov/details/{m.get('nasa_id')}",
                    "author": m.get("center", "NASA"), "license": "Public Domain (NASA)", "license_url": "https://www.nasa.gov/nasa-brand-center/images-and-media/"})
    return out
def pexels(q, kind, n):
    k = os.environ.get("PEXELS_API_KEY")
    if not k: return []
    base = "https://api.pexels.com/videos/search?" if kind == "video" else "https://api.pexels.com/v1/search?"
    d = json.loads(get(base + urllib.parse.urlencode({"query": q, "per_page": n}), {"Authorization": k})); out = []
    for r in d.get("videos" if kind == "video" else "photos", []):
        if kind == "video":
            f = max((f for f in r["video_files"] if (f.get("height") or 0) <= 1080), key=lambda f: f.get("height") or 0, default=None)
            url = f and f["link"]
        else: url = r["src"]["original"]
        out.append({"provider": "pexels", "title": r.get("url"), "url": url, "thumb": r.get("image") or r["src"]["medium"] if kind != "video" else r.get("image"),
                    "page": r.get("url"), "author": (r.get("user") or {}).get("name") or r.get("photographer"), "license": "Pexels License", "license_url": "https://www.pexels.com/license/", "duration": r.get("duration")})
    return out
def pixabay(q, kind, n):
    k = os.environ.get("PIXABAY_API_KEY")
    if not k: return []
    base = "https://pixabay.com/api/videos/?" if kind == "video" else "https://pixabay.com/api/?"
    d = json.loads(get(base + urllib.parse.urlencode({"key": k, "q": q, "per_page": max(3, n)}))); out = []
    for r in d.get("hits", []):
        url = (r.get("videos", {}).get("large") or r.get("videos", {}).get("medium") or {}).get("url") if kind == "video" else r.get("largeImageURL")
        out.append({"provider": "pixabay", "title": r.get("tags"), "url": url, "thumb": r.get("previewURL") or r.get("userImageURL"), "page": r.get("pageURL"),
                    "author": r.get("user"), "license": "Pixabay License", "license_url": "https://pixabay.com/service/license-summary/", "duration": r.get("duration")})
    return out
def unsplash(q, kind, n):
    k = os.environ.get("UNSPLASH_ACCESS_KEY")
    if not k or kind != "image": return []
    d = json.loads(get("https://api.unsplash.com/search/photos?" + urllib.parse.urlencode({"query": q, "per_page": n}), {"Authorization": f"Client-ID {k}"}))
    return [{"provider": "unsplash", "title": r.get("description") or r.get("alt_description"), "url": r["urls"]["full"], "thumb": r["urls"]["small"], "page": r["links"]["html"],
             "author": r["user"]["name"], "license": "Unsplash License", "license_url": "https://unsplash.com/license"} for r in d.get("results", [])]
def archive(q, kind, n):
    """Internet Archive moving images, public-domain / CC0 items only. Downloads redirect to a per-item
    storage host (dnNNNN.us.archive.org) that the network allowlist must permit."""
    if kind != "video": return []
    u = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode({"q": f"{q} AND mediatype:movies AND (licenseurl:*publicdomain*)", "fl[]": ["identifier", "title", "licenseurl", "creator"], "rows": n, "output": "json"}, doseq=True)
    out = []
    for r in json.loads(get(u))["response"]["docs"]:
        try: md = json.loads(get(f"https://archive.org/metadata/{r['identifier']}"))
        except Exception: continue
        f = [x for x in md.get("files", []) if x["name"].lower().endswith(".mp4")]
        if not f: continue
        f = min(f, key=lambda x: int(x.get("size", 1e12)))
        lic = r.get("licenseurl", ""); name = "CC0" if "zero" in lic else "Public Domain"
        out.append({"provider": "internet_archive", "title": r.get("title"), "url": f"https://archive.org/download/{r['identifier']}/{urllib.parse.quote(f['name'])}", "thumb": None,
                    "page": f"https://archive.org/details/{r['identifier']}", "author": str(r.get("creator") or "")[:120], "license": name, "license_url": lic, "duration": float(f.get("length") or 0)})
    return out
def openverse_audio(q, kind, n):
    if kind != "audio": return []
    u = "https://api.openverse.org/v1/audio/?" + urllib.parse.urlencode({"q": q, "page_size": n, "license_type": "commercial,modification"})
    return [{"provider": "openverse:" + r.get("source", ""), "title": r.get("title"), "url": r.get("url"), "page": r.get("foreign_landing_url"), "author": r.get("creator"),
             "license": f"CC {r.get('license','').upper()} {r.get('license_version','')}".replace("CC PDM", "PDM").replace("CC CC0", "CC0").strip(), "license_url": r.get("license_url"),
             "duration": (r.get("duration") or 0) / 1000, "genres": r.get("genres")} for r in json.loads(get(u)).get("results", [])]
PROV = [pexels, pixabay, unsplash, commons, openverse, nasa, archive, openverse_audio]
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("a1"); ap.add_argument("a2", nargs="?")
    ap.add_argument("--kind", default="image"); ap.add_argument("--n", type=int, default=8); ap.add_argument("--meta"); ap.add_argument("--log"); ap.add_argument("--shot", default="")
    ap.add_argument("--providers", default="pexels,pixabay,unsplash,commons,openverse,nasa,archive,openverse_audio"); a = ap.parse_args()
    if a.cmd == "search":
        res = []
        for f in PROV:
            if f.__name__ not in a.providers.split(","): continue
            try: res += f(a.a1, a.kind, a.n)
            except Exception as e: print(f"# {f.__name__}: {e}", file=sys.stderr)
        for r in res: r["license_ok"] = lic_ok(r.get("license"))
        print(json.dumps(res, indent=1))
    elif a.cmd == "fetch":
        meta = json.loads(a.meta) if a.meta else {}
        if meta and not lic_ok(meta.get("license")): raise SystemExit(f"REJECTED licence: {meta.get('license')!r} - pick another candidate or flag for the user")
        os.makedirs(os.path.dirname(a.a2) or ".", exist_ok=True)
        open(a.a2, "wb").write(get(a.a1, tries=2))
        if a.log:
            new = not os.path.exists(a.log)
            with open(a.log, "a", newline="") as fh:
                w = csv.writer(fh)
                if new: w.writerow(["file", "shot", "provider", "title", "author", "license", "license_url", "source_page", "download_url", "fetched_utc", "attribution_required"])
                w.writerow([a.a2, a.shot, meta.get("provider"), meta.get("title"), meta.get("author"), meta.get("license"), meta.get("license_url"), meta.get("page"), a.a1,
                            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "yes" if re.search(r"by", meta.get("license") or "", re.I) and not re.search("pd|cc0", meta.get("license") or "", re.I) else "no"])
        print("saved", a.a2)
