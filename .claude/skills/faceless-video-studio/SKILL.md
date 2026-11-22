---
name: faceless-video-studio
description: Produce a professionally edited faceless YouTube video from a written script and its voiceover, in the reference (Jack Pockets-style) editing language. Builds a HyperFrames composition, reviews it in VideoHub with the user, revises from their notes, renders with HyperFrames, runs quality control and delivers to Google Drive. Use for every new video project, and whenever the user wants to make, edit, revise, review, render or deliver a faceless/explainer/documentary video from a script + voiceover, mentions faceless-video-studio or fvs, VideoHub notes on such a film, or puts a script and voiceover in Google Drive (YouTube Production/Input) or on disk.
---

# faceless-video-studio

Script + voiceover in → edited, checked, delivered video out. **HyperFrames** composes and renders (the only video
engine). **VideoHub** is where the user reviews before anything final is rendered. You are the director: the `fvs`
tools measure, align, build, check, render and deliver; you make every creative decision with the style guide, and
you look at the frames yourself before the user does.

One new session = one video project. Work through the steps in order; each step's state is saved in the project
(`.fvs/state.json`), so a later session can resume with `fvs status <project>`.

---

## 0. Start of every session

**Find the studio** (the `Faceless-video-editor-` repository, containing `bin/fvs.mjs`), first match wins:
1. the current folder or a parent of it;
2. `$FVS_HOME`;
3. the path written in an installed copy of this skill (see "Studio folder" at the end);
4. `%USERPROFILE%\Faceless-video-editor-` (Windows laptop) or `/home/user/Faceless-video-editor-` (cloud session).

Below, `fvs` means `node <studio>/bin/fvs.mjs`. It loads `<studio>/.env` automatically (keys, settings).

**Where am I?** Decide once and say it in one line to the user:

| | Laptop (Windows, user's machine) | Cloud session (Claude Code on the web / phone) |
|---|---|---|
| VideoHub review | yes (local app) | no: review with frames/clips in the chat |
| Drive API (`drive-pull/push/upload`, any size) | yes (token in `%USERPROFILE%\.config\faceless-video-studio\`) | no token: use the Drive connector (≤ ~3 MB per file) |
| Final video delivery | `fvs drive-push` to Drive | send the MP4 in the chat; text deliverables via the connector |
| Wikimedia sourcing | works | blocked (HTTP 429) |
| Render speed (measured) | measure: `npx hyperframes benchmark` | ≈ 2.6 × real time (44 s film in 116 s, 4 vCPU) |

```bash
fvs doctor
```
Fix anything missing before starting; it prints the exact command. Ask before installing system software. In a
fresh cloud container the environment's setup script has already run `npm install`, `pip install` and Agent-Reach.

If the user wants the latest studio version: `git -C <studio> pull --ff-only` (only when they ask, or when `fvs`
reports a missing command that exists in the docs).

## 1. Inputs (ask only for what is missing)

Needed: the **script** (.docx/.txt/.md, or a Google Doc) and the **voiceover** (.mp3/.wav/.m4a/.aac).
Optional: title, format (`long` 1920×1080 default, `short` 1080×1920), a licensed music track, Pexels/Pixabay keys.

- **Google Drive** (`YouTube Production/Input/`), on the laptop:
  ```bash
  fvs drive-pull <studio>/inputs/<short-name>
  ```
  downloads the newest script + voiceover (Google Docs are exported as text). In a cloud session use the Drive
  connector (`search_files` in the Input folder → `download_file_content`) for files under ~3 MB; a larger
  voiceover must come from the laptop or be attached in the chat.
- **Files on disk**: use the paths the user gives.
- Never ask for anything you can read from the files (duration, title heading, sample rate).

## 2. Create the project and analyse

```bash
fvs new "<Title>" --script <script> --voice <voiceover> [--format short] [--workspace <VideoHub films folder>]
fvs analyse <project>
```
- Projects go in a folder VideoHub watches: `FVS_WORKSPACE` in `.env`, or ask VideoHub (`hub_workspace`) for its
  films folder. The voiceover and script are copied untouched into `input/` (read-only).
- `analyse` aligns every script word to the voiceover (faster-whisper `small.en`; the first run downloads ≈ 500 MB).
  Read `mismatchesNeedingReview` in its output. Show the user every skipped sentence and every **number that
  differs** between script and voiceover. Never edit, shorten or reorder narration; the voiceover is the clock.

## 3. Storyboard — the creative step

```bash
fvs storyboard-draft <project>
```
The draft is mechanical. **Read first, every project:**
`<studio>/references/reference-analysis/master-style-guide.md`, then for the scenes you are designing:
`visual-storytelling-guide.md`, `motion-graphics-guide.md`, `transitions-guide.md`, `typography-guide.md`,
`colour-and-composition-guide.md`, `sound-design-guide.md`, and `<studio>/docs/storyboard-schema.md` (every
visual, layer and transition with its options). Also read `<studio>/learning/style-amendments.md` (accepted ones
apply).

Rewrite every scene of `storyboard/storyboard.json`:
- what the narration says → the most concrete **honest** picture → at most one explanatory layer (label, arrow,
  price tag, handwritten note, meter, captions) → camera move → transition → sounds;
- time overlays to spoken words with `"@word"` (or `"@two words"`, `"@word+0.2"`);
- pacing from the guide: a new picture about every 1.2–2.5 s of narration, hard cuts on words, motion
  transitions only at segment changes, holds > 5 s only for reveals and endings;
- vary formats (photo, inset, map, stat, kinetic, document, ranking, cutout, collage, comparison, timeline,
  blocks3d); never 2+ consecutive scenes with the same type and camera move;
- numbers become physical (counter, meter, 3D blocks); **no on-screen figure the script does not state**
  (derived percentages included); no look-alike portraits; no logos/brands without a licence;
- a scene the components cannot express → a hand-made HyperFrames sub-composition (`visual.type: "custom"`).

```bash
fvs storyboard-check <project>      # must pass: contiguous, whole voiceover, every sentence, script order
```
Show the user a short plan (scene count, formats, anything unusual) only if they asked to see it first.

## 4. Media — specific, licensed, verified, registered

1. **Research** the actual subjects (the real ship, person, building, event, date) with Agent-Reach:
   ```bash
   agent-reach web search "<subject> photograph public domain"
   agent-reach read "<url>"
   ```
   It finds and reads pages; it does **not** prove a licence.
2. **Candidates you can verify**, and **look at them** before choosing:
   ```bash
   fvs asset-search --query "<specific subject>" --sheet <scratch>/c.jpg --save <scratch>/c.json --brief
   ```
   Open the sheet image. Choose by relevance, then resolution (≥ 1600 px wide for full-frame use). Put the chosen
   candidate object into the scene's `assets[].pick`.
3. Download, verify and register:
   ```bash
   fvs assets <project>
   ```
Licence rules (`<studio>/docs/asset-licensing.md`): only commercial-use + modifiable licences (CC0, public
domain, US-federal, CC BY, Pexels, Pixabay); CC BY-SA, NC, ND and unknown are refused; everything goes into
`assets/asset-licence-register.csv`. Never: pirated media, YouTube/platform rips, paywall/DRM bypass, watermark
removal. Agent-Reach's YouTube channel is only for metadata/subtitles (fact-checking). Paid stock or paid AI
generation only after the user approves the cost. Nothing licensed fits → design an original visual.

**Music:** a licensed track from the user (register it; `storyboard.music.track`). The procedural bed is a
placeholder and QC warns about it — tell the user.

## 5. Build, then look at it yourself

```bash
fvs build <project> --reason "<what changed>"
npx --prefix <studio> hyperframes lint <project>               # 0 errors required
npx --prefix <studio> hyperframes snapshot <project> --at <one time per scene, inside each scene> --no-end
fvs qc <project>                                               # pre-render: layout, figures, licences, story
```
Open the snapshot contact sheets and **look at every scene**. Lint and QC cannot see: empty or blank scenes,
unreadable text, labels on the wrong subject, cropped 3D/maps, irrelevant images, awkward framing. Fix, rebuild,
look again. Every build keeps the previous version in `versions/`. After structural changes, `fvs verify-preview
<project>` checks that VideoHub shows exactly what HyperFrames renders.

## 6. Review — mandatory before the final render

**Laptop (VideoHub).** Use the MCP tools if loaded (`hub_live`, `hub_notes`, `hub_note_update`, `hub_project`,
`hub_render`, `hub_job`, `hub_workspace`), otherwise `node <VideoHub>/server/cli.js <tool> '<json>'`
(`VIDEOHUB_DIR` in `.env`). Never invent tool names; never expose VideoHub's port.
1. `hub_live({project})` → tell the user to watch, scrub, draw notes on frames and press **Send to Claude**.
   **Stop and wait.**
2. On notes: `hub_notes({project})`, then `fvs notes <project>` (real frame pictures, the storyboard scene and
   the narration for each note). Open the pictures.
3. Fix in the storyboard (preferred) or in `compositions/sNN.html`, then `fvs build` (or `fvs preview` after a
   hand edit of `index.html`). VideoHub reloads by itself.
4. **Verify each fix** with a snapshot at the note's time — only then `hub_note_update({project, id,
   status:"fixed", reply:"<one sentence>"})`. Never mark a note fixed that you did not verify.
5. Repeat until the user approves in their own words.

**Cloud session (no VideoHub).** Send the scene contact sheets (and, on request, a short draft clip:
`fvs render <project> --draft --start A --end B`) in the chat; the user replies with timestamped notes; map each
to its scene with `audio/words.json` and the storyboard; revise; send updated frames.

## 7. Approval → final render → QC

Only after the user explicitly approves (their words, in this conversation):
```bash
fvs approve <project> --by "<user> in chat (<date>): '<their words>'"
fvs render <project>        # HyperFrames 1080p30 H.264/AAC; refuses if the composition changed since approval
fvs qc <project>            # reports/quality-control-report.md
```
- Never record an approval the user did not give, and never render final without one.
- Before rendering, fact-check on-screen names, dates and figures with Agent-Reach; report any claim in the
  script that sources contradict (do not change the narration).
- Loudness: the mix gets one static gain toward −14 LUFS; if the narration's peaks prevent it, QC warns. A
  limiter only with the user's approval: `storyboard.audio.limiter: true` + `limiterApprovedBy`, then rebuild.
- QC failed → fix, show the change, get approval again (approval is tied to the exact composition).
- Report QC honestly: failed / warnings / manual review. Read `reports/qc-frames/begin|middle|end.jpg`.

## 8. Deliver

```bash
fvs deliver <project>                 # deliverables/: MP4, QC report, attributions, licence register, storyboard
fvs drive-push <project>              # laptop: everything → YouTube Production/Completed Videos/<title>/
fvs drive-upload <file> --sub "<title>"   # laptop: one file of any size (resumable 8 MiB chunks)
```
Cloud session: send the MP4 in the chat and upload the text deliverables with the Drive connector into
`Completed Videos/<title>/`. Give the user `attributions.txt` (CC BY credits for the video description).
After an upload, confirm the size from Drive's metadata.

## 9. Learn

Append what the user corrected to `<studio>/learning/production-log.md`. A correction they would want in every
video → propose it in `<studio>/learning/style-amendments.md` and ask before changing anything in `references/`.
If you changed studio code or docs during the project, run `npm test` in the studio and commit on a branch only
if the user asks.

---

## Hard rules

1. The voiceover is never edited, sped up, shortened or reordered; video length = voiceover length.
2. No final render before the user's explicit approval; no approval recorded on their behalf.
3. Look at the frames yourself before showing the user; verify every fix before marking it fixed.
4. Only verified, registered, commercially usable media; nothing pirated, ripped or watermark-stripped.
5. No unsupported claims on screen; no fake portraits or documents presented as real.
6. Secrets stay in `.env` / `~/.config/faceless-video-studio/`; never in the repo, never asked for in the chat.
7. Ask before anything paid (state what, why, cost, free alternative).
8. Report failures, skipped steps and warnings plainly.

## Quick reference

| Need | Command / file |
|---|---|
| Project state, history | `fvs status <project>` |
| All commands | `fvs help` |
| Storyboard options | `<studio>/docs/storyboard-schema.md` |
| Problems | `<studio>/docs/troubleshooting.md` |
| Worked example | `<studio>/examples/box-that-changed-the-world/` |
| Drive setup | `<studio>/docs/google-drive.md` |
| Install this skill for sessions outside the studio folder | `fvs install-skill` |
