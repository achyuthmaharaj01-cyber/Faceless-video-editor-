"""Split a white-mode film into render chunks aligned to shot starts and 1/60 s.  Usage: python -I make_chunks.py shots.json out.json [--target 45]
Writes [{"i":0,"a":0.0,"b":47.5,"frames30":..}, ...]; build each with build_white_composition.py --window a b, render without --start/--end, concat."""
import sys, json
D = json.load(open(sys.argv[1])); tgt = float(sys.argv[sys.argv.index("--target") + 1]) if "--target" in sys.argv else 45.0
q = lambda t: round(round(t * 60) / 60, 5)
starts = sorted(q(s["ps"]) for s in D["shots"]); total = q(D["total"]); b = [0.0]
for t in starts:
    if t - b[-1] >= tgt and total - t > tgt * 0.4: b.append(t)
b.append(total); ch = [{"i": i, "a": b[i], "b": b[i + 1]} for i in range(len(b) - 1)]
# snap shot starts to the chunk grid so the chunk page boundaries coincide exactly
json.dump(ch, open(sys.argv[2], "w"), indent=1); print(len(ch), "chunks:", [(c["a"], c["b"]) for c in ch][:12])
