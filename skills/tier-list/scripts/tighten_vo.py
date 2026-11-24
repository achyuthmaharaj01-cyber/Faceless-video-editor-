"""Tighten a voiceover the way the reference editor does: every pause longer than --max-gap is shortened
to --to (default 0.30 -> 0.24 s). The reference keeps only ~3.6 breath gaps/min (median 0.46 s); the skill
re-adds those deliberately (pause_after on verdicts and [PAUSE] markers) with the music bed underneath.
Run BEFORE transcribe.py.   Usage: python -I tighten_vo.py vo_in.(wav|mp3|m4a) vo_out.wav [--max-gap 0.30] [--to 0.24]"""
import sys, argparse, subprocess, numpy as np, soundfile as sf, os, tempfile
ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("dst"); ap.add_argument("--max-gap", type=float, default=0.22); ap.add_argument("--to", type=float, default=0.14)
ap.add_argument("--keep-long", type=float, default=None, help="pauses >= this (s) are sentence/paragraph breaks: shorten to --long-to instead of --to")
ap.add_argument("--long-to", type=float, default=0.4)
a = ap.parse_args()
tmp = tempfile.mktemp(suffix=".wav"); subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", a.src, "-ar", "48000", tmp], check=True)
x, sr = sf.read(tmp, dtype="float32"); os.remove(tmp)
m = x.mean(1) if x.ndim > 1 else x; hop = int(0.01 * sr)
db = np.array([20 * np.log10(np.sqrt((m[i:i + hop] ** 2).mean()) + 1e-9) for i in range(0, len(m) - hop, hop)])
speech = db > (np.median(db[db > np.quantile(db, 0.5)]) - 26)        # 26 dB under typical speech level = pause (breaths included)
# runs of silence
keep = np.ones(len(m), bool); removed = 0.0; n = 0; i = 0; cuts = []
while i < len(speech):
    if not speech[i]:
        j = i
        while j < len(speech) and not speech[j]: j += 1
        dur = (j - i) * 0.01
        if dur > a.max_gap and i > 0 and j < len(speech):
            tgt = a.long_to if (a.keep_long and dur >= a.keep_long) else a.to; cut = dur - tgt; s0 = int((i * 0.01 + tgt / 2) * sr); keep[s0:s0 + int(cut * sr)] = False; removed += cut; n += 1; cuts.append([round(s0 / sr, 4), round(cut, 4)])
        i = j
    else: i += 1
y = x[keep]
# 3 ms crossfade-free cut is fine inside silence; write
sf.write(a.dst, y, sr)
import json; json.dump({"removed": cuts}, open(os.path.splitext(a.dst)[0] + ".timemap.json", "w"))   # for remap_times.py
print(f"shortened {n} pauses, removed {removed:.2f}s ({len(m)/sr:.2f}s -> {len(y)/sr:.2f}s)")
