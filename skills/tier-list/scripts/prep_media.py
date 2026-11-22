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
vo_l = lufs(J(SL["audio"]["vo"])); SL["audio"]["vo_lufs"] = round(vo_l, 1)
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
hfp = a.hf
def remove_bg(src, dst):
    run(["npx", "hyperframes", "remove-background", os.path.abspath(src), "-o", os.path.abspath(dst)], cwd=hfp or P)
def sticker(img, px):
    al = img.split()[3].filter(ImageFilter.MaxFilter(px * 2 + 1)); base = Image.new("RGBA", img.size, (255, 255, 255, 0)); base.putalpha(al)
    white = Image.new("RGBA", img.size, (255, 255, 255, 255)); white.putalpha(al); white.alpha_composite(img); return white
import cv2
casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
for j, e in enumerate(SL.get("entries", [])):
    if e.get("face_raw"):
        tmp = J("assets", "faces", f".cut_e{j}.png"); remove_bg(J(e["face_raw"]), tmp); im = Image.open(tmp).convert("RGBA")
        g = cv2.cvtColor(np.array(im.convert("RGB")), cv2.COLOR_RGB2GRAY); f = casc.detectMultiScale(g, 1.1, 5, minSize=(40, 40))
        if len(f):
            x, y, w, h = max(f, key=lambda r: r[2] * r[3]); cx, cy = x + w / 2, y + h / 2
            im = im.crop((int(cx - w * 0.85), int(cy - h * 1.15), int(cx + w * 0.85), int(cy + h * 1.05)))
            # keep only head: fade alpha below the chin
            al = np.array(im.split()[3]).astype(float); H_ = al.shape[0]; cut = int(H_ * 0.93); al[cut:] = 0; im.putalpha(Image.fromarray(al.astype("uint8")))
        im = im.crop(im.getbbox()); im = im.resize((int(im.width * 240 / im.height), 240), Image.LANCZOS)
        im = ImageOps.expand(im, 10, (0, 0, 0, 0)); sticker(im, 6).save(J("assets", "faces", f"e{j}.png")); os.remove(tmp)
        e["face"] = f"assets/faces/e{j}.png"
    if e.get("item_raw"):
        tmp = J("assets", "cutouts", f"item_e{j}.png"); remove_bg(J(e["item_raw"]), tmp); im = Image.open(tmp).convert("RGBA")
        bb = Image.fromarray((np.array(im.split()[3]) > 40).astype("uint8") * 255).getbbox(); im = im.crop(bb) if bb else im
        im.thumbnail((600, 300)); im.save(tmp); e["item_cutout"] = f"assets/cutouts/item_e{j}.png"
# ---- music level
m = SL["audio"].get("music")
if m and m.get("src"):
    ml = lufs(J(m["src"]), m.get("start", 0), 60); target = vo_l - STYLE["audio"]["music"]["bed_vs_vo_lu"]
    m["lufs"] = round(ml, 1); m["volume"] = round(10 ** ((target - ml) / 20), 4); m["duration"] = probe(J(m["src"]))[2]
json.dump(SL, open(a.shotlist, "w"), indent=1)
print("prepped", sum(1 for s in SL["shots"] if s.get("src")), "shots | VO", round(vo_l, 1), "LUFS | music vol", (m or {}).get("volume"))
