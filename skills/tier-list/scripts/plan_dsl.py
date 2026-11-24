"""Planning DSL for the 3D motion-graphics mode: write the visual plan per script sentence/word, compile to shots.json.
  python -I plan_dsl.py compile plan.py sentences.json out.json --total 450.37 [--lead 0.05] [--vo assets/vo/vo.wav ...]
A plan file does:  from plan_dsl import *   then calls S(...), TRACKER(...)  (see below).  sentences.json comes from the
align step (sentence -> words with start/end seconds).
S(si, w, scene, p=None, bg='navy', cam=None, ov=None)   a shot starting at word w of sentence si (ends where the next starts)
Overlays (all timed by a spoken word `w` (of sentence `si`, default = the shot's), or `at` seconds from shot start, `dur`):
  L(text, anchor, side='center'|'left'|'right'|'above'|'below', dx, dy, size)    lowercase label beside a 3D anchor
  CAP(text)                bottom caption (spec-caption style)         BADGE(icon, price, model)    navy/cyan stat badge top-left
  QUOTE(text, by)          quote panel (typewriter)                    STAMP(text)                  red stamp slam (+hit sfx)
  YEAR(text)               red year top-centre
TRACKER(n, title, si0, w0, si1, w1)   persistent 'move n of 5' tracker from sentence si0/word w0 to si1/word w1"""
import sys, os, json, importlib.util
PLAN = []; TRACK = []
def S(si, w, scene, p=None, bg="navy", cam=None, ov=None): PLAN.append({"si": si, "w": w, "scene": scene, "p": p or {}, "bg": bg, "cam": cam, "ov": ov or []})
def _o(kind, **k): d = {"kind": kind}; d.update({a: b for a, b in k.items() if b is not None}); return d
def L(text, anchor=None, side="center", w=None, dx=None, dy=None, size=None, at=None, dur=None, x=None, y=None, si=None, color=None, fade=None):
    return _o("label", text=text, anchor=anchor, side=side, w=w, dx=dx, dy=dy, size=size, at=at, dur=dur, x=x, y=y, si=si, color=color, fade=fade)
def CAP(text, w=None, at=None, dur=None, si=None, size=None): return _o("caption", text=text, w=w, at=at, dur=dur, si=si, size=size)
def BADGE(icon, price, model="", w=None, at=None, dur=None, si=None): return _o("badge", icon=icon, price=price, model=model, w=w, at=at, dur=dur, si=si)
def QUOTE(text, by=None, w=None, at=None, dur=None, si=None, cps=None): return _o("quote", text=text, by=by, w=w, at=at, dur=dur, si=si, cps=cps)
def STAMP(text, w=None, at=None, dur=0.9, si=None, rot=None): return _o("stamp", text=text, w=w, at=at, dur=dur, si=si, rot=rot)
def YEAR(text, w=None, at=None, dur=None, si=None): return _o("year", text=text, w=w, at=at, dur=dur, si=si)
def PH(si, w, theme, cap=None, capw=None, motion=None, vig=False, ov=None, pick=None, bg="night", **p):
    """real-photo shot (tier-list look): a licensed photo from the theme pool fills the frame (slow push/pull), with the same overlays.
    theme = key in the photo pool; pick = index into the chosen list for that theme (default: next unused). cap = bottom caption text."""
    o = list(ov or [])
    if cap: o.append(CAP(cap, w=capw))
    PLAN.append({"si": si, "w": w, "scene": "photo", "p": {"theme": theme, "pick": pick, "motion": motion, "vig": vig, **p}, "bg": bg, "cam": None, "ov": o})
def TRACKER(n, title, si0, w0, si1, w1): TRACK.append({"n": n, "title": title, "a": (si0, w0), "b": (si1, w1)})

def compile_plan(plan_py, sent_json, total, lead=0.05, extra=None):
    PLAN.clear(); TRACK.clear()
    spec = importlib.util.spec_from_file_location("plan_mod", plan_py); mod = importlib.util.module_from_spec(spec); sys.modules["plan_mod"] = mod; spec.loader.exec_module(mod)
    SD = json.load(open(sent_json))["sentences"]
    def wt(si, w, end=False):
        ws = SD[si]["words"]; w = max(0, min(w, len(ws) - 1)); return ws[w]["e" if end else "s"]
    # hybrid mode: DROP = {(si, w), ...} removes 3D shots that a photo (PH) replaces; PLAN is then put in time order
    drop = set(getattr(mod, "DROP", ()))
    PLAN[:] = [e for e in PLAN if e["scene"] == "photo" or (e["si"], e["w"]) not in drop]
    unmatched = [d for d in drop if not any(e["si"] == d[0] and e["w"] == d[1] for e in PLAN) and d not in {(e["si"], e["w"]) for e in PLAN}]
    PLAN.sort(key=lambda e: wt(e["si"], e["w"]))
    ps_list = []
    for k, e in enumerate(PLAN):
        t = 0.0 if k == 0 else max(0.0, wt(e["si"], e["w"]) - lead)
        if ps_list and t < ps_list[-1] + 0.45: print(f"  ! shot {k} (s{e['si']} w{e['w']}) starts {t:.2f}, only {t - ps_list[-1]:.2f}s after the previous one"); t = ps_list[-1] + 0.45
        ps_list.append(t)
    shots = []; ov_count = 0
    for k, e in enumerate(PLAN):
        ps = ps_list[k]; pe = ps_list[k + 1] if k + 1 < len(PLAN) else total; d = pe - ps
        ovs = []
        for o in e["ov"]:
            o = dict(o); si = o.pop("si", None) if "si" in o else None; si = si if si is not None else e["si"]; w = o.pop("w", None); at = o.pop("at", None); dur = o.pop("dur", None)
            t0 = (wt(si, w) if w is not None else ps + (at or 0.0)); t0 = max(t0, ps); t1 = min(pe, t0 + dur) if dur else pe
            if t0 >= pe - 0.12: print(f"  ! overlay {o['kind']} {o.get('text', '')!r} at {t0:.2f} is outside shot {k} ({ps:.2f}-{pe:.2f}); dropped"); continue
            if o["kind"] == "label" and str(o.get("anchor", "")).startswith("base") and "size" not in o: o["size"] = 54   # labels under compare bars
            o["t0"] = round(t0, 3); o["t1"] = round(t1, 3); ovs.append(o); ov_count += 1
        sfx = []
        for o in ovs:
            if o["kind"] == "stamp": sfx.append({"t": o["t0"], "kind": "hit"})
        hit = HIT.get(e["scene"]);
        if hit:
            h = hit(e["p"], d)
            if h is not None: sfx.append({"t": round(ps + h, 3), "kind": "hit", "gain": 0.7})
        shots.append({"id": f"s{k:03d}", "ps": round(ps, 3), "pe": round(pe, 3), "scene": e["scene"], "p": e["p"], "bg": e["bg"], "cam": e["cam"], "ov": ovs, "sfx": sfx, "src": f"s{e['si']}w{e['w']}"})
    # badges -> tick on every other badge
    nb = 0
    for s in shots:
        for o in s["ov"]:
            if o["kind"] == "badge":
                if nb % 2 == 0: s["sfx"].append({"t": o["t0"], "kind": "tick"})
                nb += 1
    gov = []
    for tr in TRACK:
        t0 = wt(*tr["a"]) - 0.1; t1 = wt(*tr["b"], end=True) + 0.2
        gov.append({"kind": "tracker", "n": tr["n"], "title": tr["title"], "t0": round(max(0, t0), 3), "t1": round(min(total, t1), 3), "fade": 0.2})
    return {"total": round(total, 3), "shots": shots, "ov": gov}

HIT = {
    "bigNumber": lambda p, d: p.get("cnt", min(1.25, d * 0.62)), "playButton": lambda p, d: p.get("cnt", min(1.3, d * 0.65)),
    "score": lambda p, d: p.get("cnt", 1.0), "lock": lambda p, d: 0.75, "giftBox": lambda p, d: 0.5,
    "claimCard": lambda p, d: p.get("strikeAt"), "gauge": lambda p, d: p.get("cnt", min(1.6, d * 0.7)),
}
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("plan"); ap.add_argument("sent"); ap.add_argument("out"); ap.add_argument("--total", type=float, required=True); ap.add_argument("--lead", type=float, default=0.05); a = ap.parse_args()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import plan_dsl as M   # same module object the plan file imports
    D = M.compile_plan(a.plan, a.sent, a.total, a.lead); json.dump(D, open(a.out, "w"))
    import statistics as st; ds = [s["pe"] - s["ps"] for s in D["shots"]]
    print(f"{len(D['shots'])} shots, {sum(len(s['ov']) for s in D['shots'])} overlays | median shot {st.median(ds):.2f}s mean {st.mean(ds):.2f}s min {min(ds):.2f} max {max(ds):.2f} | cuts/min {len(ds) / (a.total / 60):.1f}")
