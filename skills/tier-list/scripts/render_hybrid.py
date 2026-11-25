"""Resumable chunked render for the hybrid (photo + 3D) mode, where one render of the whole film would take > 1 h under software WebGL.
  1. audio: a copy of the project WITHOUT the engine/canvas is rendered once (blank frames, 24 fps, draft) -> the Hyperframes audio mix
            (VO gain, music bed, SFX placement) exactly as authored; no chunk boundaries in the sound.
  2. video: the project is rendered in CHUNK-second slices with --start/--end (skips slices that already exist, so a restart resumes).
  3. concat the slices (stream copy), mux the audio mix, master to -15 LUFS / -1 dBTP (master.py).
Usage: python -I render_hybrid.py project_dir out_dir total_seconds [--fps 30] [--chunk 75] [--only audio|video|final]
Logs: out_dir/render.log; progress lines 'CHUNK i/n done in s'."""
import sys, os, re, json, shutil, subprocess, time, argparse
SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument("proj"); ap.add_argument("out"); ap.add_argument("total", type=float)
ap.add_argument("--fps", type=int, default=30); ap.add_argument("--chunk", type=float, default=75); ap.add_argument("--only", default="all"); a = ap.parse_args()
P = os.path.abspath(a.proj); O = os.path.abspath(a.out); os.makedirs(O, exist_ok=True); LOG = open(os.path.join(O, "render.log"), "a")
def log(*x):
    m = time.strftime("%H:%M:%S ") + " ".join(map(str, x)); print(m, flush=True); LOG.write(m + "\n"); LOG.flush()
def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True); LOG.write((r.stdout or "")[-1500:] + (r.stderr or "")[-1500:] + "\n"); LOG.flush(); return r.returncode
# ---------- 1. audio ----------
AP = os.path.join(O, "audio_proj"); AUD = os.path.join(O, "audio.mp4")
if a.only in ("all", "audio") and not os.path.exists(AUD):
    if os.path.exists(AP): shutil.rmtree(AP)
    os.makedirs(os.path.join(AP, "assets"))
    for f in ("hyperframes.json",): shutil.copy(os.path.join(P, f), AP)
    for d in ("vo", "sfx"): shutil.copytree(os.path.join(P, "assets", d), os.path.join(AP, "assets", d))
    for f in os.listdir(os.path.join(P, "assets")):
        if f.endswith((".wav", ".mp3", ".css", ".js")) and os.path.isfile(os.path.join(P, "assets", f)): shutil.copy(os.path.join(P, "assets", f), os.path.join(AP, "assets", f))
    os.symlink(os.path.join(P, "node_modules"), os.path.join(AP, "node_modules")) if os.path.exists(os.path.join(P, "node_modules")) else None
    h = open(os.path.join(P, "audio_index.tpl" if os.path.exists(os.path.join(P, "audio_index.tpl")) else "index.html")).read()
    h = re.sub(r'<script type="module" src="assets/engine/engine.js"></script>', "", h); h = re.sub(r'<canvas id="gl"[^>]*></canvas><div id="ov"></div>', "", h)
    h = re.sub(r'<script id="shots" type="application/json">.*?</script>', "", h, flags=re.S); h = re.sub(r'<script type="importmap">.*?</script>', "", h, flags=re.S)
    open(os.path.join(AP, "index.html"), "w").write(h)
    t0 = time.time(); log("audio render start"); rc = run(["npx", "hyperframes", "render", "--fps", "24", "-q", "draft", "-o", AUD], cwd=AP); log("audio render rc", rc, f"{time.time()-t0:.0f}s")
    if rc != 0 or not os.path.exists(AUD): log("AUDIO FAILED"); sys.exit(1)
# ---------- 2. video chunks ----------
n = int(-(-a.total // a.chunk)); chunks = []
if n > 1 and a.total - (n - 1) * a.chunk < 0.35 * a.chunk: n -= 1      # fold a short remainder into the last chunk (each render has ~100 s start-up)
for i in range(n):
    s = i * a.chunk; e = a.total if i == n - 1 else (i + 1) * a.chunk; f = os.path.join(O, f"chunk_{i:02d}.mp4"); chunks.append(f)
    if a.only not in ("all", "video") or os.path.exists(f): continue
    t0 = time.time(); tmp = f + ".part.mp4"
    cmd = ["npx", "hyperframes", "render", "--fps", str(a.fps), "--start", f"{s:g}"] + (["--end", f"{e:g}"] if i < n - 1 else []) + ["-o", tmp]
    log(f"CHUNK {i+1}/{n} start {s:g}-{e:g}"); rc = run(cmd, cwd=P)
    if rc == 0 and os.path.exists(tmp): os.rename(tmp, f); log(f"CHUNK {i+1}/{n} done in {time.time()-t0:.0f}s")
    else: log(f"CHUNK {i+1}/{n} FAILED rc={rc}"); sys.exit(1)
# ---------- 3. final ----------
if a.only in ("all", "final") and all(os.path.exists(c) for c in chunks) and os.path.exists(AUD):
    lst = os.path.join(O, "chunks.txt"); open(lst, "w").write("".join(f"file '{c}'\n" for c in chunks))
    vid = os.path.join(O, "video_only.mp4"); mux = os.path.join(O, "render.mp4"); fin = os.path.join(O, "final.mp4")
    run(["ffmpeg", "-nostdin", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-an", "-c:v", "copy", vid])
    run(["ffmpeg", "-nostdin", "-y", "-i", vid, "-i", AUD, "-map", "0:v:0", "-map", "1:a:0", "-c", "copy", "-t", f"{a.total:.3f}", mux])
    rc = run(["python3", "-I", os.path.join(SK, "scripts", "master.py"), mux, fin]); log("FINAL rc", rc, fin)
