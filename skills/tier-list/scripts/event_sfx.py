"""Event-locked SFX measurement. For each visual event class, cut a snippet [-1.0,+1.5] s around every
event from the mix, run demucs once on the concatenation, and measure the transient in the no_vocals stem
relative to (a) the snippet's own pre-event bed and (b) random-time control snippets.
Usage: python -I event_sfx.py mix.wav events.json workdir out.json
events.json = {"class_name": [t, ...], ...}   (a "random" class is added automatically)"""
import sys, os, json, subprocess, numpy as np, soundfile as sf, librosa, random, warnings
warnings.filterwarnings("ignore")
mix, evp, wd, out = sys.argv[1:5]; os.makedirs(wd, exist_ok=True)
EV = json.load(open(evp)); x, sr = sf.read(mix, dtype="float32"); dur = len(x) / sr
excl = EV.pop("_exclude", [])
random.seed(7); allt = [t for v in EV.values() for t in v]
rnd = []
while len(rnd) < 40:
    t = random.uniform(5, dur - 5)
    if all(abs(t - u) > 1.5 for u in allt) and not any(r[0] - 2 < t < r[1] + 2 for r in excl): rnd.append(t)
EV["random_control"] = rnd
PRE, POST, GAP = 1.0, 1.5, 0.5
items, chunks, pos = [], [], 0.0
for k, ts in EV.items():
    for t in ts:
        s = int((t - PRE) * sr); e = int((t + POST) * sr)
        if s < 0 or e > len(x): continue
        chunks.append(x[s:e]); chunks.append(np.zeros((int(GAP * sr), x.shape[1]), dtype="float32"))
        items.append((k, t, pos)); pos += PRE + POST + GAP
cat = os.path.join(wd, "events_concat.wav"); sf.write(cat, np.concatenate(chunks), sr)
subprocess.run(["python3", "-m", "demucs", "--two-stems=vocals", "-n", "htdemucs", "-o", wd, cat], check=True, capture_output=True)
nv, _ = sf.read(os.path.join(wd, "htdemucs", "events_concat", "no_vocals.wav"), dtype="float32"); nv = nv.mean(1)
def rms_db(y): return 20 * np.log10(np.sqrt((y ** 2).mean()) + 1e-9)
rows = []
for k, t, p in items:
    seg = nv[int(p * sr): int((p + PRE + POST) * sr)]
    bed = rms_db(seg[int(0.1 * sr): int(0.8 * sr)])                     # -0.9..-0.2 s
    hop = int(0.01 * sr); win = int(0.05 * sr)
    env = np.array([rms_db(seg[i:i + win]) for i in range(int(0.8 * sr), int(1.9 * sr), hop)])  # -0.2..+0.9 s
    i = int(np.argmax(env)); peak_t = -0.2 + i * 0.01
    # onset: first frame within 6 dB of the peak
    j = int(np.argmax(env >= env[i] - 6)); onset_t = -0.2 + j * 0.01
    tail = env[i:]; decay = float(np.argmax(tail < env[i] - 12) * 0.01) if (tail < env[i] - 12).any() else 0.9
    post = seg[int((PRE + onset_t) * sr): int((PRE + onset_t + 0.4) * sr)]
    S = np.abs(librosa.stft(post, n_fft=2048, hop_length=256)) if len(post) > 2048 else None
    cent = float(librosa.feature.spectral_centroid(S=S, sr=sr).mean()) if S is not None else 0
    flat = float(librosa.feature.spectral_flatness(S=S).mean()) if S is not None else 0
    f = librosa.fft_frequencies(sr=sr, n_fft=2048); low = float(S[f < 150].sum() / (S.sum() + 1e-9)) if S is not None else 0
    rows.append({"class": k, "t": round(t, 3), "rise_db": round(float(env[i] - bed), 1), "onset_ms": round(onset_t * 1000), "peak_ms": round(peak_t * 1000),
                 "decay_12db_s": round(decay, 2), "centroid": round(cent), "flatness": round(flat, 3), "low_share": round(low, 2)})
summ = {}
ctrl = [r["rise_db"] for r in rows if r["class"] == "random_control"]; thr = float(np.quantile(ctrl, 0.8)) if ctrl else 6
for k in EV:
    R = [r for r in rows if r["class"] == k]
    if not R: continue
    hit = [r for r in R if r["rise_db"] > thr]
    summ[k] = {"n": len(R), "median_rise_db": round(float(np.median([r["rise_db"] for r in R])), 1),
               "hit_rate_vs_random_p80": round(len(hit) / len(R), 2),
               "onset_ms_median_hits": float(np.median([r["onset_ms"] for r in hit])) if hit else None,
               "peak_ms_median_hits": float(np.median([r["peak_ms"] for r in hit])) if hit else None,
               "decay_s_median_hits": float(np.median([r["decay_12db_s"] for r in hit])) if hit else None,
               "centroid_median_hits": float(np.median([r["centroid"] for r in hit])) if hit else None,
               "flatness_median_hits": float(np.median([r["flatness"] for r in hit])) if hit else None}
json.dump({"random_p80_rise_db": round(thr, 1), "summary": summ, "rows": rows}, open(out, "w"), indent=1)
print(json.dumps({"random_p80_rise_db": round(thr, 1), "summary": summ}, indent=1))
