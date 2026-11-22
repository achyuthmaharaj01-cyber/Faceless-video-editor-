"""Tile before/after frames for candidate cuts in a score band, to calibrate the scdet threshold by eye.
Usage: python -I cut_calibration_sheet.py video.mp4 scdet.err lo hi out.jpg [n]"""
import sys, re, random, subprocess, io
from PIL import Image, ImageDraw
v, log, lo, hi, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
n = int(sys.argv[6]) if len(sys.argv) > 6 else 16
pairs = [(float(t), float(s)) for s, t in re.findall(r"lavfi\.scd\.score: ([\d.]+), lavfi\.scd\.time: ([\d.]+)", open(log, errors="ignore").read())]
c = [p for p in pairs if lo <= p[1] < hi]; random.seed(1); c = sorted(random.sample(c, min(n, len(c))))
def fr(t):
    r = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "quiet", "-ss", f"{max(t,0):.3f}", "-i", v, "-frames:v", "1", "-vf", "scale=240:-1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
    return Image.open(io.BytesIO(r.stdout))
W, H = 240, 135; S = Image.new("RGB", (W * 4, (H + 14) * ((len(c) + 1) // 2)), "black"); d = ImageDraw.Draw(S)
for i, (t, s) in enumerate(c):
    x = (i % 2) * W * 2; y = (i // 2) * (H + 14)
    S.paste(fr(t - 0.07), (x, y + 14)); S.paste(fr(t + 0.03), (x + W, y + 14))
    d.text((x + 2, y), f"{t:.2f}s score {s:.1f}", fill="yellow")
S.save(out); print(len(c))
