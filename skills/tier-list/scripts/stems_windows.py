"""Demucs (htdemucs, vocals/no_vocals) on N evenly spaced windows of a mix, skipping excluded regions.
Usage: python -I stems_windows.py mix.wav outdir [--n 8] [--len 40] [--exclude corruption.json]"""
import sys, json, argparse, subprocess, os, soundfile as sf
ap = argparse.ArgumentParser(); ap.add_argument("mix"); ap.add_argument("outdir"); ap.add_argument("--n", type=int, default=8)
ap.add_argument("--len", type=float, default=40); ap.add_argument("--exclude"); a = ap.parse_args()
info = sf.info(a.mix); dur = info.duration; excl = json.load(open(a.exclude))["regions"] if a.exclude else []
os.makedirs(a.outdir, exist_ok=True); wins = []
step = (dur - a.len) / a.n
for i in range(a.n):
    s = 5 + i * step
    while any(s < r[1] and s + a.len > r[0] for r in excl): s += 5
    if s + a.len > dur: continue
    wins.append([round(s, 2), round(s + a.len, 2)])
for s, e in wins:
    w = os.path.join(a.outdir, f"win_{s:08.2f}.wav")
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", str(s), "-t", str(e - s), "-i", a.mix, w], check=True)
    subprocess.run(["python3", "-m", "demucs", "--two-stems=vocals", "-n", "htdemucs", "-o", a.outdir, w], check=True, capture_output=True)
json.dump({"windows": wins}, open(os.path.join(a.outdir, "windows.json"), "w")); print(wins)
