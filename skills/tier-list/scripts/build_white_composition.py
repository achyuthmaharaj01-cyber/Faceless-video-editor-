"""shots.json (plan_dsl output, white-mode scenes) -> Hyperframes project: 2D, white-background, tier-list grammar.
Scenes: article | post | filing | bignum | bars | calendar | timeline | statement | quote | pct | price | list | text | photo
Overlays: caption | label | badge | stamp | year   (+ global tracker)
Usage: python -I build_white_composition.py shots.json project_dir
Project dir needs assets/{fonts,white.css,gsap.min.js,sfx/*,vo/vo.wav,music_bed.wav,media/*}  (setup_white_project.py makes them)."""
import sys, os, json, html as H, soundfile as sf
D = json.load(open(sys.argv[1])); P = sys.argv[2]; A = D["audio"]; total = D["total"]; fps = D.get("fps", 30)
WIN = None
if "--window" in sys.argv:
    # Chunk page: only the shots that START inside [a, b) (a and b must be shot boundaries), time-shifted so the page starts at 0 and
    # its duration is b - a. Hyperframes' software capture stalls on a 450 s / 230-shot page, but renders 40-60 s pages fine.
    i = sys.argv.index("--window"); a_, b_ = float(sys.argv[i + 1]), float(sys.argv[i + 2]); WIN = (a_, b_)
    fa, fb = round(a_ * 60), round(b_ * 60)      # compare on the 60 fps grid: chunk edges are frame-quantised, shot starts are not
    keep = [x for x in D["shots"] if fa <= round(x["ps"] * 60) < fb]
    for x in keep:
        x["ps"] = round(max(x["ps"] - a_, 0.0), 4); x["pe"] = round(min(x["pe"], b_) - a_, 4)
        for o in x.get("ov", []): o["t0"] = round(o["t0"] - a_, 4); o["t1"] = round(min(o["t1"], b_) - a_, 4)
        x["sfx"] = []
    D["shots"] = keep; total = round(b_ - a_, 4)
    D["ov"] = [dict(g, t0=round(max(g["t0"], a_) - a_, 4), t1=round(min(g["t1"], b_) - a_, 4)) for g in D.get("ov", []) if g["t1"] > a_ and g["t0"] < b_]
esc = lambda s: H.escape(str(s), quote=True); r3 = lambda x: f"{x:.3f}"
els, tw, audio = [], [], []
Z = [10]
def z(): Z[0] += 1; return Z[0]
def T(js): tw.append(js)
INK = {"ink": "#111", "red": "#e0262b", "gold": "#e8a100", "grey": "#8d8d8d", "blue": "#199aff"}
def col(c): return INK.get(c, c or "#111")

def hl(text, hi, sid, mark="yellow"):
    """wrap the first occurrence of each phrase in hi (str|list) in a marker span; returns html, [ids]"""
    t = esc(text); ids = []
    for k, ph in enumerate([hi] if isinstance(hi, str) else (hi or [])):
        e = esc(ph); i = t.find(e)
        if i < 0: continue
        mid = f"{sid}-m{k}"; t = t[:i] + f'<span id="{mid}" class="mark {"red" if mark == "red" else ""}">' + e + "</span>" + t[i + len(e):]; ids.append(mid)
    return t, ids
def sweep(ids, t0, dur=0.4, gap=0.25):
    for k, mid in enumerate(ids): T(f'tl.fromTo("#{mid}", {{backgroundSize:"0% 62%"}}, {{backgroundSize:"100% 62%", duration:{dur}, ease:"power2.out"}}, {r3(t0 + k * gap)});')
def pop_in(sel, t0, d=0.22, s0=0.94): T(f'tl.fromTo("{sel}", {{opacity:0, scale:{s0}}}, {{opacity:1, scale:1, duration:{d}, ease:"power2.out"}}, {r3(t0)});')
def push(sel, st, du, a=1.0, b=1.045): T(f'tl.fromTo("{sel}", {{scale:{a}}}, {{scale:{b}, duration:{r3(du)}, ease:"sine.inOut"}}, {r3(st)});')
def counter(sid, st, to, dec, pre, suf, dur, delay=0.1):
    fmt = f'(v).toFixed({dec})'
    T(f'(function(){{ var o={{v:0}}, el=document.getElementById("{sid}-n"); tl.to(o, {{v:{to}, duration:{dur}, ease:"power2.out", onUpdate:function(){{ el.textContent={json.dumps(pre)}+({fmt.replace("(v)", "o.v")})+{json.dumps(suf)}; }}}}, {r3(st + delay)}); }})();')
import json as _j
json = _j

# ---------------- scenes ----------------
def scene(s):
    sid, p, st, du, k = s["id"], s["p"], s["ps"], s["pe"] - s["ps"], s["scene"]; h = ""
    if k == "article":
        head, ids = hl(p["head"], p.get("hi"), sid, p.get("mark", "yellow"))
        fs = int(82 * p.get("size", 1.0)); kick = f'<div class="kicker">{esc(p["kicker"])}</div>' if p.get("kicker") else ""
        h = (f'<div class="wrap"><div id="{sid}-p" class="pushw"><div id="{sid}-c" class="card art"><div class="bar"><span class="outlet">{esc(p["outlet"])}</span><span class="date">{esc(p.get("date", ""))}</span></div>'
             f'{kick}<div class="head" style="font-size:{fs}px">{head}</div><div class="src"><span>{esc(p.get("src", ""))}</span><span>{esc(p.get("note", ""))}</span></div></div></div></div>')
        pop_in(f"#{sid}-c", st, 0.24, 1.07); push(f"#{sid}-p", st, du, 1.0, 1.04); sweep(ids, st + p.get("hiAt", 0.55))
        h += f'<div class="vig-w" data-layout-ignore></div>'
    elif k == "post":
        tx, ids = hl(p["text"], p.get("hi"), sid, p.get("mark", "yellow"))
        h = (f'<div class="wrap"><div id="{sid}-p" class="pushw"><div id="{sid}-c" class="card post"><div class="who"><div class="av">{esc(p.get("init", "RG"))}</div><div><div class="nm">{esc(p["name"])}'
             f'{"<span class=ck>&#10003;</span>" if p.get("verified", True) else ""}</div><div class="hd">{esc(p["handle"])}</div></div></div><div class="tx">{tx}</div><div class="dt">{esc(p["date"])}</div></div></div></div><div class="vig-w" data-layout-ignore></div>')
        pop_in(f"#{sid}-c", st, 0.24, 1.07); push(f"#{sid}-p", st, du, 1.0, 1.04); sweep(ids, st + p.get("hiAt", 0.6))
    elif k == "filing":
        tx, ids = hl(p["text"], p.get("hi"), sid, p.get("mark", "yellow"))
        h = (f'<div class="wrap"><div id="{sid}-p" class="pushw"><div id="{sid}-c" class="card fil"><div class="l1">{esc(p.get("l1", "United States Securities and Exchange Commission"))}</div><div class="l2">{esc(p.get("l2", "FORM 8-K"))}</div>'
             f'<div class="l3">{esc(p.get("l3", ""))}</div><hr/><div class="co">{esc(p["co"])}</div><div class="tx">{tx}</div><div class="src">{esc(p.get("src", ""))}</div></div></div></div><div class="vig-w" data-layout-ignore></div>')
        pop_in(f"#{sid}-c", st, 0.24, 1.07); push(f"#{sid}-p", st, du, 1.0, 1.04); sweep(ids, st + p.get("hiAt", 0.6))
    elif k == "bignum":
        size = int(330 * p.get("size", 1.0)); c = col(p.get("color", "ink")); dec = p.get("dec", 0); pre = p.get("prefix", ""); suf = p.get("suffix", "")
        y = p.get("y", 330 if p.get("sub") else 400); zero = f"{pre}{(0):.{dec}f}{suf}"
        h = (f'<div id="{sid}-b" class="bn" style="top:{y - size // 2 + 120}px;font-size:{size}px;color:{c}"><span id="{sid}-n">{esc(zero)}</span></div>'
             + (f'<div id="{sid}-s" class="bn-sub" style="top:{y + size // 2 + 150}px">{esc(p["sub"])}</div>' if p.get("sub") else "")
             + (f'<div id="{sid}-k" class="strike" style="left:{960 - int(size * 0.3 * (len(zero) + 1))}px;width:{int(size * 0.6 * (len(zero) + 1))}px;top:{y + 130}px"></div>' if p.get("strike") else ""))
        pop_in(f"#{sid}-b", st, 0.2, 0.9); counter(sid, st, p["to"], dec, pre, suf, p.get("cnt", min(1.2, du * 0.6)))
        if p.get("sub"): T(f'tl.fromTo("#{sid}-s", {{opacity:0, y:24}}, {{opacity:1, y:0, duration:0.25, ease:"power2.out"}}, {r3(st + p.get("subAt", 0.35))});')
        if p.get("strike"): T(f'tl.fromTo("#{sid}-k", {{scaleX:0}}, {{scaleX:1, duration:0.3, ease:"power3.out"}}, {r3(st + p["strike"])});')
        push(f"#{sid}-b", st, du, 1.0, 1.03)
    elif k == "bars":
        items = p["items"]; n = len(items); mx = p.get("max") or max(i["value"] for i in items); rh = 112; gap = 58; tot = n * rh + (n - 1) * gap; y0 = (1080 - tot) // 2 - 50; W = 1020
        rows = ""
        for i, it in enumerate(items):
            y = y0 + i * (rh + gap); c = col(it.get("color", "#cfcfcf")); fw = int(W * it["value"] / mx)
            rows += (f'<div class="row" style="top:{y}px;left:140px"><div class="lab">{esc(it.get("label", ""))}</div><div class="track" style="width:{W + 330}px"><div id="{sid}-f{i}" class="fill" style="background:{c}"></div>'
                     f'<div id="{sid}-v{i}" class="val" style="left:0;opacity:0;color:{col(it.get("vcolor", "ink"))}">{esc(it.get("vlabel", ""))}</div></div></div>')
            T(f'tl.to("#{sid}-f{i}", {{width:{fw}, duration:0.75, ease:"power3.out"}}, {r3(st + 0.1 + i * 0.18)});')
            T(f'tl.fromTo("#{sid}-v{i}", {{x:20, opacity:0}}, {{x:{fw + 24}, opacity:1, duration:0.75, ease:"power3.out"}}, {r3(st + 0.1 + i * 0.18)});')
        h = f'<div class="bars" id="{sid}-bars">{rows}</div>'
    elif k == "calendar":
        h = (f'<div class="wrap"><div id="{sid}-p" class="pushw"><div id="{sid}-c" class="cal"><div class="top">{esc(p["month"])}</div><div class="day" style="font-size:{int(380 * p.get("daySize", 1.0))}px">{esc(p["day"])}</div>'
             f'{"<div class=yr>" + esc(p["year"]) + "</div>" if p.get("year") else ""}</div></div></div><div class="vig-w" data-layout-ignore></div>')
        T(f'tl.fromTo("#{sid}-c", {{rotationX:-85, opacity:0, transformPerspective:1400}}, {{rotationX:0, opacity:1, duration:0.4, ease:"power3.out"}}, {r3(st)});'); push(f"#{sid}-p", st, du, 1.0, 1.035)
    elif k == "timeline":
        nodes = p["nodes"]; n = len(nodes); x0, x1, y = 330, 1590, 520; xs = [x0 + (x1 - x0) * i / max(1, n - 1) for i in range(n)]
        h = f'<div class="tl"><div id="{sid}-ln" class="ln" style="left:{x0}px;width:{x1 - x0}px;top:{y - 5}px"></div>'
        T(f'tl.fromTo("#{sid}-ln", {{scaleX:0}}, {{scaleX:1, duration:{min(0.9, du * 0.5):.2f}, ease:"power2.inOut"}}, {r3(st)});')
        for i, nd in enumerate(nodes):
            x = xs[i]; c = col(nd.get("color", "ink"))
            h += f'<div id="{sid}-n{i}" class="nd" style="left:{x}px;top:{y - 27}px;border-color:{c}"></div><div id="{sid}-l{i}" class="nl" style="left:{x}px;top:{y - 190}px;color:{c}">{esc(nd["label"])}</div>'
            if nd.get("sub"): h += f'<div id="{sid}-s{i}" class="ns" style="left:{x}px;top:{y + 60}px">{esc(nd["sub"])}</div>'
            ta = st + 0.12 + i * min(0.5, du / (n + 1))
            T(f'tl.fromTo("#{sid}-n{i}", {{scale:0}}, {{scale:1, duration:0.25, ease:"back.out(2)"}}, {r3(ta)}); tl.fromTo("#{sid}-l{i}", {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.25, ease:"power2.out"}}, {r3(ta + 0.05)});')
            if nd.get("sub"): T(f'tl.fromTo("#{sid}-s{i}", {{opacity:0}}, {{opacity:1, duration:0.25}}, {r3(ta + 0.15)});')
        h += "</div>"
    elif k == "statement":
        lines = p["lines"]; fs = int(150 * p.get("size", 1.0)); lh = fs * 1.08; y0 = 540 - lh * len(lines) / 2 - 20; hi = p.get("hi"); his = [hi] if isinstance(hi, int) else (hi or []); at = p.get("lineAt") or [0.08 + 0.45 * i for i in range(len(lines))]
        h = ""
        for i, ln in enumerate(lines):
            if i in his: txt, ids = f'<span id="{sid}-m{i}" class="mark">{esc(ln)}</span>', [f"{sid}-m{i}"]
            else: txt, ids = esc(ln), []
            h += f'<div id="{sid}-l{i}" class="st" style="top:{y0 + i * lh:.0f}px;font-size:{fs}px">{txt}</div>'
            T(f'tl.fromTo("#{sid}-l{i}", {{opacity:0, y:34}}, {{opacity:1, y:0, duration:0.26, ease:"power2.out"}}, {r3(st + at[i])});')
            if ids: sweep(ids, st + at[i] + 0.3)
        sk = p.get("strike")
        if sk:
            ln = lines[sk["line"]]; w = int(fs * 0.5 * len(ln)); h += f'<div id="{sid}-k" class="strike" style="left:{960 - w // 2}px;width:{w}px;top:{y0 + sk["line"] * lh + fs * 0.52:.0f}px"></div>'
            T(f'tl.fromTo("#{sid}-k", {{scaleX:0}}, {{scaleX:1, duration:0.3, ease:"power3.out"}}, {r3(st + sk["at"])});')
    elif k == "quote":
        tx, ids = hl(p["text"], p.get("hi"), sid, p.get("mark", "yellow"))
        h = f'<div class="wrap"><div id="{sid}-q" class="qt"><div class="mk">&ldquo;</div><div class="tx">{tx}</div><div class="by">{esc(p.get("by", ""))}</div></div></div><div class="vig-w" data-layout-ignore></div>'
        pop_in(f"#{sid}-q", st, 0.26, 0.95); sweep(ids, st + p.get("hiAt", 0.7))
    elif k == "pct":
        c = col(p.get("color", "red")); R = 250; C = 2 * 3.14159265 * R; pct = p["pct"]
        h = (f'<svg width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute;left:0;top:0"><circle cx="{p.get("cx", 960)}" cy="520" r="{R}" fill="none" stroke="#e9e9e9" stroke-width="120"/>'
             f'<circle id="{sid}-d" cx="{p.get("cx", 960)}" cy="520" r="{R}" fill="none" stroke="{c}" stroke-width="120" stroke-dasharray="{C:.1f}" stroke-dashoffset="{C:.1f}" transform="rotate(-90 {p.get("cx", 960)} 520)"/></svg>'
             f'<div id="{sid}-b" class="bn" style="top:{520 - 120}px;font-size:240px;left:{p.get("cx", 960) - 960}px"><span id="{sid}-n">0%</span></div>')
        T(f'tl.fromTo("#{sid}-d", {{strokeDashoffset:{C:.1f}}}, {{strokeDashoffset:{C * (1 - pct / 100):.1f}, duration:1.1, ease:"power3.out"}}, {r3(st + 0.1)});'); counter(sid, st, pct, 0, "", "%", 1.1)
    elif k == "price":
        c = col(p.get("color", "ink"))
        h = (f'<div class="wrap"><div id="{sid}-p" class="pt" style="border-color:{c}"><div class="hole" style="border-color:{c}"></div><div class="pr" style="color:{c}">{esc(p["price"])}</div><div class="ps">{esc(p.get("sub", ""))}</div></div></div>')
        T(f'tl.fromTo("#{sid}-p", {{rotation:-9, y:-120, opacity:0, transformOrigin:"50% 0%"}}, {{rotation:0, y:0, opacity:1, duration:0.45, ease:"back.out(1.5)"}}, {r3(st)});')
    elif k == "list":
        items = p["items"]; n = len(items); rh = p.get("rh", 190 if n <= 4 else 150); y0 = 540 - (n * rh) // 2 - (60 if p.get("title") else 0) + 40
        h = ""
        if p.get("title"): h += f'<div class="st" style="top:{y0 - 150}px;font-size:70px;color:#555;font-weight:400">{esc(p["title"])}</div>'
        for i, it in enumerate(items):
            hi = it.get("hi") if isinstance(it, dict) else None; tx = it["text"] if isinstance(it, dict) else it
            t_, ids = hl(tx, hi, f"{sid}-{i}")
            h += f'<div id="{sid}-i{i}" class="li"><div class="it" style="top:{y0 + i * rh}px"><div class="nm" style="background:{col(it.get("color", "ink")) if isinstance(it, dict) else "#111"}">{esc(p["nums"][i] if p.get("nums") else i + 1)}</div><div class="tx">{t_}</div></div></div>'
            T(f'tl.fromTo("#{sid}-i{i}", {{opacity:0, x:-60}}, {{opacity:1, x:0, duration:0.3, ease:"power2.out"}}, {r3(st + 0.12 + i * p.get("step", 0.45))});'); sweep(ids, st + 0.5 + i * p.get("step", 0.45))
    elif k == "text":
        fs = int(p.get("size", 1.0) * 300); h = f'<div id="{sid}-t" class="st" style="top:{540 - fs * 0.55:.0f}px;font-size:{fs}px;color:{col(p.get("color", "ink"))}">{esc(p["text"])}</div>'
        pop_in(f"#{sid}-t", st, 0.25, 0.85)
    elif k == "photo":
        mo = p.get("motion", "push"); a, b = (1.0, 1.09) if mo == "push" else (1.09, 1.0)
        h = f'<img id="{sid}-i" class="ph" src="{esc(p["src"])}" alt=""/>' + ('<div class="vig-d" data-layout-ignore></div>' if p.get("vig") else "")
        T(f'tl.fromTo("#{sid}-i", {{scale:{a}}}, {{scale:{b}, duration:{r3(du)}, ease:"sine.inOut"}}, {r3(st)});')
    else: raise SystemExit(f"unknown scene {k} in {sid}")
    els.append(f'<div id="{sid}" class="clip shot" data-start="{r3(st)}" data-duration="{r3(du)}" data-track-index="1" style="z-index:{z()}">{h}</div>')

# ---------------- overlays ----------------
ICON = {"coin": '<circle cx="41" cy="41" r="34" fill="#f2b01e"/><circle cx="41" cy="41" r="25" fill="none" stroke="#b97f00" stroke-width="4"/><text x="41" y="53" font-size="34" font-weight="700" text-anchor="middle" fill="#8a5a00">$</text>',
        "play": '<rect x="4" y="16" width="74" height="50" rx="14" fill="#ff2d2d"/><polygon points="33,28 33,54 56,41" fill="#fff"/>',
        "tag": '<path d="M8 40 L40 8 L74 8 L74 42 L42 74 Z" fill="#42d9f9"/><circle cx="60" cy="24" r="6" fill="#0b1230"/>',
        "doc": '<rect x="14" y="4" width="54" height="72" rx="8" fill="#fff"/><rect x="24" y="20" width="34" height="6" fill="#199aff"/><rect x="24" y="34" width="34" height="6" fill="#9db"/><rect x="24" y="48" width="24" height="6" fill="#9db"/>',
        "people": '<circle cx="28" cy="26" r="13" fill="#42d9f9"/><circle cx="56" cy="26" r="13" fill="#199aff"/><path d="M4 70 a24 24 0 0 1 48 0 Z" fill="#42d9f9"/><path d="M30 70 a24 24 0 0 1 48 0 Z" fill="#199aff"/>',
        "chart": '<rect x="10" y="40" width="14" height="32" fill="#42d9f9"/><rect x="34" y="22" width="14" height="50" fill="#199aff"/><rect x="58" y="8" width="14" height="64" fill="#f2b01e"/>'}
def overlays():
    kinds = {s["id"]: s["scene"] for s in D["shots"]}; n = 0
    for s in D["shots"]:
        onphoto = s["scene"] == "photo"
        for o in s.get("ov", []):
            n += 1; oid = f"o{n:03d}"; t0, t1 = o["t0"], o["t1"]; du = max(0.2, t1 - t0); k = o["kind"]; cls = "onphoto" if onphoto else "onwhite"
            if k == "caption":
                fs = o.get("size") or 64; txt = esc(o["text"]).replace("&lt;r&gt;", '<span class="red">').replace("&lt;/r&gt;", "</span>")
                els.append(f'<div id="{oid}" class="clip" data-start="{r3(t0)}" data-duration="{r3(du)}" data-track-index="2" style="z-index:{z()}"><div id="{oid}-t" class="o cap {cls}" style="top:{o.get("y", 86) / 100 * 1080 - fs / 2:.0f}px;font-size:{fs}px">{txt}</div></div>')
                pop_in(f"#{oid}-t", t0, 0.18, 0.92)
            elif k == "label":
                fs = o.get("size") or 72; x = o.get("x", 50); y = o.get("y", 24)
                els.append(f'<div id="{oid}" class="clip" data-start="{r3(t0)}" data-duration="{r3(du)}" data-track-index="2" style="z-index:{z()}"><div style="position:absolute;left:{x / 100 * 1920:.0f}px;top:{y / 100 * 1080:.0f}px;transform:translate(-50%,-50%)"><div id="{oid}-t" class="o {cls}" style="position:relative;font-size:{fs}px;text-align:center{";color:" + col(o["color"]) if o.get("color") else ""}">{esc(o["text"])}</div></div></div>')
                pop_in(f"#{oid}-t", t0, 0.18, 0.92)
            elif k == "badge":
                ic = ICON.get(o.get("icon", "coin"), ICON["coin"])
                els.append(f'<div id="{oid}" class="clip" data-start="{r3(t0)}" data-duration="{r3(du)}" data-track-index="2" style="z-index:{z()}"><div id="{oid}-b" class="badge"><svg class="ic" viewBox="0 0 82 82">{ic}</svg><div class="tt"><div class="pr">{esc(o["price"])}</div><div class="md">{esc(o.get("model", ""))}</div></div></div></div>')
                pop_in(f"#{oid}-b", t0, 0.18, 0.9)
            elif k == "stamp":
                x = o.get("x", 50); y = o.get("y", 50); rot = o.get("rot", -9)
                els.append(f'<div id="{oid}" class="clip" data-start="{r3(t0)}" data-duration="{r3(du)}" data-track-index="2" style="z-index:{z()}"><div style="position:absolute;left:{x / 100 * 1920:.0f}px;top:{y / 100 * 1080:.0f}px;transform:translate(-50%,-50%) rotate({rot}deg)"><div id="{oid}-s" class="stamp" style="position:relative">{esc(o["text"])}</div></div></div>')
                T(f'tl.fromTo("#{oid}-s", {{scale:2.4, opacity:0}}, {{scale:1, opacity:1, duration:0.2, ease:"power4.in"}}, {r3(t0)});')
            elif k == "year":
                els.append(f'<div id="{oid}" class="clip" data-start="{r3(t0)}" data-duration="{r3(du)}" data-track-index="2" style="z-index:{z()}"><div id="{oid}-t" class="year" style="top:60px">{esc(o["text"])}</div></div>'); pop_in(f"#{oid}-t", t0, 0.18, 0.9)
for s in D["shots"]: scene(s)
overlays()
for j, g in enumerate(D.get("ov", [])):
    if g["kind"] == "tracker":
        oid = f"tr{j}"; els.append(f'<div id="{oid}" class="clip" data-start="{r3(g["t0"])}" data-duration="{r3(g["t1"] - g["t0"])}" data-track-index="3" style="z-index:{z()}"><div id="{oid}-t" class="tracker"><b>move {g["n"]} of 5</b><span>{esc(g["title"])}</span></div></div>')
        if g["t0"] > 0.02: T(f'tl.fromTo("#{oid}-t", {{opacity:0, y:-16}}, {{opacity:1, y:0, duration:0.25, ease:"power2.out"}}, {r3(g["t0"])});')   # no re-fade at a chunk start

# ---------------- audio ----------------
if not WIN: audio.append(f'<audio id="vo" class="clip" src="{A["vo"]}" data-start="0" data-duration="{r3(total)}" data-volume="{A.get("vo_gain", 1):.3f}" data-track-index="10" data-audio-group="voiceover"></audio>')
if A.get("music") and not WIN: audio.append(f'<audio id="music" class="clip" src="{A["music"]}" data-start="0" data-duration="{r3(total)}" data-volume="{A.get("music_gain", 0.3):.4f}" data-fade-out="1.5" data-track-index="11" data-audio-group="music"></audio>')
cnt = {}; take = {"tick": "abc", "hit": "ab", "whoosh": "ab"}; lane = {"tick": 12, "hit": 13, "whoosh": 14}; off = {"tick": -0.03, "hit": 0.0, "whoosh": -0.11}
gain = {"tick": 0.55, "hit": 0.9, "whoosh": 0.45, **A.get("sfx_gain", {})}
events = sorted([e for s in D["shots"] for e in s.get("sfx", [])], key=lambda e: e["t"]) if not WIN else []
for j, e in enumerate(events):
    k = e["kind"]; n = cnt.get(k, 0); cnt[k] = n + 1; f = f"assets/sfx/{k}_{take[k][n % len(take[k])]}.wav"; dur = sf.info(os.path.join(P, f)).duration
    audio.append(f'<audio id="sfx{j:03d}" class="clip" src="{f}" data-start="{r3(max(0, e["t"] + off[k]))}" data-duration="{dur:.3f}" data-volume="{e.get("gain", gain[k]):.3f}" data-track-index="{lane[k]}" data-audio-group="sfx"></audio>')
FONTS = '''@font-face{font-family:"Arimo";src:url("assets/fonts/arimo-latin-400-normal.woff2") format("woff2");font-weight:400}
@font-face{font-family:"Arimo";src:url("assets/fonts/arimo-latin-700-normal.woff2") format("woff2");font-weight:700}
@font-face{font-family:"Kalam";src:url("assets/fonts/kalam-latin-700-normal.woff2") format("woff2");font-weight:700}'''
head = f'<!doctype html>\n<html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=1920, height=1080"/><script src="assets/gsap.min.js"></script><link rel="stylesheet" href="assets/white.css"/><style>{FONTS}</style></head>'
page = (head + f'<body><div id="root" data-composition-id="main" data-fps="{fps}" data-start="0" data-duration="{r3(total)}" data-width="1920" data-height="1080">\n' + "\n".join(els) + "\n" + "\n".join(audio)
        + '\n</div><script>window.__timelines=window.__timelines||{};const tl=gsap.timeline({paused:true});\n' + "\n".join(tw) + '\nwindow.__timelines["main"]=tl;</script></body></html>\n')
open(os.path.join(P, "index.html"), "w").write(page)
open(os.path.join(P, "audio_index.tpl"), "w").write(head + f'<body><div id="root" data-composition-id="main" data-fps="24" data-start="0" data-duration="{r3(total)}" data-width="1920" data-height="1080"><div class="clip" data-start="0" data-duration="{r3(total)}" style="width:10px;height:10px;background:#fff"></div>\n' + "\n".join(audio)
        + '\n</div><script>window.__timelines=window.__timelines||{};window.__timelines["main"]=gsap.timeline({paused:true});</script></body></html>\n')
print("wrote", P + "/index.html", "shots", len(D["shots"]), "overlays", sum(len(s.get("ov", [])) for s in D["shots"]), "tweens", len(tw), "sfx", len(events))
