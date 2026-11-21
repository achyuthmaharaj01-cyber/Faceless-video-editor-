#!/usr/bin/env python3
"""Single-pass, low-memory analysis of one reference video.

Decodes the video once through FFmpeg at a small analysis size, and from that one
stream computes: cut detection (HSV content difference, fixed + adaptive), fades,
per-shot motion (camera push/pull/pan via dense optical flow), brightness,
saturation and dominant colours. A second, cheaper pass handles audio (loudness,
transients, speech timing). Frames are only written for what the report needs.

Memory stays flat (one or two small frames in RAM at a time), so this runs on a
16 GB laptop as well as in the cloud. Every stage caches its result as JSON in the
output folder and is skipped on re-run unless --force is given.

Usage:
    python scripts/reference-analysis/analyze_reference.py VIDEO --out DIR [--id N]
        [--analysis-fps 30] [--no-transcribe] [--whisper-model base.en] [--force]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

try:
    import cv2
except ImportError:  # pragma: no cover
    sys.exit("opencv-python-headless is required: pip install -r requirements.txt")

AW, AH = 320, 180          # analysis frame size (16:9)
FLOW_W, FLOW_H = 160, 90   # optical-flow size
CUT_THRESHOLD = 27.0       # PySceneDetect ContentDetector default
ADAPTIVE_RATIO = 3.0       # PySceneDetect AdaptiveDetector default
ADAPTIVE_MIN = 15.0
MIN_SHOT_SEC = 0.25


# ----------------------------------------------------------------------------- utils

def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def ffprobe(path: Path) -> dict:
    data = json.loads(run(["ffprobe", "-v", "error", "-print_format", "json",
                           "-show_format", "-show_streams", str(path)]))
    v = next((s for s in data["streams"] if s["codec_type"] == "video"), {})
    a = next((s for s in data["streams"] if s["codec_type"] == "audio"), {})
    num, den = (v.get("avg_frame_rate") or "0/1").split("/")
    fps = float(num) / float(den) if float(den) else 0.0
    w, h = int(v.get("width", 0)), int(v.get("height", 0))
    g = math.gcd(w, h) or 1
    return {
        "file": path.name,
        "size_bytes": int(data["format"].get("size", 0)),
        "duration_sec": round(float(data["format"].get("duration", 0)), 3),
        "width": w, "height": h, "aspect_ratio": f"{w // g}:{h // g}",
        "fps": round(fps, 3),
        "video_codec": v.get("codec_name"), "video_profile": v.get("profile"),
        "pix_fmt": v.get("pix_fmt"),
        "video_bitrate_kbps": round(int(v.get("bit_rate", 0)) / 1000) if v.get("bit_rate") else None,
        "audio_codec": a.get("codec_name"),
        "audio_channels": a.get("channels"),
        "audio_sample_rate": int(a["sample_rate"]) if a.get("sample_rate") else None,
        "audio_bitrate_kbps": round(int(a.get("bit_rate", 0)) / 1000) if a.get("bit_rate") else None,
        "overall_bitrate_kbps": round(int(data["format"].get("bit_rate", 0)) / 1000),
    }


def cached(out: Path, name: str, force: bool):
    p = out / name
    if p.exists() and not force:
        return json.loads(p.read_text())
    return None


def save(out: Path, name: str, obj) -> None:
    (out / name).write_text(json.dumps(obj, indent=1))


def fmt_ts(t: float) -> str:
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{s:05.2f}"


# ----------------------------------------------------------------------- video pass

def video_pass(path: Path, afps: float) -> dict:
    """Decode once at AWxAH/afps and compute per-frame features."""
    cmd = ["ffmpeg", "-v", "error", "-i", str(path), "-an", "-sn",
           "-vf", f"fps={afps},scale={AW}:{AH}:flags=area", "-pix_fmt", "bgr24",
           "-f", "rawvideo", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=AW * AH * 3 * 8)
    fsize = AW * AH * 3
    content, luma, sat, flow_zoom, flow_px, flow_py, flow_res = [], [], [], [], [], [], []
    prev_hsv = None
    prev_g = None
    # flow grid for zoom estimate (divergence relative to centre)
    ys, xs = np.mgrid[0:FLOW_H, 0:FLOW_W].astype(np.float32)
    cx, cy = (FLOW_W - 1) / 2, (FLOW_H - 1) / 2
    rx, ry = xs - cx, ys - cy
    rr = rx * rx + ry * ry + 1e-6
    colour_acc = []   # sparse colour samples for palette (every 15th frame)
    i = 0
    t0 = time.time()
    while True:
        buf = proc.stdout.read(fsize)
        if len(buf) < fsize:
            break
        frame = np.frombuffer(buf, np.uint8).reshape(AH, AW, 3)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.int16)
        if prev_hsv is None:
            content.append(0.0)
        else:
            d = np.abs(hsv - prev_hsv).reshape(-1, 3).mean(axis=0)
            content.append(float(d.mean()))
        prev_hsv = hsv
        luma.append(float(hsv[..., 2].mean()))
        sat.append(float(hsv[..., 1].mean()))
        g = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (FLOW_W, FLOW_H), interpolation=cv2.INTER_AREA)
        if prev_g is None:
            flow_zoom.append(0.0); flow_px.append(0.0); flow_py.append(0.0); flow_res.append(0.0)
        else:
            fl = cv2.calcOpticalFlowFarneback(prev_g, g, None, 0.5, 2, 9, 2, 5, 1.1, 0)
            fx, fy = fl[..., 0], fl[..., 1]
            px, py = float(np.median(fx)), float(np.median(fy))
            # radial component → scale change per frame (positive = zoom in)
            zx, zy = fx - px, fy - py
            zoom = float(np.median((zx * rx + zy * ry) / rr))
            resid = zx - zoom * rx, zy - zoom * ry
            res = float(np.mean(np.hypot(resid[0], resid[1])))
            flow_zoom.append(zoom); flow_px.append(px); flow_py.append(py); flow_res.append(res)
        prev_g = g
        if i % 15 == 0:
            colour_acc.append(cv2.resize(frame, (32, 18), interpolation=cv2.INTER_AREA).reshape(-1, 3))
        i += 1
        if i % (int(afps) * 120) == 0:
            print(f"  video pass: {i / afps / 60:.1f} min analysed ({time.time() - t0:.0f}s)", flush=True)
    proc.wait()
    return {
        "afps": afps, "n": i, "content": content, "luma": luma, "sat": sat,
        "zoom": flow_zoom, "px": flow_px, "py": flow_py, "res": flow_res,
        "colours": np.concatenate(colour_acc).tolist() if colour_acc else [],
        "seconds": round(time.time() - t0, 1),
    }


def detect_cuts(content: list[float], afps: float) -> list[int]:
    """Frame indices that start a new shot."""
    c = np.asarray(content)
    cuts = []
    min_gap = max(1, int(MIN_SHOT_SEC * afps))
    win = 2
    last = -min_gap
    for i in range(1, len(c)):
        lo, hi = max(1, i - win), min(len(c), i + win + 1)
        neigh = np.concatenate([c[lo:i], c[i + 1:hi]])
        avg = float(neigh.mean()) if neigh.size else 0.0
        ratio = c[i] / (avg + 1e-3)
        hard = c[i] >= CUT_THRESHOLD and c[i] >= c[lo:hi].max()
        adaptive = c[i] >= ADAPTIVE_MIN and ratio >= ADAPTIVE_RATIO
        if (hard or adaptive) and i - last >= min_gap:
            cuts.append(i)
            last = i
    return cuts


def detect_dissolves(content: list[float], cuts: list[int], afps: float) -> list[dict]:
    """Sustained moderate change (5–20 frames above a soft level, no hard cut) ≈ dissolve/whip."""
    c = np.asarray(content)
    soft = (c > 6.0) & (c < CUT_THRESHOLD)
    cutset = set(cuts)
    out, i = [], 0
    while i < len(c):
        if soft[i]:
            j = i
            while j < len(c) and soft[j]:
                j += 1
            n = j - i
            if 0.15 * afps <= n <= 1.2 * afps and not any(k in cutset for k in range(i, j)):
                out.append({"t0": round(i / afps, 2), "t1": round(j / afps, 2), "mean_change": round(float(c[i:j].mean()), 1)})
            i = j
        else:
            i += 1
    return out


def classify_motion(z: float, px: float, py: float, res: float) -> str:
    """Per-shot camera move label from median per-frame flow at FLOW_W px width."""
    # z is fractional scale change per analysis frame; px/py in flow pixels per frame
    labels = []
    if z > 0.0012:
        labels.append("push-in")
    elif z < -0.0012:
        labels.append("pull-out")
    if abs(px) > 0.12 or abs(py) > 0.12:
        if abs(px) >= abs(py):
            labels.append("pan-left" if px > 0 else "pan-right")  # content moves right => camera pans left
        else:
            labels.append("tilt-up" if py > 0 else "tilt-down")
    if not labels:
        labels.append("static" if res < 0.15 else "internal-motion")
    elif res > 0.6:
        labels.append("+internal-motion")
    return " ".join(labels)


def build_shots(vp: dict, cuts: list[int], duration: float) -> list[dict]:
    afps = vp["afps"]
    bounds = [0] + cuts + [vp["n"]]
    shots = []
    arr = {k: np.asarray(vp[k]) for k in ("luma", "sat", "zoom", "px", "py", "res", "content")}
    for k in range(len(bounds) - 1):
        a, b = bounds[k], bounds[k + 1]
        if b <= a:
            continue
        inner = slice(a + 1, b) if b - a > 2 else slice(a, b)
        z = float(np.median(arr["zoom"][inner])); px = float(np.median(arr["px"][inner]))
        py = float(np.median(arr["py"][inner])); res = float(np.median(arr["res"][inner]))
        shots.append({
            "index": k, "start": round(a / afps, 3), "end": round(min(b / afps, duration), 3),
            "duration": round((b - a) / afps, 3),
            "luma": round(float(arr["luma"][a:b].mean()), 1), "sat": round(float(arr["sat"][a:b].mean()), 1),
            "zoom_per_sec": round(z * afps, 4), "pan_x_px_per_sec": round(px * afps * (1280 / FLOW_W), 1),
            "pan_y_px_per_sec": round(py * afps * (720 / FLOW_H), 1), "internal_motion": round(res, 3),
            "motion": classify_motion(z, px, py, res),
            "cut_strength": round(float(arr["content"][a]), 1) if a > 0 else None,
        })
    return shots


def palette(colours: list, k: int = 8) -> list[dict]:
    if not colours:
        return []
    data = np.asarray(colours, np.float32)
    if len(data) > 60000:
        data = data[np.random.default_rng(0).choice(len(data), 60000, replace=False)]
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    cv2.setRNGSeed(0)
    _, labels, centres = cv2.kmeans(data, k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.ravel(), minlength=k)
    order = np.argsort(-counts)
    out = []
    for i in order:
        b, g, r = (int(x) for x in centres[i])
        out.append({"hex": f"#{r:02x}{g:02x}{b:02x}", "share": round(float(counts[i] / counts.sum()), 3)})
    return out


# ------------------------------------------------------------------------ frames

def grab_frames(path: Path, times: list[float], out_dir: Path, width: int = 640, prefix: str = "f") -> list[str]:
    """Accurate single-frame grabs (input seeking + decode to exact time)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    names = []
    for t in times:
        name = f"{prefix}_{t:08.2f}.jpg"
        dst = out_dir / name
        if not dst.exists():
            subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t):.3f}", "-i", str(path), "-frames:v", "1",
                            "-vf", f"scale={width}:-2", "-q:v", "4", "-y", str(dst)], check=False)
        if dst.exists():
            names.append(name)
    return names


def contact_sheet(frames: list[tuple[Path, str]], dst: Path, cols: int = 6, cell_w: int = 320) -> None:
    from PIL import Image, ImageDraw
    if not frames:
        return
    cell_h = cell_w * 9 // 16
    label_h = 22
    rows = math.ceil(len(frames) / cols)
    sheet = Image.new("RGB", (cols * cell_w, rows * (cell_h + label_h)), (16, 16, 16))
    d = ImageDraw.Draw(sheet)
    for i, (p, label) in enumerate(frames):
        try:
            im = Image.open(p).convert("RGB").resize((cell_w, cell_h))
        except Exception:
            continue
        x, y = (i % cols) * cell_w, (i // cols) * (cell_h + label_h)
        sheet.paste(im, (x, y + label_h))
        d.text((x + 4, y + 4), label, fill=(255, 220, 90))
    sheet.save(dst, quality=78)


# ------------------------------------------------------------------------- audio

def audio_pass(path: Path, out: Path) -> dict:
    """Loudness (EBU R128), short-term loudness curve, transients."""
    # integrated loudness + true peak + LRA
    r = subprocess.run(["ffmpeg", "-nostats", "-v", "info", "-i", str(path), "-vn", "-af",
                        "ebur128=peak=true:framelog=verbose", "-f", "null", "-"],
                       capture_output=True, text=True)
    log = r.stderr
    st = []   # short-term loudness every 0.1 s
    for line in log.splitlines():
        if "t:" in line and " S:" in line and "TARGET" not in line:
            try:
                tt = float(line.split("t:")[1].split()[0]); s = float(line.split(" S:")[1].split()[0])
                st.append((tt, s))
            except (IndexError, ValueError):
                pass
    summary = log[log.rfind("Summary:"):] if "Summary:" in log else ""
    def grab(key):
        for line in summary.splitlines():
            if line.strip().startswith(key):
                try:
                    return float(line.split(":")[1].split()[0])
                except (IndexError, ValueError):
                    return None
    integrated, lra, tpk = grab("I:"), grab("LRA:"), grab("Peak:")
    # transient / onset detection from 16 kHz mono
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000",
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0
    hop, win = 160, 1024   # 10 ms hop
    nfr = max(0, (len(x) - win) // hop)
    flux = np.zeros(nfr, np.float32)
    rms = np.zeros(nfr, np.float32)
    lowshare = np.zeros(nfr, np.float32)
    w = np.hanning(win).astype(np.float32)
    prev = None
    freqs = np.fft.rfftfreq(win, 1 / 16000)
    low = freqs < 250
    for i in range(nfr):
        seg = x[i * hop:i * hop + win]
        rms[i] = float(np.sqrt(np.mean(seg * seg)) + 1e-9)
        mag = np.abs(np.fft.rfft(seg * w))
        lm = np.log1p(mag)
        if prev is not None:
            flux[i] = float(np.maximum(lm - prev, 0).sum())
        prev = lm
        tot = float(mag.sum()) + 1e-9
        lowshare[i] = float(mag[low].sum()) / tot
    # adaptive onset threshold
    k = 50
    med = np.array([np.median(flux[max(0, i - k):i + k]) for i in range(0, nfr, 10)])
    med = np.repeat(med, 10)[:nfr]
    mad = np.array([np.median(np.abs(flux[max(0, i - k):i + k] - med[i])) for i in range(0, nfr, 10)])
    mad = np.repeat(mad, 10)[:nfr]
    thr = med + 6 * mad + 1e-3
    onsets = []
    for i in range(1, nfr - 1):
        if flux[i] > thr[i] and flux[i] >= flux[i - 1] and flux[i] >= flux[i + 1]:
            if not onsets or i - onsets[-1][0] > 8:
                onsets.append((i, float(flux[i] / thr[i])))
    rms_db = 20 * np.log10(rms)
    return {
        "integrated_lufs": integrated, "lra_lu": lra, "true_peak_dbtp": tpk,
        "short_term": st[::10],   # every 1 s
        "onsets": [{"t": round(i * hop / 16000, 2), "strength": round(s, 2)} for i, s in onsets],
        "rms_db_1s": [round(float(rms_db[i:i + 100].mean()), 1) for i in range(0, nfr, 100)],
        "low_share_1s": [round(float(lowshare[i:i + 100].mean()), 3) for i in range(0, nfr, 100)],
    }


def transcribe(path: Path, model_name: str) -> dict:
    from faster_whisper import WhisperModel
    model = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)
    # decode with FFmpeg ourselves: avoids faster-whisper's PyAV decoder (version-fragile)
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, np.float32)
    segs, info = model.transcribe(audio, language="en", word_timestamps=True, vad_filter=True,
                                  beam_size=1, condition_on_previous_text=False)
    words, segments = [], []
    for s in segs:
        segments.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()})
        for w in (s.words or []):
            words.append([round(w.start, 2), round(w.end, 2), w.word.strip()])
    return {"model": model_name, "language": info.language, "segments": segments, "words": words}


# ------------------------------------------------------------------------ derived

def derive(meta: dict, shots: list[dict], cuts_t: list[float], dissolves: list[dict], audio: dict | None,
           speech: dict | None) -> dict:
    d = np.asarray([s["duration"] for s in shots]) if shots else np.zeros(1)
    dur = meta["duration_sec"]
    res = {
        "shots": len(shots), "cuts_per_minute": round(len(cuts_t) / (dur / 60), 2),
        "shot_sec": {"mean": round(float(d.mean()), 2), "median": round(float(np.median(d)), 2),
                     "p10": round(float(np.percentile(d, 10)), 2), "p90": round(float(np.percentile(d, 90)), 2),
                     "max": round(float(d.max()), 2)},
        "shot_length_histogram": {lbl: int(((d >= lo) & (d < hi)).sum()) for lbl, lo, hi in
                                  [("<1s", 0, 1), ("1-2s", 1, 2), ("2-3s", 2, 3), ("3-5s", 3, 5), ("5-8s", 5, 8), ("8s+", 8, 1e9)]},
        "dissolve_like_transitions": len(dissolves),
    }
    motions = {}
    for s in shots:
        key = s["motion"].split()[0]
        motions[key] = motions.get(key, 0) + 1
    res["camera_motion_share"] = {k: round(v / max(1, len(shots)), 3) for k, v in sorted(motions.items(), key=lambda kv: -kv[1])}
    # pacing per minute
    per_min = np.zeros(int(math.ceil(dur / 60)) or 1, int)
    for t in cuts_t:
        per_min[min(len(per_min) - 1, int(t // 60))] += 1
    res["cuts_by_minute"] = per_min.tolist()
    if audio:
        on = np.asarray([o["t"] for o in audio["onsets"]]) if audio["onsets"] else np.zeros(0)
        if len(cuts_t) and on.size:
            near = [float(np.min(np.abs(on - t))) for t in cuts_t]
            res["cuts_with_audio_transient_within_100ms"] = round(float(np.mean(np.asarray(near) <= 0.10)), 3)
        res["onsets_per_minute"] = round(len(audio["onsets"]) / (dur / 60), 1)
    if speech and speech.get("words"):
        words = speech["words"]
        speech_sec = sum(e - s for s, e, _ in words)
        res["words_per_minute"] = round(len(words) / (dur / 60), 1)
        res["speech_coverage"] = round(speech_sec / dur, 3)
        gaps = [words[i + 1][0] - words[i][1] for i in range(len(words) - 1)]
        res["pauses_over_0_4s"] = int(sum(g > 0.4 for g in gaps))
        ends = np.asarray([w[1] for w in words])
        sentence_ends = np.asarray([w[1] for w in words if w[2].endswith((".", "?", "!"))])
        if len(cuts_t):
            ct = np.asarray(cuts_t)
            # cut lands within 0.25 s of any word boundary / of a sentence end
            res["cuts_on_word_boundary_250ms"] = round(float(np.mean([np.min(np.abs(ends - t)) <= 0.25 for t in ct])), 3)
            if sentence_ends.size:
                res["cuts_near_sentence_end_400ms"] = round(float(np.mean([np.min(np.abs(sentence_ends - t)) <= 0.4 for t in ct])), 3)
                res["sentences"] = int(sentence_ends.size)
                res["cuts_per_sentence"] = round(len(ct) / sentence_ends.size, 2)
        # background level during pauses vs speech (ducking estimate)
        if audio and audio.get("rms_db_1s"):
            rms = np.asarray(audio["rms_db_1s"])
            mask = np.zeros(len(rms), bool)
            for s, e, _ in words:
                mask[int(s):int(math.ceil(e)) + 1 if int(math.ceil(e)) + 1 <= len(mask) else len(mask)] = True
            if mask.any() and (~mask).any():
                res["rms_db_speech_seconds"] = round(float(rms[mask].mean()), 1)
                res["rms_db_non_speech_seconds"] = round(float(rms[~mask].mean()), 1)
    return res


# --------------------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--id", default=None, help="label used in reports (e.g. 3)")
    ap.add_argument("--analysis-fps", type=float, default=30.0)
    ap.add_argument("--no-transcribe", action="store_true")
    ap.add_argument("--whisper-model", default="base.en")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    if not a.video.is_file():
        sys.exit(f"ERROR: file not found: {a.video}")
    if not os.access(a.video, os.R_OK):
        sys.exit(f"ERROR: file not readable: {a.video}")
    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    timings = {}

    meta = cached(out, "metadata.json", a.force)
    if meta is None:
        meta = ffprobe(a.video); meta["label"] = a.id
        save(out, "metadata.json", meta)
    print(f"[{a.id}] {meta['file']}: {meta['duration_sec']}s {meta['width']}x{meta['height']}@{meta['fps']}", flush=True)

    shots_doc = cached(out, "shots.json", a.force)
    if shots_doc is None:
        t = time.time()
        vp = video_pass(a.video, a.analysis_fps)
        cuts = detect_cuts(vp["content"], vp["afps"])
        shots = build_shots(vp, cuts, meta["duration_sec"])
        dissolves = detect_dissolves(vp["content"], cuts, vp["afps"])
        afps = vp["afps"]
        luma = np.asarray(vp["luma"])
        fades = []
        dark = luma < 12
        i = 0
        while i < len(dark):
            if dark[i]:
                j = i
                while j < len(dark) and dark[j]:
                    j += 1
                if j - i >= 3:
                    fades.append({"t0": round(i / afps, 2), "t1": round(j / afps, 2)})
                i = j
            else:
                i += 1
        shots_doc = {
            "analysis_fps": afps, "analysis_size": [AW, AH], "frames_analysed": vp["n"],
            "cuts": [round(c / afps, 3) for c in cuts], "shots": shots, "dissolves": dissolves,
            "dark_frames": fades, "palette": palette(vp["colours"]),
            "luma_mean": round(float(luma.mean()), 1), "sat_mean": round(float(np.mean(vp["sat"])), 1),
            "content_1s": [round(float(np.mean(vp["content"][k:k + int(afps)])), 2) for k in range(0, vp["n"], int(afps))],
        }
        save(out, "shots.json", shots_doc)
        timings["video_pass_sec"] = round(time.time() - t, 1)
        print(f"  {len(shots)} shots, video pass {timings['video_pass_sec']}s", flush=True)

    audio = cached(out, "audio.json", a.force)
    if audio is None:
        t = time.time()
        audio = audio_pass(a.video, out)
        save(out, "audio.json", audio)
        timings["audio_pass_sec"] = round(time.time() - t, 1)
        print(f"  audio: {audio['integrated_lufs']} LUFS, TP {audio['true_peak_dbtp']}, {len(audio['onsets'])} onsets", flush=True)

    speech = cached(out, "transcript.json", a.force)
    if speech is None and not a.no_transcribe:
        t = time.time()
        try:
            speech = transcribe(a.video, a.whisper_model)
            save(out, "transcript.json", speech)
        except Exception as e:  # report, never silently skip
            print(f"  WARNING: transcription failed: {e}", flush=True)
            speech = None
        timings["transcribe_sec"] = round(time.time() - t, 1)

    # frames: shot mid-frames (capped and evenly thinned), regular samples, cut strips
    frames_dir = out / "frames"
    shots = shots_doc["shots"]
    mids = [round((s["start"] + s["end"]) / 2, 2) for s in shots]
    if len(mids) > 240:
        step = len(mids) / 240
        mids = [mids[int(k * step)] for k in range(240)]
    t = time.time()
    grab_frames(a.video, mids, frames_dir / "shots", 480, "shot")
    dur = meta["duration_sec"]
    regular = [round(x, 2) for x in np.arange(2.0, dur - 1, max(10.0, dur / 90))]
    grab_frames(a.video, regular, frames_dir / "regular", 480, "reg")
    # transition strips around the 12 strongest-content soft transitions + 12 evenly spaced cuts
    strips = []
    cuts_t = shots_doc["cuts"]
    picks = cuts_t[:: max(1, len(cuts_t) // 12)][:12]
    picks += [d["t0"] for d in sorted(shots_doc["dissolves"], key=lambda d: -d["mean_change"])[:8]]
    for c in sorted(set(picks)):
        ts = [round(c + o, 3) for o in (-0.30, -0.10, -0.03, 0.03, 0.10, 0.30)]
        names = grab_frames(a.video, ts, frames_dir / "strips", 320, f"strip_{c:08.2f}")
        strips.append({"cut": c, "frames": names})
    timings["frames_sec"] = round(time.time() - t, 1)

    sheets = out / "contact-sheets"
    sheets.mkdir(exist_ok=True)
    shot_files = sorted((frames_dir / "shots").glob("*.jpg"))
    per = 36
    for k in range(0, len(shot_files), per):
        chunk = shot_files[k:k + per]
        contact_sheet([(p, fmt_ts(float(p.stem.split("_")[1]))) for p in chunk], sheets / f"shots-{k // per + 1:02d}.jpg")
    reg_files = sorted((frames_dir / "regular").glob("*.jpg"))
    for k in range(0, len(reg_files), per):
        chunk = reg_files[k:k + per]
        contact_sheet([(p, fmt_ts(float(p.stem.split("_")[1]))) for p in chunk], sheets / f"regular-{k // per + 1:02d}.jpg")
    strip_frames = []
    for s in strips[:16]:
        for n in s["frames"]:
            strip_frames.append((frames_dir / "strips" / n, n.split("_")[1] + " @" + n.split("_")[2][:-4]))
    for k in range(0, len(strip_frames), 48):
        contact_sheet(strip_frames[k:k + 48], sheets / f"transitions-{k // 48 + 1:02d}.jpg", cols=6, cell_w=240)

    summary = derive(meta, shots, cuts_t, shots_doc["dissolves"], audio, speech)
    summary["palette"] = shots_doc["palette"]
    summary["luma_mean"] = shots_doc["luma_mean"]
    summary["sat_mean"] = shots_doc["sat_mean"]
    summary["audio"] = {k: audio[k] for k in ("integrated_lufs", "lra_lu", "true_peak_dbtp")}
    summary["timings"] = {**timings, "total_sec": round(time.time() - t_start, 1)}
    summary["strips"] = strips
    save(out, "summary.json", summary)
    print(f"[{a.id}] done in {summary['timings']['total_sec']}s: {summary['shots']} shots, "
          f"median shot {summary['shot_sec']['median']}s, {summary['cuts_per_minute']} cuts/min", flush=True)


if __name__ == "__main__":
    main()
