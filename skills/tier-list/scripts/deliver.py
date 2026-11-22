"""Write the delivery documents next to the final video.
  SHOTLIST.md   time (program) | VO text | visual type | source/query | overlays | SFX | audio mode
  LICENSES.csv  deduplicated licence log, only files that are in the final edit
  CREDITS.txt   attribution lines required by CC BY / BY-SA material (paste into the video description)
  THIRD_PARTY.md every third-party clip/photo + substitutions, for the user's own rights decision
Usage: python -I deliver.py shotlist.json project_dir out_dir"""
import sys, os, json, csv
SL = json.load(open(sys.argv[1])); P = sys.argv[2]; O = sys.argv[3]; os.makedirs(O, exist_ok=True)
tl = json.load(open(os.path.join(P, "timeline_resolved.json")))
shots = sorted(SL["shots"], key=lambda s: s.get("ps", 0))
fmt = lambda t: f"{int(t // 60)}:{t % 60:05.2f}"
rows = ["| # | time | VO text | visual | source / query | overlays | SFX | audio |", "|---|---|---|---|---|---|---|---|"]
for i, s in enumerate(shots):
    ov = ", ".join(f'{o["kind"]}:{o.get("text","").replace(chr(10)," ")}' for o in s.get("overlays", []))
    if s.get("badge"): ov = (ov + ", " if ov else "") + f'badge:{s["badge"]["price"]} {s["badge"].get("model","")}'
    sfx = "tick" if s.get("badge") and (i == 0 or (shots[i - 1].get("badge") or {}).get("key") != s["badge"]["key"]) else ""
    if s["type"] == "tier_chart" and s.get("chart", {}).get("drop"): sfx = "music dropout + hit"
    if s["type"] == "clip_audio": sfx = "whoosh"
    src = (s.get("source") or {}).get("title") or s.get("query") or ""
    audio = "CLIP AUDIO (VO off)" if s["type"] == "clip_audio" else ("VO + bed" + (f' + {s["pause_after"]}s breath' if s.get("pause_after") else ""))
    rows.append(f'| {i} | {fmt(s.get("ps",0))}-{fmt(s.get("pe",0))} | {s.get("text","")[:60]} | {s["type"]} | {str(src)[:50]} | {ov[:70]} | {sfx} | {audio} |')
open(os.path.join(O, "SHOTLIST.md"), "w").write(f"# Shot list - {SL.get('title','')}\n\nTotal {fmt(tl['total'])}, {len(shots)} shots.\n\n" + "\n".join(rows) + "\n")
used = {os.path.normpath(s["raw"]) for s in SL["shots"] if s.get("raw")}
used |= {os.path.normpath(e[k]) for e in SL.get("entries", []) for k in ("face_raw", "item_raw") if e.get(k)}
if SL["audio"].get("music", {}).get("src"): used.add(os.path.normpath(SL["audio"]["music"]["src"]))
log = os.path.join(P, "assets", "LICENSES.csv"); last = {}
for r in csv.DictReader(open(log)):
    f = os.path.normpath(os.path.relpath(os.path.join(os.path.dirname(os.path.dirname(log)), "..", r["file"]), P)) if r["file"].startswith("proj/") else os.path.normpath(r["file"])
    f = f.split("assets/", 1)[-1]; f = "assets/" + f
    last[os.path.normpath(f)] = r
keep = {f: r for f, r in last.items() if f in used}
with open(os.path.join(O, "LICENSES.csv"), "w", newline="") as fh:
    w = csv.writer(fh); cols = ["file", "used_for", "provider", "title", "author", "license", "license_url", "source_page", "attribution_required"]; w.writerow(cols)
    for f, r in sorted(keep.items()): w.writerow([f, r["shot"], r["provider"], r["title"], r["author"], r["license"], r["license_url"], r["source_page"], r["attribution_required"]])
cred = [f'"{r["title"]}" by {r["author"] or "unknown"} ({r["license"]}) {r["source_page"]}' for r in keep.values() if r["attribution_required"] == "yes"]
open(os.path.join(O, "CREDITS.txt"), "w").write("Media credits\n" + "\n".join(sorted(set(cred))) + "\n")
missing_log = sorted(used - set(keep))
third = [f'- {r["shot"]}: "{r["title"]}" - {r["provider"]}, {r["license"]} - {r["source_page"]}' for r in keep.values()]
open(os.path.join(O, "THIRD_PARTY.md"), "w").write("# Third-party media in this edit\n\nEvery file below is licensed for reuse with modification (licence checked at download). "
    "Check them yourself before publishing.\n\n" + "\n".join(sorted(third)) + ("\n\n## Files with no licence record (REVIEW)\n" + "\n".join(missing_log) if missing_log else "") + "\n")
print(f"SHOTLIST.md ({len(shots)} shots), LICENSES.csv ({len(keep)} files), CREDITS.txt ({len(set(cred))} credits), unlogged: {missing_log}")
