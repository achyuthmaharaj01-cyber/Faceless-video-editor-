#!/usr/bin/env python3
"""Extract narration text from a script file (.txt, .md, .docx) and analyse its structure.

Prints JSON: {text, paragraphs:[{index, heading?, text}], sentences:[{index, paragraph, text}],
entities:{years, money, numbers, percentages, names, quotes}, stats}.

Production notes / bracketed directions (e.g. "[B-ROLL: ...]", "(music swells)") are separated from the
narration: they are not spoken, so they must not be aligned against the voiceover. They are kept as
`directions` so the storyboard can use them.
"""
import json
import re
import sys
from pathlib import Path

DIRECTION = re.compile(r"^\s*[\[(].*[\])]\s*$")
INLINE_DIRECTION = re.compile(r"\[[^\]]{2,}\]")


def read_docx(path):
    import docx  # python-docx
    d = docx.Document(str(path))
    out = []
    for p in d.paragraphs:
        t = p.text.strip()
        if not t:
            continue
        style = (p.style.name or "").lower() if p.style is not None else ""
        out.append(("# " + t) if style.startswith("heading") or style == "title" else t)
    return "\n\n".join(out)


def read_text(path):
    ext = path.suffix.lower()
    if ext == ".docx":
        return read_docx(path)
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"cannot decode {path}")


def strip_md(line):
    line = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", line)          # images
    line = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", line)        # links
    line = re.sub(r"[*_`~]{1,3}([^*_`~]+)[*_`~]{1,3}", r"\1", line)
    line = re.sub(r"^\s*[-*+>]\s+", "", line)
    line = re.sub(r"^\s*\d+[.)]\s+", "", line)
    return line.strip()


SENT = re.compile(r"(?<=[.!?…])[\"”')\]]*\s+(?=[\"“'(\[]?[A-Z0-9$£€])")
ABBREV = {"mr.", "mrs.", "ms.", "dr.", "st.", "vs.", "inc.", "ltd.", "co.", "jr.", "sr.", "u.s.", "u.k.", "e.g.", "i.e.", "etc.", "no."}


def sentences(par):
    parts = SENT.split(par)
    merged = []
    for p in parts:
        if merged and merged[-1].split()[-1].lower() in ABBREV:
            merged[-1] += " " + p
        else:
            merged.append(p)
    return [s.strip() for s in merged if s.strip()]


def entities(text):
    years = sorted(set(re.findall(r"\b(1[5-9]\d\d|20\d\d)s?\b", text)))
    money = re.findall(r"[$£€]\s?\d[\d,.]*(?:\s?(?:thousand|million|billion|trillion|[kKmMbB]n?)\b)?|\b\d[\d,.]*\s?(?:dollars|pounds|euros)\b", text)
    pct = re.findall(r"\b\d[\d,.]*\s?(?:%|percent)\b", text)
    nums = re.findall(r"\b\d[\d,.]*\s?(?:thousand|million|billion|trillion)\b", text)
    quotes = re.findall(r"[\"“]([^\"”]{8,200})[\"”]", text)
    # capitalised multi-word names not at sentence start (heuristic; Claude verifies)
    names = {}
    stop = {"On", "In", "The", "A", "An", "And", "But", "So", "With", "Why", "When", "What", "How", "Today", "This", "That",
            "It", "He", "She", "They", "We", "You", "I", "If", "As", "At", "By", "For", "From", "Of", "To", "Five", "One", "Two"}
    cap = r"[A-Z][a-zA-Z'’\-]+"
    for m in re.finditer(rf"\b({cap}(?:\s+(?:{cap}|of|de|von|van|&))*)", text):
        parts = m.group(1).split()
        while parts and parts[0] in stop:
            parts = parts[1:]
        while parts and parts[-1] in {"of", "de", "von", "van", "&"}:
            parts = parts[:-1]
        if not parts or (len(parts) == 1 and len(parts[0]) < 3):
            continue
        n = " ".join(parts)
        names[n] = names.get(n, 0) + 1
    return {"years": years, "money": money, "percentages": pct, "big_numbers": nums, "quotes": quotes,
            "names": sorted(names, key=lambda k: -names[k])[:80]}


def main():
    path = Path(sys.argv[1])
    raw = read_text(path)
    is_md = path.suffix.lower() in (".md", ".markdown")
    paragraphs, directions = [], []
    heading = None
    blocks = re.split(r"\n\s*\n", raw.replace("\r\n", "\n"))
    for b in blocks:
        lines = [l for l in b.split("\n") if l.strip()]
        if not lines:
            continue
        keep = []
        for l in lines:
            s = l.strip()
            if re.match(r"^#{1,6}\s", s):
                heading = re.sub(r"^#{1,6}\s+", "", s).strip()
                continue
            if DIRECTION.match(s):
                directions.append({"after_paragraph": len(paragraphs) - 1, "text": s})
                continue
            for d in INLINE_DIRECTION.findall(s):
                directions.append({"after_paragraph": len(paragraphs), "text": d})
            s = INLINE_DIRECTION.sub("", s)
            keep.append(strip_md(s) if is_md else s)
        text = " ".join(x for x in keep if x).strip()
        text = re.sub(r"\s+", " ", text)
        if text:
            paragraphs.append({"index": len(paragraphs), "heading": heading, "text": text})
            heading = None
    sents = []
    for p in paragraphs:
        for s in sentences(p["text"]):
            sents.append({"index": len(sents), "paragraph": p["index"], "text": s})
    narration = "\n\n".join(p["text"] for p in paragraphs)
    words = len(narration.split())
    print(json.dumps({
        "source": path.name, "text": narration, "paragraphs": paragraphs, "sentences": sents,
        "directions": directions, "entities": entities(narration),
        "stats": {"words": words, "sentences": len(sents), "paragraphs": len(paragraphs),
                  "questions": sum(s["text"].endswith("?") for s in sents),
                  "exclamations": sum(s["text"].endswith("!") for s in sents)},
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
