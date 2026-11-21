# Editing rules

Measured on 3,074 shots (8 videos). Timestamps refer to the reference videos (numbering in
[reference-video-index.md](reference-video-index.md)).

## Shot duration

| Shot length | Share | Use it for |
|---|---|---|
| < 1 s | 20% | enumerations ("a jet, a yacht, a house"), punchline inserts, reaction flashes, list-board updates |
| 1–2 s | ≈ 40% | the default: one noun → one picture |
| 2–3 s | ≈ 18% | a picture with one layer appearing on it (label, arrow, price tag) |
| 3–5 s | ≈ 16% | counters, maps, documents: anything the viewer must read |
| > 5 s | 6% | reveals, emotional beats, the final line; always with motion (push/pull) or appearing layers |

Rules:
1. **Never use a fixed shot length.** Scene length = the narration span of the idea it illustrates.
2. **Readable-time minimum:** text the viewer must read stays ≥ 0.25 s per word (≥ 1 s for a 4-word label).
3. **Static holds over 4 s need a reason** and something that moves (camera push, counter, appearing layer).
4. The fvs storyboard checker warns when scene lengths barely vary (mechanical rhythm) and when one photo
   holds more than 9 s with no layers.

## Where to cut

- 75–94% of cuts land within 0.25 s of a word boundary; only 14–32% near a sentence end → **cut on the key
  word inside the sentence**, typically the noun or number being introduced (`"@word"` in the storyboard).
- Cut slightly *before* the word (≈ 2–3 frames; the draft uses −0.08 s) so the picture is there when the word lands.
- 1.6–3.4 cuts per sentence: a typical sentence carries 2–3 pictures.
- Pauses in the narration (> 0.4 s) are where the editor lets a picture breathe or places a text-only beat.

## Fast vs slow sections (examples)

- Fast: list updates and enumerations (e.g. video 3 runs 32.7 cuts/min overall; its tier segments cut
  every 0.5–1 s). Video 8's opening ranks people in ~1.5 s inserts (00:00–00:20).
- Slow: explanation with a document or a map (video 2 01:28–01:38, the white 3D block and the museum statement
  hold 2–4 s each); story beats with quotes (video 5 03:12–03:22, word-synced quote captions over one speaker shot).
- The fastest and slowest 30 s windows of each video are listed in `video-N-analysis.md`.

## Jump cuts and montage

- Jump cuts within the same clip (same speaker, same angle, time skipped) are common in quote segments: cut
  around the quote, never let the clip run.
- Montage = rapid stills (0.4–0.8 s) on a beat or an enumeration; each still gets a pop or click.

## Narrative moments

| Moment | Editing |
|---|---|
| Hook | fastest pacing, the promise as text or a number within 5 s |
| New segment / list item | home-base graphic (map, ranking board) for 1–2 s, then the item |
| Reveal (price, verdict, twist) | hold or push-in before → hard cut + impact + big figure |
| Quote | jump cuts + word-synced captions, speaker shot or document with highlight |
| Joke | text-only beat on black (0.6–1.2 s) or reaction hold, no SFX or one dry click |
| Ending | slower: 3–5 s holds, pull-out, music resolves |

## Repetition control

- Alternate formats: photo → graphic → photo → text beat. Never > 2 consecutive scenes with the same visual type
  and camera move (the checker warns).
- Reuse an image only as a deliberate callback (e.g. the same archival photo returns as the background of a stat).
- Plain photos should stay below ~75% of scenes (checker warns).
