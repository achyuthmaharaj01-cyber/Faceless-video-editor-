"""Mix the film's audio with ffmpeg (same levels/offsets as the Hyperframes audio tags): VO + music bed (fade-out 1.5 s) + SFX events.
Usage: python -I mix_audio.py shots.json project_dir out.wav"""
import sys, os, json, subprocess, soundfile as sf
D = json.load(open(sys.argv[1])); P = sys.argv[2]; out = sys.argv[3]; A = D["audio"]; total = D["total"]
off = {"tick": -0.03, "hit": 0.0, "whoosh": -0.11}; take = {"tick": "abc", "hit": "ab", "whoosh": "ab"}; cnt = {}
gain = {"tick": 0.55, "hit": 0.9, "whoosh": 0.45, **A.get("sfx_gain", {})}
ev = sorted([e for s in D["shots"] for e in s.get("sfx", [])], key=lambda e: e["t"])
inputs = ["-i", os.path.join(P, A["vo"])]; fl = [f'[0:a]volume={A.get("vo_gain",1):.4f},apad=whole_dur={total}[vo]']; labels = ["[vo]"]; n = 1
if A.get("music"):
    inputs += ["-i", os.path.join(P, A["music"])]; fl.append(f'[{n}:a]atrim=0:{total},volume={A.get("music_gain",0.3):.4f},afade=t=out:st={total-1.5:.2f}:d=1.5,apad=whole_dur={total}[mu]'); labels.append("[mu]"); n += 1
for e in ev:
    k = e["kind"]; i = cnt.get(k, 0); cnt[k] = i + 1; f = os.path.join(P, f"assets/sfx/{k}_{take[k][i % len(take[k])]}.wav"); inputs += ["-i", f]
    ms = int(max(0, e["t"] + off[k]) * 1000); fl.append(f'[{n}:a]volume={e.get("gain", gain[k]):.3f},adelay={ms}|{ms},apad=whole_dur={total}[s{n}]'); labels.append(f"[s{n}]"); n += 1
fl.append("".join(labels) + f"amix=inputs={len(labels)}:duration=longest:normalize=0,atrim=0:{total}[m]")
subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y"] + inputs + ["-filter_complex", ";".join(fl), "-map", "[m]", "-ar", "48000", "-ac", "2", out], check=True)
print("mixed", out, len(ev), "sfx")
