"""Face detection (YuNet) + identity matching (SFace) for cutouts and name-label placement.
Models (OpenCV zoo, Apache-2.0) are fetched once from huggingface.co/opencv into ~/.cache/tierlist_models.
  detect(img_rgb)            -> list of dicts {box:(x,y,w,h), score, raw}   (largest first)
  embed(img_rgb, face)       -> 128-d feature
  same_person(f1, f2)        -> cosine similarity (SFace: >= 0.363 = same person)"""
import os, urllib.request, numpy as np, cv2
D = os.path.expanduser("~/.cache/tierlist_models"); os.makedirs(D, exist_ok=True)
M = {"det": ("face_detection_yunet_2023mar.onnx", "opencv/face_detection_yunet"),
     "rec": ("face_recognition_sface_2021dec.onnx", "opencv/face_recognition_sface")}
def _path(k):
    f, repo = M[k]; p = os.path.join(D, f)
    if not os.path.exists(p) or os.path.getsize(p) < 10000:
        urllib.request.urlretrieve(f"https://huggingface.co/{repo}/resolve/main/{f}", p)
    return p
_det = None; _rec = None
SAME = 0.363
def detect(img, min_size=24, thresh=0.75):
    global _det
    bgr = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR); h, w = bgr.shape[:2]
    # YuNet works best <= ~1280 px: downscale big images, scale boxes back
    s = min(1.0, 1280 / max(h, w)); small = cv2.resize(bgr, (int(w * s), int(h * s))) if s < 1 else bgr
    if _det is None: _det = cv2.FaceDetectorYN.create(_path("det"), "", (small.shape[1], small.shape[0]), thresh, 0.3, 5000)
    _det.setInputSize((small.shape[1], small.shape[0])); _det.setScoreThreshold(thresh)
    _, faces = _det.detect(small)
    out = []
    for f in (faces if faces is not None else []):
        raw = f.copy(); raw[:14] /= s
        x, y, fw, fh = raw[:4]
        if fw * s >= min_size: out.append({"box": (float(x), float(y), float(fw), float(fh)), "score": float(f[14]), "raw": raw})
    return sorted(out, key=lambda d: -d["box"][2] * d["box"][3])
def embed(img, face):
    global _rec
    if _rec is None: _rec = cv2.FaceRecognizerSF.create(_path("rec"), "")
    bgr = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
    return _rec.feature(_rec.alignCrop(bgr, face["raw"])).flatten()
def same_person(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
def face_from_box(img, box):
    """manual [x,y,w,h]: run detection inside the box to get landmarks (needed for alignment)."""
    x, y, w, h = box; pad = 0.6
    X0, Y0 = max(0, int(x - w * pad)), max(0, int(y - h * pad))
    crop = np.asarray(img)[Y0:int(y + h * (1 + pad)), X0:int(x + w * (1 + pad))]
    f = detect(crop, min_size=12, thresh=0.5)
    if not f: return None
    f = f[0]; f["raw"][[0, 4, 6, 8, 10, 12]] += X0; f["raw"][[1, 5, 7, 9, 11, 13]] += Y0   # x,y + 5 landmarks (not w,h)
    bx = f["box"]; f["box"] = (bx[0] + X0, bx[1] + Y0, bx[2], bx[3]); return f
