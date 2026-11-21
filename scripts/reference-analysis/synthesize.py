#!/usr/bin/env python3
"""Aggregate the per-video analysis folders into the reference library's data documents.

Usage: synthesize.py ANALYSIS_ROOT OUT_DIR [--titles manifest.tsv]
  ANALYSIS_ROOT/video-N/{metadata,shots,audio,transcript,summary}.json  (from analyze_reference.py)
Writes OUT_DIR/reference-video-index.md, OUT_DIR/video-N-analysis.md (measured sections; the qualitative
sections are written by the analyst from the contact sheets), OUT_DIR/aggregate-stats.json and
OUT_DIR/data/video-N/*.json (compact copies: no frames, so the library stays small and shareable).
"""
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np

root, out = Path(sys.argv[1]), Path(sys.argv[2])
titles = {}
if "--titles" in sys.argv:
    for line in Path(sys.argv[sys.argv.index("--titles") + 1]).read_text().splitlines():
        p = line.split("\t")
        if len(p) >= 4:
            titles[p[0]] = p[3]
out.mkdir(parents=True, exist_ok=True)
(out / "data").mkdir(exist_ok=True)


def fmt(t):
    m, s = divmod(float(t), 60)
    return f"{int(m):02d}:{s:05.2f}"


rows, agg = [], {"shot_durations": [], "per_video": {}}
for d in sorted(root.glob("video-*"), key=lambda p: int(p.name.split("-")[1])):
    n = d.name.split("-")[1]
    try:
        meta = json.loads((d / "metadata.json").read_text())
        shots = json.loads((d / "shots.json").read_text())
        audio = json.loads((d / "audio.json").read_text())
        summ = json.loads((d / "summary.json").read_text())
    except FileNotFoundError as e:
        rows.append((n, None, f"incomplete: {e.filename}"))
        continue
    tr = json.loads((d / "transcript.json").read_text()) if (d / "transcript.json").exists() else None
    dd = out / "data" / d.name
    dd.mkdir(exist_ok=True)
    for f in ("metadata.json", "summary.json", "shots.json"):
        shutil.copy2(d / f, dd / f)
    (dd / "audio-summary.json").write_text(json.dumps({k: audio[k] for k in ("integrated_lufs", "lra_lu", "true_peak_dbtp")} | {"onsets": len(audio["onsets"])}))
    durs = [s["duration"] for s in shots["shots"]]
    agg["shot_durations"] += durs
    agg["per_video"][n] = {k: summ.get(k) for k in ("shots", "cuts_per_minute", "shot_sec", "camera_motion_share", "words_per_minute",
                                                    "cuts_on_word_boundary_250ms", "cuts_near_sentence_end_400ms", "cuts_per_sentence",
                                                    "cuts_with_audio_transient_within_100ms", "rms_db_speech_seconds", "rms_db_non_speech_seconds",
                                                    "dissolve_like_transitions", "luma_mean", "sat_mean")} | {"audio": summ.get("audio"), "duration": meta["duration_sec"]}
    rows.append((n, meta, summ))
    # pacing curve: cuts per 30 s window; find the fastest and slowest stretches
    cuts = shots["cuts"]
    win = 30
    nb = max(1, math.ceil(meta["duration_sec"] / win))
    counts = np.zeros(nb, int)
    for c in cuts:
        counts[min(nb - 1, int(c // win))] += 1
    fast = np.argsort(-counts)[:3]
    slow = [i for i in np.argsort(counts) if i * win < meta["duration_sec"] - win][:3]
    longest = sorted(shots["shots"], key=lambda s: -s["duration"])[:5]
    motion_examples = {}
    for s in shots["shots"]:
        k = s["motion"].split()[0]
        if k not in ("static",) and s["duration"] > 1.5:
            motion_examples.setdefault(k, []).append(s)
    md = [f"# Reference video {n} — measured analysis", "",
          f"Title (from the file name): **{titles.get(n, meta['file'])}**", "",
          "> The measured sections below are produced by `scripts/reference-analysis/analyze_reference.py` and",
          "> `synthesize.py`. Qualitative observations are in the `## Observations` section, written from the contact sheets.", "",
          "## Technical metadata", "",
          f"| Duration | Resolution | FPS | Aspect | Video | Audio | Bitrate |", "|---|---|---|---|---|---|---|",
          f"| {fmt(meta['duration_sec'])} | {meta['width']}×{meta['height']} | {meta['fps']} | {meta['aspect_ratio']} | {meta['video_codec']} {meta.get('video_profile') or ''} | {meta['audio_codec']} {meta['audio_channels']} ch {meta.get('audio_sample_rate')} Hz | {meta['overall_bitrate_kbps']} kb/s |", "",
          "## Editing rhythm", "",
          f"- Shots: **{summ['shots']}**, **{summ['cuts_per_minute']} cuts/min**",
          f"- Shot length: median **{summ['shot_sec']['median']} s**, mean {summ['shot_sec']['mean']} s, 10th pct {summ['shot_sec']['p10']} s, 90th pct {summ['shot_sec']['p90']} s, longest {summ['shot_sec']['max']} s",
          f"- Distribution: " + ", ".join(f"{k}: {v}" for k, v in summ["shot_length_histogram"].items()),
          f"- Dissolve-like (soft, multi-frame) transitions: {summ['dissolve_like_transitions']} — almost every change is a hard cut or a fast motion transition",
          f"- Fastest 30 s windows: " + ", ".join(f"{fmt(i * win)}–{fmt(i * win + win)} ({counts[i]} cuts)" for i in fast),
          f"- Slowest 30 s windows: " + ", ".join(f"{fmt(i * win)}–{fmt(i * win + win)} ({counts[i]} cuts)" for i in slow),
          f"- Longest holds: " + ", ".join(f"{fmt(s['start'])} ({s['duration']:.1f} s, {s['motion']})" for s in longest), "",
          "## Camera movement (optical-flow classification per shot)", "",
          "| Motion | Share of shots |", "|---|---|"] + [f"| {k} | {v * 100:.1f}% |" for k, v in summ["camera_motion_share"].items()] + [""] + \
         [f"- Example {k}: " + ", ".join(f"{fmt(s['start'])} ({s['duration']:.1f} s)" for s in v[:4]) for k, v in motion_examples.items()] + ["",
          "## Narration ↔ picture", ""]
    if tr:
        md += [f"- Narration pace: **{summ.get('words_per_minute')} words/min**; speech covers {summ.get('speech_coverage', 0) * 100:.0f}% of the running time; {summ.get('pauses_over_0_4s')} pauses > 0.4 s",
               f"- **{(summ.get('cuts_on_word_boundary_250ms') or 0) * 100:.0f}%** of cuts fall within 0.25 s of a word boundary; {(summ.get('cuts_near_sentence_end_400ms') or 0) * 100:.0f}% within 0.4 s of a sentence end",
               f"- {summ.get('cuts_per_sentence')} cuts per spoken sentence on average ({summ.get('sentences')} sentences)"]
    else:
        md += ["- Transcript not available (transcription failed or was skipped)."]
    md += ["", "## Sound", "",
           f"- Integrated loudness **{summ['audio']['integrated_lufs']} LUFS**, LRA {summ['audio']['lra_lu']} LU, true peak {summ['audio']['true_peak_dbtp']} dBTP",
           f"- {len(audio['onsets'])} transient onsets ({summ.get('onsets_per_minute')} per minute); **{(summ.get('cuts_with_audio_transient_within_100ms') or 0) * 100:.0f}%** of cuts have a transient within 100 ms (SFX / music hits on cuts)"]
    if summ.get("rms_db_speech_seconds") is not None:
        md += [f"- Average level in seconds with speech {summ['rms_db_speech_seconds']} dB vs without speech {summ['rms_db_non_speech_seconds']} dB (music/SFX bed level in pauses)"]
    md += ["", "## Colour", "", f"- Mean brightness {summ['luma_mean']}/255, mean saturation {summ['sat_mean']}/255",
           "- Dominant colours: " + " ".join(f"`{c['hex']}` {c['share'] * 100:.0f}%" for c in summ["palette"]), "",
           "## Files", "", f"- Contact sheets and frames (private, not in Git): `reference-library/{d.name}/contact-sheets/`",
           f"- Shot list and per-frame metrics: `data/{d.name}/shots.json`", "", "## Observations", "",
           f"<!-- qualitative notes for video {n} are maintained in timestamped-observations.md and the guides -->", ""]
    (out / f"video-{n}-analysis.md").write_text("\n".join(md))

all_d = np.asarray(agg["shot_durations"]) if agg["shot_durations"] else np.zeros(1)
agg["overall"] = {"videos": len(agg["per_video"]), "shots": int(all_d.size), "median_shot_sec": round(float(np.median(all_d)), 2),
                  "mean_shot_sec": round(float(all_d.mean()), 2), "p10": round(float(np.percentile(all_d, 10)), 2), "p90": round(float(np.percentile(all_d, 90)), 2),
                  "share_under_1s": round(float((all_d < 1).mean()), 3), "share_over_5s": round(float((all_d > 5).mean()), 3)}
agg.pop("shot_durations")
(out / "aggregate-stats.json").write_text(json.dumps(agg, indent=1))
idx = ["# Reference video index", "", "Eight reference videos (Jack Pockets channel), analysed locally from the copies in the user's Google Drive",
       "reference folder. Numbering follows the Drive upload order and **may differ from the numbering of the local",
       "Windows copies** (`video 1.mp4` … `video 8.mp4`), which were not reachable from the cloud session.", "",
       "| # | Title (from file name) | Duration | Format | Shots | Cuts/min | Median shot | Words/min | Loudness |", "|---|---|---|---|---|---|---|---|---|"]
for n, meta, summ in rows:
    if meta is None:
        idx.append(f"| {n} | — | — | — | — | — | — | — | {summ} |"); continue
    idx.append(f"| [{n}](video-{n}-analysis.md) | {titles.get(n, meta['file'])} | {fmt(meta['duration_sec'])} | {meta['width']}×{meta['height']} @ {meta['fps']} | {summ['shots']} | {summ['cuts_per_minute']} | {summ['shot_sec']['median']} s | {summ.get('words_per_minute', '—')} | {summ['audio']['integrated_lufs']} LUFS |")
o = agg["overall"]
idx += ["", f"**All videos:** {o['shots']} shots; median shot **{o['median_shot_sec']} s** (10th–90th pct {o['p10']}–{o['p90']} s); {o['share_under_1s'] * 100:.0f}% of shots under 1 s, {o['share_over_5s'] * 100:.0f}% over 5 s.", ""]
(out / "reference-video-index.md").write_text("\n".join(idx))
print(json.dumps(agg["overall"]))
