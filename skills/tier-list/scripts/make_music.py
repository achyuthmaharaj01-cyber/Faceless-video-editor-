"""Generate a licence-free music bed (numpy only): ~118 BPM modern pop/trap-ish beat for narrated videos.
Kick + clap + swung hats, sub bass, plucked arpeggio, soft pad; 8-bar sections with variations so it does
not loop audibly; seeded -> identical every run.  The reference bed is a ~120 BPM beat under the narration.
Usage: python -I make_music.py out.wav [--seconds 480] [--bpm 118] [--seed 7]"""
import sys, argparse, numpy as np, soundfile as sf
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--seconds", type=float, default=480); ap.add_argument("--bpm", type=float, default=118); ap.add_argument("--seed", type=int, default=7)
a = ap.parse_args(); SR = 44100; rng = np.random.default_rng(a.seed)
beat = 60 / a.bpm; step = beat / 4; bar = beat * 4; N = int(a.seconds * SR); out = np.zeros((N, 2), dtype=np.float32)
def put(x, t, pan=0.0, g=1.0):
    i = int(t * SR)
    if i >= N: return
    x = x[: N - i] * g; out[i:i + len(x), 0] += x * (1 - max(0, pan)); out[i:i + len(x), 1] += x * (1 + min(0, pan))
def env(n, a_, d_): t = np.arange(n) / SR; return np.minimum(t / max(a_, 1e-4), 1) * np.exp(-t / d_)
def kick():
    n = int(0.42 * SR); t = np.arange(n) / SR; f = 46 + 110 * np.exp(-t / 0.035); ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-t / 0.16) + 0.25 * np.sin(2 * ph) * np.exp(-t / 0.05)).astype(np.float32)
def clap():
    n = int(0.30 * SR); x = np.zeros(n); nz = rng.normal(0, 1, n)
    for k, off in enumerate((0, 0.011, 0.022)): s0 = int(off * SR); x[s0:] += nz[: n - s0] * np.exp(-np.arange(n - s0) / SR / 0.05) * (0.6 + 0.2 * k)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR); X[(f < 900) | (f > 7000)] = 0; return np.fft.irfft(X, n).astype(np.float32) * 0.5
def hat(open_=False):
    n = int((0.18 if open_ else 0.05) * SR); x = rng.normal(0, 1, n); X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR); X[f < 6500] = 0
    return (np.fft.irfft(X, n) * env(n, 0.001, 0.09 if open_ else 0.018)).astype(np.float32) * 0.22
def bass(freq, dur):
    n = int(dur * SR); t = np.arange(n) / SR; x = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(4 * np.pi * freq * t)
    return (np.tanh(x * 1.6) * env(n, 0.005, dur * 0.8) * np.minimum(1, (dur - t) / 0.03)).astype(np.float32) * 0.55
def pluck(freq, dur=0.28):
    n = int(dur * SR); t = np.arange(n) / SR; x = sum(np.sin(2 * np.pi * freq * k * t) / k for k in (1, 2, 3, 4)); return (x * env(n, 0.002, 0.09)).astype(np.float32) * 0.16
def pad(freqs, dur):
    n = int(dur * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for f0 in freqs:
        for det in (-0.004, 0.0, 0.004): x += np.sin(2 * np.pi * f0 * (1 + det) * t + rng.uniform(0, 6.28))
    e = np.minimum(t / 0.6, 1) * np.minimum(1, (dur - t) / 0.8); return (x * e / (3 * len(freqs))).astype(np.float32) * 0.5
mid = lambda m_: 440 * 2 ** ((m_ - 69) / 12)
prog = [(45, (57, 60, 64)), (41, (53, 57, 60)), (48, (55, 60, 64)), (43, (55, 59, 62))]        # Am F C G (bass root, chord)
K, C, H, HO = kick(), clap(), hat(), hat(True)
nbars = int(a.seconds / bar) + 1
for b in range(nbars):
    t0 = b * bar; root, chord = prog[b % 4]; sec = (b // 8) % 4; intro = b < 4
    swing = 0.012
    put(pad([mid(n_) for n_ in chord] + [mid(chord[0] - 12)], bar * 1.02), t0, 0, 0.5 if sec != 2 else 0.75)
    for s in range(16):
        t = t0 + s * step + (swing if s % 2 else 0)
        if s in (0, 10) or (s == 7 and sec in (1, 3)) or (s == 14 and b % 2 and sec != 0): put(K, t, 0, 0.9)
        if s in (4, 12) and not intro: put(C, t, 0.1, 0.8)
        if s % 2 == 0 and not intro or (intro and s % 4 == 0): put(H, t, -0.2, 0.7 if s % 4 else 1.0)
        if s == 15 and b % 4 == 3: put(HO, t, 0.2, 0.8)
        if s in (0, 3, 6, 10, 12) and sec != 0 or s == 0: put(bass(mid(root), step * (2.6 if s in (0, 6) else 1.6)), t, 0, 0.9)
        if sec in (1, 2, 3) and s % 2 == 0 and not intro:
            arp = [chord[(s // 2) % 3] + 12, chord[((s // 2) + 1) % 3] + 24][(s // 2) % 2]
            put(pluck(mid(arp)), t, (-0.3 if (s // 2) % 2 else 0.3), 0.8 if sec == 2 else 0.5)
out /= max(1e-6, np.abs(out).max()) * 1.05
import pyloudnorm as pyln
l = pyln.Meter(SR).integrated_loudness(out); out *= 10 ** ((-14 - l) / 20); out = np.tanh(out * 0.9) / 0.9
sf.write(a.out, out, SR); print(f"{a.out} {a.seconds}s {a.bpm}bpm, loudness {pyln.Meter(SR).integrated_loudness(out):.1f} LUFS")
