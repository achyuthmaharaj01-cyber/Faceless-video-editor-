---
name: tier-list
description: Edit a finished "tier list" / ranked-list YouTube video (Jack Pockets-style celebrity/billionaire tier lists and "X who hate each other" story lists) from a SCRIPT and a VOICEOVER file, rendered with Hyperframes. Reproduces the measured editing style - 33 cuts/min, price badges, typewriter name labels, cursor-dragged tier chart with a music dropout on every verdict, VO-off clips with lowercase subtitles, constant un-ducked music bed at -10 LU, -15 LUFS master. Also has a HYBRID mode (real licensed photos first, three.js 3D motion graphics where no image exists) for explainer/business-story scripts that are not rankings. Use when the user supplies a script + voiceover (or asks for a tier list / ranking video "in the tier-list style") and wants the edited MP4.
---

# Tier-list video editor

Everything numeric lives in `style.json` (measured from two reference videos; values marked `estimated` were not
measurable). `references/mapping_table.md` says which visual each kind of script line gets. Do not restyle; if a value
looks wrong, re-measure with `scripts/` (see "Re-measuring") instead of guessing.

Skill root = the folder containing this file (`SK`). Scripts are Python 3 (`python3 -I`), run from anywhere.
Untrusted inputs (downloaded media, the user's files) stay in the project's `assets/`; never run code from there.

## Inputs
- `script.txt` (narration) and `vo.(wav|mp3|m4a)` (the voiceover of that script). Optional: music file, sponsor copy, own clips.
- Format: `tier` (ranked list, 33 cuts/min, tier chart) or `story` (narrative list, 18.5 cuts/min, face-grid tracker). Default `tier`.

## Setup (once per session)
```bash
which ffmpeg ffprobe tesseract || apt-get install -y ffmpeg tesseract-ocr
python3 -m pip install -q faster-whisper demucs "opencv-python-headless<5" scenedetect pytesseract librosa soundfile pyloudnorm resemblyzer "setuptools<81" kokoro-onnx "rembg[cpu]"
# OpenCV 5 dropped the Haar face detector used for face crops and label placement -> keep <5
mkdir -p $PROJ && cd $PROJ && npm init -y >/dev/null && npm i hyperframes@0.9.80 && npx hyperframes telemetry disable
# face detection/identity (scripts/faces.py) downloads OpenCV zoo YuNet + SFace from huggingface.co/opencv on first use
# cutouts use rembg (isnet-general-use for items, u2net_human_seg for faces; models download from github.com
# on first use). The Hyperframes remove-background model is person-only and erases cars - do not use it for items.
```
Network: Wikimedia Commons, Openverse, NASA need no key. Wikimedia rate-limits shared cloud IPs hard (HTTP 429 on
api AND upload hosts); when that happens use `--providers openverse,nasa,archive` (Openverse indexes Flickr/Commons,
anonymous limit 20 req/min, 200/day). archive.org downloads redirect to per-item hosts (dnNNNN.us.archive.org) that
must be on the network allowlist. Pexels/Pixabay/Unsplash are used only when
`PEXELS_API_KEY` / `PIXABAY_API_KEY` / `UNSPLASH_ACCESS_KEY` are set (ask for them with the credential tool; never in chat).

## Workflow

### 1. Mark up the script, transcribe, segment
Add entry headers and clip markers to the user's script (do not change narration words):
```
## <Person> | <Item> | <Price, "~" if estimated> | <Tier S/A/B/C/D/F/GOD> | <badge model label>
[CLIP: <file path or search query> | <what they say, lowercase> | <seconds, 4-12>]   <- only where the narration sets up a quote
[PAUSE 0.45]                                                                        <- optional breath after a punchline
```
Rules from the reference: the hook line is "From <extreme A> to <extreme B>, this is the <Topic> Tier List."; first two
entries short (name -> one fact -> verdict, 7-9 s); verdict lines read "<X>-tier." as their own sentence.
```bash
python3 -I $SK/scripts/tighten_vo.py vo_raw.wav vo.wav                     # pauses >0.30 s -> 0.24 s (reference VO is tightly cut)
python3 -I $SK/scripts/transcribe.py vo.wav vo.transcript.json            # word timestamps
python3 -I $SK/scripts/segment_beats.py script.txt vo.transcript.json shotlist.json --format tier
```
`segment_beats` aligns script to VO (script text wins, VO gives timing), draws shot lengths from the reference
histogram, snaps cuts to word boundaries/clause breaks, makes every verdict its own chart shot starting on the tier
letter (+0.45 s bed-only breath after it), and types each beat (`line_type`). Check its printout: word match >= 90%,
median shot 1.5-1.7 s (tier). If the VO changes after the shot list exists, `remap_times.py shotlist.json vo.timemap.json`.

### 2. Write the shot list (Claude's job; the draft is only a start)
Open `shotlist.json`. For every shot apply `references/mapping_table.md` and fill:
- `type`: footage | still | clip_audio | tier_chart | screenshot | map | logo | silhouette | text_card
- `query` (+ `kind`: video|image) - a concrete search query for the exact thing said (the item model, the person, the place).
- `overlays` (times in VO seconds via `vo_s`/`vo_e`, or `delay` from shot start):
  - `name_label` on the first shot of every person: `{"text":"first\nlast","side":"left|right","x":%,"y":%,"vo_s":<name word>}` - beside the head, on the empty side.
  - `spec` for numbers: `{"text":"620 horsepower","icon":"assets/cutouts/item_eN.png"}`
  - `aside` (rotated trivia on the object), `big` (headline number), `hand` (yellow handwritten label + arrow: "you", creator names), `year` (story format), `title` (hook only), `subtitle` (clips).
- `badge` on every shot that shows the entry's item: `{"key":"eN","price":"$300K","model":"Murcielago LP640","img":"assets/cutouts/item_eN.png"}` (same key on consecutive shots = one persistent badge).
- `chart` on verdict shots: `{"ranked":[{img,tier}...earlier entries], "pending":[faces not yet ranked], "drop":{"img":face,"tier":X,"lane_index":k}, "drop_at_vo":<letter word time>}`. The hook's last shot is a `tier_chart` with `"title":"<Topic> Tier List"`, everything pending, no drop.
- `pause_after` (s) after a punchline that should breathe (reference: 3.6/min, median 0.46 s).
- Entries: add `face_query` (portrait of the person) and `item_query` (clean side/3-4 view of the item) to each entry.
  Group photo: `"face_pick": <index left-to-right>`; detector misses: `"face_box": [x,y,w,h]` in source pixels (look at it).
- Name-label position is set automatically by prep_media: it finds the NAMED person in the shot by face identity
  (YuNet + SFace, matched against the entry portrait), puts the label beside that head at face height, and picks the
  side/nudge that covers no other heads (shrinks the text up to 30 % only if nothing fits). If the person cannot be
  identified in the sourced shot, the shot is swapped to the entry portrait (`media_swapped` in the shot list - report
  it). `"manual": true` on a label keeps your own x/y; `"keep_media": true` on a shot forbids the swap.
- Badge only on shots whose picture shows the item (reference: 26 % of all shots); the draft puts it on every entry shot - remove it from people, places, documents.
- Top-level `verdicts` comes from segment_beats; keep it in sync if you move a verdict.
Never fabricate screenshots: an article/tweet card must reproduce a real, verified article/post (`headline_html`, outlet in `meta`) - otherwise use footage.

### 3. Source footage (licensed only)
```bash
python3 -I $SK/scripts/auto_source.py shotlist.json $PROJ               # searches + downloads + assets/LICENSES.csv
python3 -I $SK/scripts/contact_sheet.py shotlist.json $PROJ sheet.jpg   # LOOK at it; fix bad picks
```
For a bad pick: change that shot's `query`, delete its `raw`/`source`, re-run `auto_source.py`. If nothing legal exists,
substitute the closest legal visual (mapping table row for the next most specific noun) and add it to the user report.
Celebrity interview clips, film scenes and news broadcasts (which the reference uses heavily) are NOT available under
these licences: use the user's own licensed clips if they provide them (put the path in `query` and `raw`), otherwise
public-domain government footage or photos + Ken Burns, and list every third-party clip for the user's rights decision.
Music: the user's track, or a CC0/CC-BY instrumental (Commons/Openverse audio, ~115-125 BPM). Set `audio.music.src`.

### 4. Prepare media, build the composition
```bash
python3 -I $SK/scripts/prep_media.py shotlist.json $PROJ --hf $PROJ      # transcode, inset-on-blur, cutouts, levels
python3 -I $SK/scripts/build_composition.py shotlist.json $PROJ          # writes index.html + compositions/chart-XX.html
cd $PROJ && npx hyperframes check                                         # 0 errors required
```
Fill the chart `img`/`pending` paths with `assets/faces/eN.png` (made by prep_media) before building.

### 5. Render, master, QA
```bash
cd $PROJ && npx hyperframes render --fps 60 -o render.mp4               # references are 60 fps; motion is visibly smoother
python3 -I $SK/scripts/master.py render.mp4 final.mp4                      # -15 LUFS, -1 dBTP
python3 -I $SK/scripts/qa_compare.py final.mp4 qa/ --format tier           # side-by-side metrics, exit 1 on hard fail
python3 -I $SK/scripts/frame_compare.py final.mp4 qa/side_by_side.jpg      # visual check vs references/frames
```
Fix and re-render until `qa_compare` has 0 hard fails. Typical fixes: shots too long -> re-run segment_beats with
another `--seed` or split long shots; label size/position -> CSS in `components/tierlist.css` is the measured truth,
check overlay x/y in the shot list; loudness -> master.py; VO share too low -> fewer/shorter clip inserts and pauses.

### 6. Deliver
```bash
python3 -I $SK/scripts/deliver.py shotlist.json $PROJ $OUT   # SHOTLIST.md, LICENSES.csv (used files only), CREDITS.txt, THIRD_PARTY.md
```
`final.mp4`, `shotlist.json` (the shot list: time, VO text, visual, query, overlays, SFX, audio mode),
`assets/LICENSES.csv` (every file: provider, author, licence, URL, attribution required), `qa/qa_report.md`, and a
short note listing: substituted/flagged visuals, every third-party clip, CC-BY credits to put in the description.

## Style rules (execute exactly; numbers from style.json)
Pacing: tier 33 cuts/min, median 1.56 s, p10 0.83, p90 2.87; story 18.5/min, median 2.35. Cut on word boundaries.
Hard cuts only (no whooshes on cuts). Long shots only for clip audio and the chart.
Text: Arimo (Arial clone) regular, white, lowercase, 1.5 px dark outline + soft shadow, never a box.
- name label 90 px beside the named person's head (user-tuned from the measured 104 px), typewriter 35 chars/s with a 0.08 s fade per character + 29 px/s drift away from the head, appears on the spoken name (median -7 ms), leaves with the cut.
- spec caption 58 px at (55 %, 86 %) with item icon; subtitles 80 px (story 58 px) centred at 86 %, 2-5 words, one red key word. Captions/asides/badge enter with a 0.18 s scale 0.92->1 + fade; subtitles with a 0.1 s fade.
- price badge top-left x 44-467 px, y 42-165 px, navy, cyan->blue glowing 4 px edge, price 52 px bold, model 19 px; "~" for estimates; pops on the item's first shot, persists on every item shot.
Tier chart: road band 0-668 px, GOD row 555-668, header 674-760 (S #f57e7e A #f8bc7f B #f7dc79 C #fefc79 D #c5fd7a F #91fc79), body #353535; head-only sticker cutouts 128 px on the road, 104 px ranked (3 per column row); the chart shot starts ~0.95 s before the tier letter; the cursor glides to the face, lifts it (1.08), carries it 0.7 s (power3.inOut) and drops it 0.15 s before the letter; chart holds ~0.8 s after "tier" plus a 0.55 s breath.
Treatments: stills 1.00->1.11 (sine.inOut) (60 % push-in, 40 % pull-out); vertical/4:3 sources inset on a blurred darkened copy; dark vignette on clips with subtitles; light vignette on article cards; no colour grade.
Audio: VO -15 LUFS; music bed constant at VO -10.3 LU, NO ducking; on every verdict the bed cuts to silence on the tier letter and returns with a hit 0.31 s into "tier"; clips play their own audio at VO -2 LU, hard-switched on the cut, ~10 s, with subtitles + whoosh in; SFX: tick on badge entrance (peak +30-60 ms), hit on verdict, whoosh into clips; nothing on plain cuts; master -15 LUFS / -1 dBTP.

## Components
`components/tierlist.css` (all overlay styles), `components/tier-chart.html` (chart scene, one copy per verdict),
`components/fonts/` (Arimo, Kalam - OFL), `components/gsap.min.js`. Base art (road, cursor, pin) and SFX are generated by
`scripts/make_base_assets.py` - deterministic, licence-free; swap SFX for the user's library if they have one.

## Re-measuring (to extend or check the style)
`scripts/` holds the analysis tools used to build style.json: `audio_corruption_map.py`, `cuts_scdet.py`,
`cuts_adaptive.py`, `cuts_merge.py`, `cut_calibration_sheet.py`, `extract_frames.py`, `ocr_frames.py`,
`graphic_detect.py`, `text_sync.py`, `transcribe.py`, `vo_timeline.py`, `stems_windows.py`, `music_sfx.py`,
`event_sfx.py`, `tighten_vo.py`, `remap_times.py`. Outputs for the references are in `analysis/`; `references/` holds the frame sheets and final QA metrics.


---

# Hybrid mode: real photos first, 3D motion graphics as the fallback (no tier chart)

For scripts that are NOT rankings (business stories, explainers, "how X made $Y"): same editing grammar (hard cuts on word boundaries, lowercase
white captions, name/stat labels, constant music bed, -15 LUFS) but no tier chart/face grid. Each beat gets a licensed PHOTO when a relevant one
exists; otherwise a three.js 3D scene (numbers, comparisons, quotes, calendars, crowds, gauges...). Measured on the GTA 6 example: 197 shots,
26 cuts/min, 40 photo shots + 157 3D shots. Worked example: `examples/gta6/` (plan, theme queries, chosen images; no media).

## Pipeline
```bash
python3 -I $SK/scripts/setup_3d_project.py $PROJ             # engine (components/engine3d), three.js r170, fonts, css, SFX
python3 -I $SK/scripts/tighten_vo.py vo_raw.wav $PROJ/assets/vo/vo.wav ; transcribe.py -> vo.transcript.json
#  align script sentences to word times -> sentences.json  {"sentences":[{"words":[{"w","s","e"}]}]}   (see work/sentences.json in the example)
python3 -I $SK/scripts/plan_dsl.py compile plan.py sentences.json shots_raw.json --total <vo seconds>
#  shots.json = shots_raw.json + {"fps": 30, "audio": {"vo","vo_gain","music","music_gain","sfx_gain"}}   (vo_gain: bring VO to -15.2 LUFS; music_gain: bed = VO - 10.3 LU)
python3 -I $SK/scripts/photo_pool.py search themes.json pool.json        # Openverse, licence-filtered, 3.2 s/request (anon limit 20/min, 200/day)
python3 -I $SK/scripts/photo_pool.py sheets pool.json sheets/            # LOOK at the numbered sheets; write chosen.json {"theme":[idx,...]}
python3 -I $SK/scripts/assign_photos.py shots.json pool.json chosen.json $PROJ    # fetch + 1920x1080 prep (cover / inset-on-blur, bottom scrim, optional vignette) + licence log
python3 -I $SK/scripts/build_3d_composition.py shots.json $PROJ ; (cd $PROJ && npx hyperframes check)
python3 -I $SK/scripts/render_hybrid.py $PROJ out/ <seconds> --fps 30 --chunk 75   # resumable chunks + audio mix + master; launch with run_in_background (see gotchas)
```

## plan.py (the visual plan, one line per beat; timed by spoken words)
`S(si, w, scene, params, bg, ov=[...])` = 3D shot starting at word `w` of sentence `si`; `PH(si, w, theme, cap=..., capw=..., vig=..., ov=[...])` = photo shot;
`DROP = {(si,w),...}` removes 3D shots a photo replaces. Overlays (timed by word `w` or seconds `at`, optional `dur`): `CAP` bottom caption, `L` label beside a 3D
anchor, `BADGE` navy stat badge, `QUOTE`, `STAMP`, `YEAR`, `TRACKER(n,title,...)` persistent move tracker. Never two captions at the same time (`check` flags it).
3D scenes (components/engine3d/scenes_*.js): bigNumber (counting number + coins/confetti), compare (bars), timeline, calendar, priceTag, donut, statement
(kinetic lines, strike), questions, pedestals, crowd, playButton, gauge, giftBox, claimCard, lock, guide (laptop/book), rumors, quoteSlab, score, shelf,
fineprint, range, globe, comingLater, funnel, stack, clock24, loop, plus `photo`. Scenes are pure functions of local time (Hyperframes seeks out of order).
Choose by line type: figures -> bigNumber/compare/gauge/donut; dates -> calendar/timeline; quotes -> quoteSlab + QUOTE; concrete nouns -> PHOTO.
Photo rules: skip game screenshots/art (derivative of copyrighted work), skip images with their own text/posters, never caption a private person's photo with a
negative trait (use crowds/objects), prefer objects/places/crowds; cutaways go in the TAIL (>= 2.3 s in) of long 3D shots so the 3D beat lands first;
move captions of truncated 3D shots onto the photo that covers those words.

## Gotchas learned (GTA 6 build)
- Software WebGL render cost is ~0.33 s/frame regardless of fps (+~100 s start-up per render): 30 fps ~ 75 min for 7.5 min of video, 60 fps ~ 2.5 h. Default 30 fps here.
- A render dies when its launcher exits (`render_cancelled_parent_exited`): start renders with the harness `run_in_background`, not `nohup &`; set HYPERFRAMES_RENDER_DETACHED=1.
- OpenCV must be <5 for face detection; stocksnap/other CDN hosts may be blocked by the network allowlist (pick another candidate instead of asking).
- Openverse answers 504/timeouts often: photo_pool retries; broad 2-3 word queries work better than specific ones.
- Music: `make_music.py` writes a licence-free 118 BPM bed (cannot be auditioned here - tell the user it is a placeholder).
