#!/usr/bin/env python3
"""Signal-level QC of a rendered video: container/stream spec, black frames, frozen frames, loudness and
true peak, silences, and audio sync against the project's mix (cross-correlation).

Usage: av_checks.py VIDEO --mix audio/mix.wav [--fps 30]   → JSON on stdout
"""
import argparse
import json
import re
import subprocess

import numpy as np


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    d = json.loads(run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path]).stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), {})
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), {})
    num, den = (v.get("r_frame_rate") or "0/1").split("/")
    nb = v.get("nb_frames")
    return {"duration": float(d["format"].get("duration", 0)), "width": v.get("width"), "height": v.get("height"),
            "fps": round(float(num) / float(den), 3) if float(den) else None, "video_codec": v.get("codec_name"),
            "pix_fmt": v.get("pix_fmt"), "profile": v.get("profile"), "frames": int(nb) if nb else None,
            "video_duration": float(v.get("duration", 0) or 0),
            "audio_codec": a.get("codec_name"), "audio_channels": a.get("channels"), "audio_rate": int(a["sample_rate"]) if a.get("sample_rate") else None,
            "audio_duration": float(a.get("duration", 0) or 0), "bitrate_kbps": round(int(d["format"].get("bit_rate", 0)) / 1000)}


def detect(path):
    r = run(["ffmpeg", "-nostats", "-i", path, "-vf", "blackdetect=d=0.2:pix_th=0.08,freezedetect=n=0.0015:d=2",
             "-af", "ebur128=peak=true,silencedetect=noise=-50dB:d=1.5", "-f", "null", "-"])
    log = r.stderr
    black = [{"start": float(a), "end": float(b), "duration": float(c)} for a, b, c in
             re.findall(r"black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)", log)]
    fz_s = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", log)]
    fz_e = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", log)]
    frozen = [{"start": s, "end": e, "duration": round(e - s, 3)} for s, e in zip(fz_s, fz_e + [None] * (len(fz_s) - len(fz_e))) if e]
    if len(fz_s) > len(fz_e):
        frozen.append({"start": fz_s[-1], "end": None, "duration": None})
    sil_s = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", log)]
    sil_e = [(float(a), float(b)) for a, b in re.findall(r"silence_end: ([\d.]+) \| silence_duration: ([\d.]+)", log)]
    silences = [{"start": max(0, s), "end": e, "duration": d} for s, (e, d) in zip(sil_s, sil_e)]
    summ = log[log.rfind("Summary:"):]
    def g(k):
        m = re.search(rf"{k}:\s+(-?[\d.]+|-inf)", summ)
        return None if not m or m.group(1) == "-inf" else float(m.group(1))
    return {"black": black, "frozen": frozen, "silences": silences,
            "loudness": {"integrated_lufs": g("I"), "lra_lu": g("LRA"), "true_peak_dbtp": g("Peak")}}


def pcm(path, sr=8000, t=None):
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(sr)]
    if t:
        cmd += ["-t", str(t)]
    out = subprocess.run(cmd + ["-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(out, np.float32)


def sync(video, mix, sr=8000, seconds=60):
    """Offset of the video's audio against the mix (positive = video audio late)."""
    a = pcm(video, sr, seconds); b = pcm(mix, sr, seconds)
    n = min(len(a), len(b))
    if n < sr:
        return None
    a, b = a[:n] - a[:n].mean(), b[:n] - b[:n].mean()
    N = 1 << int(np.ceil(np.log2(2 * n)))
    c = np.fft.irfft(np.fft.rfft(a, N) * np.conj(np.fft.rfft(b, N)), N)
    max_lag = int(0.5 * sr)
    c = np.concatenate([c[-max_lag:], c[:max_lag + 1]])
    lag = int(np.argmax(c)) - max_lag
    peak = float(c.max() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-9))
    # tail: the last 50 ms should be quiet (no abrupt cut)
    tail = pcm(video, 16000)
    tail_db = float(20 * np.log10(np.sqrt(np.mean(tail[-800:] ** 2)) + 1e-9)) if len(tail) > 800 else None
    return {"offset_ms": round(lag / sr * 1000, 1), "correlation": round(peak, 3), "tail_rms_db": round(tail_db, 1) if tail_db is not None else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--mix"); ap.add_argument("--fps", type=float, default=30)
    a = ap.parse_args()
    out = {"probe": probe(a.video), **detect(a.video)}
    if a.mix:
        out["sync"] = sync(a.video, a.mix)
    print(json.dumps(out))


if __name__ == "__main__":
    main()
