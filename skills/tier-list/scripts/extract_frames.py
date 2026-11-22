"""Extract a full-res frame at the middle of every shot (+ every 0.5 s inside shots >= 1.5 s
in dense minutes when --dense). Usage: python -I extract_frames.py video.mp4 cuts.json outdir [--dense]"""
import sys, json, subprocess, os, argparse
ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("cuts"); ap.add_argument("outdir")
ap.add_argument("--dense", action="store_true"); a = ap.parse_args()
d = json.load(open(a.cuts)); os.makedirs(a.outdir, exist_ok=True)
times = []
for i, (s, e) in enumerate(d["shot_spans"]):
    times.append(("shot", i, round((s + e) / 2, 3)))
    if a.dense:
        t = s + 0.25
        while t < e - 0.2: times.append(("dense", i, round(t, 3))); t += 0.5
man = []
for kind, i, t in times:
    fn = f"{kind}_{i:04d}_{t:08.2f}.jpg"; p = os.path.join(a.outdir, fn)
    if not os.path.exists(p):
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-ss", str(t), "-i", a.video, "-frames:v", "1", "-q:v", "3", p])
    man.append({"kind": kind, "shot": i, "t": t, "file": fn})
json.dump(man, open(os.path.join(a.outdir, "manifest.json"), "w"))
print(len(man))
