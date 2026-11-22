"""Final cut list = scdet score >= HI  U  (LO <= score < HI confirmed by adaptive detector within 0.12 s).
Calibrated by eye on video-3: score>=12 ~94% real; 8-12 ~44% real unless confirmed.
Usage: python -I cuts_merge.py scdet.err adaptive.json duration out.json [--exclude corruption.json]"""
import re, sys, json, argparse, subprocess, os
ap = argparse.ArgumentParser(); ap.add_argument("log"); ap.add_argument("adaptive"); ap.add_argument("dur", type=float); ap.add_argument("out")
ap.add_argument("--exclude"); ap.add_argument("--hi", type=float, default=12); ap.add_argument("--lo", type=float, default=8); a = ap.parse_args()
pairs = [(float(t), float(s)) for s, t in re.findall(r"lavfi\.scd\.score: ([\d.]+), lavfi\.scd\.time: ([\d.]+)", open(a.log, errors="ignore").read())]
ad = json.load(open(a.adaptive))["cuts"]
keep = [(t, s) for t, s in pairs if s >= a.hi or (s >= a.lo and any(abs(t - c) < 0.12 for c in ad))]
# write a fake scdet log for cuts_scdet.py stats
tmp = a.out + ".log"
open(tmp, "w").write("\n".join(f"lavfi.scd.score: {max(s, a.hi):.3f}, lavfi.scd.time: {t}" for t, s in keep))
cmd = ["python3", "-I", os.path.join(os.path.dirname(__file__), "cuts_scdet.py"), tmp, str(a.dur), a.out, "--threshold", str(a.hi)]
if a.exclude: cmd += ["--exclude", a.exclude]
subprocess.run(cmd); os.remove(tmp)
