"""Remap every VO-time field of a shot list onto a tightened (or re-edited) VO using tighten_vo's timemap.
Usage: python -I remap_times.py shotlist.json vo.timemap.json   (in place; fields: vo_s, vo_e, overlay vo_s/vo_e, chart.drop_at_vo, verdicts)"""
import sys, json
SL = json.load(open(sys.argv[1])); cuts = json.load(open(sys.argv[2]))["removed"]
def f(t):
    out = t
    for s0, d in cuts:
        if t >= s0 + d: out -= d
        elif t > s0: out -= (t - s0)
    return round(out, 3)
for s in SL["shots"]:
    for k in ("vo_s", "vo_e"):
        if k in s: s[k] = f(s[k])
    for o in s.get("overlays", []):
        for k in ("vo_s", "vo_e"):
            if k in o: o[k] = f(o[k])
    if s.get("chart", {}).get("drop_at_vo") is not None: s["chart"]["drop_at_vo"] = f(s["chart"]["drop_at_vo"])
for v in SL.get("verdicts", []):
    v["letter_vo"] = f(v["letter_vo"]); v["tier_vo"] = f(v["tier_vo"])
json.dump(SL, open(sys.argv[1], "w"), indent=1); print("remapped", len(cuts), "cuts")
