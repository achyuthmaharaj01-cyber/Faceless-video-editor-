"""Master the rendered video to the reference loudness: two-pass EBU R128 loudnorm, video copied untouched.
Target: style.json audio.master (-15 LUFS integrated, -1 dBTP).  Usage: python -I master.py render.mp4 final.mp4"""
import sys, os, json, subprocess, re
SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); M = json.load(open(os.path.join(SK, "style.json")))["audio"]["master"]
src, dst = sys.argv[1], sys.argv[2]; I, TP, LRA = M["target_lufs"], M["true_peak_dbtp"], 11
r = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-i", src, "-af", f"loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
m = json.loads(re.findall(r"\{[^{}]*\}", r.stderr)[-1])
af = (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
      f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true:print_format=json")
r2 = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-y", "-i", src, "-c:v", "copy", "-af", af, "-ar", "48000", "-c:a", "aac", "-b:a", "192k", dst], capture_output=True, text=True)
o = json.loads(re.findall(r"\{[^{}]*\}", r2.stderr)[-1])
print(json.dumps({"input_lufs": float(m["input_i"]), "output_lufs": float(o["output_i"]), "output_tp": float(o["output_tp"]), "file": dst}))
