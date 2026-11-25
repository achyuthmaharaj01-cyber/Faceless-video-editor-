"""Prepare a Hyperframes project for WHITE mode (2D, no WebGL).  Usage: python -I setup_white_project.py project_dir [--vo vo.wav] [--music bed.wav]
Needs hyperframes installed in or above project_dir (node_modules may be a symlink)."""
import sys, os, shutil, subprocess, argparse
SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument("proj"); ap.add_argument("--vo"); ap.add_argument("--music"); ap.add_argument("--nm"); a = ap.parse_args()
P = os.path.abspath(a.proj); A = os.path.join(P, "assets"); os.makedirs(os.path.join(A, "vo"), exist_ok=True); os.makedirs(os.path.join(A, "media"), exist_ok=True)
shutil.copytree(os.path.join(SK, "components", "fonts"), os.path.join(A, "fonts"), dirs_exist_ok=True)
shutil.copy(os.path.join(SK, "components", "white", "white.css"), os.path.join(A, "white.css")); shutil.copy(os.path.join(SK, "components", "gsap.min.js"), os.path.join(A, "gsap.min.js"))
subprocess.run(["python3", "-I", os.path.join(SK, "scripts", "make_base_assets.py"), A], check=True, capture_output=True)
if a.vo: shutil.copy(a.vo, os.path.join(A, "vo", "vo.wav"))
if a.music: shutil.copy(a.music, os.path.join(A, "music_bed.wav"))
open(os.path.join(P, "hyperframes.json"), "w").write('{"$schema":"https://hyperframes.heygen.com/schema/hyperframes.json","paths":{"blocks":"compositions","components":"compositions/components","assets":"assets"},"media":{"autoProxy":true}}')
if a.nm and not os.path.exists(os.path.join(P, "node_modules")): os.symlink(a.nm, os.path.join(P, "node_modules"))
print("white project ready:", P)
