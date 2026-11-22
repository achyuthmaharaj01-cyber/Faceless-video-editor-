"""QA: measure a rendered video with the SAME scripts used on the references and compare to style.json.
Usage: python -I qa_compare.py final.mp4 workdir [--format tier|story] [--ref-analysis <skill>/analysis] [--ref video-3]
Writes workdir/qa_report.md + qa_metrics.json; exit code 1 if any hard metric is out of tolerance."""
import sys, os, json, subprocess, argparse, statistics as st, numpy as np, soundfile as sf, re, warnings
warnings.filterwarnings("ignore")
SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); S = lambda n: os.path.join(SK, "scripts", n)
STYLE = json.load(open(os.path.join(SK, "style.json")))
ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("wd"); ap.add_argument("--format", default="tier")
ap.add_argument("--ref-analysis", default=os.path.join(SK, "analysis")); ap.add_argument("--ref", default="video-3"); a = ap.parse_args()
os.makedirs(a.wd, exist_ok=True); W = lambda n: os.path.join(a.wd, n)
def sh(*c, **k): return subprocess.run(list(c), check=True, capture_output=True, text=True, **k)
dur = float(sh("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.video).stdout)
# 1. cuts (identical detector)
sh("bash", "-c", f'ffmpeg -nostdin -hide_banner -i "{a.video}" -an -vf "fps=30,scale=320:180,scdet=threshold=8:sc_pass=0,metadata=print" -f null - 2> "{W("scdet.err")}"')
sh("python3", "-I", S("cuts_adaptive.py"), a.video, W("adaptive.json"))
sh("python3", "-I", S("cuts_merge.py"), W("scdet.err"), W("adaptive.json"), str(dur), W("cuts.json"))
C = json.load(open(W("cuts.json")))
# 2. frames + graphic detectors + OCR
sh("python3", "-I", S("extract_frames.py"), a.video, W("cuts.json"), W("frames"))
sh("python3", "-I", S("graphic_detect.py"), W("frames"), W("graphics.json"))
sh("python3", "-I", S("ocr_frames.py"), W("frames"), W("ocr.json"))
G = json.load(open(W("graphics.json"))); O = json.load(open(W("ocr.json")))
# 3. audio: transcript of the mix, VO timeline, loudness
sh("ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", a.video, "-vn", "-ac", "2", "-ar", "44100", W("mix.wav"))
sh("python3", "-I", S("transcribe.py"), W("mix.wav"), W("transcript.json"))
sh("python3", "-I", S("vo_timeline.py"), W("mix.wav"), W("transcript.json"), W("vo_timeline.json"))
V = json.load(open(W("vo_timeline.json")))
def lab_stats(R):
    lab, sub = [], []
    for r in R:
        for l in r["lines"]:
            t = l["text"]
            if l["conf"] < 80 or not re.fullmatch(r"[a-z0-9\(\)' .\-,:$]+", t) or not re.search("[a-z]{3}", t): continue
            (sub if l["cy_pct"] >= 75 else lab).append(l)
    f = lambda L, k: round(st.median([x[k] for x in L]), 2) if L else None
    return {"label_h_pct": f(lab, "h_pct"), "label_cy_pct": f(lab, "cy_pct"), "bottom_h_pct": f(sub, "h_pct"), "bottom_cy_pct": f(sub, "cy_pct"), "n_label": len(lab), "n_bottom": len(sub)}
ref = a.ref; RA = lambda n: json.load(open(os.path.join(a.ref_analysis, f"{ref}.{n}.json")))
Rg = RA("graphics"); Rv = RA("vo_timeline"); Ro = RA("ocr"); Rc = RA("cuts")
share = lambda G_, k: round(sum(g[k] for g in G_) / max(1, len(G_)), 3)
mine = {"cuts_per_minute": C["cuts_per_minute"], "shot_median": C["shot_sec"]["median"], "shot_mean": C["shot_sec"]["mean"], "shot_p10": C["shot_sec"]["p10"], "shot_p90": C["shot_sec"]["p90"],
        "price_badge_share": share(G, "price_badge"), "vignette_share": share(G, "vignette"), "tier_chart_share": share(G, "tier_chart"),
        "luma_mean": round(st.mean(g["mean_luma"] for g in G), 1), "sat_mean": round(st.mean(g["mean_sat"] for g in G), 1),
        "vo_share": V["vo_on_share"], "integrated_lufs": V["integrated_lufs_mean_of_valid_parts"], "lufs_vo_on": V["lufs_vo_on"],
        "breath_gaps_per_min": V["off_summary"].get("music_or_sfx", {}).get("per_min", 0), "breath_gap_median_s": V["off_summary"].get("music_or_sfx", {}).get("median_dur"),
        "clip_audio_per_min": V["off_summary"].get("clip_speech", {}).get("per_min", 0), **lab_stats(O)}
refm = {"cuts_per_minute": Rc["cuts_per_minute"], "shot_median": Rc["shot_sec"]["median"], "shot_mean": Rc["shot_sec"]["mean"], "shot_p10": Rc["shot_sec"]["p10"], "shot_p90": Rc["shot_sec"]["p90"],
        "price_badge_share": share(Rg, "price_badge"), "vignette_share": share(Rg, "vignette"), "tier_chart_share": share(Rg, "tier_chart"),
        "luma_mean": round(st.mean(g["mean_luma"] for g in Rg), 1), "sat_mean": round(st.mean(g["mean_sat"] for g in Rg), 1),
        "vo_share": Rv["vo_on_share"], "integrated_lufs": Rv["integrated_lufs_mean_of_valid_parts"], "lufs_vo_on": Rv["lufs_vo_on"],
        "breath_gaps_per_min": Rv["off_summary"]["music_or_sfx"]["per_min"], "breath_gap_median_s": Rv["off_summary"]["music_or_sfx"]["median_dur"],
        "clip_audio_per_min": Rv["off_summary"]["clip_speech"]["per_min"], **lab_stats(Ro)}
# tolerance: relative (r) or absolute (a); hard = blocks delivery
TOL = {"cuts_per_minute": ("r", .15, 1), "shot_median": ("r", .15, 1), "shot_mean": ("r", .2, 1), "shot_p10": ("r", .3, 0), "shot_p90": ("r", .3, 0),
       "price_badge_share": ("a", .12, 0), "vignette_share": ("a", .12, 0), "tier_chart_share": ("a", .1, 0), "luma_mean": ("r", .25, 0), "sat_mean": ("r", .35, 0),
       "vo_share": ("a", .08, 1), "integrated_lufs": ("a", 1.0, 1), "lufs_vo_on": ("a", 1.5, 1), "breath_gaps_per_min": ("r", .5, 0), "breath_gap_median_s": ("r", .5, 0),
       "clip_audio_per_min": ("a", .6, 0), "label_h_pct": ("r", .2, 1), "label_cy_pct": ("a", 8, 0), "bottom_h_pct": ("r", .25, 0), "bottom_cy_pct": ("a", 5, 1)}
rows, fail = [], 0
for k, (mode, tol, hard) in TOL.items():
    m, r = mine.get(k), refm.get(k)
    if m is None or r is None: rows.append((k, r, m, "n/a", "")); continue
    ok = abs(m - r) <= (tol * abs(r) if mode == "r" else tol)
    if not ok and hard: fail += 1
    rows.append((k, r, m, f"{'±' + str(int(tol*100)) + '%' if mode == 'r' else '±' + str(tol)}", "PASS" if ok else ("FAIL" if hard else "warn")))
md = ["| metric | reference (" + ref + ") | this video | tolerance | result |", "|---|---|---|---|---|"] + [f"| {a_} | {b} | {c} | {d} | {e} |" for a_, b, c, d, e in rows]
open(W("qa_report.md"), "w").write("\n".join(md) + "\n")
json.dump({"mine": mine, "ref": refm, "rows": rows}, open(W("qa_metrics.json"), "w"), indent=1)
print("\n".join(md)); print("HARD FAILS:", fail)
sys.exit(1 if fail else 0)
