"""shotlist.json -> Hyperframes project (index.html + compositions/chart-XX.html + assets).

Time model. Shots carry VO time (vo_s, vo_e) from the aligned transcript. Two kinds of shots add program
time that the VO does not have:
  * type "clip_audio": the subject's own clip plays its sound (VO-off); has "dur"; inserted at vo_s.
  * "pause_after": seconds of bed-only breath after a shot (style: median 0.46 s after punchlines).
program_t = vo_t + sum(inserted time before vo_t). The VO is split into <audio> segments around inserts.

Usage: python -I build_composition.py shotlist.json project_dir
All styling comes from components/tierlist.css and style.json; see SKILL.md for the shotlist schema."""
import sys, os, json, shutil, html, math, subprocess
SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STYLE = json.load(open(os.path.join(SK, "style.json")))
SL = json.load(open(sys.argv[1])); P = sys.argv[2]
os.makedirs(os.path.join(P, "compositions"), exist_ok=True); os.makedirs(os.path.join(P, "assets", "fonts"), exist_ok=True)
for f in os.listdir(os.path.join(SK, "components", "fonts")):
    shutil.copy(os.path.join(SK, "components", "fonts", f), os.path.join(P, "assets", "fonts", f))
shutil.copy(os.path.join(SK, "components", "tierlist.css"), os.path.join(P, "assets", "tierlist.css"))
shutil.copy(os.path.join(SK, "components", "gsap.min.js"), os.path.join(P, "assets", "gsap.min.js"))
if not os.path.exists(os.path.join(P, "assets", "chart", "road.png")):
    subprocess.run(["python3", "-I", os.path.join(SK, "scripts", "make_base_assets.py"), os.path.join(P, "assets")], check=True)
esc = lambda s: html.escape(str(s), quote=True)
W, H = 1920, 1080

# ---------------- time mapping ----------------
shots = SL["shots"]
inserts = []   # (vo_t, dur)
for s in shots:
    if s["type"] == "clip_audio": inserts.append((s["vo_s"], s["dur"]))
    if s.get("pause_after"): inserts.append((s["vo_e"], s["pause_after"]))
inserts.sort()
def prog(t, after=False):
    """VO time -> program time. after=True: an insert exactly at t is counted (time after the insert)."""
    return t + sum(d for (v, d) in inserts if (v < t or (after and v <= t)))
# program spans of shots
for s in shots:
    if s["type"] == "clip_audio":
        s["ps"] = prog(s["vo_s"]); s["pe"] = s["ps"] + s["dur"]
    else:
        s["ps"] = prog(s["vo_s"], after=True); s["pe"] = prog(s["vo_e"]) + (s.get("pause_after") or 0)
# close gaps between consecutive shots so the frame is never empty
shots.sort(key=lambda s: s["ps"])
for a, b in zip(shots, shots[1:]): a["pe"] = b["ps"]
total = round(shots[-1]["pe"], 3)
r3 = lambda x: f"{x:.3f}"

els, tweens, audio, zc = [], [], [], [10]
def z(): zc[0] += 1; return zc[0]
def clip_div(id_, start, dur, inner, cls="", style="", extra=""):
    els.append(f'<div id="{id_}" class="clip {cls}" data-start="{r3(start)}" data-duration="{r3(dur)}" data-track-index="{2 if cls.startswith("ov") else 1}" style="z-index:{z()};{style}" {extra}>{inner}</div>')

# ---------------- visuals ----------------
chart_i = 0
for i, s in enumerate(shots):
    sid = f"s{i:03d}"; st, du = s["ps"], s["pe"] - s["ps"]; t = s["type"]
    if t in ("footage", "clip_audio"):
        has_audio = t == "clip_audio"
        vol = s.get("clip_volume", 1.0)
        attrs = f'data-has-audio="true" data-volume="{vol:.3f}"' if has_audio else "muted"
        if s.get("inset"):
            els.append(f'<video id="{sid}-bg" class="clip tl-inset-bg" src="{esc(s["inset_bg"])}" data-start="{r3(st)}" data-duration="{r3(du)}" data-media-start="{r3(s.get("media_start",0))}" data-track-index="0" muted playsinline style="z-index:{z()}"></video>')
            els.append(f'<video id="{sid}" class="clip tl-inset-fg" src="{esc(s["src"])}" data-start="{r3(st)}" data-duration="{r3(du)}" data-media-start="{r3(s.get("media_start",0))}" data-track-index="0" {attrs} playsinline style="z-index:{z()}"></video>')
        else:
            els.append(f'<video id="{sid}" class="clip tl-media" src="{esc(s["src"])}" data-start="{r3(st)}" data-duration="{r3(du)}" data-media-start="{r3(s.get("media_start",0))}" data-track-index="0" {attrs} playsinline style="z-index:{z()}"></video>')
        if s.get("vignette") or has_audio:
            clip_div(f"{sid}-vig", st, du, "", "ov tl-vignette")
    elif t == "still":
        inner = f'<img id="{sid}-img" src="{esc(s["src"])}" alt="" />'
        clip_div(sid, st, du, inner, "tl-still-wrap")
        m = s.get("motion", "push_in"); a, b = (1.0, 1.11) if m == "push_in" else (1.11, 1.0) if m == "pull_out" else (1.0, 1.0)
        if a != b:
            tweens.append(f'tl.fromTo("#{sid}-img", {{scale:{a}}}, {{scale:{b}, duration:{r3(du)}, ease:"none"}}, {r3(st)});')
        if s.get("vignette"): clip_div(f"{sid}-vig", st, du, "", "ov tl-vignette")
    elif t == "tier_chart":
        chart_i += 1; cid = f"chart-{chart_i:02d}"
        tpl = open(os.path.join(SK, "components", "tier-chart.html")).read().replace('data-composition-id="tier-chart"', f'data-composition-id="{cid}"')
        open(os.path.join(P, "compositions", f"{cid}.html"), "w").write(tpl)
        c = s["chart"]; drop_local = (prog(c["drop_at_vo"], after=True) - st) if c.get("drop_at_vo") is not None else 0.5
        vals = {"title": c.get("title", ""), "ranked": json.dumps(c.get("ranked", [])), "pending": json.dumps(c.get("pending", [])),
                "drop": json.dumps(c["drop"]) if c.get("drop") else "", "drop_at": f"{max(0.3, drop_local):.3f}", "cid": cid}
        els.append(f'<div id="{cid}" data-composition-id="{cid}" data-composition-src="compositions/{cid}.html" data-start="{r3(st)}" data-duration="{r3(du)}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080" data-variable-values=\'{esc(json.dumps(vals))}\' style="z-index:{z()}"></div>')
    elif t == "screenshot":
        k = s.get("card", "article"); bgcol = "#000" if k == "post" else "#fff"
        if k == "article":
            body = (f'<div class="kicker">{esc(s.get("kicker",""))}</div><div class="headline">{s["headline_html"]}</div>'
                    f'<div class="meta">{esc(s.get("meta",""))}</div>' + (f'<img src="{esc(s["img"])}" alt=""/>' if s.get("img") else ""))
        else:
            body = f'<div class="who">{esc(s.get("who",""))}</div><div class="handle">{esc(s.get("handle",""))}</div><div class="body">{s["body_html"]}</div>'
        clip_div(sid, st, du, f'<div id="{sid}-card" class="tl-card {k}">{body}</div>', "", f"position:absolute;inset:0;background:{bgcol};")
        clip_div(f"{sid}-vig", st, du, "", "ov " + ("tl-vignette-light" if k == "article" else "tl-vignette"))
        if s.get("zoom_reveal"):  # photo -> article reveal: start zoomed on the image, pull out in 0.3 s
            tweens.append(f'tl.fromTo("#{sid}-card", {{scale:2.2, yPercent:-18}}, {{scale:1, yPercent:0, duration:0.3, ease:"power2.out"}}, {r3(st)});')
        else:
            tweens.append(f'tl.fromTo("#{sid}-card", {{scale:1.0}}, {{scale:1.06, duration:{r3(du)}, ease:"none"}}, {r3(st)});')
    elif t == "map":
        inner = f'<img id="{sid}-img" src="{esc(s["src"])}" alt="" style="position:absolute;inset:0;width:1920px;height:1080px;object-fit:cover"/><img id="{sid}-pin" class="tl-pin" src="assets/chart/pin.png" style="left:{s.get("pin_x",50)*19.2:.0f}px;top:{s.get("pin_y",50)*10.8:.0f}px" alt=""/>'
        clip_div(sid, st, du, inner, "tl-still-wrap")
        tweens.append(f'tl.fromTo("#{sid}-img", {{scale:1.0}}, {{scale:1.11, duration:{r3(du)}, ease:"none"}}, {r3(st)});')
        tweens.append(f'tl.fromTo("#{sid}-pin", {{y:-260, opacity:0}}, {{y:0, opacity:1, duration:0.25, ease:"bounce.out"}}, {r3(st+0.15)});')
    elif t == "logo":
        clip_div(sid, st, du, f'<img class="tl-logo" src="{esc(s["src"])}" alt=""/>', "", "position:absolute;inset:0;background:#000;")
    elif t == "silhouette":
        clip_div(sid, st, du, f'<img class="tl-silhouette" src="{esc(s["src"])}" alt=""/><div class="tl-text tl-big" style="left:50%;top:52%;transform:translate(-50%,-50%)">{esc(s.get("number",""))}</div>', "", "position:absolute;inset:0;background:" + s.get("bg", "#cfd6dc") + ";")
    elif t == "text_card":
        clip_div(sid, st, du, f'<div class="tl-text" style="left:50%;top:50%;transform:translate(-50%,-50%);font-size:70px">{esc(s["text"])}</div>', "", "position:absolute;inset:0;background:#000;")
    else:
        raise SystemExit(f"unknown shot type {t} in {sid}")

# ---------------- overlays ----------------
def P_(vo_t): return prog(vo_t, after=True)
ov_i = 0
for i, s in enumerate(shots):
    for o in s.get("overlays", []):
        ov_i += 1; oid = f"o{ov_i:03d}"; k = o["kind"]
        os_ = P_(o["vo_s"]) if "vo_s" in o else s["ps"] + o.get("delay", 0)
        oe_ = min(s["pe"], P_(o["vo_e"])) if "vo_e" in o else s["pe"]
        du = max(0.2, oe_ - os_)
        if k == "name_label":
            text = o["text"]; chars = "".join(f'<span class="ch">{esc(c) if c != chr(10) else "<br/>"}</span>' if c != "\n" else "<br/>" for c in text)
            side = o.get("side", "left"); x = o.get("x", 30 if side == "left" else 62); y = o.get("y", 40)
            anchor = "right:%dpx" % (W - x * 19.2) if side == "left" else "left:%dpx" % (x * 19.2)
            clip_div(oid, os_, du, f'<div id="{oid}-t" class="tl-text tl-name {side}" style="{anchor};top:{y*10.8:.0f}px;transform:translateY(-50%)">{chars}</div>', "ov")
            n = len([c for c in text if c != "\n"])
            tweens.append(f'tl.fromTo("#{oid}-t .ch", {{opacity:0}}, {{opacity:1, duration:0.001, stagger:{1/35:.4f}}}, {r3(os_)});')
            tweens.append(f'tl.fromTo("#{oid}-t", {{x:0}}, {{x:{29*du:.1f}, duration:{r3(du)}, ease:"none"}}, {r3(os_)});')
        elif k == "spec":
            icon = f'<img src="{esc(o["icon"])}" alt=""/>' if o.get("icon") else ""
            clip_div(oid, os_, du, f'<div class="tl-text tl-spec" style="left:{o.get("x",55)*19.2:.0f}px;top:{o.get("y",86)*10.8:.0f}px">{icon}<span>{esc(o["text"])}</span></div>', "ov")
        elif k == "subtitle":
            red = set(w.lower() for w in o.get("red", []))
            words = " ".join(f'<span class="red">{esc(w)}</span>' if w.lower().strip(".,!?") in red else esc(w) for w in o["text"].split())
            clip_div(oid, os_, du, f'<div class="tl-text tl-sub {"story" if SL.get("format")=="story" else ""}" style="left:960px;top:{o.get("y",86)*10.8:.0f}px">{words}</div>', "ov")
        elif k == "aside":
            clip_div(oid, os_, du, f'<div class="tl-text tl-aside" style="left:{o["x"]*19.2:.0f}px;top:{o["y"]*10.8:.0f}px;transform:translate(-50%,-50%) rotate({o.get("rotate",0)}deg)">{esc(o["text"])}</div>', "ov")
        elif k == "big":
            clip_div(oid, os_, du, f'<div class="tl-text tl-big" style="left:{o["x"]*19.2:.0f}px;top:{o["y"]*10.8:.0f}px;transform:translate(-50%,-50%) rotate({o.get("rotate",0)}deg)">{esc(o["text"])}</div>', "ov")
        elif k == "year":
            clip_div(oid, os_, du, f'<div class="tl-text tl-year" style="left:960px;top:{o.get("y",8)*10.8:.0f}px">{esc(o["text"])}</div>', "ov")
        elif k == "hand":
            ax, ay, tx, ty = o["arrow"]   # % coords: arrow tail (near text) -> tip
            col = o.get("color", "#ffe14d")
            svg = (f'<svg class="tl-arrow" width="1920" height="1080" style="left:0;top:0"><defs><marker id="{oid}-m" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="{col}"/></marker></defs>'
                   f'<path d="M{ax*19.2:.0f},{ay*10.8:.0f} Q{(ax+tx)/2*19.2+40:.0f},{(ay+ty)/2*10.8-30:.0f} {tx*19.2:.0f},{ty*10.8:.0f}" stroke="{col}" stroke-width="10" fill="none" stroke-linecap="round" marker-end="url(#{oid}-m)"/></svg>')
            clip_div(oid, os_, du, svg + f'<div class="tl-hand" style="position:absolute;left:{o["x"]*19.2:.0f}px;top:{o["y"]*10.8:.0f}px;transform:translate(-50%,-50%) rotate({o.get("rotate",-6)}deg);color:{col}">{esc(o["text"])}</div>', "ov")
        elif k == "title":
            clip_div(oid, os_, du, f'<div class="tl-text tl-title" style="left:960px;top:{o.get("y",54)*10.8:.0f}px">{esc(o["text"])}</div>', "ov")
        else:
            raise SystemExit(f"unknown overlay {k}")

# price badges: one clip per consecutive run of shots sharing the same badge key
runs = []
for s in shots:
    b = s.get("badge")
    if b and runs and runs[-1][0]["key"] == b["key"] and abs(runs[-1][2] - s["ps"]) < 0.05: runs[-1][2] = s["pe"]
    elif b: runs.append([b, s["ps"], s["pe"]])
for j, (b, st, en) in enumerate(runs):
    img = f'<img src="{esc(b["img"])}" alt=""/>' if b.get("img") else ""
    clip_div(f"badge{j:02d}", st, en - st, f'<div class="tl-badge">{img}<div class="txt"><div class="price">{esc(b["price"])}</div><div class="model" data-layout-ignore>{esc(b.get("model",""))}</div></div></div>', "ov")
    if b.get("sfx", True): audio.append(("sfx", st + 0.0, "tick"))

# ---------------- audio ----------------
A = SL["audio"]; vo_src = A["vo"]; vo_len = A["vo_duration"]
cuts = [0.0] + [v for v, d in inserts] + [vo_len]
seg_i = 0
for a_, b_ in zip(cuts, cuts[1:]):
    if b_ - a_ < 0.02: continue
    seg_i += 1; ps = prog(a_, after=True)
    els.append(f'<audio id="vo{seg_i:02d}" class="clip" src="{esc(vo_src)}" data-start="{r3(ps)}" data-duration="{r3(b_-a_)}" data-media-start="{r3(a_)}" data-volume="{A.get("vo_volume",1.0):.3f}" data-track-index="10" data-audio-group="voiceover"></audio>')
# music bed: constant level (no ducking), verdict dropouts
mus = A.get("music")
if mus:
    seg_len = mus["duration"]; t0 = 0.0; k = 0
    drops = [(prog(d["letter_vo"], after=True), prog(d["tier_vo"], after=True)) for d in SL.get("verdicts", [])]
    while t0 < total:
        k += 1; dur = min(seg_len - mus.get("start", 0), total - t0)
        pts = [{"t": 0, "v": 1}]
        for (ls, ts) in drops:
            if t0 <= ls < t0 + dur:
                a1 = ls - t0; b1 = ts - t0 + STYLE["audio"]["music"]["verdict_dropout"]["return_ms_after_tier_word"] / 1000
                pts += [{"t": round(max(0, a1 - 0.03), 3), "v": 1}, {"t": round(a1, 3), "v": 0}, {"t": round(b1, 3), "v": 0}, {"t": round(b1 + 0.02, 3), "v": 1}]
        auto = esc(json.dumps({"version": 1, "lanes": [{"target": "volume", "points": pts}]}))
        els.append(f'<audio id="music{k:02d}" class="clip" src="{esc(mus["src"])}" data-start="{r3(t0)}" data-duration="{r3(dur)}" data-media-start="{r3(mus.get("start",0))}" data-volume="{mus["volume"]:.4f}" data-automation="{auto}" data-fade-out="{1.5 if t0+dur>=total-0.01 else 0}" data-track-index="11" data-audio-group="music"></audio>')
        t0 += dur
    for (ls, ts) in drops:
        audio.append(("sfx", ts + STYLE["audio"]["music"]["verdict_dropout"]["return_ms_after_tier_word"] / 1000, "hit"))
for s in shots:
    if s["type"] == "clip_audio" or s.get("vignette_whoosh"):
        audio.append(("sfx", s["ps"] - 0.08, "whoosh"))
take = {"tick": "abc", "hit": "ab", "whoosh": "ab"}; cnt = {}
import soundfile as _sf
lane = {"tick": 12, "hit": 13, "whoosh": 14}
lvl = A.get("sfx_volume", {"tick": 0.55, "hit": 0.9, "whoosh": 0.45})
offset = {"tick": -0.03, "hit": 0.0, "whoosh": -0.11}   # place so the file's peak lands 30-60 ms after the picture
for j, (_, t, kind) in enumerate(sorted(audio, key=lambda x: x[1])):
    n = cnt.get(kind, 0); cnt[kind] = n + 1; f = f"assets/sfx/{kind}_{take[kind][n % len(take[kind])]}.wav"
    els.append(f'<audio id="sfx{j:03d}" class="clip" src="{f}" data-start="{r3(max(0, t + offset[kind]))}" data-duration="{_sf.info(os.path.join(P, f)).duration:.3f}" data-volume="{lvl[kind]:.3f}" data-track-index="{lane[kind]}" data-audio-group="sfx"></audio>')

doc = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" /><meta name="viewport" content="width=1920, height=1080" />
<script src="assets/gsap.min.js"></script>
<link rel="stylesheet" href="assets/tierlist.css" />
<style>
  @font-face {{ font-family: "Arimo"; src: url("assets/fonts/arimo-latin-400-normal.woff2") format("woff2"); font-weight: 400; }}
  @font-face {{ font-family: "Arimo"; src: url("assets/fonts/arimo-latin-700-normal.woff2") format("woff2"); font-weight: 700; }}
  @font-face {{ font-family: "Kalam"; src: url("assets/fonts/kalam-latin-700-normal.woff2") format("woff2"); font-weight: 700; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1920px; height: 1080px; overflow: hidden; background: #000; }}
  #root {{ position: relative; width: 1920px; height: 1080px; overflow: hidden; background: #000; }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{r3(total)}" data-width="1920" data-height="1080">
{chr(10).join(els)}
</div>
<script>
  const tl = gsap.timeline({{ paused: true }});
  {chr(10)+'  '.join(tweens)}
  window.__timelines["main"] = tl;
</script>
</body>
</html>
'''
open(os.path.join(P, "index.html"), "w").write(doc)
json.dump({"total": total, "shots": [{k: s[k] for k in ("type", "ps", "pe", "vo_s", "vo_e") if k in s} for s in shots], "inserts": inserts},
          open(os.path.join(P, "timeline_resolved.json"), "w"), indent=1)
print("wrote", os.path.join(P, "index.html"), "duration", total, "shots", len(shots), "charts", chart_i, "badges", len(runs), "sfx", len(audio))
