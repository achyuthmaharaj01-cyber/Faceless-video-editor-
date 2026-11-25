"""Delivery documents for WHITE mode.  Usage: python -I deliver_white.py shots.json project_dir card_sources.json plan_white.py out_dir
Writes SHOTLIST.md, SOURCES.md (every news/filing/post card: outlet, text shown, URL, how verified), LICENSES.csv, CREDITS.txt, THIRD_PARTY.md."""
import sys, os, json, csv, re
D = json.load(open(sys.argv[1])); P = sys.argv[2]; SRC = json.load(open(sys.argv[3])); plan = open(sys.argv[4]).read(); O = sys.argv[5]; os.makedirs(O, exist_ok=True)
fmt = lambda t: f"{int(t // 60)}:{t % 60:05.2f}"
rows = ["| # | time | visual | what is on screen | source | overlays |", "|---|---|---|---|---|---|"]
for i, s in enumerate(D["shots"]):
    p = s["p"]; k = s["scene"]
    what = {"article": lambda: f'{p.get("outlet")}: {p.get("head")}', "post": lambda: f'{p.get("name")}: {p.get("text")}', "filing": lambda: p.get("text"), "bignum": lambda: f'{p.get("prefix","")}{p.get("to")}{p.get("suffix","")} {p.get("sub") or ""}',
            "bars": lambda: " vs ".join(f'{x.get("label","")}={x.get("vlabel", x["value"])}' for x in p["items"]).replace("\n", " "), "calendar": lambda: f'{p.get("month")} {p.get("day")} {p.get("year") or ""}', "timeline": lambda: " > ".join(n["label"] for n in p["nodes"]),
            "statement": lambda: " / ".join(p["lines"]), "quote": lambda: p["text"], "pct": lambda: f'{p["pct"]}%', "price": lambda: f'{p["price"]} {p.get("sub","")}', "list": lambda: " | ".join(x if isinstance(x, str) else x["text"] for x in p["items"]),
            "text": lambda: p["text"], "photo": lambda: f'photo: {p.get("credit", {}).get("title", "")}'}[k]()
    src = (p.get("credit") or {}).get("page", "") if k == "photo" else ""
    ov = ", ".join(f'{o["kind"]}:{(o.get("text") or o.get("price") or "").replace(chr(10), " ")}' for o in s.get("ov", []))
    rows.append(f'| {i} | {fmt(s["ps"])}-{fmt(s["pe"])} | {k} | {str(what)[:110].replace("|", "/")} | {src} | {ov[:70]} |')
open(os.path.join(O, "SHOTLIST.md"), "w").write(f"# Shot list\n\n{len(D['shots'])} shots, {fmt(D['total'])}\n\n" + "\n".join(rows) + "\n")
used = []
for key, m in re.findall(r'(\w+)": dict\(', plan) and []: pass
keys = sorted(set(re.findall(r'AR\(\d+, \d+, "(\w+)"', plan)) | ({"sec"} if re.search(r'\bFI\(', plan) else set()) | ({"post"} if re.search(r'\bPO\(', plan) else set()))
md = ["# Cards shown in the video (news / filing / social)\n", "These are RE-TYPESET in code from the real headline/quote text (outlet name as plain text, no logos, no body copy, no images). They are not screenshots.",
      "Each was found by web search; open the URL to confirm before publishing. `title_status` says how well the wording is confirmed.\n"]
for k in keys:
    c = SRC.get(k, {}); md.append(f"- **{c.get('outlet', k)}** - {c.get('url') or '(page not opened)'}  \n  verification: {c.get('title_status', '')}")
open(os.path.join(O, "SOURCES.md"), "w").write("\n".join(md) + "\n")
used = {os.path.normpath((s["p"]["src"])) for s in D["shots"] if s["scene"] == "photo"}
logf = os.path.join(P, "assets", "LICENSES.csv"); last = {}
for r in csv.DictReader(open(logf)): last[os.path.basename(r["file"]).split(".")[0]] = r
rows2 = []
for s in D["shots"]:
    if s["scene"] != "photo": continue
    c = s["p"].get("credit", {}); rows2.append((os.path.basename(s["p"]["src"]), c))
seen = {}; 
for f, c in rows2: seen.setdefault(c.get("page"), (f, c))
with open(os.path.join(O, "LICENSES.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["file", "title", "author", "license", "source_page"])
    for pg, (f, c) in seen.items(): w.writerow([f, c.get("title"), c.get("author"), c.get("license"), pg])
cred = sorted({f'"{c.get("title")}" by {c.get("author")} ({c.get("license")}) {c.get("page")}' for pg, (f, c) in seen.items() if re.search(r"by", c.get("license", ""), re.I) and not re.search("pd|cc0|pdm", c.get("license", ""), re.I)})
open(os.path.join(O, "CREDITS.txt"), "w").write("Photo credits\n" + "\n".join(cred) + "\n")
open(os.path.join(O, "THIRD_PARTY.md"), "w").write("# Third-party material\n\n- Photos: " + str(len(seen)) + " licensed images (CC BY / CC BY-SA / CC0 / public domain, licence filtered at download); see LICENSES.csv and CREDITS.txt.\n- News, filing and social cards: headline/quote text only, from the sources in SOURCES.md (quotation of real headlines for commentary: your rights decision).\n- No game footage, screenshots, trailers or key art. 2D graphics, SFX and the music bed are generated in code.\n")
print("wrote", O, "photos", len(seen), "credits", len(cred), "card sources", len(keys))
