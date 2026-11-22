# Using the skill

## Every new video = a new Claude Code session

1. Put the script + voiceover in Drive `YouTube Production/Input/` (or have them on the laptop).
2. Laptop: open Claude Code in the studio folder (`C:\Users\achyu\Faceless-video-editor-`), or anywhere after
   `node bin/fvs.mjs install-skill`. Phone: start a Claude Code session on the repository.
3. Say: *"New video: <title>. Use the faceless-video-studio skill with the files in my Drive Input folder"*
   (or give the file paths). Claude follows `.claude/skills/faceless-video-studio/SKILL.md` step by step.
4. Review in VideoHub (laptop) or in the chat (phone), approve in your own words, receive the video in
   `Completed Videos/<title>/`.
5. To continue an unfinished project in a later session: *"Continue the <title> video"* — Claude runs
   `fvs status <project>` and resumes where it stopped.

## From the phone (Claude app → Claude Code → this repository)

1. Put the script (.docx/.txt/.md) and voiceover (.mp3/.wav/.m4a) in Drive `YouTube Production/Input/`.
2. Start a session on the repository and say: *"Make the video from my Drive input folder."* (or run `/faceless-video-studio`).
3. Claude finds the newest pair, creates the project, aligns the narration, writes the storyboard with the style
   guide, gathers licensed media, builds the HyperFrames composition and checks it.
4. Review: Claude sends scene frames to the chat (or, at the desk, opens VideoHub). Reply with timestamped notes.
5. Approve explicitly ("approved — render it"). Claude renders with HyperFrames, runs QC and reports.
6. Delivery to `Completed Videos/<title>/` (Drive API) with the QC report and the credits text for the description.

## At the desk (VideoHub)

Same conversation; when the preview is ready Claude calls `hub_live` and stops. Watch, draw on frames, write notes,
press **Send to Claude**. Claude fixes, VideoHub reloads by itself, **Check fixes** walks you through each change.

## Commands (for running steps by hand)

```
fvs new "<name>" --script s.docx --voice vo.mp3 [--format short]
fvs analyse <project>
fvs storyboard-draft <project>      # then refine storyboard/storyboard.json
fvs storyboard-check <project>
fvs asset-search --query "…" --sheet c.jpg --brief
fvs assets <project>
fvs build <project> --reason "…"
fvs verify-preview <project>
fvs qc <project>
fvs notes <project>
fvs approve <project> --by "<you>"
fvs render <project>
fvs deliver <project>
fvs drive-push <project>
```
(`fvs` = `node bin/fvs.mjs`; `fvs help` lists everything.)

Short-form: `--format short` creates a 1080×1920 project; storyboard positions are fractions of the frame, but
compose the scenes for vertical rather than reusing a long-form storyboard.
