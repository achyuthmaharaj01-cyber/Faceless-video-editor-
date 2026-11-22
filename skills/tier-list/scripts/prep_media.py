"""Normalise sourced media into render-ready assets + set audio levels from measurements.
  footage  -> assets/media/sNNN.mp4  1920x1080 30 fps h264, cover-cropped; vertical/4:3 sources get the
              style's inset treatment pre-baked (blurred, darkened copy behind, source centred full height)
  stills   -> assets/media/sNNN.jpg  1920x1080 cover (inset treatment for portrait images)
  clips    -> keep audio (aac); clip_volume set so clip loudness = VO - 2 LU (style.json clip_vs_vo_lu)
  faces    -> assets/faces/eN.png    head cutout (background removed, face-centred crop, 6 px white sticker outline)
  items    -> assets/cutouts/item_eN.png  background removed + trimmed (price badge + spec icon)
  music    -> audio.music.volume so bed = VO - 10.3 LU (style.json bed_vs_vo_lu)
Usage: python -I prep_media.py shotlist.json project_dir [--hf /path/to/hyperframes/project/with/node_modules]"""
import sys, os, json, subprocess, argparse, numpy as np, soundfile as sf, warnings
warnings.filterwarnings("ignore")
from PIL import Image, ImageFilter, ImageOps
import pyloudnorm as pyln
SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); STYLE = json.load(open(os.path.join(SK, "style.json")))
ap = argparse.ArgumentParser(); ap.add_argument("shotlist"); ap.add_argument("project"); ap.add_argument("--hf", default=None); a = ap.parse_args()
SL = json.load(open(a.shotlist)); P = a.project; J = lambda *x: os.path.join(P, *x)
for d in ("media", "faces", "cutouts"): os.makedirs(J("assets", d), exist_ok=True)
def run(cmd, **k): return subprocess.run(cmd, check=True, capture_output=True, **k)
def probe(f):
    o = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height:format=duration", "-of", "json", f]).stdout)
    v = next((s for s in o["streams"] if s["codec_type"] == "video"), {}); has_a = any(s["codec_type"] == "audio" for s in o["streams"])
    return v.get("width", 0), v.get("height", 0), float(o["format"].get("duration", 0) or 0), has_a
def lufs(path, t0=0, dur=None):
    tmp = J("assets", ".tmp_l.wav"); cmd = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", str(t0), "-i", path] + (["-t", str(dur)] if dur else []) + ["-vn", "-ac", "2", "-ar", "48000", tmp]
    run(cmd); x, sr = sf.read(tmp); os.remove(tmp); return pyln.Meter(sr).integrated_loudness(x)
INSET = "[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=40:2,eq=brightness=-0.18[bg];[0:v]scale=-2:1080[fg];[bg][fg]overlay=(W-w)/2:0,fps=30,format=yuv420p[v]"
COVER = "[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30,format=yuv420p[v]"
motion_cycle = ["push_in", "push_in", "pull_out", "push_in", "pull_out"]   # 60/40 split (style.json ken_burns)
vo_raw = lufs(J(SL["audio"]["vo"])); SL["audio"]["vo_lufs_raw"] = round(vo_raw, 1)
# bring the VO to the reference VO level (style.json audio.vo.lufs_vo_on_sections video-3) via data-volume (max +12 dB)
VO_T = STYLE["audio"]["vo"]["lufs_vo_on_sections"]["video-3"]
SL["audio"]["vo_volume"] = round(min(3.98, 10 ** ((VO_T - vo_raw) / 20)), 3)
vo_l = vo_raw + 20 * np.log10(SL["audio"]["vo_volume"]); SL["audio"]["vo_lufs"] = round(vo_l, 1)
for i, s in enumerate(SL["shots"]):
    if not s.get("raw"): continue
    src = J(s["raw"]); w, h, dur, has_a = probe(src)
    if s.get("raw_kind") == "video" or src.lower().endswith((".webm", ".ogv", ".mp4", ".mov")):
        need = (s["dur"] if s["type"] == "clip_audio" else max(0.5, s.get("vo_e", 0) - s["vo_s"]) + 1.0)
        ms = float(s.get("raw_media_start", 0)); out = J("assets", "media", f"s{i:03d}.mp4")
        fc = INSET if w / max(h, 1) < 1.5 else COVER
        cmd = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", str(ms), "-t", f"{need:.2f}", "-i", src, "-filter_complex", fc, "-map", "[v]"]
        if s["type"] == "clip_audio" and has_a: cmd += ["-map", "0:a:0", "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
        else: cmd += ["-an"]
        run(cmd + ["-c:v", "libx264", "-preset", "veryfast", "-crf", "19", out])
        s["src"] = os.path.relpath(out, P); s["media_start"] = 0
        if s["type"] == "clip_audio":
            if has_a:
                l = lufs(out); target = vo_l + STYLE["audio"]["vo_off"]["clip_speech"]["clip_vs_vo_lu"]
                s["clip_volume"] = round(min(3.98, 10 ** ((target - l) / 20)), 3); s["clip_lufs"] = round(l, 1)
            s["dur"] = min(s["dur"], round(dur - ms, 2))
        elif s["type"] not in ("tier_chart", "map", "screenshot", "logo", "silhouette", "text_card"): s["type"] = "footage"
    else:
        im = ImageOps.exif_transpose(Image.open(src)).convert("RGB"); out = J("assets", "media", f"s{i:03d}.jpg")
        if im.width / im.height < 1.5:   # inset on blurred copy
            bg = ImageOps.fit(im, (1920, 1080)).filter(ImageFilter.GaussianBlur(40)).point(lambda v: int(v * 0.62))
            fg = im.resize((int(im.width * 1080 / im.height), 1080), Image.LANCZOS); bg.paste(fg, ((1920 - fg.width) // 2, 0)); bg.save(out, quality=92)
        else: ImageOps.fit(im, (1920, 1080), Image.LANCZOS).save(out, quality=92)
        s["src"] = os.path.relpath(out, P)
        if s["type"] == "footage": s["type"] = "still"; s.setdefault("motion", motion_cycle[i % len(motion_cycle)])
        if s["type"] == "map": s["src"] = os.path.relpath(out, P)
# ---- cutouts (faces + items)
# general salient-object segmentation (cars, objects AND people); the Hyperframes remover is person-only
from rembg import remove as _rb_remove, new_session as _rb_session
_RB = {}
def remove_bg(src, dst, model="isnet-general-use"):
    if model not in _RB: _RB[model] = _rb_session(model)
    _rb_remove(ImageOps.exif_transpose(Image.open(src)).convert("RGB"), session=_RB[model]).save(dst)
def sticker(img, px):
    al = img.split()[3].filter(ImageFilter.MaxFilter(px * 2 + 1)); base = Image.new("RGBA", img.size, (255, 255, 255, 0)); base.putalpha(al)
    white = Image.new("RGBA", img.size, (255, 255, 255, 255)); white.putalpha(al); white.alpha_composite(img); return white
import cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import faces as FC
NAME_PX = STYLE["text"]["name_label"]["font_px"]          # name label font size at 1920x1080
REF_EMB = {}                                              # entry index -> SFace embedding of the named person
for j, e in enumerate(SL.get("entries", [])):
    if e.get("face_raw"):
        src_im = ImageOps.exif_transpose(Image.open(J(e["face_raw"]))).convert("RGB")
        tmp = J("assets", "faces", f".cut_e{j}.png")
        if e.get("face_box"): fc = FC.face_from_box(src_im, e["face_box"]) or {"box": tuple(e["face_box"]), "raw": None}
        else:
            ff = FC.detect(src_im)
            # several people: entry "face_pick" = index left-to-right (default: largest face)
            fc = (sorted(ff, key=lambda d: d["box"][0])[e["face_pick"]] if ff and "face_pick" in e and -len(ff) <= e["face_pick"] < len(ff) else (ff[0] if ff else None))
        if fc:
            if fc.get("raw") is not None: REF_EMB[j] = FC.embed(src_im, fc)
            x, y, w, h = fc["box"]; cx, cy = x + w / 2, y + h / 2
            box = (max(0, int(cx - w * 1.1)), max(0, int(cy - h * 1.4)), min(src_im.width, int(cx + w * 1.1)), min(src_im.height, int(cy + h * 1.3)))
            src_im.crop(box).save(tmp + ".jpg"); remove_bg(tmp + ".jpg", tmp, "u2net_human_seg"); os.remove(tmp + ".jpg")
            im = Image.open(tmp).convert("RGBA"); x, y = x - box[0], y - box[1]; cx, cy = x + w / 2, y + h / 2
            # head-only cutout like the reference: hair to chin + a short neck, ears included
            im = im.crop((max(0, int(cx - w * 0.78)), max(0, int(cy - h * 1.05)), int(cx + w * 0.78), int(cy + h * 0.80)))
            al = np.array(im.split()[3]).astype(float); H_ = al.shape[0]; fade0 = int(H_ * 0.86)
            al[fade0:] *= np.linspace(1, 0, H_ - fade0)[:, None]; im.putalpha(Image.fromarray(al.astype("uint8")))
        else:
            remove_bg(J(e["face_raw"]), tmp, "u2net_human_seg"); im = Image.open(tmp).convert("RGBA")
        im = im.crop(im.getbbox()); im = im.resize((int(im.width * 320 / im.height), 320), Image.LANCZOS)
        im = ImageOps.expand(im, 12, (0, 0, 0, 0)); sticker(im, 7).save(J("assets", "faces", f"e{j}.png")); os.remove(tmp)
        e["face"] = f"assets/faces/e{j}.png"
    if e.get("item_raw"):
        tmp = J("assets", "cutouts", f"item_e{j}.png"); remove_bg(J(e["item_raw"]), tmp); im = Image.open(tmp).convert("RGBA")
        bb = Image.fromarray((np.array(im.split()[3]) > 40).astype("uint8") * 255).getbbox(); im = im.crop(bb) if bb else im
        im.thumbnail((600, 300)); im.save(tmp); e["item_cutout"] = f"assets/cutouts/item_e{j}.png"
# ---- name-label placement: beside the NAMED person's head (identity-matched to the entry portrait),
#      vertically centred on the face, on the side where the text fits (style.json text.name_label)
def frame_of(path):
    if path.endswith(".mp4"):
        r = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "quiet", "-ss", "0.3", "-i", path, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
        import io; return Image.open(io.BytesIO(r.stdout)).convert("RGB")
    return Image.open(path).convert("RGB")
label_report = []
for i, s in enumerate(SL["shots"]):
    labs = [o for o in s.get("overlays", []) if o["kind"] == "name_label" and not o.get("manual")]
    if not labs or not s.get("src"): continue
    im = frame_of(J(s["src"])); ff = FC.detect(im, min_size=40)
    ref = REF_EMB.get(s.get("entry", -1)); pick, how = None, "none"
    if ff and ref is not None:
        sims = [(FC.same_person(FC.embed(im, f), ref), f) for f in ff]
        best = max(sims, key=lambda t: t[0])
        if best[0] >= FC.SAME: pick, how = best[1], f"identity {best[0]:.2f}"
    e_ = SL["entries"][s["entry"]] if 0 <= s.get("entry", -1) < len(SL.get("entries", [])) else {}
    if pick is None and e_.get("face_raw") and s["type"] in ("still", "footage") and not s.get("keep_media"):
        # the named person is not identifiable in this shot -> use the entry portrait (a name intro must show the face)
        out = J("assets", "media", f"s{i:03d}_portrait.jpg"); pim = ImageOps.exif_transpose(Image.open(J(e_["face_raw"]))).convert("RGB")
        if pim.width / pim.height < 1.5:
            bg = ImageOps.fit(pim, (1920, 1080)).filter(ImageFilter.GaussianBlur(40)).point(lambda v: int(v * 0.62))
            fg = pim.resize((int(pim.width * 1080 / pim.height), 1080), Image.LANCZOS); bg.paste(fg, ((1920 - fg.width) // 2, 0)); bg.save(out, quality=92)
        else: ImageOps.fit(pim, (1920, 1080), Image.LANCZOS).save(out, quality=92)
        s["src"] = os.path.relpath(out, P); s["type"] = "still"; s.setdefault("motion", "push_in"); s["media_swapped"] = "entry portrait (named person not identifiable in the sourced shot)"
        im = Image.open(out).convert("RGB"); ff = FC.detect(im, min_size=40)
        if ff and ref is not None:
            best = max(((FC.same_person(FC.embed(im, f), ref), f) for f in ff), key=lambda t: t[0])
            pick, how = best[1], f"portrait swap, identity {best[0]:.2f}"
        elif ff: pick, how = ff[0], "portrait swap"
    if pick is None and ff: pick, how = ff[0], "largest face (identity not confirmed - check)"
    for o in labs:
        lines = o["text"].split("\n"); size = o.get("size", NAME_PX)
        tw = max(len(l) for l in lines) * 0.52 * size; th = len(lines) * 0.98 * size; gap = 0.35 * size
        if pick:
            x, y, w, h = pick["box"]; hl, hr = x - 0.3 * w, x + 1.3 * w        # head incl. hair/ears
            # other people's heads (expanded boxes) the label should not cover
            others = [(f["box"][0] - 0.3 * f["box"][2], f["box"][1] - 0.5 * f["box"][3], f["box"][0] + 1.3 * f["box"][2], f["box"][1] + 1.6 * f["box"][3]) for f in ff if f is not pick]
            def area(a, b): return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
            best = None
            for sz in (size, size * 0.9, size * 0.8, size * 0.7):
                tw = max(len(l) for l in lines) * 0.52 * sz; th = len(lines) * 0.98 * sz
                for side in ("left", "right"):
                    for dy in (0, -0.6, 0.6, -1.1, 1.1):              # beside the face, nudged up/down by face heights
                        cyl = y + h * 0.5 + dy * h
                        x0 = (hl - gap - tw) if side == "left" else (hr + gap); bx = (x0, cyl - th / 2, x0 + tw, cyl + th / 2)
                        if bx[0] < 30 or bx[2] > 1890 or bx[1] < 30 or bx[3] > 1050: continue
                        cost = sum(area(bx, ob) for ob in others) / (tw * th) + 0.15 * abs(dy) + 0.6 * (1 - sz / size)
                        if best is None or cost < best[0]: best = (cost, side, x0, cyl, sz, th)
                if best and best[0] < 0.05: break
            if best is None: best = (9, "right", hr + gap, y + h / 2, size * 0.7, len(lines) * 0.98 * size * 0.7)
            _, side, x0, cyl, sz, th = best
            if sz != size: o["size"] = round(sz)
            o["side"] = side; o["x"] = round(((x0 + max(len(l) for l in lines) * 0.52 * sz) if side == "left" else x0) / 19.2, 2)
            o["y"] = round(cyl / 10.8, 2); o["overlap_cost"] = round(best[0], 3)
        else: o.setdefault("side", "left"); o.setdefault("x", 30); o.setdefault("y", 40)
        label_report.append((i, o["text"].replace("\n", " "), how, o["side"], o["x"], o["y"]))
for r in label_report: print("label s%03d %-22s %-45s %s x=%s y=%s" % r)
# ---- music level
m = SL["audio"].get("music")
if m and m.get("src"):
    ml = lufs(J(m["src"]), m.get("start", 0), 60); target = vo_l - STYLE["audio"]["music"]["bed_vs_vo_lu"]
    m["lufs"] = round(ml, 1); m["volume"] = round(10 ** ((target - ml) / 20), 4); m["duration"] = probe(J(m["src"]))[2]
json.dump(SL, open(a.shotlist, "w"), indent=1)
print("prepped", sum(1 for s in SL["shots"] if s.get("src")), "shots | VO", round(vo_l, 1), "LUFS | music vol", (m or {}).get("volume"))
