"""Prepare a Hyperframes project for the hybrid (photo + 3D) mode: engine, styles, fonts, three.js r170 (3 addons), SFX, gsap.
Usage: python -I setup_3d_project.py project_dir
Needs node/npm. three.js is installed once into ~/.cache/tierlist_three and copied (MIT)."""
import sys, os, shutil, subprocess
SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); P = os.path.abspath(sys.argv[1]); A = os.path.join(P, "assets"); os.makedirs(A, exist_ok=True)
C = os.path.expanduser("~/.cache/tierlist_three")
if not os.path.exists(os.path.join(C, "node_modules", "three", "build", "three.module.js")):
    os.makedirs(C, exist_ok=True); subprocess.run(["npm", "install", "three@0.170.0", "--no-audit", "--no-fund", "--prefix", C], check=True)
T = os.path.join(C, "node_modules", "three")
for rel in ("loaders/FontLoader.js", "geometries/TextGeometry.js", "geometries/RoundedBoxGeometry.js"):
    d = os.path.join(A, "three", "jsm", rel); os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copy(os.path.join(T, "examples", "jsm", rel), d)
shutil.copy(os.path.join(T, "build", "three.module.js"), os.path.join(A, "three", "three.module.js"))
shutil.copytree(os.path.join(SK, "components", "engine3d"), os.path.join(A, "engine"), dirs_exist_ok=True); shutil.move(os.path.join(A, "engine", "gfx.css"), os.path.join(A, "gfx.css"))
shutil.copytree(os.path.join(SK, "components", "fonts"), os.path.join(A, "fonts"), dirs_exist_ok=True)
for f in ("tierlist.css", "gsap.min.js"): shutil.copy(os.path.join(SK, "components", f), os.path.join(A, f))
subprocess.run(["python3", "-I", os.path.join(SK, "scripts", "make_base_assets.py"), A], check=True)   # SFX + chart art
if not os.path.exists(os.path.join(P, "hyperframes.json")):
    open(os.path.join(P, "hyperframes.json"), "w").write('{"$schema":"https://hyperframes.heygen.com/schema/hyperframes.json","paths":{"blocks":"compositions","components":"compositions/components","assets":"assets"},"media":{"autoProxy":true}}')
print("3D project ready:", P, "(run `npm i hyperframes@0.9.80` in or above it; node_modules may be a symlink)")
