"""shots.json -> Hyperframes project (index.html) for the 3D motion-graphics mode.
shots.json: {"total": s, "fps": 60, "shots": [{id, ps, pe, scene, p, bg, cam, ov:[{kind,t0,t1,...}], sfx:[{t,kind}]}],
             "audio": {"vo": "assets/vo/vo.wav", "vo_gain": 1.8, "music": "assets/music_bed.wav", "music_gain": 0.3, "sfx_gain": {"tick":.55,"hit":.9,"whoosh":.45}}}
Usage: python -I build_3d_composition.py shots.json project_dir"""
import sys, os, json, soundfile as sf, subprocess
SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(sys.argv[1])); P = sys.argv[2]; A = D["audio"]; total = D["total"]
if not os.path.exists(os.path.join(P, "assets", "sfx", "tick_a.wav")):
    subprocess.run(["python3", "-I", os.path.join(SK, "scripts", "make_base_assets.py"), os.path.join(P, "assets")], check=True)
r3 = lambda x: f"{x:.3f}"
audio = [f'<audio id="vo" class="clip" src="{A["vo"]}" data-start="0" data-duration="{r3(total)}" data-volume="{A.get("vo_gain",1):.3f}" data-track-index="10" data-audio-group="voiceover"></audio>']
if A.get("music"):
    audio.append(f'<audio id="music" class="clip" src="{A["music"]}" data-start="0" data-duration="{r3(total)}" data-volume="{A.get("music_gain",0.3):.4f}" data-fade-out="1.5" data-track-index="11" data-audio-group="music"></audio>')
cnt = {}; take = {"tick": "abc", "hit": "ab", "whoosh": "ab"}; lane = {"tick": 12, "hit": 13, "whoosh": 14}; off = {"tick": -0.03, "hit": 0.0, "whoosh": -0.11}
gain = {"tick": 0.55, "hit": 0.9, "whoosh": 0.45, **A.get("sfx_gain", {})}
events = sorted([e for s in D["shots"] for e in s.get("sfx", [])], key=lambda e: e["t"])
for j, e in enumerate(events):
    k = e["kind"]; n = cnt.get(k, 0); cnt[k] = n + 1; f = f"assets/sfx/{k}_{take[k][n % len(take[k])]}.wav"; dur = sf.info(os.path.join(P, f)).duration
    audio.append(f'<audio id="sfx{j:03d}" class="clip" src="{f}" data-start="{r3(max(0, e["t"] + off[k]))}" data-duration="{dur:.3f}" data-volume="{e.get("gain", gain[k]):.3f}" data-track-index="{lane[k]}" data-audio-group="sfx"></audio>')
shots_json = json.dumps({"total": total, "shots": D["shots"]}, separators=(",", ":")).replace("</", "<\\/")
fps = D.get("fps", 60)
html = f'''<!doctype html>
<html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=1920, height=1080"/>
<script type="importmap">{{"imports":{{"three":"./assets/three/three.module.js","three/addons/":"./assets/three/jsm/"}}}}</script>
<script src="assets/gsap.min.js"></script>
<link rel="stylesheet" href="assets/tierlist.css"/><link rel="stylesheet" href="assets/gfx.css"/>
<style>*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:1920px;height:1080px;overflow:hidden;background:#000}}
#root{{position:relative;width:1920px;height:1080px;overflow:hidden;background:#000}}canvas#gl{{position:absolute;left:0;top:0;width:1920px;height:1080px}}</style></head>
<body>
<div id="root" data-composition-id="main" data-fps="{fps}" data-start="0" data-duration="{r3(total)}" data-width="1920" data-height="1080">
<canvas id="gl" width="1920" height="1080"></canvas><div id="ov"></div>
{chr(10).join(audio)}
</div>
<script id="shots" type="application/json">{shots_json}</script>
<script>window.__timelines = window.__timelines || {{}}; window.__timelines["main"] = gsap.timeline({{ paused: true }});</script>
<script type="module" src="assets/engine/engine.js"></script>
</body></html>
'''
open(os.path.join(P, "index.html"), "w").write(html)
print("wrote", os.path.join(P, "index.html"), "shots", len(D["shots"]), "sfx", len(events), "total", total)
