# Master style guide

The permanent reference for every production. It describes **how** the reference channel edits (pacing,
visual grammar, motion, sound), measured on eight reference videos (2 h 00 m, 3,074 shots) and read from their
contact sheets. The user's script decides **what** a video shows.

Companion guides: [editing rules](editing-rules.md) · [visual storytelling](visual-storytelling-guide.md) ·
[motion graphics](motion-graphics-guide.md) · [transitions](transitions-guide.md) · [typography](typography-guide.md) ·
[colour & composition](colour-and-composition-guide.md) · [sound design](sound-design-guide.md) ·
[timestamped observations](timestamped-observations.md) · [video index](reference-video-index.md)

## Never copy

Learn the principles; build original scenes. Never reuse the reference videos' footage, graphics, scripts, exact
shot sequences, recurring set pieces in their exact form (for example their specific tier-board artwork) or
their unique compositions. The fvs components are original implementations of *generic* devices: labels,
arrows, maps, ranking boards, counters, documents, price tags.

## The style in one paragraph

Fast, conversational, information-dense. A new picture roughly every **1.7 s** (median; 21–33 cuts/min), almost
always a **hard cut on a word**. The base layer is real imagery (photos, footage, screenshots); the explanation
sits on top as **minimal, lowercase labels, red arrows, green money figures, handwritten notes and price tags**
placed beside the subject. A recurring **"home base" graphic** (ranking board / map) re-orients the viewer between
segments. Abstract ideas become **objects**: numbers grow into 3D blocks or stacks, comparisons become split
screens, quotes become highlighted documents. Humour comes from **timing**: text-only beats, a held reaction,
a deadpan caption. Sound is busy but tidy: a music bed far below the voice, a pop, whoosh or ding on most visual
events, impacts on reveals.

## Measured baseline (all 8 videos)

| Metric | Value | Rule it gives |
|---|---|---|
| Median shot | **1.70 s** (10th–90th pct 0.63–4.0 s) | Plan ~1 visual change per 1.2–2.5 s of narration; holds over 5 s are rare (6%) and must be earned |
| Cuts per minute | 20.9–32.7 (videos 4 → 3) | Long-form explainer pacing: 22–28 cuts/min; list/tier segments run faster (30+) |
| Shots < 1 s | 20% | Use quick inserts for punchlines and enumerations |
| Cuts on a word boundary (±0.25 s) | 75–94% (median ≈ 80%) | **Cut on words**, never mid-word |
| Cuts near a sentence end (±0.4 s) | 14–32% | Most cuts happen *inside* sentences, on the key noun |
| Cuts per spoken sentence | 1.6–3.4 | One sentence usually carries 2–3 pictures |
| Soft/dissolve transitions | 1–2% of changes | Hard cuts and fast motion transitions only; no slow dissolves |
| Camera motion (per shot) | static 40–64%, push-in 10–22%, pull-out 5–13%, pans 2–8% | Static or a slow push is the default; pans are accents |
| Narration pace | 154–205 words/min (typ. 160–175) | Fast narration: visuals must be readable in < 1 s |
| Loudness | −13.0 to −15.3 LUFS integrated, TP ≈ −0.1 to −0.7 dBTP | Deliver near −14 LUFS; keep TP ≤ −1 dBTP (safer than the references) |
| Cuts with an audio transient within 100 ms | 20–32% | SFX on a quarter of the cuts, not on every one |
| Level in speech vs non-speech seconds | ≈ 5–15 dB lower without speech | Music bed sits well under the voice and stays present in pauses |

Per-video numbers: [reference-video-index.md](reference-video-index.md).

## Core rules (apply all of them)

1. **The voiceover is the clock.** Visual changes land on the spoken word they illustrate (`"@word"` timing in the
   storyboard). Never re-time, shorten or reorder narration.
2. **One idea per picture, one picture per idea-change.** When the narration moves to a new noun (person, place,
   object, number), the picture changes. When it elaborates the same idea, keep the picture and add a layer
   (label, arrow, counter) instead of cutting.
3. **Real first, then explain on top.** Prefer a real photo/clip of the subject + a label/arrow over an abstract
   graphic. Use graphics when there is no picture (numbers, processes, comparisons, places).
4. **Make numbers physical.** Every important figure becomes the biggest thing on screen (counter, 3D blocks,
   meter, money stack), timed to the spoken figure. Never show a number the narration does not state.
5. **Re-orient with a home base.** Long list-style videos return to a recurring map / ranking board between
   items; build one per film (original artwork) when the script is a list.
6. **Vary formats.** Never more than two consecutive scenes of the same visual type with the same camera move.
   Alternate photo → graphic → photo → text beat.
7. **Lowercase, minimal, beside the subject.** Labels are short lowercase phrases placed next to what they name,
   not boxed lower-thirds (see [typography](typography-guide.md)).
8. **Red points, green pays.** Red = attention (arrows, highlights, warnings); green = money; white = neutral
   information (see [colour](colour-and-composition-guide.md)).
9. **Timing is the joke.** Deadpan text-only beats on black, a 0.5–1 s hold on a reaction, a handwritten aside.
   Never explain the joke on screen.
10. **Sound every event, quietly.** Pops on labels, whooshes on motion transitions, a ding/cash on money, an
    impact on reveals; music bed ducked under the narration (see [sound](sound-design-guide.md)).
11. **Honest visuals.** No fake portraits of real people, no invented documents presented as real, no logos or
    third-party footage without a licence. Pixelate or omit what cannot be licensed.
12. **Vignette and depth.** Photos get a soft vignette and a slow move; insets and cutouts get a drop shadow.

## Decision table: what to show

| The narration is… | Default visual (fvs) | Notes |
|---|---|---|
| Introducing a person | `photo` of the person (licensed) + `label` name at `@Surname`; or `cutout` on studio | No licensed portrait → show their world (company, place, object), never a look-alike |
| Introducing a place | `map` zoom + pin at `@Place`, then a `photo` with a pin `label` | Location labels carry the pin glyph (`style: pin`) |
| A date / era | `kinetic` year, or `label` year top-left on an archival-looking photo (B&W grade) | Era shift → B&W grade or `timeline` |
| A price, amount, statistic | `stat` counter (money = green), `meter`, `blocks3d`, or `pricetag` on the object | Count lands on the spoken figure |
| A comparison / before-after | `comparison` split (right side enters on the contrasting word) or a counter that counts *down* | |
| A quote / document / claim | `document` with highlight on the key phrase; `captions` for spoken quotes | Real articles only as licensed screenshots; otherwise neutral original cards |
| A process / journey | `map` with `route`, `timeline`, or a sequence of quick photos | |
| A list item | `ranking` board update, then the item's photos | One board design per film |
| A punchline / aside | `kinetic` text-only beat on black, `hand` annotation, reaction hold | Keep it 0.6–1.5 s |
| Scale / quantity | `blocks3d` (count the objects), money stacks, crowd + count label | 3D only when the count matters |

## Pacing curve

- **Hook (0–20 s):** fastest section (cuts every 0.8–1.5 s), the main promise on screen within 5 s.
- **Body:** 1.5–2.5 s per picture; each new segment starts with a re-orientation (home base / map / title beat).
- **Reveals:** slow down *before* the reveal (a 2–4 s hold or push-in), then hit it with an impact and a hard cut.
- **Ending:** the last line gets a calmer hold (3–5 s) and a pull-out.

## How this guide is used by the pipeline

- `fvs storyboard-draft` produces a mechanical first pass; Claude then rewrites every scene with this guide
  (SKILL.md, step 4) and `fvs storyboard-check` enforces timing, coverage and repetition rules.
- `fvs qc` checks text placement, on-screen figures vs narration, loudness and sync.
- Reusable preferences learned from review feedback are proposed as amendments in `learning/style-amendments.md`
  and only merged here when the user confirms them.
