"""OCR every frame in a manifest with tesseract; output text lines with boxes as % of frame.
Usage: python -I ocr_frames.py frames_dir out.json"""
import sys, json, os, pytesseract
os.environ["OMP_THREAD_LIMIT"] = "1"
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
d, out = sys.argv[1], sys.argv[2]
man = json.load(open(os.path.join(d, "manifest.json")))
def one(m):
    im = Image.open(os.path.join(d, m["file"])); W, H = im.size
    try:
        t = pytesseract.image_to_data(im, config="--psm 11", output_type=pytesseract.Output.DICT, timeout=15)
    except RuntimeError:
        return {**m, "lines": [], "ocr_timeout": True}
    lines = {}
    for i, w in enumerate(t["text"]):
        if not w.strip() or float(t["conf"][i]) < 60 or len(w.strip()) < 2: continue
        k = (t["block_num"][i], t["par_num"][i], t["line_num"][i])
        x, y, ww, hh = t["left"][i], t["top"][i], t["width"][i], t["height"][i]
        L = lines.setdefault(k, {"words": [], "x0": x, "y0": y, "x1": x + ww, "y1": y + hh, "conf": []})
        L["words"].append(w); L["conf"].append(float(t["conf"][i]))
        L["x0"] = min(L["x0"], x); L["y0"] = min(L["y0"], y); L["x1"] = max(L["x1"], x + ww); L["y1"] = max(L["y1"], y + hh)
    res = []
    for L in lines.values():
        res.append({"text": " ".join(L["words"]), "conf": round(sum(L["conf"]) / len(L["conf"]), 1),
                    "x_pct": round(100 * L["x0"] / W, 1), "y_pct": round(100 * L["y0"] / H, 1),
                    "w_pct": round(100 * (L["x1"] - L["x0"]) / W, 1), "h_pct": round(100 * (L["y1"] - L["y0"]) / H, 2),
                    "cx_pct": round(50 * (L["x0"] + L["x1"]) / W, 1), "cy_pct": round(50 * (L["y0"] + L["y1"]) / H, 1)})
    return {**m, "lines": res}
with ProcessPoolExecutor(4) as ex: R = list(ex.map(one, man, chunksize=8))
json.dump(R, open(out, "w")); print(sum(bool(r["lines"]) for r in R), "/", len(R), "frames with text")
