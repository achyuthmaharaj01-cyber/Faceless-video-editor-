"""Chunked, resumable render for WHITE mode.  Hyperframes' software capture stalls on a 450 s page, so the film is cut into ~40 s chunks
(aligned to shot starts), each a small page, rendered with retries; then concat + ffmpeg audio mix + mastering.
Usage: python -I render_white.py shots.json project_dir out_dir [--fps 60] [--target 40] [--tries 3]"""
import sys, os, json, shutil, subprocess, time, argparse
SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument("shots"); ap.add_argument("proj"); ap.add_argument("out"); ap.add_argument("--fps", type=int, default=60)
ap.add_argument("--target", type=float, default=40); ap.add_argument("--tries", type=int, default=3); ap.add_argument("--chunk-timeout", type=int, default=1500); a = ap.parse_args()
P = os.path.abspath(a.proj); O = os.path.abspath(a.out); os.makedirs(O, exist_ok=True); LOG = open(os.path.join(O, "render.log"), "a")
def log(*x):
    m = time.strftime("%H:%M:%S ") + " ".join(map(str, x)); print(m, flush=True); LOG.write(m + "\n"); LOG.flush()
subprocess.run(["python3", "-I", os.path.join(SK, "scripts", "make_chunks.py"), a.shots, os.path.join(O, "chunks.json"), "--target", str(a.target)], check=True, capture_output=True)
CH = json.load(open(os.path.join(O, "chunks.json"))); files = []
for c in CH:
    f = os.path.join(O, f"chunk_{c['i']:02d}.mp4"); files.append(f)
    if os.path.exists(f): continue
    cd = os.path.join(O, f"c{c['i']:02d}"); shutil.rmtree(cd, ignore_errors=True); os.makedirs(cd)
    shutil.copy(os.path.join(P, "hyperframes.json"), cd); os.symlink(os.path.join(P, "node_modules"), os.path.join(cd, "node_modules")) if os.path.exists(os.path.join(P, "node_modules")) else None
    subprocess.run(["cp", "-al", os.path.join(P, "assets"), os.path.join(cd, "assets")], check=True)
    subprocess.run(["python3", "-I", os.path.join(SK, "scripts", "build_white_composition.py"), a.shots, cd, "--window", str(c["a"]), str(c["b"])], check=True, capture_output=True)
    ok = False
    for t in range(a.tries):
        t0 = time.time(); log(f"CHUNK {c['i']+1}/{len(CH)} {c['a']}-{c['b']} try {t+1}")
        try:
            r = subprocess.run(["npx", "hyperframes", "render", "--protocol-timeout", "120000", "--fps", str(a.fps), "-o", f + ".part.mp4"], cwd=cd, capture_output=True, text=True, timeout=a.chunk_timeout)
            LOG.write((r.stdout or "")[-800:] + (r.stderr or "")[-800:] + "\n"); LOG.flush(); rc = r.returncode
        except subprocess.TimeoutExpired: rc = -9; subprocess.run(["pkill", "-f", "chrome"]); subprocess.run(["pkill", "-f", "hyperframes"])
        if rc == 0 and os.path.exists(f + ".part.mp4"): os.rename(f + ".part.mp4", f); ok = True; log(f"CHUNK {c['i']+1} done in {time.time()-t0:.0f}s"); break
        log(f"CHUNK {c['i']+1} failed rc={rc} after {time.time()-t0:.0f}s")
    if not ok: log("GIVING UP"); sys.exit(1)
    shutil.rmtree(cd, ignore_errors=True)
lst = os.path.join(O, "chunks.txt"); open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
vid = os.path.join(O, "video_only.mp4"); subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-an", "-c:v", "copy", vid], check=True)
wav = os.path.join(O, "mix.wav"); subprocess.run(["python3", "-I", os.path.join(SK, "scripts", "mix_audio.py"), a.shots, P, wav], check=True)
D = json.load(open(a.shots)); mux = os.path.join(O, "render.mp4")
subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", vid, "-i", wav, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-t", f"{D['total']:.3f}", mux], check=True)
fin = os.path.join(O, "final.mp4"); rc = subprocess.run(["python3", "-I", os.path.join(SK, "scripts", "master.py"), mux, fin]).returncode; log("FINAL rc", rc, fin)
