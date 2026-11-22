"""Map AAC packets that fail to decode (download corruption) so they are excluded
from VO on/off analysis. Usage: python -I audio_corruption_map.py video.mp4 out.json"""
import sys, json, av
src, out = sys.argv[1], sys.argv[2]
c = av.open(src); st = c.streams.audio[0]; tb = float(st.time_base)
bad = []
for pkt in c.demux(st):
    if pkt.pts is None: continue
    try:
        pkt.decode()
    except Exception:
        bad.append(round(pkt.pts * tb, 3))
# merge consecutive bad packets into regions
regions = []
for t in bad:
    if regions and t - regions[-1][1] < 0.1: regions[-1][1] = t + 0.0232
    else: regions.append([t, t + 0.0232])
regions = [[round(a, 3), round(b, 3)] for a, b in regions]
json.dump({"source": src.split('/')[-1], "bad_packets": len(bad),
           "corrupt_seconds": round(sum(b - a for a, b in regions), 2),
           "regions": regions}, open(out, "w"), indent=1)
print(len(bad), len(regions), round(sum(b - a for a, b in regions), 1))
