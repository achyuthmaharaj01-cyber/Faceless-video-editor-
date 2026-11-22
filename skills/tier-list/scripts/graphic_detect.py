"""Pixel-rule detectors for the tier-list style's recurring graphics/treatments. Used for reference
analysis AND for QA of renders (same code both sides). Works on any resolution (coords in % of frame).
Usage: python -I graphic_detect.py frames_dir out.json"""
import sys, os, json, numpy as np
from PIL import Image, ImageFilter
TIER = np.array([[0xf5,0x7e,0x7e],[0xf8,0xbc,0x7f],[0xf7,0xdc,0x79],[0xfe,0xfc,0x79],[0xc5,0xfd,0x7a],[0x91,0xfc,0x79]])
def detect(path):
    im = Image.open(path).convert("RGB").resize((640, 360)); a = np.asarray(im).astype(int); H, W, _ = a.shape
    out = {}
    # price badge: saturated blue/cyan border pixels in the top-left box (x 2-25%, y 3-16%)
    box = a[int(.03*H):int(.16*H), int(.02*W):int(.25*W)]
    blue = (box[..., 2] > 200) & (box[..., 0] < 110) & (box[..., 1] > 120)
    out["price_badge"] = bool(blue.mean() > 0.04)
    # tier chart: header row (y 62-70%) matches the 6 tier colours in order
    row = a[int(.66*H)]; cols = [row[int((i + .5) * W / 6)] for i in range(6)]
    d = np.abs(np.array(cols) - TIER).sum(1)
    out["tier_chart"] = bool((d < 90).sum() >= 4)
    # vignette: corners much darker than centre (on non-dark frames)
    lum = a.mean(2); c = lum[int(.35*H):int(.65*H), int(.35*W):int(.65*W)].mean()
    corners = np.mean([lum[:int(.12*H), :int(.12*W)].mean(), lum[:int(.12*H), -int(.12*W):].mean(), lum[-int(.12*H):, :int(.12*W)].mean(), lum[-int(.12*H):, -int(.12*W):].mean()])
    edge_mid = np.mean([lum[int(.4*H):int(.6*H), :int(.06*W)].mean(), lum[int(.4*H):int(.6*H), -int(.06*W):].mean()])
    out["vignette"] = bool(c > 60 and corners < 0.55 * c and corners < edge_mid * 0.9)
    out["corner_to_centre"] = round(float(corners / max(c, 1)), 2)
    # blurred side fill (vertical/4:3 clip on blurred copy): side bands low detail, centre high detail
    g = np.asarray(im.convert("L").filter(ImageFilter.FIND_EDGES)).astype(float)
    side = np.mean([g[:, :int(.18*W)].mean(), g[:, -int(.18*W):].mean()]); mid = g[:, int(.35*W):int(.65*W)].mean()
    side_lum = np.mean([lum[:, :int(.18*W)].mean(), lum[:, -int(.18*W):].mean()])
    out["blur_side_fill"] = bool(mid > 6 and side < 0.35 * mid and side_lum > 25)
    out["black_side_bars"] = bool(side_lum < 12 and mid > 6)
    # white/plain background (cutout on plain bg, or article screenshot)
    out["white_bg_share"] = round(float(((a > 235).all(2)).mean()), 2)
    out["black_share"] = round(float((lum < 18).mean()), 2)
    out["text_card_black"] = bool(out["black_share"] > 0.9 and (lum > 200).mean() > 0.002)
    # red frame border
    top = a[:int(.02*H)]; out["red_border"] = bool(((top[..., 0] > 180) & (top[..., 1] < 60) & (top[..., 2] < 60)).mean() > 0.6)
    out["mean_luma"] = round(float(lum.mean()), 1); out["mean_sat"] = round(float((a.max(2) - a.min(2)).mean()), 1)
    return out
if __name__ == "__main__":
    d, outp = sys.argv[1], sys.argv[2]
    man = json.load(open(os.path.join(d, "manifest.json")))
    R = [{**m, **detect(os.path.join(d, m["file"]))} for m in man]
    json.dump(R, open(outp, "w"))
    keys = ["price_badge", "tier_chart", "vignette", "blur_side_fill", "black_side_bars", "text_card_black", "red_border"]
    print({k: round(sum(r[k] for r in R) / len(R), 3) for k in keys}, "white>0.5:", round(sum(r["white_bg_share"] > .5 for r in R) / len(R), 3))
