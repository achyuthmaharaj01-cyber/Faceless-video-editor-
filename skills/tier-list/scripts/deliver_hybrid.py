"""Delivery documents for the hybrid (photo + 3D) mode.
Usage: python -I deliver_hybrid.py shots.json sentences.json project_dir out_dir
Writes SHOTLIST.md (program time | spoken words | visual | source | overlays | SFX), LICENSES.csv (only photos used in the edit),
CREDITS.txt (CC BY / BY-SA lines for the video description), THIRD_PARTY.md and metrics.json (cuts/min, photo share, shot-length stats)."""
import sys, os, json, csv, statistics as st
shots_p, sent_p, P, O = sys.argv[1:5]; os.makedirs(O, exist_ok=True)
D = json.load(open(shots_p)); SD = json.load(open(sent_p))["sentences"]; words = [w for s in SD for w in s["words"]]
fmt = lambda t: f"{int(t // 60)}:{t % 60:05.2f}"
rows = ["| # | time | spoken words | visual | source | overlays | sfx |", "|---|---|---|---|---|---|---|"]
for i, s in enumerate(D["shots"]):
    spoken = " ".join(w["w"] for w in words if s["ps"] - 0.02 <= w["s"] < s["pe"])[:70]
    if s["scene"] == "photo":
        c = s["p"].get("credit", {}); vis = f"PHOTO ({s['p']['theme']})"; src = f"{c.get('title','')[:38]} - {c.get('license','')}"
    else: vis = f"3D {s['scene']}"; src = "built in three.js"
    ov = ", ".join(f"{o['kind']}:{str(o.get('text', o.get('price', '')))[:28].replace(chr(10), ' ')}" for o in s.get("ov", []))
    sfx = ", ".join(e["kind"] for e in s.get("sfx", []))
    rows.append(f"| {i} | {fmt(s['ps'])}-{fmt(s['pe'])} | {spoken} | {vis} | {src} | {ov[:80]} | {sfx} |")
open(os.path.join(O, "SHOTLIST.md"), "w").write(f"# Shot list\n\nTotal {fmt(D['total'])}, {len(D['shots'])} shots.\n\n" + "\n".join(rows) + "\n")
used = {s["p"]["src"].split("/")[-1].replace("_v", "").rsplit(".", 1)[0] for s in D["shots"] if s["scene"] == "photo"}
log = os.path.join(P, "assets", "LICENSES.csv"); keep = []
for r in csv.DictReader(open(log)):
    if os.path.basename(r["file"]).rsplit(".", 1)[0] in used: keep.append(r)
with open(os.path.join(O, "LICENSES.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["file", "used_in_shot", "provider", "title", "author", "license", "license_url", "source_page", "attribution_required"])
    for r in keep: w.writerow([r["file"], r["shot"], r["provider"], r["title"], r["author"], r["license"], r["license_url"], r["source_page"], r["attribution_required"]])
cred = sorted({f'"{r["title"]}" by {r["author"] or "unknown"} ({r["license"]}) {r["source_page"]}' for r in keep if r["attribution_required"] == "yes"})
open(os.path.join(O, "CREDITS.txt"), "w").write("Photo credits\n" + "\n".join(cred) + "\n")
open(os.path.join(O, "THIRD_PARTY.md"), "w").write("# Third-party media in this edit\n\nEvery photo below was licensed for reuse with modification at download time (Openverse licence filter). "
    "Check each yourself before publishing. No game footage, screenshots or trailers are used. 3D graphics, SFX and the music bed are generated in code (no third-party audio).\n\n"
    + "\n".join(f'- {r["file"]}: "{r["title"]}" - {r["provider"]}, {r["license"]} - {r["source_page"]}' for r in keep) + "\n")
d = [s["pe"] - s["ps"] for s in D["shots"]]; ph = sum(s["scene"] == "photo" for s in D["shots"])
M = {"shots": len(d), "photo_shots": ph, "photo_share": round(ph / len(d), 3), "cuts_per_minute": round(len(d) / (D["total"] / 60), 1), "shot_median_s": round(st.median(d), 2),
     "shot_mean_s": round(st.mean(d), 2), "shot_p10_s": round(sorted(d)[len(d) // 10], 2), "shot_p90_s": round(sorted(d)[int(len(d) * .9)], 2), "photos_with_attribution": len(cred)}
json.dump(M, open(os.path.join(O, "metrics.json"), "w"), indent=1); print(M)
