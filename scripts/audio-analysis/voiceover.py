#!/usr/bin/env python3
"""Voiceover analysis + script alignment.

The voiceover is the timing authority; the script is the text authority. Whisper (faster-whisper, local,
CPU) produces word timestamps; those are aligned onto the script's own words with a sequence alignment,
so every script word gets a measured start/end. Words the narrator skipped or changed are reported, never
silently "fixed".

Usage:
  voiceover.py VOICE SCRIPT_JSON --out ANALYSIS_DIR --words WORDS_JSON [--model small.en] [--force]

Writes ANALYSIS_DIR/voiceover.json (technical + loudness + pauses), ANALYSIS_DIR/alignment.json
(sentences with times, per-word times, emphasis, mismatch report) and WORDS_JSON in VideoHub's
[[start, end, "word"], ...] format.
"""
import argparse
import difflib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

SR = 16000


def probe(path):
    d = json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
                                  capture_output=True, text=True, check=True).stdout)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    if not a:
        raise SystemExit(f"ERROR: no audio stream in {path}")
    return {"file": Path(path).name, "codec": a.get("codec_name"), "sample_rate": int(a.get("sample_rate", 0)),
            "channels": a.get("channels"), "duration_sec": round(float(d["format"]["duration"]), 3),
            "bitrate_kbps": round(int(d["format"].get("bit_rate", 0)) / 1000) or None}


def loudness(path):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    s = r.stderr[r.stderr.rfind("Summary:"):]
    def g(k):
        m = re.search(rf"{k}:\s+(-?[\d.]+|-inf)", s)
        return None if not m or m.group(1) == "-inf" else float(m.group(1))
    return {"integrated_lufs": g("I"), "lra_lu": g("LRA"), "true_peak_dbtp": g("Peak")}


def silences(path, noise_db=-40, min_d=0.25):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-af", f"silencedetect=noise={noise_db}dB:d={min_d}", "-f", "null", "-"],
                       capture_output=True, text=True)
    out, start = [], None
    for line in r.stderr.splitlines():
        m = re.search(r"silence_start: (-?[\d.]+)", line)
        if m:
            start = max(0.0, float(m.group(1)))
        m = re.search(r"silence_end: ([\d.]+) \| silence_duration: ([\d.]+)", line)
        if m and start is not None:
            out.append({"start": round(start, 3), "end": round(float(m.group(1)), 3), "duration": round(float(m.group(2)), 3)})
            start = None
    return out


def decode(path):
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(pcm, np.float32)


def asr(audio, model_name):
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    from faster_whisper import WhisperModel
    model = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)
    segs, _ = model.transcribe(audio, language="en", word_timestamps=True, vad_filter=True, beam_size=5,
                               condition_on_previous_text=False)
    words = []
    for s in segs:
        for w in s.words or []:
            if w.word.strip():
                words.append({"w": w.word.strip(), "s": float(w.start), "e": float(w.end), "p": float(w.probability)})
    return words


NUM_WORDS = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7",
             "eight": "8", "nine": "9", "ten": "10", "eleven": "11", "twelve": "12", "twenty": "20", "thirty": "30",
             "forty": "40", "fifty": "50", "hundred": "100", "percent": "%"}


def norm(tok):
    t = tok.lower().replace("’", "'")
    t = re.sub(r"[^\w%$']", "", t)
    t = t.replace(",", "")
    return NUM_WORDS.get(t, t)


def align(script_words, asr_words, duration):
    """Give every script word a time from the ASR words (sequence alignment on normalised tokens)."""
    a = [norm(w) for w in script_words]
    b = [norm(w["w"]) for w in asr_words]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    times = [None] * len(a)
    how = ["missing"] * len(a)
    extra = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                w = asr_words[j1 + k]
                times[i1 + k] = (w["s"], w["e"]); how[i1 + k] = "matched"
        elif tag == "replace":
            s, e = asr_words[j1]["s"], asr_words[j2 - 1]["e"]
            lens = [max(1, len(script_words[i])) for i in range(i1, i2)]
            tot, acc = sum(lens), s
            for k, L in enumerate(lens):
                d = (e - s) * L / tot
                times[i1 + k] = (acc, acc + d); how[i1 + k] = "approximate"
                acc += d
            extra.append({"script": " ".join(script_words[i1:i2]), "heard": " ".join(w["w"] for w in asr_words[j1:j2]),
                          "start": round(s, 2), "end": round(e, 2), "kind": "different"})
        elif tag == "insert":
            extra.append({"script": "", "heard": " ".join(w["w"] for w in asr_words[j1:j2]),
                          "start": round(asr_words[j1]["s"], 2), "end": round(asr_words[j2 - 1]["e"], 2), "kind": "not in script"})
        elif tag == "delete":
            extra.append({"script": " ".join(script_words[i1:i2]), "heard": "", "kind": "not heard (skipped or unclear)",
                          "after_word": i1 - 1})
    # interpolate words that have no time (deleted from the audio, or unmatched ends)
    known = [i for i, t in enumerate(times) if t]
    for i, t in enumerate(times):
        if t:
            continue
        prev = max((k for k in known if k < i), default=None)
        nxt = min((k for k in known if k > i), default=None)
        s = times[prev][1] if prev is not None else 0.0
        e = times[nxt][0] if nxt is not None else duration
        gap_words = (nxt if nxt is not None else len(times)) - (prev if prev is not None else -1) - 1
        pos = i - (prev if prev is not None else -1) - 1
        step = max(0.0, e - s) / max(1, gap_words)
        times[i] = (s + pos * step, s + (pos + 1) * step)
    return times, how, extra


FUNCTION_WORDS = set("a an the and or but of to in on at by for with from as is was were be been it its this that these those "
                     "he she they we you i his her their our your my me him them us there here so if then than".split())


UNITS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
                                     "fifteen sixteen seventeen eighteen nineteen".split())}
TENS = {w: 10 * i for i, w in enumerate("_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()) if w != "_"}
SCALES = {"hundred": 100, "thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12}


def number_value(text):
    """Numeric value of '58', '$5 .86', '24,000', 'fifty-eight', 'twenty-four thousand', '$70 billion'; else None."""
    t = text.lower().replace("$", " ").replace("£", " ").replace("€", " ").replace(",", "").replace("-", " ")
    t = re.sub(r"(\d)\s+\.(\d)", r"\1.\2", t)
    t = re.sub(r"(\d)\s+(\d{3})\b", r"\1\2", t)   # "24 ,000" -> "24000"
    toks = [x for x in re.findall(r"[a-z]+|\d+(?:\.\d+)?", t) if x not in ("and", "a", "dollars", "dollar", "cents", "per", "th", "st", "nd", "rd")]
    if not toks:
        return None
    total, cur, seen = 0.0, 0.0, False
    for x in toks:
        if re.fullmatch(r"\d+(?:\.\d+)?", x):
            cur += float(x); seen = True
        elif x in UNITS:
            cur += UNITS[x]; seen = True
        elif x in TENS:
            cur += TENS[x]; seen = True
        elif x == "hundred":
            cur = (cur or 1) * 100; seen = True
        elif x in SCALES:
            total += (cur or 1) * SCALES[x]; cur = 0; seen = True
        else:
            return None
    return total + cur if seen else None


def classify(m):
    """Mark mismatches that only differ in how a number or name is written (not a narration change)."""
    sc, hd = m.get("script", ""), m.get("heard", "")
    if not sc or not hd:
        return m
    a, b = number_value(sc), number_value(hd)
    if a is not None and b is not None:
        if abs(a - b) < 1e-6:
            m["benign"] = "number written differently"
        else:
            m["number_differs"] = {"script": a, "heard": b}
        return m
    if difflib.SequenceMatcher(None, re.sub(r"\W", "", sc.lower()), re.sub(r"\W", "", hd.lower())).ratio() >= 0.7:
        m["benign"] = "spelling / transcription variant"
    elif len(sc.split()) == len(hd.split()) == 1 and len(sc) <= 2:
        m["benign"] = "letter name"
    return m


def emphasis(audio, words, times):
    rms = []
    for (s, e) in times:
        seg = audio[int(s * SR):max(int(s * SR) + 1, int(e * SR))]
        rms.append(float(np.sqrt(np.mean(seg * seg)) + 1e-9) if seg.size else 1e-9)
    db = 20 * np.log10(np.asarray(rms))
    dur = np.asarray([max(0.01, e - s) / max(1, len(w)) for w, (s, e) in zip(words, times)])
    scores = []
    for i in range(len(words)):
        lo, hi = max(0, i - 12), min(len(words), i + 13)
        loud = db[i] - np.median(db[lo:hi])
        slow = dur[i] / (np.median(dur[lo:hi]) + 1e-6)
        pause = times[i][0] - times[i - 1][1] if i else 0.0
        scores.append(round(float(0.5 * max(0, loud) + 1.5 * max(0, slow - 1.2) + 2.0 * max(0, pause - 0.3)), 2))
    return scores


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("voice", type=Path)
    ap.add_argument("script_json", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--words", type=Path, required=True)
    ap.add_argument("--model", default="small.en")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    vo_file = a.out / "voiceover.json"
    if vo_file.exists() and not a.force:
        vo = json.loads(vo_file.read_text())
    else:
        vo = {"probe": probe(a.voice), "loudness": loudness(a.voice), "silences": silences(a.voice)}
        vo_file.write_text(json.dumps(vo, indent=1))
    duration = vo["probe"]["duration_sec"]

    audio = decode(a.voice)
    asr_file = a.out / "asr.json"
    if asr_file.exists() and not a.force:
        asr_words = json.loads(asr_file.read_text())["words"]
    else:
        asr_words = asr(audio, a.model)
        asr_file.write_text(json.dumps({"model": a.model, "words": asr_words}))

    script = json.loads(a.script_json.read_text(encoding="utf-8"))
    sw, owner = [], []
    for s in script["sentences"]:
        for w in s["text"].split():
            sw.append(w); owner.append(s["index"])
    if not sw:
        raise SystemExit("ERROR: the script has no narration text")
    times, how, mism = align(sw, asr_words, duration)
    mism = [classify(m) for m in mism]
    emph = emphasis(audio, sw, times)

    sentences = []
    for s in script["sentences"]:
        idx = [i for i, o in enumerate(owner) if o == s["index"]]
        st, en = times[idx[0]][0], times[idx[-1]][1]
        matched = sum(how[i] == "matched" for i in idx) / len(idx)
        top = sorted((i for i in idx if re.sub(r"\W", "", sw[i].lower()) not in FUNCTION_WORDS), key=lambda i: -emph[i])[:2]
        sentences.append({"index": s["index"], "paragraph": s["paragraph"], "text": s["text"],
                          "start": round(st, 3), "end": round(en, 3), "duration": round(en - st, 3),
                          "words": [idx[0], idx[-1]], "match_ratio": round(matched, 3),
                          "emphasis": [sw[i] for i in top if emph[i] >= 1.0]})
    # pauses between sentences (narration rhythm)
    for k in range(1, len(sentences)):
        sentences[k]["pause_before"] = round(sentences[k]["start"] - sentences[k - 1]["end"], 3)
    matched = sum(h == "matched" for h in how) / len(how)
    align_doc = {
        "duration_sec": duration, "asr_model": a.model, "script_words": len(sw), "asr_words": len(asr_words),
        "matched_ratio": round(matched, 4),
        "speech_start": round(times[0][0], 3), "speech_end": round(times[-1][1], 3),
        "words_per_minute": round(len(sw) / max(1e-6, (times[-1][1] - times[0][0]) / 60), 1),
        "sentences": sentences,
        "words": [{"i": i, "w": w, "s": round(t[0], 3), "e": round(t[1], 3), "how": h, "emphasis": e, "sentence": o}
                  for i, (w, t, h, e, o) in enumerate(zip(sw, times, how, emph, owner))],
        "mismatches": mism,
    }
    (a.out / "alignment.json").write_text(json.dumps(align_doc, indent=1, ensure_ascii=False))
    a.words.parent.mkdir(parents=True, exist_ok=True)
    a.words.write_text(json.dumps([[round(t[0], 3), round(t[1], 3), w] for w, t in zip(sw, times)], ensure_ascii=False))
    print(json.dumps({"duration_sec": duration, "sentences": len(sentences), "matched_ratio": align_doc["matched_ratio"],
                      "mismatches": len(mism), "mismatches_needing_review": sum(1 for m in mism if not m.get("benign")), "wpm": align_doc["words_per_minute"], "loudness": vo["loudness"]}))


if __name__ == "__main__":
    main()
