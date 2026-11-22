"""Generate the style's base assets in code (no third-party artwork, no licence issues):
  chart/road.png    top-down two-lane road with grass verges (tier chart background, 1920x668)
  chart/cursor.png  mouse pointer used for the drag
  chart/pin.png     red map pin
  sfx/*.wav         SFX matched to the measured spectra (style.json audio.sfx):
                    tick_a/b/c  bright tick, centroid ~5.5 kHz, peak at +60 ms, 12 dB decay ~0.2 s   (price badge)
                    hit_a/b     short low impact, decay ~0.1-0.25 s                                (verdict)
                    whoosh_a/b  band-passed noise swell, peak ~190 ms, decay ~0.6 s                 (clip/vignette in)
Usage: python -I make_base_assets.py <project>/assets   (seeded -> identical every run)"""
import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFilter
import soundfile as sf

out = sys.argv[1]; os.makedirs(f"{out}/chart", exist_ok=True); os.makedirs(f"{out}/sfx", exist_ok=True)
rng = np.random.default_rng(42)

# ---------- road.png ----------
W, H = 1920, 668
g = rng.normal(0, 1, (H // 4, W // 4)); img = Image.fromarray(((g - g.min()) / (g.max() - g.min()) * 255).astype("uint8")).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(2))
n = np.asarray(img).astype(float) / 255
fine = rng.normal(0, 1, (H, W)) * 0.08
grass = np.stack([60 + 50 * n + 30 * fine, 120 + 70 * n + 40 * fine, 30 + 30 * n + 20 * fine], -1)
a = grass.copy()
def band(y0, y1, col, noise=10):
    a[y0:y1] = np.array(col)[None, None, :] + rng.normal(0, noise, (y1 - y0, W, 1))
band(86, 286, (128, 128, 130)); band(302, 497, (126, 126, 128))          # two lanes (asphalt), measured 8%-46% of frame
band(286, 302, (150, 150, 150), 6)                                         # median strip
a = np.clip(a, 0, 255).astype("uint8"); road = Image.fromarray(a); d = ImageDraw.Draw(road)
for y in (88, 282, 304, 491): d.rectangle([0, y, W, y + 5], fill=(235, 235, 235))   # edge lines
for y in (184, 397):
    for x in range(0, W, 140): d.rectangle([x, y, x + 70, y + 4], fill=(230, 230, 230))  # dashed centre lines
road = road.filter(ImageFilter.GaussianBlur(0.6)); road.save(f"{out}/chart/road.png")

# ---------- cursor.png (classic arrow, white fill, black edge) ----------
c = Image.new("RGBA", (34, 50), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
pts = [(2, 2), (2, 40), (11, 31), (18, 47), (24, 44), (17, 29), (30, 29)]
d.polygon(pts, fill=(255, 255, 255, 255), outline=(0, 0, 0, 255)); d.line(pts + [pts[0]], fill=(0, 0, 0, 255), width=2)
c.save(f"{out}/chart/cursor.png")

# ---------- pin.png ----------
p = Image.new("RGBA", (180, 240), (0, 0, 0, 0)); d = ImageDraw.Draw(p)
d.ellipse([20, 10, 160, 150], fill=(226, 38, 43, 255)); d.polygon([(34, 110), (146, 110), (90, 232)], fill=(226, 38, 43, 255))
d.ellipse([62, 52, 118, 108], fill=(140, 18, 22, 255)); p.save(f"{out}/chart/pin.png")

# ---------- SFX ----------
SR = 44100
def env_ad(n, attack, decay_tau):
    t = np.arange(n) / SR; e = np.where(t < attack, t / attack, np.exp(-(t - attack) / decay_tau)); return e
def bandpass(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0; return np.fft.irfft(X, len(x))
def norm(x, peak_db=-3):
    return (x / (np.abs(x).max() + 1e-9) * 10 ** (peak_db / 20)).astype("float32")
def save(name, x): sf.write(f"{out}/sfx/{name}.wav", np.stack([x, x], 1), SR)
for i, (f0, seed) in enumerate([(5200, 1), (5800, 2), (6100, 3)]):
    r = np.random.default_rng(seed); n = int(0.35 * SR); t = np.arange(n) / SR
    noise = bandpass(r.normal(0, 1, n), f0 - 1800, f0 + 2600)
    tone = np.sin(2 * np.pi * (f0 + 900) * t) * 0.35 + np.sin(2 * np.pi * (f0 * 1.5) * t) * 0.15
    x = (noise + tone) * env_ad(n, 0.055, 0.05)           # 12 dB decay ~ 0.06 * ln(4) * ... -> ~0.2 s total tail
    save(f"tick_{'abc'[i]}", norm(x, -4))
for i, (f0, seed) in enumerate([(70, 4), (58, 5)]):
    r = np.random.default_rng(seed); n = int(0.5 * SR); t = np.arange(n) / SR
    sweep = np.sin(2 * np.pi * (f0 + 90 * np.exp(-t / 0.03)) * t)
    click = bandpass(r.normal(0, 1, n), 1200, 6000) * np.exp(-t / 0.008)
    x = sweep * env_ad(n, 0.004, 0.09) + 0.5 * click
    save(f"hit_{'ab'[i]}", norm(x, -2))
for i, seed in enumerate([6, 7]):
    r = np.random.default_rng(seed); n = int(0.9 * SR); t = np.arange(n) / SR
    x = np.zeros(n); noise = r.normal(0, 1, n)
    # moving band: low->high->low, peak ~0.19 s
    for k, (lo, hi) in enumerate([(300, 900), (600, 2000), (1200, 3500), (800, 2400), (400, 1200)]):
        seg = bandpass(noise, lo, hi); w = np.exp(-((t - (0.05 + 0.09 * k)) / 0.09) ** 2); x += seg * w
    x *= env_ad(n, 0.19, 0.22)
    save(f"whoosh_{'ab'[i]}", norm(x, -6))
print("assets written to", out)
