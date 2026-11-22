"""Word-level transcription with faster-whisper.
Usage: python -I transcribe.py <audio> <out.json> [--model small.en] [--exclude regions.json]
Output: {"words":[{"w","s","e","p"}], "segments":[{"s","e","text"}]}"""
import sys, json, argparse
from faster_whisper import WhisperModel
import numpy as np, soundfile as sf, subprocess, tempfile, os
ap = argparse.ArgumentParser(); ap.add_argument("audio"); ap.add_argument("out")
ap.add_argument("--model", default="small.en"); ap.add_argument("--exclude")
a = ap.parse_args()
m = WhisperModel(a.model, device="cpu", compute_type="int8", cpu_threads=4)
def load16k(path):
    tmp = tempfile.mktemp(suffix=".wav")
    subprocess.run(["ffmpeg","-nostdin","-loglevel","error","-y","-i",path,"-ac","1","-ar","16000",tmp], check=True)
    x, _ = sf.read(tmp, dtype="float32"); os.remove(tmp); return x
segs, info = m.transcribe(load16k(a.audio), word_timestamps=True, vad_filter=False,
                          condition_on_previous_text=False, beam_size=1)
excl = json.load(open(a.exclude))["regions"] if a.exclude else []
inx = lambda t: any(r[0] <= t <= r[1] for r in excl)
words, segments = [], []
for s in segs:
    if inx((s.start + s.end) / 2): continue
    segments.append({"s": round(s.start, 3), "e": round(s.end, 3), "text": s.text.strip()})
    for w in s.words or []:
        words.append({"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 3)})
json.dump({"model": a.model, "duration": info.duration, "excluded_regions": excl,
           "words": words, "segments": segments}, open(a.out, "w"))
print("words", len(words), "segments", len(segments))
