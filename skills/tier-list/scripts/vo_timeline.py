"""VO on/off architecture from a finished video (or a VO file).
Usage: python -I vo_timeline.py mix.wav transcript.json out.json [--exclude corruption.json] [--vocals vocals.wav]
- Narrator vs other speakers: resemblyzer embeddings per whisper segment, narrator = dominant cluster.
- VO-on = narrator words merged across gaps < MERGE s.  VO-off = the rest (minus excluded regions).
- Each VO-off region is classified by what plays: digital_silence / near_silence / clip_speech / music_or_sfx."""
import sys, json, argparse, numpy as np, soundfile as sf, warnings
warnings.filterwarnings("ignore")
import pyloudnorm as pyln
from resemblyzer import VoiceEncoder
ap = argparse.ArgumentParser(); ap.add_argument("mix"); ap.add_argument("transcript"); ap.add_argument("out")
ap.add_argument("--exclude"); ap.add_argument("--merge", type=float, default=0.35); a = ap.parse_args()
x, sr = sf.read(a.mix, dtype="float32"); mono = x.mean(1) if x.ndim > 1 else x; dur = len(mono) / sr
T = json.load(open(a.transcript)); excl = json.load(open(a.exclude))["regions"] if a.exclude else []
inx = lambda s, e: any(s < r[1] and e > r[0] for r in excl)
segs = [s for s in T["segments"] if not inx(s["s"], s["e"])]
# --- speaker labelling
enc = VoiceEncoder("cpu", verbose=False)
import librosa
def emb(s, e):
    seg = mono[int(s * sr):int(e * sr)]
    seg = librosa.resample(seg, orig_sr=sr, target_sr=16000)
    return enc.embed_utterance(seg) if len(seg) > 16000 * 0.6 else None
E = [emb(s["s"], s["e"]) for s in segs]
idx = [i for i, e in enumerate(E) if e is not None]; M = np.array([E[i] for i in idx])
c = M.mean(0)
for _ in range(5):
    sim = M @ c / np.linalg.norm(c); keep = sim >= np.quantile(sim, 0.4); c = M[keep].mean(0)
sim_all = {i: float(E[i] @ c / np.linalg.norm(c)) for i in idx}
sims = np.array(list(sim_all.values()))
# threshold: valley between modes, bounded
hist, edges = np.histogram(sims, bins=40, range=(0.3, 1.0))
lo_i, hi_i = np.searchsorted(edges, 0.55), np.searchsorted(edges, 0.8)
thr = float(edges[lo_i + int(np.argmin(hist[lo_i:hi_i]))]) if hi_i > lo_i else 0.7
thr = min(0.80, max(0.68, thr))   # references settled at 0.70; few other speakers -> no valley -> clamp
# narrator median F0 (reported; a pitch gate was tried and rejected: some clip speakers share the pitch)
def f0(s, e):
    seg = librosa.resample(mono[int(s * sr):int(e * sr)], orig_sr=sr, target_sr=16000)
    f, v, _ = librosa.pyin(seg, fmin=60, fmax=400, sr=16000, frame_length=1024)
    return float(np.nanmedian(f)) if np.isfinite(f).any() else float("nan")
top = [i for i in idx if sim_all[i] >= max(thr, 0.8)][:40]
nar_f0 = float(np.nanmedian([f0(segs[i]["s"], segs[i]["e"]) for i in top]))
for i, s in enumerate(segs):
    sm = sim_all.get(i, 1.0); s["sim"] = round(sim_all.get(i, -1), 3)
    if sm >= thr: s["speaker"] = "narrator"
    else: s["speaker"] = "other"
# isolation rule: a lone short line (<2.5 s, sim >= 0.55) between narrator lines is the narrator
# (verdict lines sit on top of SFX); real clip audio arrives as runs or longer lines.
for i, s in enumerate(segs):
    if s["speaker"] == "other" and s["e"] - s["s"] < 2.5 and s["sim"] >= 0.55:
        p_ = segs[i - 1]["speaker"] if i > 0 else "narrator"; n_ = segs[i + 1]["speaker"] if i + 1 < len(segs) else "narrator"
        if p_ == "narrator" and n_ == "narrator": s["speaker"] = "narrator"; s["isolation_rule"] = True
# --- words with speaker
words = [w for w in T["words"] if not inx(w["s"], w["e"])]
def spk(t):
    for s in segs:
        if s["s"] - 0.05 <= t <= s["e"] + 0.05: return s["speaker"]
    return "narrator"
for w in words: w["spk"] = spk((w["s"] + w["e"]) / 2)
nar = [(w["s"], w["e"]) for w in words if w["spk"] == "narrator"]
on = []
for s, e in nar:
    if on and s - on[-1][1] < a.merge: on[-1][1] = max(on[-1][1], e)
    else: on.append([s, e])
# --- VO-off regions
meter = pyln.Meter(sr)
def rms_db(s, e):
    seg = mono[int(s * sr):int(e * sr)]; return float(20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9)) if len(seg) else -120
def peak_db(s, e):
    seg = mono[int(s * sr):int(e * sr)]; return float(20 * np.log10(np.abs(seg).max() + 1e-9)) if len(seg) else -120
bounds = [0.0] + [v for r in on for v in r] + [dur]
off = []
for s, e in zip(bounds[0::2], bounds[1::2]):
    if e - s < 0.15: continue
    # split around exclusions
    if inx(s, e): continue
    other_words = [w for w in words if w["spk"] == "other" and s <= w["s"] < e]
    r = rms_db(s, e); pk = peak_db(s, e)
    if pk < -90: kind = "digital_silence"
    elif r < -45: kind = "near_silence"
    elif len(other_words) >= 2: kind = "clip_speech"
    else: kind = "music_or_sfx"
    prev = [w["w"] for w in words if w["e"] <= s + 0.01 and w["spk"] == "narrator"][-6:]
    nxt = [w["w"] for w in words if w["s"] >= e - 0.01 and w["spk"] == "narrator"][:6]
    off.append({"s": round(s, 3), "e": round(e, 3), "dur": round(e - s, 3), "kind": kind, "rms_db": round(r, 1), "peak_db": round(pk, 1),
                "other_words": " ".join(w["w"] for w in other_words)[:160], "before": " ".join(prev), "after": " ".join(nxt)})
# --- loudness: VO-on vs VO-off (short-term windows)
def lufs_regions(regs, min_len=0.4):
    vals = []
    for s, e in regs:
        if e - s < min_len: continue
        seg = x[int(s * sr):int(e * sr)]
        try:
            v = meter.integrated_loudness(seg) if e - s >= 0.4 else None
            if v is not None and np.isfinite(v): vals.append((v, e - s))
        except Exception: pass
    if not vals: return None
    w = np.array([d for _, d in vals]); v = np.array([l for l, _ in vals]); return round(float((v * w).sum() / w.sum()), 1)
valid = [r for r in [[0, dur]]]
segs_valid = []
cur = 0.0
for r in sorted(excl):
    segs_valid.append([cur, r[0]]); cur = r[1]
segs_valid.append([cur, dur])
integ = np.mean([meter.integrated_loudness(x[int(s * sr):int(e * sr)]) for s, e in segs_valid if e - s > 5])
from collections import Counter, defaultdict
kinds = defaultdict(list)
for o in off: kinds[o["kind"]].append(o["dur"])
valid_sec = sum(e - s for s, e in segs_valid)
res = {"duration": dur, "valid_seconds": round(valid_sec, 1), "speaker_threshold": round(thr, 3), "narrator_f0_hz": round(nar_f0, 1),
       "segments_other_speaker": sum(s["speaker"] == "other" for s in segs), "segments_total": len(segs),
       "vo_on_seconds": round(sum(e - s for s, e in on), 1), "vo_on_share": round(sum(e - s for s, e in on) / valid_sec, 3),
       "integrated_lufs_mean_of_valid_parts": round(float(integ), 1),
       "lufs_vo_on": lufs_regions(on), "lufs_by_off_kind": {k: lufs_regions([(o["s"], o["e"]) for o in off if o["kind"] == k]) for k in kinds},
       "off_summary": {k: {"count": len(v), "per_min": round(len(v) / (valid_sec / 60), 2), "median_dur": round(float(np.median(v)), 3),
                           "p90_dur": round(float(np.quantile(v, .9)), 3), "total_s": round(sum(v), 1)} for k, v in kinds.items()},
       "vo_on": [[round(s, 3), round(e, 3)] for s, e in on], "vo_off": off,
       "segments": [{k: s[k] for k in ("s", "e", "text", "speaker", "sim")} for s in segs]}
json.dump(res, open(a.out, "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ("vo_on", "vo_off", "segments")}, indent=1))
