#!/usr/bin/env python3
"""Original sound design, synthesised from scratch (no third-party samples, so no licence questions).

  synth.py sfx   --cues CUES_JSON --duration SEC --out sfx.wav
  synth.py music --duration SEC --out bed.wav [--mood curious|tense|uplifting|dramatic] [--bpm N] [--seed N]
  synth.py list

SFX vocabulary (matches the reference analysis: transitions land on whooshes, labels on pops, money on a
cash ding, reveals on impacts): whoosh, swish, pop, click, impact, thud, riser, cash, ding, marker.
Everything is deterministic (seeded noise), 48 kHz stereo, peak-safe.
"""
import argparse
import json
import math
import sys
import wave

import numpy as np

SR = 48000


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    pcm = (x * 32767).astype(np.int16)
    if pcm.ndim == 1:
        pcm = np.stack([pcm, pcm], axis=1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def env(n, attack, release, shape=2.0):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    r = np.clip((n / SR - t) / max(release, 1e-4), 0, 1)
    return (a * r) ** shape


def bandnoise(n, rng, lo, hi):
    """Noise band-limited by FFT masking (lo/hi may be arrays → time-varying via STFT blocks)."""
    x = rng.standard_normal(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    y = np.fft.irfft(X, n)
    return y / (np.abs(y).max() + 1e-9)


def sweep_noise(n, rng, f0, f1, width=0.6):
    """Noise whose centre frequency glides f0→f1 (block-wise band-pass)."""
    out = np.zeros(n)
    blk = 1024
    x = rng.standard_normal(n + blk)
    for i in range(0, n, blk // 2):
        seg = x[i:i + blk]
        if len(seg) < blk:
            break
        c = f0 * (f1 / f0) ** (i / max(1, n))
        S = np.fft.rfft(seg * np.hanning(blk))
        f = np.fft.rfftfreq(blk, 1 / SR)
        S *= np.exp(-0.5 * (np.log((f + 1) / c) / width) ** 2)
        y = np.fft.irfft(S, blk)
        out[i:i + blk] += y[:max(0, min(blk, n - i))]
    return out / (np.abs(out).max() + 1e-9)


def pan(x, p):  # p: -1..1 scalar or array
    p = np.asarray(p)
    l = np.cos((p + 1) * math.pi / 4); r = np.sin((p + 1) * math.pi / 4)
    return np.stack([x * l, x * r], axis=1)


def make(name, rng):
    if name in ("whoosh", "swish"):
        dur = 0.42 if name == "whoosh" else 0.22
        n = int(dur * SR)
        x = sweep_noise(n, rng, 500 if name == "whoosh" else 1500, 3500 if name == "whoosh" else 6000, 0.7)
        e = np.sin(np.linspace(0, math.pi, n)) ** 2.2
        return pan(x * e * 0.8, np.linspace(-0.6, 0.6, n))
    if name == "pop":
        n = int(0.09 * SR); t = np.arange(n) / SR
        f = 950 * np.exp(-t * 28) + 260
        x = np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-t * 38)
        x[:60] += np.linspace(0.5, 0, 60)
        return pan(x * 0.7, 0)
    if name == "click":
        n = int(0.025 * SR)
        x = bandnoise(n, rng, 2000, 9000) * np.exp(-np.arange(n) / SR * 260)
        return pan(x * 0.55, 0)
    if name in ("impact", "thud"):
        dur = 1.1 if name == "impact" else 0.4
        n = int(dur * SR); t = np.arange(n) / SR
        f = 48 + 70 * np.exp(-t * 18)
        body = np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-t * (4.5 if name == "impact" else 11))
        hit = bandnoise(n, rng, 60, 2500) * np.exp(-t * 30) * 0.6
        x = np.tanh((body + hit) * 1.6) * 0.85
        return pan(x, 0)
    if name == "riser":
        n = int(1.3 * SR); t = np.arange(n) / SR
        f = 180 * (8 ** (t / t[-1]))
        tone = np.sin(2 * math.pi * np.cumsum(f) / SR) * 0.25
        nz = sweep_noise(n, rng, 400, 7000, 0.9) * 0.5
        e = (t / t[-1]) ** 2.2
        e[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR))
        return pan((tone + nz) * e * 0.8, np.sin(t * 6) * 0.3)
    if name in ("cash", "ding"):
        n = int(0.9 * SR); t = np.arange(n) / SR
        base = 1568.0
        x = sum(a * np.sin(2 * math.pi * base * r * t) * np.exp(-t * d) for r, a, d in [(1, 1, 5), (2.76, .5, 8), (5.4, .25, 12), (8.93, .12, 16)])
        if name == "cash":
            k = bandnoise(int(0.06 * SR), rng, 1500, 8000) * np.exp(-np.arange(int(0.06 * SR)) / SR * 70) * 0.6
            x[:len(k)] += k
        return pan(x / 1.9 * 0.7, 0.1)
    if name == "marker":
        n = int(0.3 * SR); t = np.arange(n) / SR
        x = bandnoise(n, rng, 2500, 7000) * (0.5 + 0.5 * np.sin(2 * math.pi * 23 * t)) * env(n, 0.02, 0.06, 1)
        return pan(x * 0.35, 0.2)
    raise SystemExit(f"unknown sfx {name}")


SFX = ["whoosh", "swish", "pop", "click", "impact", "thud", "riser", "cash", "ding", "marker"]


def render_sfx(cues, duration):
    out = np.zeros((int(duration * SR) + SR, 2))
    rng = np.random.default_rng(7)
    cache = {}
    last = {}
    for c in cues:
        name = c.get("name") or c.get("k")
        if name not in SFX:
            print(f"warning: unknown cue {name}", file=sys.stderr); continue
        t = float(c.get("t", 0))
        if name in last and t - last[name] < 0.12:   # never stack the same sound within 120 ms
            continue
        last[name] = t
        if name not in cache:
            cache[name] = make(name, rng)
        s = cache[name] * 10 ** (float(c.get("gain", c.get("g", 0))) / 20)
        start = int(t * SR) - (int(1.25 * SR) if name == "riser" else 0)   # a riser ends on its cue
        if start < 0:
            s = s[-start:]; start = 0
        end = min(len(out), start + len(s))
        out[start:end] += s[:end - start]
    return out[:int(duration * SR)]


MOODS = {  # (scale degrees of chords in semitones from root, root Hz, bpm, brightness)
    "curious": ([[0, 3, 7], [8, 12, 15], [3, 7, 10], [10, 14, 17]], 110.0, 96, 0.55),
    "tense": ([[0, 3, 7], [1, 5, 8], [0, 3, 7], [11, 14, 18]], 98.0, 88, 0.4),
    "uplifting": ([[0, 4, 7], [7, 11, 14], [9, 12, 16], [5, 9, 12]], 130.8, 104, 0.7),
    "dramatic": ([[0, 3, 7], [8, 12, 15], [5, 8, 12], [7, 11, 14]], 87.3, 76, 0.45),
}


def render_music(duration, mood="curious", bpm=None, seed=3):
    chords, root, b, bright = MOODS.get(mood, MOODS["curious"])
    bpm = bpm or b
    beat = 60.0 / bpm
    n = int(duration * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    rng = np.random.default_rng(seed)
    bar = beat * 4
    for k in range(int(duration / bar) + 1):
        ch = chords[k % len(chords)]
        s0 = int(k * bar * SR); s1 = min(n, int((k + 1) * bar * SR) + int(0.3 * SR))
        if s0 >= n:
            break
        tt = np.arange(s1 - s0) / SR
        pad = np.zeros(s1 - s0)
        for st in ch:
            f = root * 2 ** (st / 12)
            for det in (-0.12, 0.12):
                ph = rng.uniform(0, 2 * math.pi)
                pad += np.sin(2 * math.pi * f * (1 + det / 100) * tt + ph) + 0.3 * np.sin(4 * math.pi * f * tt + ph)
        e = np.clip(tt / 0.6, 0, 1) * np.clip((tt[-1] - tt) / 0.5, 0, 1)
        out[s0:s1] += pan(pad * e * 0.05, 0)
        # plucked arpeggio, 8th notes
        for j in range(8):
            a0 = s0 + int(j * beat / 2 * SR)
            if a0 >= n:
                break
            st = ch[j % 3] + 12 * (1 + (j // 3) % 2)
            f = root * 2 ** (st / 12)
            L = min(int(0.5 * SR), n - a0)
            ta = np.arange(L) / SR
            pl = (np.sin(2 * math.pi * f * ta) + bright * 0.4 * np.sin(4 * math.pi * f * ta)) * np.exp(-ta * 7)
            out[a0:a0 + L] += pan(pl * 0.06, 0.35 if j % 2 else -0.35)
        # soft kick on beats 1 and 3, shaker on off-beats
        for j in (0, 2):
            a0 = s0 + int(j * beat * SR)
            if a0 >= n:
                break
            L = min(int(0.25 * SR), n - a0); ta = np.arange(L) / SR
            kick = np.sin(2 * math.pi * np.cumsum(45 + 90 * np.exp(-ta * 30)) / SR) * np.exp(-ta * 14)
            out[a0:a0 + L] += pan(kick * 0.16, 0)
        for j in range(4):
            a0 = s0 + int((j + 0.5) * beat * SR)
            if a0 >= n:
                break
            L = min(int(0.05 * SR), n - a0)
            sh = rng.standard_normal(L) * np.exp(-np.arange(L) / SR * 80)
            out[a0:a0 + L] += pan(sh * 0.012, 0.2)
    fade = int(min(2.0, duration / 4) * SR)
    out[:fade] *= np.linspace(0, 1, fade)[:, None]
    out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return out / (np.abs(out).max() + 1e-9) * 0.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["sfx", "music", "list"])
    ap.add_argument("--cues"); ap.add_argument("--duration", type=float); ap.add_argument("--out")
    ap.add_argument("--mood", default="curious"); ap.add_argument("--bpm", type=float); ap.add_argument("--seed", type=int, default=3)
    a = ap.parse_args()
    if a.what == "list":
        print(json.dumps({"sfx": SFX, "moods": list(MOODS)})); return
    if a.what == "sfx":
        cues = json.load(open(a.cues))
        cues = cues.get("cues", cues) if isinstance(cues, dict) else cues
        write_wav(a.out, render_sfx(cues, a.duration))
    else:
        write_wav(a.out, render_music(a.duration, a.mood, a.bpm, a.seed))
    print(json.dumps({"out": a.out}))


if __name__ == "__main__":
    main()
