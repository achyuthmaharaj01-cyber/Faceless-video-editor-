"""Script + VO transcript -> beats + draft shotlist (tier-list style).

Script markup (lines; everything else is narration):
  ## <Person> | <Item> | <Price> | <Tier> [| <item model label>]    entry header (not spoken)
  [CLIP: <file or search query> | <subtitle text> | <seconds>]        subject's own clip plays its audio here (VO-off)
  [PAUSE <seconds>]                                                   extra bed-only breath here
Usage: python -I segment_beats.py script.txt vo.transcript.json out_shotlist.json [--format tier|story] [--seed 7]
The script text is authoritative; the VO only provides timing. Shot lengths are drawn from the measured
reference histogram (style.json pacing) and snapped to word boundaries, preferring clause breaks."""
import sys, re, json, argparse, difflib, random, os
SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STYLE = json.load(open(os.path.join(SK, "style.json")))
ap = argparse.ArgumentParser(); ap.add_argument("script"); ap.add_argument("transcript"); ap.add_argument("out")
ap.add_argument("--format", default="tier"); ap.add_argument("--seed", type=int, default=7); a = ap.parse_args()
random.seed(a.seed)
norm = lambda w: re.sub(r"[^a-z0-9$]", "", w.lower())

# ---- parse script
entries, items, cur = [], [], None   # items: ("word", text, entry_idx) | ("clip", dict, entry_idx) | ("pause", s, entry_idx)
for line in open(a.script, encoding="utf-8"):
    line = line.strip()
    if not line: continue
    if line.startswith("##"):
        f = [x.strip() for x in line[2:].split("|")]
        cur = {"person": f[0], "item": f[1] if len(f) > 1 else "", "price": f[2] if len(f) > 2 else "", "tier": (f[3] if len(f) > 3 else "").upper(),
               "model": f[4] if len(f) > 4 else (f[1] if len(f) > 1 else "")}
        entries.append(cur); continue
    m = re.match(r"\[CLIP:\s*(.*?)\]$", line, re.I)
    if m:
        f = [x.strip() for x in m.group(1).split("|")]
        items.append(("clip", {"src": f[0], "subtitle": f[1] if len(f) > 1 else "", "dur": float(f[2]) if len(f) > 2 else 8.0}, len(entries) - 1)); continue
    m = re.match(r"\[PAUSE\s+([\d.]+)\]$", line, re.I)
    if m: items.append(("pause", float(m.group(1)), len(entries) - 1)); continue
    for w in line.split(): items.append(("word", w, len(entries) - 1))
swords = [it for it in items if it[0] == "word"]
T = json.load(open(a.transcript)); tw = T["words"]
# ---- align script words to transcript words
A = [norm(w[1]) for w in swords]; B = [norm(w["w"]) for w in tw]
sm = difflib.SequenceMatcher(a=A, b=B, autojunk=False)
timing = [None] * len(A)
for blk in sm.get_matching_blocks():
    for k in range(blk.size): timing[blk.a + k] = (tw[blk.b + k]["s"], tw[blk.b + k]["e"])
# interpolate unmatched
known = [i for i, t in enumerate(timing) if t]
for i in range(len(timing)):
    if timing[i]: continue
    p = max([k for k in known if k < i], default=None); n = min([k for k in known if k > i], default=None)
    s0 = timing[p][1] if p is not None else 0.0; s1 = timing[n][0] if n is not None else T["duration"]
    gap = [k for k in range(p + 1 if p is not None else 0, n if n is not None else len(timing))]
    j = gap.index(i); step = (s1 - s0) / max(1, len(gap)); timing[i] = (s0 + j * step, s0 + (j + 1) * step)
match_rate = len(known) / max(1, len(A))
W = [{"w": swords[i][1], "s": timing[i][0], "e": timing[i][1], "entry": swords[i][2]} for i in range(len(swords))]
# where clips/pauses sit (after the word before them)
wi = 0; anchors = []
for it in items:
    if it[0] == "word": wi += 1
    else: anchors.append((wi - 1, it))
# ---- verdict detection: "<letter>-tier" / "<letter> tier" / "god tier"
verdicts = []
for i, w in enumerate(W):
    if re.match(r"^-?tier[.,!]?$", w["w"], re.I) and i > 0:
        L = re.sub(r"[^A-Za-z]", "", W[i - 1]["w"]).upper()
        if L in ("S", "A", "B", "C", "D", "F", "GOD"): verdicts.append({"letter_i": i - 1, "tier_i": i, "tier": L})
    m = re.match(r"^([SABCDF])-tier[.,!]?$", w["w"], re.I)
    if m: verdicts.append({"letter_i": i, "tier_i": i, "tier": m.group(1).upper()})
verdicts = [v for v in verdicts if v["letter_i"] > 12 or v["tier"] != ""]   # keep all; the title line "Tier List" has no letter
# ---- shot-length sampler from the measured histogram
fmt = STYLE["pacing"]["tier_list_format (video-3)" if a.format == "tier" else "story_format (video-4)"]
hist = STYLE["pacing"]["tier_list_format (video-3)"]["shot_hist_pct"]
bins = {"<0.5": (0.35, 0.5), "0.5-1": (0.5, 1), "1-1.5": (1, 1.5), "1.5-2": (1.5, 2), "2-3": (2, 3), "3-5": (3, 5), "5+": (5, 6)}
scale = fmt["shot_sec"]["median"] / STYLE["pacing"]["tier_list_format (video-3)"]["shot_sec"]["median"]
def draw():
    r = random.uniform(0, sum(hist.values())); acc = 0
    for k, p in hist.items():
        acc += p
        if r <= acc: lo, hi = bins[k]; return random.uniform(lo, hi) * scale
    return 1.5 * scale
# ---- segment
breaks_hard = set()
for v in verdicts: breaks_hard.add(v["letter_i"]); breaks_hard.add(v["tier_i"] + 1)
for wi_, it in anchors: breaks_hard.add(wi_ + 1)
for i in range(1, len(W)):
    if W[i]["entry"] != W[i - 1]["entry"]: breaks_hard.add(i)
beats, i = [], 0
while i < len(W):
    start = W[i]["s"]; target = draw(); j = i + 1
    cap = lambda k: k < len(W) and (W[k]["w"][:1].isupper() or re.match(r"^[A-Z]\.$", W[k]["w"]))
    while j < len(W) and j not in breaks_hard and (W[j]["s"] - start < target or (cap(j) and cap(j - 1) and not re.search(r"[,.;:!?]$", W[j - 1]["w"]) or re.match(r"^[A-Z]\.$", W[j - 1]["w"]))): j += 1
    # snap: prefer a clause break within +-0.4 s of the target
    if j < len(W) and j not in breaks_hard:
        cands = [k for k in range(i + 1, min(len(W), j + 6)) if abs(W[k]["s"] - start - target) <= 0.4 and re.search(r"[,.;:!?]$", W[k - 1]["w"]) and not re.match(r"^[A-Z]\.$", W[k - 1]["w"])]
        if cands: j = min(cands, key=lambda k: abs(W[k]["s"] - start - target))
    beats.append((i, j)); i = j
# merge beats shorter than 0.5 s into the previous beat (never across a hard break into a verdict/entry start)
merged = []
for (i, j) in beats:
    dur = (W[j]["s"] if j < len(W) else W[-1]["e"]) - W[i]["s"]
    if merged and dur < 0.5 and i not in breaks_hard: merged[-1] = (merged[-1][0], j)
    elif merged and dur < 0.5 and j < len(W) and j not in breaks_hard: merged.append((i, j)); continue
    else: merged.append((i, j))
# second pass: a short beat that starts on a hard break absorbs the next non-hard beat
out_b = []
for b in merged:
    if out_b:
        pi, pj = out_b[-1]; pd = (W[pj]["s"] if pj < len(W) else W[-1]["e"]) - W[pi]["s"]
        if pd < 0.5 and b[0] not in breaks_hard: out_b[-1] = (pi, b[1]); continue
    out_b.append(b)
beats = out_b
# ---- classify beats
def kind_of(text, ent, has_verdict, first_of_entry):
    t = text.lower()
    if has_verdict: return "verdict"
    if first_of_entry and ent and ent["person"] and norm(ent["person"].split()[0]) in [norm(x) for x in text.split()]: return "named_person"
    if re.search(r"\$\s?\d|\d+(\.\d+)?\s?(million|billion|thousand|k\b)|\bdollars?\b", t): return "money"
    if re.search(r"\b\d[\d,]*\s?(horsepower|hp|mph|km/h|kph|miles|seconds|pounds|tons|feet|liters?|cylinders?|copies|units|of \d+)\b", t): return "spec_number"
    if re.search(r"\b(19|20)\d\d\b", t): return "year"
    if re.search(r"\b(crashed|sued|arrested|sold|reported|announced|leaked|fined|banned|stolen|robbed|auction)", t): return "news"
    if re.search(r"\byou('re|'ll|r)?\b", t): return "you_joke"
    if re.search(r"\b(in|at|from|to) [A-Z][a-z]+", text): return "place_or_brand"
    return "subject"
MAP = {"verdict": ("tier_chart", "cut to chart, cursor drags face into the column"),
       "named_person": ("footage", "clip/photo of the person + typewriter name label beside the head"),
       "money": ("footage", "item footage; badge price; big rotated number if it is the headline figure"),
       "spec_number": ("footage", "interior/POV footage + spec caption (icon + text) bottom-centre"),
       "year": ("footage", "archival footage of the event; red year label top-centre (story format)"),
       "news": ("screenshot", "article card, zoom-out reveal, headline highlighted"),
       "you_joke": ("still", "stock photo of a person + handwritten 'you' + arrow"),
       "place_or_brand": ("footage", "map with pin (place) or logo on black (brand)"),
       "subject": ("footage", "item b-roll; badge persists")}
shots, seen_entry = [], set()
vset = {v["letter_i"]: v for v in verdicts}; vtier = {v["tier_i"]: v for v in verdicts}
for (i, j) in beats:
    text = " ".join(w["w"] for w in W[i:j]); ent_i = W[i]["entry"]; ent = entries[ent_i] if 0 <= ent_i < len(entries) else None
    hv = any(k in vset or k in vtier for k in range(i, j))
    first = ent_i not in seen_entry; seen_entry.add(ent_i)
    k = kind_of(text, ent, hv, first); vis, note = MAP[k]
    sh = {"vo_s": round(W[i]["s"], 3), "vo_e": round(W[j]["s"] if j < len(W) else W[-1]["e"] + 0.3, 3), "text": text, "line_type": k,
          "type": vis, "note": note, "entry": ent_i, "query": "", "overlays": []}
    if ent and k not in ("verdict",):
        sh["query"] = (ent["person"] if k == "named_person" else ent["item"] or ent["person"])
        if k != "named_person" and ent.get("item"): sh["badge"] = {"key": f"e{ent_i}", "price": ent["price"], "model": ent["model"], "img": f"assets/cutouts/item_e{ent_i}.png"}
        if k == "named_person": sh["overlays"].append({"kind": "name_label", "text": ent["person"].lower().replace(" ", "\n", 1), "side": "left", "x": 30, "y": 40,
                                                       "vo_s": round(next((w["s"] for w in W[i:j] if norm(w["w"]) == norm(ent["person"].split()[0])), W[i]["s"]), 3)})
        if k == "spec_number":
            m = re.search(r"\d[\d,]*\s?\w+", text); sh["overlays"].append({"kind": "spec", "text": (m.group(0) if m else text).lower(), "icon": f"assets/cutouts/item_e{ent_i}.png", "vo_s": sh["vo_s"]})
    if k == "verdict":
        v = next(v for kk, v in list(vset.items()) + list(vtier.items()) if i <= kk < j)
        sh["chart"] = {"drop_at_vo": round(W[v["letter_i"]]["s"], 3), "tier": v["tier"]}
        sh["pause_after"] = 0.55   # bed-only breath after the verdict (reference vocal-stem pause median 0.6 s)
    shots.append(sh)
# clip inserts + pauses
for wi_, it in anchors:
    t = W[wi_]["e"] if wi_ >= 0 else 0.0
    if it[0] == "clip":
        c = it[1]; shots.append({"vo_s": round(t, 3), "type": "clip_audio", "dur": c["dur"], "src_or_query": c["src"], "entry": it[2],
                                 "overlays": [{"kind": "subtitle", "text": c["subtitle"].lower(), "delay": 0.2}] if c["subtitle"] else [], "line_type": "quote_clip"})
    else:
        prev = max((s for s in shots if s["type"] != "clip_audio" and s["vo_e"] <= t + 0.5), key=lambda s: s["vo_e"], default=None)
        if prev: prev["pause_after"] = it[1]
shots.sort(key=lambda s: (s["vo_s"], s["type"] != "clip_audio"))
out = {"title": "", "format": a.format, "entries": entries, "match_rate": round(match_rate, 3),
       "verdicts": [{"letter_vo": round(W[v["letter_i"]]["s"], 3), "tier_vo": round(W[v["tier_i"]]["s"], 3), "tier": v["tier"], "entry": W[v["letter_i"]]["entry"]} for v in verdicts],
       "audio": {"vo": "assets/vo/vo.wav", "vo_duration": T["duration"]}, "shots": shots}
json.dump(out, open(a.out, "w"), indent=1)
import statistics as st
d = [s["vo_e"] - s["vo_s"] for s in shots if s["type"] != "clip_audio"]
print(f"shots {len(shots)} | script-VO word match {match_rate:.0%} | median shot {st.median(d):.2f}s mean {st.mean(d):.2f}s | verdicts {len(verdicts)} | clips {sum(s['type']=='clip_audio' for s in shots)}")
from collections import Counter; print(Counter(s["line_type"] for s in shots))
