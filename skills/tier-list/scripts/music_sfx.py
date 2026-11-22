"""Music bed + SFX analysis on demucs windows (no_vocals stem).
Usage: python -I music_sfx.py stems_dir vo_timeline.json cuts.json out.json
Per window: momentary loudness (400 ms, 100 ms hop) of the no_vocals stem, split by VO on/off -> ducking depth;
attack/release from VO boundaries; tempo; SFX = transients >= 6 dB above the local bed median, classified
by duration / spectral centroid / low-band share; offset to the nearest cut."""
import sys, os, json, glob, numpy as np, soundfile as sf, librosa, warnings
warnings.filterwarnings("ignore")
sd, vo_p, cuts_p, out = sys.argv[1:5]
VO = json.load(open(vo_p)); on = VO["vo_on"]; C = [c["t"] for c in json.load(open(cuts_p))["cuts"]]
wins = json.load(open(os.path.join(sd, "windows.json")))["windows"]
def in_on(t): return any(s <= t <= e for s, e in on)
def lufs_m(y, sr, hop=0.1, win=0.4):
    # momentary loudness approximation: K-weighting omitted -> RMS dBFS of 400 ms windows (relative values only)
    n, h = int(win * sr), int(hop * sr)
    return np.array([20 * np.log10(np.sqrt((y[i:i + n] ** 2).mean()) + 1e-9) for i in range(0, len(y) - n, h)])
res = {"windows": [], "sfx": []}
on_lv, off_lv, tempos, attacks, releases = [], [], [], [], []
for s0, e0 in wins:
    d = os.path.join(sd, "htdemucs", f"win_{s0:08.2f}")
    nv, sr = sf.read(os.path.join(d, "no_vocals.wav"), dtype="float32"); nv = nv.mean(1)
    vc, _ = sf.read(os.path.join(d, "vocals.wav"), dtype="float32"); vc = vc.mean(1)
    L = lufs_m(nv, sr); t = s0 + 0.2 + np.arange(len(L)) * 0.1
    Lv = lufs_m(vc, sr)
    mask_on = np.array([in_on(x) for x in t])
    on_lv += list(L[mask_on]); off_lv += list(L[~mask_on & (L > -60)])
    tempo = float(librosa.feature.tempo(y=nv, sr=sr, aggregate=np.median)[0]); tempos.append(tempo)
    # attack/release: around VO on->off boundaries, time for bed to move 63% of its jump
    for s, e in on:
        for b, kind in ((e, "release"), (s, "attack")):
            if not (s0 + 1.5 < b < e0 - 1.5): continue
            i = int(np.argmin(abs(t - b))); pre = np.median(L[max(0, i - 8):i - 1]); post_seg = L[i:i + 15]
            if len(post_seg) < 10: continue
            post = np.median(post_seg[5:]); jump = post - pre
            if abs(jump) < 3: continue
            k = np.argmax((post_seg - pre) / jump >= 0.63) * 0.1
            (releases if kind == "release" else attacks).append(round(float(k), 2))
    # SFX transients
    on_env = librosa.onset.onset_strength(y=nv, sr=sr, hop_length=512)
    peaks = librosa.util.peak_pick(on_env, pre_max=5, post_max=5, pre_avg=20, post_avg=20, delta=np.std(on_env) * 1.5, wait=10)
    bed = np.median(L)
    for p in peaks:
        tt = p * 512 / sr; i0 = int(tt * sr)
        seg = nv[max(0, i0 - int(0.05 * sr)): i0 + int(0.8 * sr)]
        if len(seg) < 2048: continue
        lvl = 20 * np.log10(np.sqrt((seg[:int(0.3 * sr)] ** 2).mean()) + 1e-9)
        if lvl < bed + 6: continue
        env = np.abs(librosa.stft(seg, n_fft=2048, hop_length=256)); en = env.sum(0)
        above = en > en.max() * 0.25; dur = above.sum() * 256 / sr
        cent = float(librosa.feature.spectral_centroid(S=env, sr=sr).mean())
        f = librosa.fft_frequencies(sr=sr, n_fft=2048); low = env[f < 150].sum() / env.sum()
        flat = float(librosa.feature.spectral_flatness(S=env).mean())
        rise = int(np.argmax(en)) * 256 / sr  # time to peak
        if low > 0.45: kind = "boom/impact"
        elif flat > 0.25 and dur > 0.25: kind = "whoosh/swish"
        elif dur < 0.15 and cent > 2500: kind = "click/pop"
        elif flat < 0.05 and cent > 1500: kind = "ding/chime (tonal)"
        else: kind = "hit/other"
        T = s0 + tt; nc = min(C, key=lambda c: abs(c - T)) if C else None
        vo_spk = float(np.sqrt((vc[i0:i0 + int(0.3 * sr)] ** 2).mean()))
        res["sfx"].append({"t": round(T, 3), "kind": kind, "lvl_over_bed_db": round(lvl - bed, 1), "dur": round(dur, 2),
                           "centroid": round(cent), "low_share": round(float(low), 2), "flatness": round(flat, 3), "peak_after_onset_s": round(rise, 3),
                           "nearest_cut_offset_ms": round((T - nc) * 1000) if nc is not None else None, "during_vo": in_on(T)})
    res["windows"].append({"s": s0, "e": e0, "tempo": round(tempo, 1), "bed_median_db": round(float(bed), 1)})
from collections import Counter
total_min = sum(e - s for s, e in wins) / 60
offs = [x["nearest_cut_offset_ms"] for x in res["sfx"] if x["nearest_cut_offset_ms"] is not None]
res["summary"] = {
    "bed_db_under_vo_median": round(float(np.median(on_lv)), 1), "bed_db_vo_off_median": round(float(np.median(off_lv)), 1),
    "ducking_depth_db": round(float(np.median(off_lv) - np.median(on_lv)), 1),
    "attack_s_median": float(np.median(attacks)) if attacks else None, "release_s_median": float(np.median(releases)) if releases else None,
    "n_attack": len(attacks), "n_release": len(releases),
    "tempo_bpm_median": round(float(np.median(tempos)), 1), "tempo_by_window": [round(x) for x in tempos],
    "sfx_per_min": round(len(res["sfx"]) / total_min, 1), "sfx_kinds_per_min": {k: round(v / total_min, 1) for k, v in Counter(x["kind"] for x in res["sfx"]).items()},
    "sfx_within_100ms_of_cut": round(sum(abs(o) <= 100 for o in offs) / max(1, len(offs)), 2),
    "sfx_offset_to_cut_ms_median_when_within_250": float(np.median([o for o in offs if abs(o) <= 250])) if any(abs(o) <= 250 for o in offs) else None,
    "analysed_minutes": round(total_min, 1)}
json.dump(res, open(out, "w"), indent=1, default=float); print(json.dumps(res["summary"], indent=1))
