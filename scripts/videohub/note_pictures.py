#!/usr/bin/env python3
"""Rebuild VideoHub note pictures for a HyperFrames film.

VideoHub cuts a live-preview note's pictures from the page's <canvas> elements. A HyperFrames composition
is DOM, so those pictures come out black with only the drawing on them. Each note also stores its frame
number, fps, a normalised region and the drawing as normalised shapes, so this script redraws them onto a
frame that HyperFrames itself captured at exactly that time, then writes:
    <frame>   the clean frame          (images.frame)
    <ann>     frame + drawing          (images.annotated)
    <crop>    close-up of the region   (images.crop)
The black originals are kept once as *.vhblank.jpg.

Usage: note_pictures.py NOTES_JSON FRAMES_JSON
  FRAMES_JSON maps note id -> path of the captured PNG for that note's frame.
"""
import json
import math
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def font(size):
    for name in ("DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_shapes(img, shapes):
    W, H = img.size
    d = ImageDraw.Draw(img)
    for s in shapes or []:
        col = s.get("color") or "#ff4d4d"
        lw = max(3, round(W * 0.0035 * (s.get("width") or 1)))
        P = [(x * W, y * H) for x, y in s.get("pts") or []]
        t = s.get("type")
        if not P:
            continue
        if t == "rect" and len(P) >= 2:
            (ax, ay), (bx, by) = P[0], P[-1]
            d.rectangle([min(ax, bx), min(ay, by), max(ax, bx), max(ay, by)], outline=col, width=lw)
        elif t == "ellipse" and len(P) >= 2:
            (ax, ay), (bx, by) = P[0], P[-1]
            d.ellipse([min(ax, bx), min(ay, by), max(ax, bx), max(ay, by)], outline=col, width=lw)
        elif t == "arrow" and len(P) >= 2:
            (ax, ay), (bx, by) = P[0], P[-1]
            d.line([ax, ay, bx, by], fill=col, width=lw)
            ang = math.atan2(by - ay, bx - ax)
            head = max(14, W * 0.015)
            for da in (2.6, -2.6):
                d.line([bx, by, bx + head * math.cos(ang + da), by + head * math.sin(ang + da)], fill=col, width=lw)
        elif t == "pen":
            d.line(P, fill=col, width=lw, joint="curve")
        elif t == "pin":
            x, y = P[0]
            r = max(12, W * 0.011)
            d.ellipse([x - r, y - 2 * r, x + r, y], fill=col, outline="white", width=2)
            if s.get("num") is not None:
                d.text((x, y - r), str(s["num"]), fill="white", font=font(int(r * 1.1)), anchor="mm")
        elif t == "text":
            size = int(H * 0.035 * (s.get("size") or 1))
            d.text(P[0], s.get("text") or "", fill=col, font=font(size))
    return img


def main():
    notes_file, frames_file = Path(sys.argv[1]), Path(sys.argv[2])
    notes = json.loads(notes_file.read_text(encoding="utf-8"))
    frames = json.loads(frames_file.read_text(encoding="utf-8"))
    done = []
    for n in notes:
        src = frames.get(str(n.get("id")))
        imgs = n.get("images") or {}
        if not src or not imgs:
            continue
        base = Image.open(src).convert("RGB")
        shapes = n.get("drawing")
        if isinstance(shapes, str):
            try:
                shapes = json.loads(shapes)
            except ValueError:
                shapes = []
        for key in ("frame", "annotated", "crop"):
            p = imgs.get(key)
            if p and Path(p).exists():
                keep = Path(p).with_suffix(".vhblank.jpg")
                if not keep.exists():
                    shutil.copy2(p, keep)
        if imgs.get("frame"):
            base.resize((1280, round(1280 * base.height / base.width))).save(imgs["frame"], quality=88)
        ann = draw_shapes(base.copy(), shapes)
        if imgs.get("annotated"):
            ann.resize((1280, round(1280 * ann.height / ann.width))).save(imgs["annotated"], quality=88)
        if imgs.get("crop") and n.get("region"):
            x0, y0, x1, y1 = n["region"]
            W, H = ann.size
            mx, my = 0.04 * W, 0.04 * H
            box = [max(0, x0 * W - mx), max(0, y0 * H - my), min(W, x1 * W + mx), min(H, y1 * H + my)]
            if box[2] - box[0] > 8 and box[3] - box[1] > 8:
                ann.crop([round(v) for v in box]).save(imgs["crop"], quality=90)
        done.append(n["id"])
    print(json.dumps({"rebuilt": done}))


if __name__ == "__main__":
    main()
