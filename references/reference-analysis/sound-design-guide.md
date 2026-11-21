# Sound design guide

## Measured

| | Value |
|---|---|
| Integrated loudness | −13.0 to −15.3 LUFS (all 8 videos) |
| True peak | −0.0 to −0.7 dBTP (the references run hot; fvs keeps ≤ −1 dBTP) |
| Loudness range | 2–5 LU (dense, controlled) |
| Transient onsets | ≈ 60–75 per minute |
| Cuts with a transient within 100 ms | 20–32% |
| Level without speech vs with speech | ≈ 5–15 dB lower (music bed audible in pauses, far below the voice) |

## Rules

1. **Narration first.** The voiceover is never edited or processed without approval; music is ducked under it
   (sidechain keyed on the voice, ≈ 10–14 dB reduction), and comes back up in pauses.
2. **One sound per visual event, at a low level:**

   | Event | Sound (fvs cue) | Level |
   |---|---|---|
   | label / pin / item lands | `pop` | −9 dB |
   | word-by-word kinetic text | `click` | −6 dB |
   | whip / zoom transition | `whoosh` / `swish` | −4 to −8 dB |
   | money figure | `cash` / `ding` | −3 to −10 dB |
   | counter start / build-up | `riser` (ends on the reveal) | −3 to −12 dB |
   | reveal, verdict, split opening | `impact` | −4 to −6 dB |
   | object lands (board item, box) | `thud` | −4 dB |
   | highlighter / handwriting | `marker` | −8 to −10 dB |

3. **Not every cut gets a sound** — about a quarter of cuts in the references carry a transient.
4. **Music:** one bed per segment, mood matched to the segment (curious / tense / uplifting / dramatic); change
   music at segment boundaries, ideally on a whoosh or impact. Fade the end; never cut music abruptly.
5. **Mix targets:** ≈ −14 LUFS integrated, ≤ −1 dBTP. fvs reaches the target with one static gain; if the voice's
   peaks prevent it, the shortfall is reported and limiting is applied only with approval
   (`storyboard.audio.limiter: true`, with `limiterApprovedBy`).

## Sources

- SFX: synthesised from scratch by `scripts/sound-design/synth.py` (original, no licence questions).
- Music: a licensed track from the user's library (registered in the licence register) or a stock source with
  a verified licence; the procedural bed is a placeholder and QC warns about it.
