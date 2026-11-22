"""Build a cut list from ffmpeg scdet output (stderr log) and report shot statistics.
Usage: python -I cuts_scdet.py <scdet.err> <duration_sec> <out.json> [--threshold 14] [--min-gap 0.15]
ffmpeg pass used to make the log:
  ffmpeg -i in.mp4 -an -vf "fps=30,scale=320:180,scdet=threshold=8:sc_pass=0,metadata=print" -f null - 2> x.err"""
import re, sys, json, argparse, statistics as st
ap = argparse.ArgumentParser(); ap.add_argument("log"); ap.add_argument("dur", type=float); ap.add_argument("out")
ap.add_argument("--threshold", type=float, default=14.0); ap.add_argument("--min-gap", type=float, default=0.15); ap.add_argument("--exclude")
a = ap.parse_args()
pairs = re.findall(r"lavfi\.scd\.score: ([\d.]+), lavfi\.scd\.time: ([\d.]+)", open(a.log, errors="ignore").read())
cands = sorted((float(t), float(s)) for s, t in pairs if float(s) >= a.threshold)
cuts = []
for t, s in cands:
    if cuts and t - cuts[-1][0] < a.min_gap:
        if s > cuts[-1][1]: cuts[-1] = (t, s)
        continue
    cuts.append((t, s))
excl = json.load(open(a.exclude))["regions"] if a.exclude else []
cuts = [c for c in cuts if not any(r[0] - 0.5 <= c[0] <= r[1] + 0.5 for r in excl)]
bounds = [0.0] + [c[0] for c in cuts] + [a.dur]
spans = [(a_, b) for a_, b in zip(bounds, bounds[1:])]
valid = [(a_, b) for a_, b in spans if not any(a_ < r[1] + 0.5 and b > r[0] - 0.5 for r in excl)]
shots = [round(b - a_, 3) for a_, b in valid]
valid_dur = sum(b - a_ for a_, b in valid)
def q(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))]
per_min = [0] * (int(a.dur // 60) + 1)
for t, _ in cuts: per_min[int(t // 60)] += 1
res = {"threshold": a.threshold, "cuts": [{"t": round(t, 3), "score": s} for t, s in cuts],
       "n_shots": len(shots), "cuts_per_minute": round(len(shots) / (valid_dur / 60), 2), "valid_seconds": round(valid_dur, 1), "excluded_regions": excl,
       "shot_sec": {"mean": round(st.mean(shots), 3), "median": round(st.median(shots), 3),
                    "min": min(shots), "max": max(shots), "p10": q(shots, .1), "p90": q(shots, .9)},
       "hist": {k: sum(lo <= x < hi for x in shots) for k, (lo, hi) in
                {"<0.5": (0, .5), "0.5-1": (.5, 1), "1-1.5": (1, 1.5), "1.5-2": (1.5, 2), "2-3": (2, 3), "3-5": (3, 5), "5+": (5, 1e9)}.items()},
       "cuts_by_minute": per_min, "shots": shots, "shot_spans": [[round(x, 3), round(y, 3)] for x, y in valid]}
json.dump(res, open(a.out, "w"), indent=1)
print(a.out, res["n_shots"], res["cuts_per_minute"], res["shot_sec"])
