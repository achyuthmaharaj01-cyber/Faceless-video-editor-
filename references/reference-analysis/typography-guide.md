# Typography guide

## Observed

- **Labels**: lowercase, clean grotesque sans (Arial/Helvetica-like), white with a soft dark shadow, no box,
  placed beside the subject (v8 00:00.57 "steve ballmer"; v2 01:16 "salvator mundi"; v5 02:38 "775 rooms").
- **Money**: green (sometimes with a green glow/particles), or white on a dark pill (price tags).
- **Emphasis words**: red, often heavier (v7 06:16 "16 cylinder engine", v7 06:19 "wind up toy" rotated).
- **Quotes / subtitles**: lowercase, lower centre, word-synced; sometimes white on a black bar (v7 06:04).
- **Text-only beats**: small lowercase white (or red) text centred on black (v7 05:24 "but nowadays").
- **Documents**: serif headlines (newspaper feel) with a red or yellow highlighter on the key phrase.
- **Handwritten asides**: marker/handwriting font, slight rotation, with a hand-drawn arrow (v1 02:22).

## fvs type system (all fonts local, SIL OFL)

| Role | Font | Default size (1080p) | Class |
|---|---|---|---|
| Label | Inter 700 | 64 px (46–96) | `.label` (`lower`) |
| Money label / stat | Inter 800 / Anton | 64 / 210 px | `.label.money`, `.stat.money` |
| Hero number, kinetic words | Anton (condensed display) | 150–330 px | `.stat`, `.kt` |
| Stat unit line | Inter 700 lowercase | 54 px | `.stat-sub` |
| Document headline | Playfair Display 700 | 64 px | `.doc h2` |
| Handwritten | Caveat 700 | 72 px | `.hand` |
| Captions | Inter 700 lowercase | 58 px | `.cap-strip` |

Rules:
1. Lowercase for labels, captions and units; UPPERCASE only for kinetic display words.
2. ≤ 5 words per label; ≤ 8 words per caption line.
3. Keep text inside the title-safe area (3% margin); `fvs qc` fails text cut off by the frame edge and overlaps.
4. Tabular figures for counters (no jitter).
5. Contrast: white text gets the shadow token `--label-shadow`; on light backgrounds use `style: dark`.
