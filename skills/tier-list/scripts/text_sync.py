"""Measure on-screen text entrance/exit times precisely and their offset to the spoken word.
For each OCR line whose words appear in the transcript, scan frames at 60 fps in [shot_start-0.5, shot_end+0.5]
inside the OCR box: text is 'on' when the box's bright-pixel ratio is >= 50% of the mid-shot value.
Usage: python -I text_sync.py video.mp4 ocr.json transcript.json cuts.json out.json [--max 60]"""
import sys, json, re, subprocess, numpy as np, argparse
ap = argparse.ArgumentParser(); [ap.add_argument(x) for x in ("video", "ocr", "tr", "cuts", "out")]; ap.add_argument("--max", type=int, default=60); a = ap.parse_args()
R = json.load(open(a.ocr)); W = json.load(open(a.tr))["words"]; spans = json.load(open(a.cuts))["shot_spans"]
norm = lambda s: re.sub(r"[^a-z0-9$]", "", s.lower())
def frames(t0, t1, box, W_=1280, H_=720):
    x0, y0, x1, y1 = box
    cmd = ["ffmpeg", "-nostdin", "-loglevel", "quiet", "-ss", f"{max(0,t0):.3f}", "-t", f"{t1-t0:.3f}", "-i", a.video, "-vf", f"fps=60,crop={x1-x0}:{y1-y0}:{x0}:{y0},format=gray", "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout; n = (x1 - x0) * (y1 - y0)
    arr = np.frombuffer(raw, np.uint8)[: (len(raw) // n) * n].reshape(-1, y1 - y0, x1 - x0)
    return arr
rows = []
for r in R:
    for l in r["lines"]:
        if l["conf"] < 80 or len(norm(l["text"])) < 4: continue
        toks = [norm(t) for t in l["text"].split() if len(norm(t)) >= 3]
        if not toks: continue
        s0, s1 = spans[r["shot"]]
        # spoken match within +-4 s of the shot
        cand = [w for w in W if s0 - 4 <= w["s"] <= s1 + 4 and norm(w["w"]) in toks]
        if not cand: continue
        box = (int(l["x_pct"] / 100 * 1280) - 4, int(l["y_pct"] / 100 * 720) - 4, int((l["x_pct"] + l["w_pct"]) / 100 * 1280) + 4, int((l["y_pct"] + l["h_pct"]) / 100 * 720) + 4)
        box = (max(0, box[0]), max(0, box[1]), min(1280, box[2]), min(720, box[3]))
        if box[2] - box[0] < 8 or box[3] - box[1] < 6: continue
        t0 = s0 - 0.5; F = frames(t0, s1 + 0.5, box)
        if len(F) < 5: continue
        br = (F > 225).mean((1, 2)); ref = br[int((r["t"] - t0) * 60)] if int((r["t"] - t0) * 60) < len(br) else br.max()
        if ref < 0.02: continue
        on = br >= 0.5 * ref; idx = np.where(on)[0]
        if not len(idx): continue
        # contiguous run containing the mid-shot frame
        mid = min(len(on) - 1, int((r["t"] - t0) * 60)); i0 = mid; i1 = mid
        while i0 > 0 and on[i0 - 1]: i0 -= 1
        while i1 < len(on) - 1 and on[i1 + 1]: i1 += 1
        t_in, t_out = t0 + i0 / 60, t0 + (i1 + 1) / 60
        # ramp length (entrance animation): frames from 10% to 90% of ref
        pre = br[max(0, i0 - 30): i0 + 30]; ramp = int(((pre > 0.1 * ref) & (pre < 0.9 * ref)).sum())
        wbest = min(cand, key=lambda w: abs(w["s"] - t_in))
        rows.append({"text": l["text"], "zone_cy": l["cy_pct"], "h_pct": l["h_pct"], "shot_start": round(s0, 3), "t_in": round(t_in, 3), "t_out": round(t_out, 3),
                     "on_screen_s": round(t_out - t_in, 2), "in_minus_shot_start_ms": round((t_in - s0) * 1000), "word": wbest["w"], "word_start": wbest["s"],
                     "in_minus_word_ms": round((t_in - wbest["s"]) * 1000), "out_minus_shot_end_ms": round((t_out - s1) * 1000), "ramp_frames_60fps": ramp})
        if len(rows) >= a.max: break
    if len(rows) >= a.max: break
json.dump(rows, open(a.out, "w"), indent=1)
import statistics as st
for key in ("in_minus_word_ms", "in_minus_shot_start_ms", "on_screen_s", "out_minus_shot_end_ms", "ramp_frames_60fps"):
    v = [x[key] for x in rows]; print(key, "median", st.median(v), "q25/q75", np.quantile(v, [.25, .75]).round(2).tolist())
print(len(rows))
